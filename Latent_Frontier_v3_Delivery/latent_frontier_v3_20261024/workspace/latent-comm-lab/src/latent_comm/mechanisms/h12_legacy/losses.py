from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('multiquery','mean_document weighted_mean_query task_error','sum valid document weighted query means','count valid documents, inner sum query_weights*query_valid','query_valid; sum(query_weights * query_valid)>0 per document','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('query_errors',),(),GradientEstimator.EXACT,'documents then weighted queries'),
)

def tensor_losses(query_errors,query_valid,query_weights):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if query_errors.shape!=query_valid.shape or query_weights.shape!=query_errors.shape or bool((query_weights<0).any()):raise ContractError('DimensionMismatch','explicit query distribution')
    weights=query_weights*query_valid.to(query_errors.dtype);denominator=weights.sum(-1);valid=denominator>0
    safe_errors=torch.where(query_valid.bool(),query_errors,torch.zeros_like(query_errors))
    safe_denominator=torch.where(valid,denominator,torch.ones_like(denominator))
    by_document=(safe_errors*weights).sum(-1)/safe_denominator
    total=by_document[valid].mean() if bool(valid.any()) else safe_errors.sum()*0.
    return {'total':total,'multiquery':total,'valid_documents':valid,'normalization':'documents, then valid weighted queries'}
