from dataclasses import replace
from latent_comm.core import ContractError
from latent_comm.core.finite import matmul,inverse

def gauge_protocol_member(member,gauge,source,target):
    from latent_comm.mechanisms.h25_gauge.reference import condition_check
    if member.versions.frame!=source.version or len(member.writer)!=source.dimension or target.dimension!=source.dimension:raise ContractError('FrameMismatch','H25 protocol message axes must be bound')
    condition_check(gauge,source)
    return replace(member,writer=matmul(gauge,member.writer),reader=matmul(member.reader,inverse(gauge)),versions=replace(member.versions,frame=target.version))

def learning_effect_boundary(member,linearization):
    if linearization.parameter_version!=member.model_revision or linearization.anchors.coordinate_ids!=member.behavior_coordinates or linearization.anchors.public_task_version!=member.versions.task:raise ContractError('AnchorMismatch','H37 compares common behavior coordinates, not heterogeneous token logits')
    return linearization

def quotient_protocol_boundary(member,quotient,*,supported_queries):
    if any(q.version!=member.versions.task for q in quotient.queries) or not {q.query_id for q in quotient.queries}<=set(supported_queries):raise ContractError('QueryFamilyUndefined','H47 protocol compression needs explicit supported task/query versions')
    return tuple(c.signature for c in quotient.classes)
