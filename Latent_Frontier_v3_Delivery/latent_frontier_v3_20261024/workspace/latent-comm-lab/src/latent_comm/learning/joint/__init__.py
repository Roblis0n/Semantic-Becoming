"""L13: versioned joint phases and an actual live H37 → H38 training subgraph."""
from dataclasses import dataclass,replace,fields
from collections.abc import Mapping
import importlib
import re
from latent_comm.core import ContractError,ErrorCode,RoleView,VersionSet,Visibility
from latent_comm.core.learning import LossSpec,GradientEstimator,LossValue
from latent_comm.data.collate import RoleBatch,SupervisionBatch
from latent_comm.data.records import SupervisionView
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.safety.policy import require_research_action

COMPONENT_MODULES={'L01':'views','L02':'objects','L03':'frames','L04':'concept_questions','L05':'causal_analogy','L06':'dynamics_scales','L07':'transport','L08':'meta_rules','L09':'isa_search','L10':'worlds','L11':'uncertainty','L12':'evidence'}

@dataclass(frozen=True)
class BoundaryContract:
    source: str
    target: str
    object_type: str
    version_axes: tuple[str,...]
    scope_components: tuple[str,...]
    mode: str
    reason: str
    def __post_init__(self):
        from latent_comm.core.scopes import RESEARCH_COMPONENTS
        object.__setattr__(self,'version_axes',tuple(self.version_axes));object.__setattr__(self,'scope_components',tuple(self.scope_components))
        if not set(self.version_axes)<={f.name for f in fields(VersionSet)} or not set(self.scope_components)<=RESEARCH_COMPONENTS:raise ContractError(ErrorCode.SCOPE_VIOLATION,'joint boundaries cannot invent semantic axes or host authority')
        if not self.source or not self.target or self.source==self.target or not self.object_type or not self.version_axes or not self.scope_components or not self.reason:raise ContractError(ErrorCode.INVALID_SCHEMA,'joint boundary needs identities, type, semantic axes, scope and reason')
        if self.mode not in {'stop','serialized_recompute','policy_gradient','live_transport_update'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'joint gradient boundary must be explicitly supported')

