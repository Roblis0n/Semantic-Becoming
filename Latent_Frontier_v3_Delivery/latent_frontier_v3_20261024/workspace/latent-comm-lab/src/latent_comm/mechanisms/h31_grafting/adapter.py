"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_scm(modules,noise,interventions,*,batch_size):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    # Modules are a validated topological sequence of (name, parents, weights, bias, noise_ids, noise_weights).
    values={}
    for name,parents,weights,bias,noise_ids,noise_weights in modules:
        if name in interventions:
            value=interventions[name]
        else:
            if any(p not in values for p in parents):raise ContractError('CycleIntroduced','module order is not topological')
            if weights.shape!=(len(parents),) or noise_weights.shape!=(len(noise_ids),):raise ContractError('BoundaryMismatch','coefficient axes do not match named causal parents/noise')
            value=bias.expand(batch_size)
            for i,p in enumerate(parents):value=value+weights[i]*values[p]
            for i,n in enumerate(noise_ids):
                if n not in noise:raise ContractError('NoiseIdentityConflict','shared identity missing')
                value=value+noise_weights[i]*noise[n]
        if value.shape!=(batch_size,):raise ContractError('InvalidShape','one scalar per batch causal variable required')
        values[name]=value
    return values
