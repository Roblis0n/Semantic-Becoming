from latent_comm.core import ContractError

def residual_vector_quantize(values,codebooks):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if values.ndim!=2 or not codebooks:raise ContractError('DimensionMismatch','values [B,D], nonempty ordered codebooks')
    accumulated=torch.zeros_like(values);prefixes=[];indices=[];commitments=[];codebook_errors=[]
    for codebook in codebooks:
        if codebook.ndim!=2 or codebook.shape[1]!=values.shape[1]:raise ContractError('DimensionMismatch','codebook [codes,D]')
        residual=values-accumulated.detach();index=torch.cdist(residual,codebook).argmin(-1);selected=codebook[index]
        # Explicit biased straight-through estimator for discrete nearest-code assignment.
        quantized=residual+(selected-residual).detach()
        commitments.append((residual-selected.detach()).square());codebook_errors.append((selected-residual.detach()).square())
        accumulated=accumulated+quantized;prefixes.append(accumulated);indices.append(index)
    return tuple(prefixes),tuple(indices),tuple(commitments),tuple(codebook_errors)