def component_order(components):
    """Canonical order is covered by the sort-key-invariant configuration digest."""
    if not isinstance(components,Mapping) or any(not isinstance(alias,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',alias) for alias in components):raise ContractError(ErrorCode.INVALID_SCHEMA,'component aliases must be stable names')
    return tuple(sorted(components))

def prefixed_specs(alias,specs):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',alias):raise ContractError(ErrorCode.INVALID_SCHEMA,'component alias must be nonempty and cannot contain namespace separator')
    return tuple(replace(s,name=alias+'.'+s.name,parameter_owners=tuple(alias+'.'+o for o in s.parameter_owners),requires_grad_inputs=tuple(alias+'.'+i for i in s.requires_grad_inputs),stop_gradient_edges=tuple((alias+'.'+a,alias+'.'+b) for a,b in s.stop_gradient_edges)) for s in specs)

def project_component_role(batch,alias,versions):
    if not isinstance(batch,RoleBatch):raise ContractError(ErrorCode.ROLE_LEAKAGE,'joint projection requires physical role batch')
    projected=[]
    for view in batch.views:
        components=view.features.get('components')
        if not isinstance(components,Mapping) or alias not in components:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'component role projection missing: '+alias)
        raw=components[alias]
        if set(raw)!={'public_task','features','versions'}:raise ContractError(ErrorCode.ROLE_LEAKAGE,'component payload may contain only explicit role inputs and versions')
        semantic=VersionSet(**raw['versions']);axes=tuple(k for k,v in versions.as_dict().items() if v is not None)
        if not semantic.matches(versions,axes):raise ContractError(ErrorCode.VERSION_MISMATCH,'component batch semantic identity differs: '+alias)
        projected.append(RoleView(batch.role,raw['public_task'],raw['features'],semantic))
    return RoleBatch(batch.role,tuple(projected))

def project_component_supervision(batch,alias):
    if not isinstance(batch,SupervisionBatch):raise ContractError(ErrorCode.ROLE_LEAKAGE,'joint losses require a separate supervisor batch')
    values=[]
    for view in batch.views:
        raw=view.targets['components'][alias]
        if set(raw)!={'targets','valid_masks','source_kind'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'component supervision schema differs')
        values.append(SupervisionView(raw['targets'],{k:tuple(v) for k,v in raw['valid_masks'].items()},raw['source_kind']))
    return SupervisionBatch(tuple(values))

class JointStage:
    """Multiple real stages optimized in explicit phases, not fake serialized AD.

    Components receive separately projected data. They do not receive each
    other's serialized outputs as live tensors. A declared live edge is rejected
    here and must use a concrete coupled stage such as TransportPlasticityStage.
    """
    required_version_axes=('schema','task')
    def __init__(self,components,unroll_allocations,versions,*,boundaries=(),device='cpu'):
        require_research_action('model_initialize')
        if not components or set(components)!=set(unroll_allocations) or any(type(v) is not int or v<1 for v in unroll_allocations.values()):raise ContractError(ErrorCode.INVALID_SCHEMA,'every joint component needs an explicit positive unroll allocation')
        if any(b.mode=='live_transport_update' for b in boundaries):raise ContractError(ErrorCode.CONFLICT,'a live tensor edge cannot be forged through projected serialized RoleViews')
        if any(b.source not in components or b.target not in components for b in boundaries):raise ContractError(ErrorCode.UNBOUND_REFERENCE,'boundary references an absent component')
        for boundary in boundaries:
            source=components[boundary.source].versions;target=components[boundary.target].versions;source.require(*boundary.version_axes);target.require(*boundary.version_axes)
            if not source.matches(target,boundary.version_axes):raise ContractError(ErrorCode.VERSION_MISMATCH,'joint boundary needs an explicit semantic migration before training')
        self.components={alias:components[alias] for alias in component_order(components)};self.unroll_allocations={alias:unroll_allocations[alias] for alias in component_order(components)};self.versions=versions;self.device=device;self.boundaries=tuple(boundaries)
        self.loss_specs=tuple(s for alias,stage in self.components.items() for s in prefixed_specs(alias,stage.loss_specs));validate_parameter_ownership(self.parameter_groups(),self.frozen_parameters())
    def parameter_groups(self):return {alias+'.'+owner:parameters for alias,stage in self.components.items() for owner,parameters in stage.parameter_groups().items()}
    def frozen_parameters(self):return {alias+'.'+name:p for alias,stage in self.components.items() for name,p in stage.frozen_parameters().items()}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        if sum(self.unroll_allocations.values())>maximum_unroll:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'total joint unroll allocation exceeds run budget')
        outputs={}
        for alias,stage in self.components.items():
            s=project_component_role(sender,alias,stage.versions);r=project_component_role(receiver,alias,stage.versions)
            outputs[alias]=stage.forward_roles(s,r,maximum_unroll=self.unroll_allocations[alias])
        return outputs
    def losses(self,output,supervision):
        require_research_action('model_forward')
        terms={}
        for alias,stage in self.components.items():
            scoped=stage.losses(output[alias],project_component_supervision(supervision,alias))
            for spec in stage.loss_specs:
                if spec.name not in scoped:raise ContractError(ErrorCode.INVALID_SCHEMA,'component omitted declared loss: '+alias+'.'+spec.name)
                terms[alias+'.'+spec.name]=scoped[spec.name]
        return terms

COUPLED_OWNERS=('transport.transport_operator','transport.behavior_encoder','plasticity_rule_parameters')
COUPLED_SPECS=(
    LossSpec('coupled_query_full','mean_valid_query((query(theta_T(initial+transport_delta,psi))-target)^2)','held-out query errors after live transport and support-only exact unroll','valid query elements per valid episode','query target masks with nonempty support','skip_with_reason',COUPLED_OWNERS,('live_transport_update','support_gradients','rule_parameters'),(),GradientEstimator.SECOND_ORDER,'held-out query elements; equal valid episode weight'),
    LossSpec('coupled_query_first_order','mean query loss with stopped support Hessian edge','held-out query errors after live transport and first-order support unroll','valid query elements per valid episode','query target masks with nonempty support','skip_with_reason',COUPLED_OWNERS,('live_transport_update','rule_parameters'),(('support_gradients','inner_update'),),GradientEstimator.FIRST_ORDER,'held-out query elements; equal valid episode weight'),
    LossSpec('coupled_update_budget','mean(relu(raw_rule_update_norm-max_update_norm)^2)','pre-clipping norm exceedance squared','valid inner update groups','valid support/query episodes','skip_with_reason',COUPLED_OWNERS,('raw_inner_update',),(),GradientEstimator.EXACT,'inner update groups'),
    LossSpec('realized_transport','mean((Jtarget*clipped_delta-desired_behavior)^2)','post-trust-clipping behavior effect residual','shared behavior coordinates','all public anchors','skip_with_reason',COUPLED_OWNERS[:2],('clipped_transport_update',),(),GradientEstimator.EXACT,'shared behavior coordinates'))

