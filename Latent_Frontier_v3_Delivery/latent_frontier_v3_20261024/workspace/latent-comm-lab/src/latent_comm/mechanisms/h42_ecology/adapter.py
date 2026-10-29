"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_niche_policy(competence,novelty,solvability,valid_mask,niche_ids,*,novelty_weight=1.,solvability_weight=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if competence.ndim!=1 or any(x.shape!=competence.shape for x in (novelty,solvability,valid_mask,niche_ids)):raise ContractError('InvalidShape','explicit per-candidate measures required; IDs are not features')
    output=torch.zeros_like(competence)
    for niche_id in torch.unique(niche_ids):
        members=(niche_ids==niche_id)&valid_mask
        if bool(members.any()):
            score=competence[members]+novelty_weight*novelty[members]+solvability_weight*solvability[members]
            output=output.masked_scatter(members,torch.softmax(score,dim=0))
    return output

def alternating_train(interface_parameters,proposal_parameters,interface_optimizer,proposal_optimizer,interface_objective,proposal_objective,role_batches,*,rounds=8,clip=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    if not 1<=rounds<=128 or clip<=0:raise ContractError('UnboundedExpansion','future alternating learning rounds must be bounded')
    interface_parameters=tuple(interface_parameters);proposal_parameters=tuple(proposal_parameters)
    if {id(p) for p in interface_parameters}&{id(p) for p in proposal_parameters}:raise ContractError('InvalidMutation','alternating interface/proposal parameter owners must be disjoint')
    for optimizer,parameters in ((interface_optimizer,interface_parameters),(proposal_optimizer,proposal_parameters)):
        expected={id(p) for p in parameters};actual=[id(p) for group in optimizer.param_groups for p in group['params']]
        if set(actual)!=expected or len(actual)!=len(expected):raise ContractError('InvalidMutation','optimizer owner mismatch')
    history=[]
    for _ in range(rounds):
        for owner,parameters,optimizer,objective in (('interface',interface_parameters,interface_optimizer,interface_objective),('proposer',proposal_parameters,proposal_optimizer,proposal_objective)):
            optimizer.zero_grad(set_to_none=True);loss=objective(role_batches);loss.backward();torch.nn.utils.clip_grad_norm_(parameters,clip);optimizer.step()
            history.append((owner,float(loss.detach())))
    return tuple(history)
