"""L02: ordered operator programs, local response capsules and sequence beliefs."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action

@dataclass(frozen=True)
class OperatorOutput:
    first: object
    composed: object
    task: object

class OperatorProgramStage:
    """Distinct sender programs applied in declared order to receiver state."""
    def __init__(self,weight,bias,read,write,versions,*,rank,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h01_legacy.losses import LEDGER
        self.weight=weight;self.bias=bias;self.read=read;self.write=write;self.versions=versions;self.rank=rank;self.device=device;self.loss_specs=LEDGER;validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'mechanism_writer':{'factor_weight':self.weight,'factor_bias':self.bias},'mechanism_reader':{'read_matrix':self.read,'write_matrix':self.write}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h01_legacy.adapter import generate_operator,tensor_operator
        programs=tensor_field(sender,'operator_features',device=self.device);state=tensor_field(receiver,'state',device=self.device);readout=tensor_field(receiver,'readout',device=self.device)
        if programs.ndim!=3 or not 1<=programs.shape[1]<=maximum_unroll:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'explicit bounded ordered operator program required')
        first=None
        for features in programs.unbind(1):
            factors=generate_operator(features,self.weight,self.bias,dimension=self.read.shape[0],rank=self.rank);local=state@self.read.T;updated=tensor_operator(local,*factors);state=state+(updated-local)@self.write.T
            if first is None:first=state
        return OperatorOutput(first,state,(readout@state.unsqueeze(-1)).squeeze(-1))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h01_legacy.losses import tensor_losses
        target,valid=tensor_target(supervision,'first_operator_target',device=self.device);composition,composition_valid=tensor_target(supervision,'composition_target',device=self.device);task_target,task_mask=tensor_target(supervision,'task_target',device=self.device)
        task=masked_tensor_mean((output.task-task_target).square(),task_mask,zero_valid_policy='differentiable_zero');terms=tensor_losses(output.first,target,output.composed,composition,valid,composition_valid,task_loss=task)
        return {s.name:terms[s.name] for s in self.loss_specs}

@dataclass(frozen=True)
class ResponseOutput:
    prediction: object
    locality: object
    refresh: object
    task: object

class ResponseStage:
    def __init__(self,weight,bias,refresh_weight,refresh_bias,readout,versions,*,condition_dim,output_dim,rank,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h02_legacy.losses import LEDGER
        self.weight=weight;self.bias=bias;self.refresh_weight=refresh_weight;self.refresh_bias=refresh_bias;self.readout=readout;self.versions=versions;self.condition_dim=condition_dim;self.output_dim=output_dim;self.rank=rank;self.device=device
        self.loss_specs=tuple(replace(s,parameter_owners=('mechanism_writer',)) if s.name=='response' else s for s in LEDGER);validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'mechanism_writer':{'factor_weight':self.weight,'factor_bias':self.bias,'refresh_weight':self.refresh_weight,'refresh_bias':self.refresh_bias},'mechanism_reader':{'response_readout':self.readout}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h02_legacy.adapter import predict_response_factors,tensor_predict
        features=tensor_field(sender,'response_features',device=self.device);anchor=tensor_field(sender,'anchor',device=self.device);query=tensor_field(receiver,'query',device=self.device)
        for s,r in zip(sender.views,receiver.views):
            kind=s.public_task['response_kind'];conditions=s.public_task['observation_conditions']
            if kind not in {'observational','structural_intervention'} or kind=='structural_intervention' and not conditions or r.public_task['response_kind']!=kind:raise ContractError(ErrorCode.INVALID_SCHEMA,'derivative response needs explicit observational or assumed structural semantics')
        directions,left,base,radius=predict_response_factors(features,self.weight,self.bias,condition_dim=self.condition_dim,output_dim=self.output_dim,rank=self.rank)
        prediction,valid=tensor_predict(anchor,base,left,directions,query,radius)
        diagnostics=torch.cat((query-anchor,((query-anchor).norm(dim=-1)/radius).unsqueeze(-1)),-1);refresh=diagnostics@self.refresh_weight+self.refresh_bias
        return ResponseOutput(prediction,valid,refresh,prediction@self.readout.T)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h02_legacy.losses import tensor_losses
        target,valid=tensor_target(supervision,'response_target',device=self.device);refresh,refresh_mask=tensor_target(supervision,'refresh_target',device=self.device);task_target,task_mask=tensor_target(supervision,'task_target',device=self.device)
        valid=valid&output.locality.unsqueeze(-1);task_mask=task_mask&output.locality.unsqueeze(-1)
        task=masked_tensor_mean((output.task-task_target).square(),task_mask,zero_valid_policy='differentiable_zero');terms=tensor_losses(output.prediction,target,valid,output.refresh,refresh,refresh_mask,task_loss=task)
        return {s.name:terms[s.name] for s in self.loss_specs}

def acquire_local_response(response_function,anchor,directions,*,method,step=.001):
    """Future exact JVP and central finite-difference alternatives, explicitly named."""
    require_research_action('model_forward')
    from latent_comm.mechanisms.h02_legacy.adapter import acquire_response
    return acquire_response(response_function,anchor,directions,method=method,step=step)

@dataclass(frozen=True)
class BeliefOutput:
    branches: object
    log_weights: object
    context: object
    maximum_unroll: int
    semantic_domains: tuple
    ontology_domains: tuple
    unknown_mask: object

class BeliefStage:
    """Finite categorical autoregressive decoder conditioned on distinct branches.

    Teacher-forced previous tokens are supplied inside losses, never projected
    into sender or receiver data. No target's current/future token affects its
    own conditional logits. Shared tokenizer semantics are explicit.
    """
    def __init__(self,branch_projection,branch_offsets,weight_head,decoder,transition,context_decoder,versions,*,tokenizer_contracts,bos_id=0,generation_mode='sequence_mixture',device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h03_legacy.losses import LEDGER
        if not 0<=bos_id<decoder.shape[0]:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'BOS outside declared vocabulary')
        if generation_mode not in {'sequence_mixture','select_then_generate','rerank'}:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'explicit belief generation mode required')
        self.branch_projection=branch_projection;self.branch_offsets=branch_offsets;self.weight_head=weight_head;self.decoder=decoder;self.transition=transition;self.context_decoder=context_decoder;self.versions=versions;self.tokenizer_contracts=tuple(tokenizer_contracts);self.bos_id=bos_id;self.generation_mode=generation_mode;self.device=device;self.loss_specs=LEDGER
        if len(self.tokenizer_contracts)!=branch_offsets.shape[0]:raise ContractError(ErrorCode.INVALID_SHAPE,'one tokenizer contract per branch')
        for contract in self.tokenizer_contracts[1:]:self.tokenizer_contracts[0].require_same_vocabulary(contract)
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'mechanism_writer':{'branch_projection':self.branch_projection,'branch_offsets':self.branch_offsets,'weight_head':self.weight_head},'mechanism_reader':{'branch_decoder':self.decoder,'token_transition':self.transition,'context_decoder':self.context_decoder}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        features=tensor_field(sender,'branch_features',device=self.device);context=tensor_field(receiver,'context_features',device=self.device)
        if features.ndim!=3 or features.shape[1]!=self.branch_offsets.shape[0] or context.ndim!=2:raise ContractError(ErrorCode.INVALID_SHAPE,'distinct branch features[B,K,F] and receiver context[B,C] required')
        semantic_domains=[];ontology_domains=[];unknown=[]
        for s in sender.views:
            domains=tuple(s.public_task['branch_domains']);ontologies=tuple(s.public_task['branch_ontologies'])
            ids=tuple(s.public_task['branch_ids']);missing=tuple(s.public_task['branch_unknown'])
            if len(ids)!=features.shape[1] or len(set(ids))!=len(ids) or len(missing)!=len(ids) or any(type(x) is not bool for x in missing):raise ContractError(ErrorCode.INVALID_SCHEMA,'branch identity and unknown-support status must remain explicit')
            semantic_domains.append(domains);ontology_domains.append(ontologies);unknown.append(missing)
            if len(domains)!=features.shape[1] or len(set(domains))!=1 or len(set(ontologies))!=1 or len(ontologies)!=len(domains):raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'coverage requires an explicitly common semantic/ontology domain, not a forced average of incomparable branches')
        branches=features@self.branch_projection.T+self.branch_offsets.unsqueeze(0);weights=features@self.weight_head
        return BeliefOutput(branches,weights,context,maximum_unroll,tuple(semantic_domains),tuple(ontology_domains),torch.as_tensor(unknown,device=self.device,dtype=torch.bool))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h03_legacy.adapter import mixture_sequence_logprob,matched_branch_cost
        from latent_comm.mechanisms.h03_legacy.losses import tensor_losses
        tokens,token_mask=tensor_target(supervision,'target_tokens',device=self.device,dtype='int64')
        if tokens.ndim!=2 or tokens.shape[1]>output.maximum_unroll or tokens.shape[1]<1:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'bounded nonempty target sequence required')
        if bool(((~token_mask[:,:-1])&token_mask[:,1:]).any()):raise ContractError(ErrorCode.INVALID_SCHEMA,'causal targets require contiguous prefix then right padding')
        if bool((((tokens<0)|(tokens>=self.decoder.shape[0]))&token_mask).any()):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'valid token outside declared categorical vocabulary')
        safe=torch.where(token_mask,tokens,torch.zeros_like(tokens));previous=torch.cat((torch.full_like(safe[:,:1],self.bos_id),safe[:,:-1]),1)
        # First-order Markov categorical conditionals; no current/future teacher
        # token enters the logits at its own position.
        base=output.branches@self.decoder.T+(output.context@self.context_decoder.T).unsqueeze(1)
        logits=base.unsqueeze(2)+self.transition[previous].unsqueeze(1)
        sequence=mixture_sequence_logprob(logits,tokens,token_mask,output.log_weights,tokenizer_contracts=self.tokenizer_contracts)
        calibration,calibration_mask=tensor_target(supervision,'branch_probabilities',device=self.device);states,state_mask=tensor_target(supervision,'target_branch_states',device=self.device);assignment,assignment_mask=tensor_target(supervision,'matched_target_indices',device=self.device,dtype='int64')
        if bool((calibration<0).any()) or not torch.allclose(calibration.sum(-1),torch.ones_like(calibration[:,0])):raise ContractError(ErrorCode.INVALID_SCHEMA,'calibration weights must be a declared normalized candidate distribution')
        for row,view in enumerate(supervision.views):
            if view.targets['matching_verified'] is not True:raise ContractError(ErrorCode.INVALID_SCHEMA,'coverage assignments must be independently checked against compatible branch domains')
            target_domains=tuple(view.targets['target_branch_domains']);target_ontologies=tuple(view.targets['target_branch_ontologies'])
            if len(target_domains)!=states.shape[1] or len(target_ontologies)!=states.shape[1]:raise ContractError(ErrorCode.INVALID_SHAPE,'target branch semantics must align with states')
            selected=[]
            for k in range(assignment.shape[1]):
                if bool(assignment_mask[row,k]) and not bool(output.unknown_mask[row,k]):
                    j=int(assignment[row,k].detach())
                    if not 0<=j<states.shape[1] or target_domains[j]!=output.semantic_domains[row][k] or target_ontologies[j]!=output.ontology_domains[row][k]:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'matched branch lacks a common semantic projection')
                    selected.append(j)
            if len(selected)!=len(set(selected)):raise ContractError(ErrorCode.INVALID_SCHEMA,'coverage matching must be one-to-one over represented branches')
        safe_assignment=assignment.clamp(0,states.shape[1]-1);matched_target_valid=state_mask.all(-1).gather(1,safe_assignment);coverage_valid=assignment_mask&matched_target_valid&~output.unknown_mask
        cost=matched_branch_cost(output.branches,states,assignment,coverage_valid)
        terms=tensor_losses(sequence,token_mask.any(-1),output.log_weights,calibration,calibration_mask,cost,coverage_valid)
        return {s.name:terms[s.name] for s in self.loss_specs}
    def generate(self,output,*,max_steps,eos_id):
        require_research_action('model_generate')
        import torch
        from latent_comm.mechanisms.h03_legacy.adapter import generate_branches
        base=output.branches@self.decoder.T+(output.context@self.context_decoder.T).unsqueeze(1)
        def branch_step(history):
            previous=history[-1] if history else torch.full((base.shape[0],),self.bos_id,device=self.device,dtype=torch.long)
            return base+self.transition[previous].unsqueeze(1)
        def branch_generate(selected,steps):
            row=torch.arange(base.shape[0],device=self.device);previous=torch.full_like(selected,self.bos_id);alive=torch.ones_like(selected,dtype=torch.bool);tokens=[]
            for _ in range(steps):
                logits=base[row,selected]+self.transition[previous];token=logits.argmax(-1);token=torch.where(alive,token,torch.full_like(token,eos_id));tokens.append(token);alive=alive&(token!=eos_id);previous=token
                if not bool(alive.any()):break
            return torch.stack(tokens,1)
        return generate_branches(output.log_weights,branch_step,branch_generate,mode=self.generation_mode,max_steps=min(max_steps,output.maximum_unroll),eos_id=eos_id,tokenizer_contracts=self.tokenizer_contracts)

def build_stage(variant,versions,*,state_dim=2,feature_dim=4,rank=1,condition_dim=2,response_dim=2,task_outputs=1,branches=2,vocabulary=4,context_dim=2,generation_mode='sequence_mixture',device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    from latent_comm.backends.behavior import TokenizerContract
    def p(value):return torch.nn.Parameter(torch.as_tensor(value,device=device,dtype=getattr(torch,dtype)))
    if variant=='operators':
        width=2*state_dim*rank+rank+1;bias=torch.zeros(width);seed=.1*torch.eye(state_dim,rank).flatten();bias[:state_dim*rank]=seed;bias[state_dim*rank:2*state_dim*rank]=seed
        return OperatorProgramStage(p(torch.zeros(width,feature_dim)),p(bias),p(torch.eye(state_dim)),p(torch.eye(state_dim)),versions,rank=rank,device=device)
    if variant=='responses':
        width=(response_dim+condition_dim)*rank+response_dim+1;bias=torch.zeros(width);bias[:response_dim*rank]=torch.eye(response_dim,rank).flatten()*.1;bias[response_dim*rank:(response_dim+condition_dim)*rank]=torch.eye(condition_dim,rank).flatten()*.1
        return ResponseStage(p(torch.zeros(width,feature_dim)),p(bias),p(torch.zeros(condition_dim+1)),p(0.),p(torch.eye(task_outputs,response_dim)),versions,condition_dim=condition_dim,output_dim=response_dim,rank=rank,device=device)
    if variant=='beliefs':
        contract=TokenizerContract('finite-symbols','v1','finite-vocabulary:'+str(vocabulary),'one-symbol-one-index:v1')
        return BeliefStage(p(torch.eye(state_dim,feature_dim)),p(torch.arange(branches*state_dim).reshape(branches,state_dim)/max(1,branches*state_dim)),p(torch.zeros(feature_dim)),p(torch.eye(vocabulary,state_dim)),p(torch.zeros(vocabulary,vocabulary)),p(torch.zeros(vocabulary,context_dim)),versions,tokenizer_contracts=(contract,)*branches,generation_mode=generation_mode,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown object learning stage')
