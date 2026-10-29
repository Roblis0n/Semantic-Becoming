"""L03: coordinate covariance calibration and anchored local restriction learning."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import LossSpec,GradientEstimator,masked_tensor_mean
from latent_comm.safety.policy import require_research_action
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.mechanisms.h25_gauge.losses import LOSS_SPECS as H25_LOSS_SPECS
FRAME_LOSS_SPECS=tuple(replace(spec,parameter_owners=('cross_map',)) if spec.name=='covariance' else spec for spec in H25_LOSS_SPECS)

@dataclass(frozen=True)
class FrameOutputs:
    transported_state: object
    covariance_residual: object
    behavior: object
    source_behavior: object

@dataclass(frozen=True)
class SectionOutputs:
    section: object
    overlap: object
    conflict_logits: object

class FrameStage:
    """Learn low-rank calibration around an explicit observed invertible frame.

    This does not infer a frame without observations. Singular/rectangular worlds
    take the typed cross-map branch of H25 rather than pretending GL inversion.
    """
    def __init__(self,left,right,readout_delta,versions,*,device='cpu',condition_limit=10000.):
        require_research_action('model_initialize')
        versions.require('schema','state','frame','world','task')
        self.left=left;self.right=right;self.readout_delta=readout_delta;self.versions=versions;self.device=device;self.condition_limit=condition_limit;self.loss_specs=FRAME_LOSS_SPECS
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'cross_map':{'left':self.left,'right':self.right},'read_write_heads':{'readout_delta':self.readout_delta}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        from latent_comm.mechanisms.h25_gauge.adapter import tensor_transport
        z=tensor_field(receiver,'state',device=self.device);g=tensor_field(sender,'frame',device=self.device);t=tensor_field(sender,'operator',device=self.device);r=tensor_field(receiver,'readout',device=self.device)
        if g.shape[-1]!=g.shape[-2]:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'FrameStage is the GL branch; use declared H25 cross-map stage for rectangular maps')
        zg,tg,rg,_=tensor_transport(z,t,r,g,condition_limit=self.condition_limit)
        correction=self.left@self.right
        if correction.shape!=g.shape[1:] or self.readout_delta.shape!=r.shape[1:]:raise ContractError(ErrorCode.INVALID_SHAPE,'calibration owner shapes do not match frame/readout')
        predicted=((g+correction.unsqueeze(0))@z.unsqueeze(-1)).squeeze(-1)
        behavior=((rg+self.readout_delta.unsqueeze(0))@tg@predicted.unsqueeze(-1)).squeeze(-1)
        return FrameOutputs(predicted,predicted-zg,behavior,(r@t@z.unsqueeze(-1)).squeeze(-1))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h25_gauge.losses import tensor_losses
        # This covariance objective has analytic targets already declared in the
        # public role data; hidden supervision is not supplied to the forward.
        return tensor_losses(output.covariance_residual,output.behavior-output.source_behavior,torch.ones_like(output.covariance_residual,dtype=torch.bool),torch.ones_like(output.behavior,dtype=torch.bool))

class RestrictionStage:
    def __init__(self,restriction_delta,bias_delta,conflict_weight,conflict_bias,versions,*,device='cpu'):
        require_research_action('model_initialize')
        self.restriction_delta=restriction_delta;self.bias_delta=bias_delta;self.conflict_weight=conflict_weight;self.conflict_bias=conflict_bias;self.versions=versions;self.device=device
        self.loss_specs=(LossSpec('section','mean((z-z_reference)^2)','valid section coordinate squared errors','valid coordinates','section_mask','skip_with_reason',('restriction_maps',),('restriction_matrix','bias'),(),GradientEstimator.EXACT,'coordinates'),LossSpec('overlap','mean((Az-b)^2)','valid overlap squared errors','valid declared overlaps','overlap_mask','skip_with_reason',('restriction_maps',),('section','restriction_matrix'),(),GradientEstimator.EXACT,'overlap coordinates'),LossSpec('obstruction','mean(BCE(logit,not_gluable))','graph classification CE','valid graphs','graph_mask','skip_with_reason',('restriction_maps','conflict_head'),('overlap',),(),GradientEstimator.EXACT,'graphs'))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'restriction_maps':{'matrix_delta':self.restriction_delta,'bias_delta':self.bias_delta},'conflict_head':{'weight':self.conflict_weight,'bias':self.conflict_bias}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h26_sheaf.adapter import tensor_glue
        ab=tensor_field(sender,'edge_ab',device=self.device);bc=tensor_field(sender,'edge_bc',device=self.device);ca=tensor_field(receiver,'edge_ca',device=self.device);anchor=tensor_field(sender,'anchor',device=self.device,public=True).reshape(-1,1)
        zero=torch.zeros_like(ab[:,0]);base=torch.stack((torch.stack((-ab[:,0],-ab[:,1],zero),-1),torch.stack((zero,-bc[:,0],-bc[:,1]),-1),torch.stack((-ca[:,1],zero,-ca[:,0]),-1)),1)
        bias=torch.stack((ab[:,2],bc[:,2],ca[:,2]),-1)+self.bias_delta
        if self.restriction_delta.shape!=(3,3) or self.bias_delta.shape!=(3,):raise ContractError(ErrorCode.INVALID_SHAPE,'triangle restriction head requires 3x3 and 3 owners')
        # Preserve sparse cover: a learned map cannot invent undeclared overlaps.
        incidence=(base!=0).to(base.dtype);a=base+self.restriction_delta.unsqueeze(0)*incidence
        section,residual,_=tensor_glue(a,bias,(0,),anchor)
        logits=(residual.square()@self.conflict_weight).reshape(-1)+self.conflict_bias
        return SectionOutputs(section,residual,logits)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        target,mask=tensor_target(supervision,'global_section',device=self.device);gluable,valid=tensor_target(supervision,'exactly_gluable',device=self.device)
        return {'section':masked_tensor_mean((output.section-target).square(),mask),'overlap':masked_tensor_mean(output.overlap.square(),torch.ones_like(output.overlap,dtype=torch.bool)),'obstruction':masked_tensor_mean(torch.nn.functional.binary_cross_entropy_with_logits(output.conflict_logits,1-gluable,reduction='none'),valid)}

@dataclass(frozen=True)
class CrossMapOutputs(FrameOutputs):
    unreachable_readout_residual: object
    rank: object

class CrossMapStage(FrameStage):
    """Rectangular maps are not gauge equivalences. Report lost readout directions."""
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        z=tensor_field(receiver,'state',device=self.device);g=tensor_field(sender,'frame',device=self.device);t=tensor_field(sender,'operator',device=self.device);r=tensor_field(receiver,'readout',device=self.device)
        correction=self.left@self.right
        if correction.shape!=g.shape[1:] or self.readout_delta.shape!=(r.shape[1],g.shape[1]):raise ContractError(ErrorCode.INVALID_SHAPE,'rectangular map and target readout shapes differ')
        transported=((g+correction.unsqueeze(0))@z.unsqueeze(-1)).squeeze(-1)
        target=(g@z.unsqueeze(-1)).squeeze(-1);source_readout=r@t
        least=torch.linalg.lstsq(g.transpose(-1,-2),source_readout.transpose(-1,-2))
        reachable_readout=least.solution.transpose(-1,-2)
        residual=source_readout-reachable_readout@g
        behavior=((reachable_readout+self.readout_delta.unsqueeze(0))@transported.unsqueeze(-1)).squeeze(-1)
        return CrossMapOutputs(transported,transported-target,behavior,(source_readout@z.unsqueeze(-1)).squeeze(-1),residual,torch.linalg.matrix_rank(g))


def build_stage(kind,versions,*,source_dim=2,target_dim=2,observations=1,rank=1,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    if not 0<rank<=min(source_dim,target_dim) or observations<=0:raise ContractError(ErrorCode.INVALID_SHAPE,'positive model dimensions and valid low rank required')
    def parameter(value):return torch.nn.Parameter(value.to(device=device,dtype=getattr(torch,dtype)))
    if kind in {'gauge','cross_map'}:
        left=parameter(torch.eye(target_dim,rank));right=parameter(torch.zeros(rank,source_dim));head=parameter(torch.zeros(observations,target_dim))
        if kind=='gauge' and source_dim!=target_dim:raise ContractError(ErrorCode.INVALID_SHAPE,'GL gauge needs square axes')
        cls=FrameStage if kind=='gauge' else CrossMapStage
        return cls(left,right,head,versions,device=device)
    if kind=='restrictions':return RestrictionStage(parameter(torch.zeros(3,3)),parameter(torch.zeros(3)),parameter(torch.ones(3)),parameter(torch.zeros(())),versions,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown frames stage kind')
