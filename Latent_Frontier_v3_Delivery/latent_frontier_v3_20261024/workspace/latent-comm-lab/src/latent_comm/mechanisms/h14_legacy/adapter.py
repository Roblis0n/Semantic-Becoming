from latent_comm.core import ContractError

def choose_production(features,production_embeddings,legal_mask,*,temperature=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if features.ndim!=2 or production_embeddings.ndim!=2 or features.shape[1]!=production_embeddings.shape[1] or legal_mask.shape!=(features.shape[0],production_embeddings.shape[0]) or temperature<=0:raise ContractError('DimensionMismatch','typed production proposal axes')
    if not bool(legal_mask.any(-1).all()):raise ContractError('NoProduction','grammar has no legal completion')
    logits=(features@production_embeddings.T/temperature).masked_fill(~legal_mask.bool(),-torch.inf)
    return logits,logits.argmax(-1) # Selection is discrete, not an exact structural gradient.

def execute_expanded(compiled,inputs,operator_parameters):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from latent_comm.mechanisms.h07_legacy.adapter import tensor_execute
    return tensor_execute(compiled,inputs,operator_parameters)
