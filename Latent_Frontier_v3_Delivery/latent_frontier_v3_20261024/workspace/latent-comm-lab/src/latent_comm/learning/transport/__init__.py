"""L07: shared-behavior matrix-free direction transport with explicit scope."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import LossSpec,GradientEstimator,masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action
from latent_comm.mechanisms.h37_gradient_transport.types import BehaviorAnchorSet

def anchor_contract(sender,receiver):
    if sender.versions.task!=receiver.versions.task or sender.public_task['public_probes']!=receiver.public_task['public_probes']:raise ContractError(ErrorCode.VERSION_MISMATCH,'transport requires identical named public probe coordinates')
    probes=sender.public_task['public_probes']
    if not probes:raise ContractError(ErrorCode.INVALID_SCHEMA,'empty common behavior probes')
    return BehaviorAnchorSet(tuple('probe:'+str(i) for i in range(len(probes))),sender.versions.task)

@dataclass(frozen=True)
class TransportOutput:
    actual_effect: object
    desired: object
    linear_effect: object
    updates: object
    original_desired: object
    unreachable: object
    diagnostics: tuple

class TransportStage:
    """W08 exact linear public behavior family with an explicit learned residual.

    JVP/VJP are still performed by the H37 solver; no full neural Jacobian is
    materialized or aligned. The residual operator calibrates the transport only
    within the declared target parameter scope. Anchor preservation prevents the
    learned source direction calibration from collapsing the behavior target.
    """
    def __init__(self,correction,direction_gain,versions,*,ridge=0.,solver_steps=16,tolerance=1e-7,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h37_gradient_transport.losses import LOSS_SPECS
        self.correction=correction;self.direction_gain=direction_gain;self.versions=versions;self.ridge=ridge;self.solver_steps=solver_steps;self.tolerance=tolerance;self.device=device
        self.loss_specs=tuple(replace(s,parameter_owners=('transport_operator','behavior_encoder')) for s in LOSS_SPECS)+(LossSpec('anchors','mean((calibrated_source_direction-original_direction)^2)','shared behavior calibration residual','valid public behavior coordinates','behavior_direction valid mask','skip_with_reason',('behavior_encoder',),('source_direction',),(),GradientEstimator.EXACT,'shared public behavior coordinates'),)
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'transport_operator':{'residual_map':self.correction},'behavior_encoder':{'direction_gain':self.direction_gain}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h37_gradient_transport.adapter import tensor_transport
        from torch.func import jvp
        source_j=tensor_field(sender,'source_jacobian',device=self.device);target_j=tensor_field(receiver,'target_jacobian',device=self.device);direction=tensor_field(sender,'source_direction',device=self.device)
        rows=[];diagnostics=[]
        for s,r,a,b,d in zip(sender.views,receiver.views,source_j,target_j,direction):
            anchors=anchor_contract(s,r)
            if a.shape[0]!=len(anchors.coordinate_ids) or b.shape[0]!=len(anchors.coordinate_ids) or d.shape!=self.direction_gain.shape or self.correction.shape!=(b.shape[1],a.shape[0]):raise ContractError(ErrorCode.INVALID_SHAPE,'behavior or scoped parameter axes differ')
            source_parameters=torch.zeros_like(d);target_parameters=d.new_zeros(b.shape[1]);calibrated=d*self.direction_gain
            source_behavior=lambda p:a@p
            target_behavior=lambda p:b@p
            names=tuple('external_state.'+str(i) for i in range(b.shape[1]))
            result=tensor_transport(source_behavior,target_behavior,source_parameters,calibrated,target_parameters,source_anchors=anchors,target_anchors=anchors,parameter_names=names,ridge=self.ridge,max_steps=min(self.solver_steps,maximum_unroll),tolerance=self.tolerance)
            if not result['converged'] or not result['projection_converged']:raise ContractError(ErrorCode.CONFLICT,'transport solver did not converge; do not silently train against an unestablished solve')
            update=result['update']+self.correction@result['desired_behavior']
            actual=target_behavior(target_parameters+update)-target_behavior(target_parameters)
            linear=jvp(target_behavior,(target_parameters,),(update,))[1]
            rows.append((actual,result['desired_behavior'],linear,update,a@d,result['unreachable_residual']))
            diagnostics.append({k:result[k] for k in ('converged','projection_converged','iterations','rank_status','minimum_norm_interpretation','parameter_names')})
        return TransportOutput(*(torch.stack(v) for v in zip(*rows)),tuple(diagnostics))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h37_gradient_transport.losses import tensor_losses
        _,mask=tensor_target(supervision,'behavior_direction',device=self.device)
        terms=tensor_losses(output.actual_effect,output.desired,output.linear_effect,output.updates,self.ridge,(mask,mask,torch.ones_like(output.updates,dtype=torch.bool)))
        terms['anchors']=masked_tensor_mean((output.desired-output.original_desired).square(),mask)
        return terms

def functional_probe(model,layout,role_view,probe_kwargs,public_readout):
    """Bind a real future model to H37 without detaching its live input graph.

    Caller must supply only kwargs encoded from the passed RoleView; this helper
    also enforces that their names are explicitly whitelisted by its features.
    Returned closure consumes a flat adapter/reader vector, never base weights.
    """
    require_research_action('model_forward')
    from latent_comm.mechanisms.h37_gradient_transport.adapter import functional_behavior
    if set(probe_kwargs)-set(role_view.features.get('probe_fields',())):raise ContractError(ErrorCode.ROLE_LEAKAGE,'model kwargs were not declared in the role probe contract')
    def observe(scoped_vector):return functional_behavior(model,layout,(role_view,probe_kwargs),public_readout,scoped_vector)
    return observe

def build_stage(variant,versions,*,source_parameters=2,target_parameters=2,behavior_coordinates=2,ridge=0.,solver_steps=16,tolerance=1e-7,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    if variant!='linear_behavior':raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'default manifest binding is W08 linear public behavior; functional models require explicit probe/layout binding')
    correction=torch.nn.Parameter(torch.zeros(target_parameters,behavior_coordinates,device=device,dtype=getattr(torch,dtype)));gain=torch.nn.Parameter(torch.ones(source_parameters,device=device,dtype=getattr(torch,dtype)))
    return TransportStage(correction,gain,versions,ridge=ridge,solver_steps=solver_steps,tolerance=tolerance,device=device)
