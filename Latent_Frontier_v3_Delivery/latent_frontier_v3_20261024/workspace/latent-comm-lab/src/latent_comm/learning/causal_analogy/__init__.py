"""L05: type-constrained analogy and structural, shared-noise causal grafting."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import LossSpec,GradientEstimator,masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action
from latent_comm.mechanisms.h30_analogy.losses import LOSS_SPECS as H30_LOSS_SPECS
ANALOGY_LOSS_SPECS=tuple(replace(s,parameter_owners=('object_map',)) if s.name=='matching' else replace(s,parameter_owners=('object_map','operation_map','target_readout')) if s.name=='behavior' else s for s in H30_LOSS_SPECS)

def module_coefficient(view,name):
    value=view.features[name]
    if not isinstance(value,(list,tuple)) or len(value)!=2 or value[0]!='mul_add_noise':raise ContractError(ErrorCode.INVALID_SCHEMA,'W05 requires an explicit mul_add_noise module')
    from latent_comm.core.finite import finite_scalar
    return finite_scalar(value[1])

def noise_atoms(contract):
    if contract=='shared_bit':return ((0.,0.,.5),(1.,1.,.5))
    if contract=='independent_bits':return ((0.,0.,.25),(0.,1.,.25),(1.,0.,.25),(1.,1.,.25))
    raise ContractError(ErrorCode.INVALID_SCHEMA,'noise identities must be shared or explicitly independent')

@dataclass(frozen=True)
class AnalogyOutput:
    matching: object
    commuting: object
    behavior: object

class AnalogyStage:
    """Finite-dimensional learned morphism, not an embedding similarity stand-in.

    Graph records explicitly expose source_operator[B,S,S], target_operators
    [B,K,T,T], type_compatible[B,S,T], state[B,S], readout[B,O,T]. The
    type-compatible partial subdomain must be projected before batching.
    """
    def __init__(self,matching_logits,operation_logits,readout_delta,versions,*,device='cpu'):
        require_research_action('model_initialize')
        self.matching_logits=matching_logits;self.operation_logits=operation_logits;self.readout_delta=readout_delta;self.versions=versions;self.device=device
        self.loss_specs=ANALOGY_LOSS_SPECS
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'object_map':{'logits':self.matching_logits},'operation_map':{'logits':self.operation_logits},'target_readout':{'delta':self.readout_delta}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h30_analogy.adapter import soft_matching,tensor_commuting_residual
        a=tensor_field(sender,'source_operator',device=self.device);bs=tensor_field(receiver,'target_operators',device=self.device);mask=tensor_field(receiver,'type_compatible',device=self.device,dtype='bool');state=tensor_field(sender,'state',device=self.device);r=tensor_field(receiver,'readout',device=self.device)
        if bs.ndim!=4 or self.operation_logits.shape!=(bs.shape[1],):raise ContractError(ErrorCode.INVALID_SHAPE,'target operation candidates[B,K,T,T] and K logits required')
        p=soft_matching(self.matching_logits.unsqueeze(0).expand(mask.shape[0],-1,-1),mask,iterations=min(maximum_unroll,32));p=p/p.sum(-1,keepdim=True);f=p.transpose(-1,-2)
        b=(bs*self.operation_logits.softmax(-1).reshape(1,-1,1,1)).sum(1)
        commuting=tensor_commuting_residual(f,a,b)
        behavior=((r+self.readout_delta.unsqueeze(0))@b@f@state.unsqueeze(-1)).squeeze(-1)
        return AnalogyOutput(p,commuting,behavior)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h30_analogy.losses import tensor_losses
        match,match_mask=tensor_target(supervision,'matched_target',device=self.device,dtype='int64');behavior,behavior_mask=tensor_target(supervision,'target_behavior',device=self.device);_,square_mask=tensor_target(supervision,'commuting_reference',device=self.device)
        if bool(((match<0)|(match>=output.matching.shape[-1])).logical_and(match_mask).any()):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'valid object match target outside target domain')
        probability=output.matching.gather(-1,match.clamp(0,output.matching.shape[-1]-1).unsqueeze(-1)).squeeze(-1)
        return tensor_losses(probability,output.commuting,output.behavior-behavior,(match_mask,square_mask,behavior_mask))

@dataclass(frozen=True)
class GraftOutput:
    effects: tuple
    boundary: object
    commutation: object

class GraftStage:
    """W05 binding. Enumeration preserves public exogenous noise identities.

    The source coefficient and interface scale are calibrated. The target module
    remains unchanged; no target labels are encoded into the transplanted module.
    """
    def __init__(self,module_delta,boundary_delta,versions,*,device='cpu'):
        require_research_action('model_initialize')
        self.module_delta=module_delta;self.boundary_delta=boundary_delta;self.versions=versions;self.device=device
        self.loss_specs=(LossSpec('graft','sum_atoms p(u,v)*mean_coordinates((effect-target)^2)','joint effect squared errors weighted by declared atom probability','valid records with nonempty noise support','joint_outputs_after_graft mask','skip_with_reason',('source_module_generator','boundary_reader'),('source_coefficient','boundary_scale'),(),GradientEstimator.EXACT,'records; noise probability inside record'),LossSpec('boundary','mean((learned_boundary-declared_boundary)^2)','boundary calibration squared residual','valid records','all declared boundaries','skip_with_reason',('boundary_reader',),('boundary_scale',),(),GradientEstimator.EXACT,'boundary coordinates'),LossSpec('commutation','mean((abs(F A-B F)-label)^2)','squared commuting-defect error','valid labeled records','analogy_commutation_error mask','skip_with_reason',('source_module_generator','boundary_reader'),('source_coefficient','boundary_scale'),(),GradientEstimator.EXACT,'declared square defects'))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'source_module_generator':{'coefficient_delta':self.module_delta},'boundary_reader':{'scale_delta':self.boundary_delta}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h31_grafting.adapter import tensor_scm
        effects=[];defects=[];boundaries=[]
        if len(sender.views)!=len(receiver.views):raise ContractError(ErrorCode.INVALID_SHAPE,'paired causal records required')
        for s,r in zip(sender.views,receiver.views):
            a=module_coefficient(s,'source_module');b=module_coefficient(r,'target_module');scale=float(r.features['boundary_scale'])
            if not torch.isfinite(torch.tensor(scale)) or scale==0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'nonzero finite boundary scale required')
            if s.public_task['noise_contract']!=r.public_task['noise_contract']:raise ContractError(ErrorCode.CONFLICT,'paired noise identities disagree')
            atoms=noise_atoms(s.public_task['noise_contract'])
            if maximum_unroll<3:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'SCM requires three topological equations')
            data=torch.as_tensor(atoms,device=self.device,dtype=self.module_delta.dtype);u=data[:,0];v=u if len(atoms)==2 else data[:,1];n=len(atoms)
            learned_scale=self.boundary_delta+scale;coefficient=self.module_delta+a;zero=coefficient.new_zeros(());empty=coefficient.new_empty((0,));one=coefficient.new_ones((1,))
            modules=(('x',(),empty,learned_scale,(),empty),('grafted',('x',),coefficient.reshape(1),zero,('source_noise',),one),('unaffected',(),empty,zero+b,('target_noise',),one))
            values=tensor_scm(modules,{'source_noise':u,'target_noise':v},{},batch_size=n)
            effects.append(torch.stack((values['grafted'],values['unaffected']),-1));boundaries.append(learned_scale-scale);defects.append((learned_scale*coefficient-b*learned_scale).abs())
        return GraftOutput(tuple(effects),torch.stack(boundaries),torch.stack(defects))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.core.learning import LossValue
        rows=[]
        for prediction,view in zip(output.effects,supervision.views):
            target=torch.as_tensor(view.targets['joint_outputs_after_graft'],device=self.device,dtype=prediction.dtype)
            if target.shape!=(prediction.shape[0],3) or bool((target[:,2]<0).any()) or not torch.isclose(target[:,2].sum(),target.new_tensor(1.)):raise ContractError(ErrorCode.INVALID_SHAPE,'supervised joint distribution must align public noise atoms')
            declared=view.valid_masks.get('joint_outputs_after_graft')
            if declared is not None and not all(declared):continue
            rows.append(((prediction-target[:,:2]).square().mean(-1)*target[:,2]).sum())
        defect,mask=tensor_target(supervision,'analogy_commutation_error',device=self.device)
        return {'graft':torch.stack(rows).mean() if rows else LossValue(0.,0.,None,True,'no complete joint distribution targets'),'boundary':masked_tensor_mean(output.boundary.square(),torch.ones_like(output.boundary,dtype=torch.bool)),'commutation':masked_tensor_mean((output.commutation-defect).square(),mask)}

def build_stage(variant,versions,*,source_dim=3,target_dim=3,operation_candidates=2,observations=1,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    def p(shape):return torch.nn.Parameter(torch.zeros(shape,device=device,dtype=getattr(torch,dtype)))
    if variant=='graft':return GraftStage(p(()),p(()),versions,device=device)
    if variant=='analogy':return AnalogyStage(p((source_dim,target_dim)),p((operation_candidates,)),p((observations,target_dim)),versions,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown causal analogy variant')


def harden_and_verify(source,target,object_map,operation_map,type_map,valid_domain):
    """No straight-through claim: hard maps always receive exact fresh validation."""
    from latent_comm.mechanisms.h30_analogy.adapter import validate_hardened
    return validate_hardened(source,target,object_map,operation_map,type_map,valid_domain)
