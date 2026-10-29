from dataclasses import replace
from latent_comm.core import ContractError
from latent_comm.core.finite import eye

def transport_latent_frame_only(obj,latent_state,gauge,source,target):
    from latent_comm.mechanisms.h25_gauge.types import GaugePacket
    from latent_comm.mechanisms.h25_gauge.reference import transport
    if obj.frame.latent_frame_id!=source.frame_id or obj.versions.frame!=source.version:raise ContractError('FrameConflation','H25 latent frame is separate from physical units/handedness')
    report=transport(GaugePacket(source,latent_state,eye(source.dimension),eye(source.dimension)),gauge,target)
    return replace(obj,frame=replace(obj.frame,latent_frame_id=target.frame_id),versions=replace(obj.versions,frame=target.version)),report.transported.state

def coordinate_intervention(obj,axis,world,variable,*,allowed_variables):
    from latent_comm.mechanisms.h09_legacy.types import Intervention
    modules={m.output:m for m in world.modules}
    if obj.position is None or axis not in (0,1) or obj.versions.world!=world.version or variable not in modules or modules[variable].unit!=obj.frame.unit:raise ContractError('UnboundGrounding','H31 coordinate requires known object, typed unit and exact world binding')
    return Intervention(variable,obj.position[axis],obj.frame.unit,frozenset(allowed_variables),world.version)

def predicted_observation_row(obj,kernel,state):
    if obj.versions.world!=kernel.version or state not in kernel.states:raise ContractError('VersionMismatch','H43 grounding-to-world state correspondence must be explicit')
    return kernel.observation_matrix[kernel.states.index(state)],'model_prediction_not_real_observation'
