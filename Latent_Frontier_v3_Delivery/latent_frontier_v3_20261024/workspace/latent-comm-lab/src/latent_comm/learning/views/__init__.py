"""L01: physically isolated role encoders, operator interface and exact dual channel."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,ErrorCode,Visibility,VersionSet
from latent_comm.core.learning import masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import RoleTensors,validate_parameter_ownership
from latent_comm.safety.policy import require_research_action
from latent_comm.mechanisms.h16_legacy.losses import LEDGER as H16_LEDGER
DUAL_LOSS_SPECS=tuple(replace(s,parameter_owners=('mechanism_writer','mechanism_reader','symbol_predictor')) if s.name=='symbol_structure' else replace(s,parameter_owners=('mechanism_writer','mechanism_reader')) if s.name=='conflict' else s for s in H16_LEDGER)

def checked_symbol_packet(sender_view,receiver_view):
    """Resolve typed, scoped role data before any learned dual-channel fusion."""
    import json
    from latent_comm.core import ObjectRef,ObjectRegistry,RegisteredObject,Scope
    from latent_comm.mechanisms.h16_legacy.reference import parse_symbols,resolve_latent
    packet=parse_symbols(json.dumps(sender_view.features['symbol_packet'],default=dict,allow_nan=False))
    if not packet.versions.matches(sender_view.versions,('ontology','task','evidence')) or not packet.versions.matches(receiver_view.versions,('ontology','task','evidence')):raise ContractError(ErrorCode.VERSION_MISMATCH,'symbol packet is stale for this role batch')
    registry=ObjectRegistry();actor='learning_receiver';axes=('ontology','task','evidence')
    for name,record in receiver_view.features.get('verified_target_refs',{}).items():
        registry.register(RegisteredObject(ObjectRef(name),record['type_name'],record['value'],VersionSet(**record['versions']),axes,Scope(**record['scope']),Visibility(record['visibility'])))
    sources=receiver_view.features['verified_symbol_sources']
    for symbol in packet.symbols:
        source=sources.get(symbol.source.value)
        if source is None or set(source)!={'name','kind','value','unit','origin_role','versions','scope','visibility'}:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'symbol source is not a complete scoped registry record')
        value={key:source[key] for key in ('name','kind','value','unit','origin_role')}
        registry.register(RegisteredObject(symbol.source,'exact_symbol_source',value,VersionSet(**source['versions']),axes,Scope(**source['scope']),Visibility(source['visibility'])))
        verified=registry.resolve(symbol.source,expected_type='exact_symbol_source',versions=packet.versions,actor=actor,role=Visibility.RECEIVER)
        if any(verified[key]!=getattr(symbol,key) for key in verified):raise ContractError(ErrorCode.CONFLICT,'exact symbol contradicts its registry source')
        if symbol.target_ref is not None:
            target=receiver_view.features.get('verified_target_refs',{}).get(symbol.target_ref.value)
            if target is None:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'entity/reference target was not independently resolved')
            registry.resolve(symbol.target_ref,expected_type=target['type_name'],versions=packet.versions,actor=actor,role=Visibility.RECEIVER)
    if packet.latent_handle.value!=receiver_view.features['latent_handle']:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'exact and latent channel handles do not match')
    registry.register(RegisteredObject(packet.latent_handle,'latent_slots',receiver_view.features['latent_slots'],packet.versions,axes,Scope(**receiver_view.features['latent_scope']),Visibility.RECEIVER))
    resolve_latent(packet,registry,actor=actor,expected_type='latent_slots')
    return packet

@dataclass(frozen=True)
class OperatorOutput:
    predicted: object
    composed: object
    target: object
    composition_target: object
    task: object

class RoleOperatorStage:
    """W01 source-coordinate interface; frame transport itself belongs to L03."""
    def __init__(self,writer_weight,writer_bias,read,write,versions,*,rank,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h01_legacy.losses import LEDGER
        self.writer_weight=writer_weight;self.writer_bias=writer_bias;self.read=read;self.write=write;self.versions=versions;self.rank=rank;self.device=device;self.loss_specs=LEDGER;validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'mechanism_writer':{'factor_weight':self.writer_weight,'factor_bias':self.writer_bias},'mechanism_reader':{'read_matrix':self.read,'write_matrix':self.write}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h01_legacy.adapter import generate_operator,tensor_operator
        if maximum_unroll<2:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'operator composition needs two finite applications')
        operation=tensor_field(sender,'operator',device=self.device);state=tensor_field(receiver,'state',device=self.device);readout=tensor_field(receiver,'readout',device=self.device)
        features=operation.flatten(1);encoded=RoleTensors(sender,{'operator_features':features},{'operator_features':('operator',)})
        factors=generate_operator(encoded.values['operator_features'],self.writer_weight,self.writer_bias,dimension=self.read.shape[0],rank=self.rank)
        local=state@self.read.T;updated=tensor_operator(local,*factors,nonlinearity='identity');prediction=state+(updated-local)@self.write.T
        second_local=prediction@self.read.T;second=tensor_operator(second_local,*factors,nonlinearity='identity');composed=prediction+(second-second_local)@self.write.T
        target=(operation@state.unsqueeze(-1)).squeeze(-1);composition=(operation@target.unsqueeze(-1)).squeeze(-1);task=(readout@prediction.unsqueeze(-1)).squeeze(-1)
        return OperatorOutput(prediction,composed,target,composition,task)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h01_legacy.losses import tensor_losses
        target,mask=tensor_target(supervision,'source_result',device=self.device);task=masked_tensor_mean((output.task-target).square(),mask,zero_valid_policy='differentiable_zero')
        terms=tensor_losses(output.predicted,output.target,output.composed,output.composition_target,torch.ones_like(output.predicted,dtype=torch.bool),torch.ones_like(output.composed,dtype=torch.bool),task_loss=task)
        return {spec.name:terms[spec.name] for spec in self.loss_specs}

@dataclass(frozen=True)
class DualOutput:
    task: object
    symbols: object
    conflicts: object
    packets: tuple

class DualChannelStage:
    """H01-generated latent operation plus H16 exact-symbol cross attention.

    Exact strings/decimal/unit/source identities never become predicted strings.
    A category classifier and conflict detector are auxiliary, not authority.
    """
    def __init__(self,writer_weight,writer_bias,query,key,value,task_readout,symbol_classifier,conflict_head,versions,*,rank,device='cpu'):
        require_research_action('model_initialize')
        self.writer_weight=writer_weight;self.writer_bias=writer_bias;self.query=query;self.key=key;self.value=value;self.task_readout=task_readout;self.symbol_classifier=symbol_classifier;self.conflict_head=conflict_head;self.versions=versions;self.rank=rank;self.device=device;self.loss_specs=DUAL_LOSS_SPECS;validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'mechanism_writer':{'factor_weight':self.writer_weight,'factor_bias':self.writer_bias},'mechanism_reader':{'query_projection':self.query,'key_projection':self.key,'value_projection':self.value,'task_readout':self.task_readout,'conflict_head':self.conflict_head},'symbol_predictor':{'classifier':self.symbol_classifier}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h01_legacy.adapter import generate_operator,tensor_operator
        from latent_comm.mechanisms.h16_legacy.adapter import tensor_dual_fusion
        features=tensor_field(sender,'sender_features',device=self.device);states=tensor_field(receiver,'latent_slots',device=self.device);symbol_features=tensor_field(sender,'symbol_features',device=self.device);symbol_mask=tensor_field(sender,'symbol_mask',device=self.device,dtype='bool')
        RoleTensors(sender,{'latent_features':features,'symbol_features':symbol_features},{'latent_features':('sender_features',),'symbol_features':('symbol_features',)})
        if maximum_unroll<1 or states.ndim!=3:raise ContractError(ErrorCode.INVALID_SHAPE,'one finite latent operation and [B,S,D] role state required')
        factors=generate_operator(features,self.writer_weight,self.writer_bias,dimension=states.shape[-1],rank=self.rank);tasks=[];categories=[];conflicts=[];packets=[]
        for row,(s,r) in enumerate(zip(sender.views,receiver.views)):
            packet=checked_symbol_packet(s,r);slots=states[row];n=slots.shape[0]
            expanded=tuple(f[row:row+1].expand(n,*f.shape[1:]) for f in factors);updated=tensor_operator(slots,*expanded).unsqueeze(0)
            context,unchanged=tensor_dual_fusion(updated,symbol_features[row:row+1],symbol_mask[row:row+1],self.query,self.key,self.value,verified_symbol_packet=packet)
            pooled=context.mean(1);symbol_projection=symbol_features[row]@self.value.T;pair=torch.cat((pooled.expand(symbol_projection.shape[0],-1),symbol_projection),-1)
            tasks.append((pooled@self.task_readout.T).squeeze(0));categories.append(pair@self.symbol_classifier.T);conflicts.append((pair@self.conflict_head).reshape(-1));packets.append(unchanged)
        return DualOutput(torch.stack(tasks),torch.stack(categories),torch.stack(conflicts),tuple(packets))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h16_legacy.losses import tensor_losses
        task,task_mask=tensor_target(supervision,'task_target',device=self.device);symbols,symbol_mask=tensor_target(supervision,'symbol_categories',device=self.device,dtype='int64');conflicts,conflict_mask=tensor_target(supervision,'symbol_conflicts',device=self.device)
        task_loss=masked_tensor_mean((output.task-task).square(),task_mask,zero_valid_policy='differentiable_zero')
        terms=tensor_losses(output.symbols,symbols,symbol_mask,output.conflicts,conflicts,conflict_mask,latent_task_loss=task_loss)
        return {spec.name:terms[spec.name] for spec in self.loss_specs}

def inject_role_receiver(stage,model,capabilities,sender,receiver,*,injection='prefix',layer=None,slot_mask=None):
    """Real future backend path, never a detached serialized latent substitute."""
    require_research_action('model_forward')
    from latent_comm.backends.capabilities import ModelInputs
    from latent_comm.mechanisms.h01_legacy.adapter import generate_operator,apply_to_receiver
    capabilities.require('input_gradients');capabilities.require(injection)
    features=tensor_field(sender,'operator',device=stage.device).flatten(1);state=tensor_field(receiver,'state',device=stage.device)
    ids=tensor_field(receiver,'input_ids',device=stage.device,dtype='int64');mask=tensor_field(receiver,'attention_mask',device=stage.device,dtype='bool');inputs=ModelInputs(receiver.views,{'input_ids':ids,'attention_mask':mask})
    factors=generate_operator(features,stage.writer_weight,stage.writer_bias,dimension=stage.read.shape[0],rank=stage.rank)
    return apply_to_receiver(state,stage.read,stage.write,factors,model,capabilities=capabilities,inputs=inputs,injection=injection,layer=layer,slot_mask=slot_mask)

def build_stage(variant,versions,*,state_dim=2,sender_features=4,rank=1,symbol_features=4,task_outputs=1,symbol_categories=4,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    if not 0<rank<=state_dim:raise ContractError(ErrorCode.INVALID_SHAPE,'low rank within state dimension required')
    def p(value):return torch.nn.Parameter(torch.as_tensor(value,device=device,dtype=getattr(torch,dtype)))
    width=2*state_dim*rank+rank+1;weight=p(torch.zeros(width,sender_features));bias=torch.zeros(width);factor=torch.eye(state_dim,rank).flatten()*.1;bias[:state_dim*rank]=factor;bias[state_dim*rank:2*state_dim*rank]=factor;bias=p(bias)
    if variant=='role_operator':return RoleOperatorStage(weight,bias,p(torch.eye(state_dim)),p(torch.eye(state_dim)),versions,rank=rank,device=device)
    if variant=='dual_channel':return DualChannelStage(weight,bias,p(torch.eye(state_dim)),p(torch.eye(state_dim,symbol_features)),p(torch.eye(state_dim,symbol_features)),p(torch.eye(task_outputs,state_dim)),p(torch.zeros(symbol_categories,2*state_dim)),p(torch.zeros(2*state_dim)),versions,rank=rank,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown role interface stage')
