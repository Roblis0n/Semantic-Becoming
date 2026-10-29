"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_commit_policy(conflict_features,cost_features,weights,bias):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if conflict_features.ndim!=2 or cost_features.ndim!=2 or conflict_features.shape[0]!=cost_features.shape[0]:raise ContractError('InvalidShape','conflict and redo-cost features need [B,F]')
    features=torch.cat((conflict_features,cost_features),dim=-1)
    if weights.shape!=(features.shape[1],2):raise ContractError('InvalidShape','two policy heads: commit propensity and redo cost')
    prediction=features@weights+bias
    return torch.sigmoid(prediction[:,0]),torch.nn.functional.softplus(prediction[:,1])

def commit_candidate(store,transaction,policy_recommends_commit):
    # Learned policy may postpone; it never replaces store version/type/scope checks.
    if not policy_recommends_commit:return {'status':'deferred','transaction_id':transaction.transaction_id}
    return store.commit(transaction)