@dataclass(frozen=True)
class CoupledOutput:
    transport: object
    initial: object
    support_inputs: object
    query_inputs: object
    target_jacobians: object
    partition_ids: tuple

class TransportPlasticityStage:
    """Concrete live subgraph of C13; symbolic provenance checks remain separate.

    Transported update → functional initial adapter → support-only H38 AST unroll
    → held-out query objective is one live graph. The source/target behavior here
    is the explicit W08 linear family, not an unbound neural model claim.
    """
    def __init__(self,transport,raw_rate,raw_memory,raw_clip,versions,*,inner_steps=3,max_update_norm=1.,trust_radius=1.,estimator='exact_unroll',device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.learning.meta_rules import rule_ast
        from latent_comm.mechanisms.h38_plasticity.types import PlasticityProgram
        self.transport=transport;self.raw_rate=raw_rate;self.raw_memory=raw_memory;self.raw_clip=raw_clip;self.versions=versions;self.device=device;self.trust_radius=trust_radius;self.estimator=estimator
        if trust_radius<=0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'positive local transport trust radius required')
        self.program=PlasticityProgram(rule_ast(),('adapter.theta',),max_update_norm,inner_steps,inner_steps,versions.isa,estimator)
        query_name='coupled_query_full' if estimator=='exact_unroll' else 'coupled_query_first_order'
        self.loss_specs=prefixed_specs('transport',transport.loss_specs)+tuple(replace(s,parameter_owners=('plasticity_rule_parameters',)) if s.name=='coupled_update_budget' and estimator=='first_order' else s for s in COUPLED_SPECS if s.name in {query_name,'coupled_update_budget','realized_transport'});validate_parameter_ownership(self.parameter_groups(),self.frozen_parameters())
    def parameter_groups(self):return {**{'transport.'+owner:params for owner,params in self.transport.parameter_groups().items()},'plasticity_rule_parameters':{'raw_rate':self.raw_rate,'raw_memory':self.raw_memory,'raw_clip':self.raw_clip}}
    def frozen_parameters(self):return {'transport.'+name:p for name,p in self.transport.frozen_parameters().items()}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        from latent_comm.learning.meta_rules import validate_episode_ids
        if maximum_unroll<=self.program.inner_steps:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'joint budget must cover both transport solve and support unroll')
        result=self.transport.forward_roles(sender,receiver,maximum_unroll=maximum_unroll-self.program.inner_steps)
        initial=tensor_field(receiver,'initial_adapter',device=self.device,public=True);support=tensor_field(receiver,'support_inputs',device=self.device);query=tensor_field(receiver,'query_inputs',device=self.device);jacobian=tensor_field(receiver,'target_jacobian',device=self.device);ids=[]
        for view in receiver.views:
            support_id=view.public_task['support_partition'];query_id=view.public_task['query_partition'];validate_episode_ids(support_id,query_id);ids.append((support_id,query_id))
        if initial.shape!=result.updates.shape or support.ndim!=3 or query.ndim!=3 or support.shape[0]!=initial.shape[0] or query.shape[0]!=initial.shape[0] or support.shape[-1]!=initial.shape[-1] or query.shape[-1]!=initial.shape[-1]:raise ContractError(ErrorCode.INVALID_SHAPE,'coupled support/query features must use the transported parameter scope')
        return CoupledOutput(result,initial,support,query,jacobian,tuple(ids))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h38_plasticity.adapter import tensor_interpret
        from latent_comm.mechanisms.h38_plasticity.types import SupportBatch,QueryBatch
        from latent_comm.mechanisms.h38_plasticity.reference import validate_partitions
        terms={'transport.'+name:value for name,value in self.transport.losses(output.transport,supervision).items()}
        support_targets,support_mask=tensor_target(supervision,'support_targets',device=self.device);query_targets,query_mask=tensor_target(supervision,'query_targets',device=self.device)
        if support_targets.shape!=output.support_inputs.shape[:-1] or query_targets.shape!=output.query_inputs.shape[:-1]:raise ContractError(ErrorCode.INVALID_SHAPE,'coupled target partitions do not align')
        norm=output.transport.updates.norm(dim=-1,keepdim=True);delta=output.transport.updates*(self.trust_radius/norm.clamp_min(1e-12)).clamp(max=1.)
        realized=(output.target_jacobians@delta.unsqueeze(-1)).squeeze(-1)
        terms['realized_transport']=(realized-output.transport.desired).square().mean()
        psi={'rate':-.1*self.raw_rate.exp(),'memory_decay':self.raw_memory.sigmoid(),'clip':self.raw_clip.exp()};queries=[];norms=[]
        for i in range(output.initial.shape[0]):
            if not bool(support_mask[i].any()) or not bool(query_mask[i].any()):continue
            support=SupportBatch(output.support_inputs[i],support_targets[i],output.partition_ids[i][0]);query=QueryBatch(output.query_inputs[i],query_targets[i],output.partition_ids[i][1]);validate_partitions(support,query)
            theta=output.initial[i]+delta[i]
            if not theta.requires_grad:theta=theta.detach().requires_grad_(True)
            memory=torch.zeros_like(theta)
            for _ in range(self.program.inner_steps):
                error=(support.inputs@theta-support.targets).square();loss=error.masked_select(support_mask[i]).mean()
                gradient=torch.autograd.grad(loss,theta,create_graph=self.estimator=='exact_unroll',allow_unused=False)[0]
                if self.estimator=='first_order':gradient=gradient.detach()
                environment={'gradient':gradient,'theta':theta,'memory':memory,'diagonal':gradient.square(),'mask':torch.ones_like(theta)};updated_memory={}
                update=tensor_interpret(self.program.ast,environment,psi,updated_memory);norms.append(update.norm());update=update*(self.program.max_update_norm/update.norm().clamp_min(1e-12)).clamp(max=1.)
                theta=theta+update;memory=updated_memory.get('memory',memory)
            queries.append((query.inputs@theta-query.targets).square().masked_select(query_mask[i]).mean())
        query_name='coupled_query_full' if self.estimator=='exact_unroll' else 'coupled_query_first_order'
        terms[query_name]=torch.stack(queries).mean() if queries else LossValue(0.,0.,None,True,'no valid paired support/query episodes')
        terms['coupled_update_budget']=torch.stack([(n-self.program.max_update_norm).clamp_min(0).square() for n in norms]).mean() if norms else LossValue(0.,0.,None,True,'no raw inner update groups')
        return terms

