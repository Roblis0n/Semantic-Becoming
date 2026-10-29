from dataclasses import replace
from latent_comm.core import ContractError
from latent_comm.core.finite import matmul,inverse,eye,scale
from .reference import encode

def gauge_chart(chart,gauge,source,target):
    from latent_comm.mechanisms.h25_gauge.reference import condition_check
    if chart.versions.frame!=source.version or len(chart.read_map)!=source.dimension or source.dimension!=target.dimension:raise ContractError('FrameMismatch','H25 local chart gauge requires explicit equal-dimensional frame')
    condition_check(gauge,source)
    return replace(chart,chart_id=chart.chart_id+':'+target.version,read_map=matmul(gauge,chart.read_map),write_map=matmul(chart.write_map,inverse(gauge)),versions=replace(chart.versions,frame=target.version))

def overlap_restriction(edge,source,target,*,support):
    from latent_comm.mechanisms.h26_sheaf.types import AffineRestriction
    if (edge.source_chart,edge.target_chart,edge.source_frame,edge.target_frame)!=(source.chart_id,target.chart_id,source.versions.frame,target.versions.frame):raise ContractError('FrameMismatch','H26 overlap must reference actual chart/frame endpoints')
    return AffineRestriction(source.chart_id+'->'+target.chart_id,source.chart_id,target.chart_id,edge.mapping,eye(len(target.read_map)),scale(edge.bias,-1.),tuple(support))

def refine_then_encode(chart,scale_packet,multiscale_state,*,task,model_revision):
    from latent_comm.mechanisms.h35_renormalization.reference import refine
    if multiscale_state.scale_version!=scale_packet.target_version:raise ContractError('VersionMismatch','H35 multiscale residual cannot be read under another scale')
    return encode(chart,refine(scale_packet,multiscale_state),task=task,model_revision=model_revision)

def bind_query_quotient(chart,quotient):
    if not {q.query_id for q in quotient.queries}<=chart.task_family or quotient.domain_version!=chart.versions.state:raise ContractError('QueryFamilyUndefined','H47 equivalence applies only to declared chart task family and source-state version')
    return tuple((c.class_id,c.representative,c.signature) for c in quotient.classes)
