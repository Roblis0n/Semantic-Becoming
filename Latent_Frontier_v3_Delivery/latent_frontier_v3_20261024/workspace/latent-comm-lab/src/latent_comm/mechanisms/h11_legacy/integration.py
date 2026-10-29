from latent_comm.core import ContractError

def multiscale_from_progressive(state,scale_packet,*,has_detail):
    from latent_comm.mechanisms.h35_renormalization.types import MultiScaleState
    if not state.layers or state.next_sequence==0 or any(layer.semantic_scale!=scale_packet.target_version for layer in state.layers):raise ContractError('ScaleMismatch','H35 prefix must explicitly name its macro scale')
    macro=len(scale_packet.macro_axes);micro=len(scale_packet.micro_axes)
    if len(state.value)!=(macro+micro if has_detail else macro):raise ContractError('DimensionMismatch','coarse and optional retained detail axes explicitly separated')
    return MultiScaleState(state.value[:macro],state.value[macro:] if has_detail else None,scale_packet.target_version),state.uncertainty_bound

def quotient_candidates(state,quotient,*,task_family):
    if quotient.source_domain is None:raise ContractError('IrrecoverableDetail','H47 candidate refinement requires retained finite source domain')
    if state.versions.state!=quotient.domain_version or task_family not in {q.query_id for q in quotient.queries} or len(state.value)!=1:raise ContractError('QueryFamilyUndefined','scalar progressive source and declared quotient family/version')
    if state.uncertainty_bound is None:return (), 'missing_prefix_unknown'
    possible={name for name,value in zip(quotient.source_domain.state_ids,quotient.source_domain.values) if abs(value-state.value[0])<=state.uncertainty_bound}
    classes=tuple(c.class_id for c in quotient.classes if set(c.members)&possible)
    return classes,'unique_within_declared_domain' if len(classes)==1 else 'ambiguous_or_outside_retained_domain'