def build_stage(variant,versions,*,components=None,boundaries=(),inner_steps=3,trust_radius=1.,max_update_norm=1.,solver_steps=8,source_parameters=2,target_parameters=2,behavior_coordinates=2,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    if variant=='stagewise':
        if not isinstance(components,dict):raise ContractError(ErrorCode.INVALID_SCHEMA,'stagewise joint mode needs named concrete component bindings')
        stages={};allocations={}
        for alias in component_order(components):
            entry=components[alias]
            if entry['stage'] not in COMPONENT_MODULES:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'component is not a registered L-stage')
            module=importlib.import_module('latent_comm.learning.'+COMPONENT_MODULES[entry['stage']]);stages[alias]=module.build_stage(entry['variant'],VersionSet(**entry['versions']),device=device,**entry.get('dimensions',{}));allocations[alias]=entry['maximum_unroll']
        return JointStage(stages,allocations,versions,boundaries=tuple(BoundaryContract(**b) for b in boundaries),device=device)
    if variant in {'transport_meta_full','transport_meta_first_order'}:
        from latent_comm.learning.transport import build_stage as build_transport
        transport=build_transport('linear_behavior',versions,source_parameters=source_parameters,target_parameters=target_parameters,behavior_coordinates=behavior_coordinates,solver_steps=solver_steps,device=device,dtype=dtype)
        def p():return torch.nn.Parameter(torch.zeros((),device=device,dtype=getattr(torch,dtype)))
        return TransportPlasticityStage(transport,p(),p(),p(),versions,inner_steps=inner_steps,trust_radius=trust_radius,max_update_norm=max_update_norm,estimator='exact_unroll' if variant=='transport_meta_full' else 'first_order',device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown joint training mode')
