from latent_comm.core import ContractError

def portfolio_scores(branch_states,goal_features,score_projection,coverage,valid):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    # Goal features originate in public task; outcome labels never enter this scorer.
    interaction=branch_states*goal_features[:,None,:]
    scores=(interaction@score_projection).squeeze(-1)+coverage
    return scores.masked_fill(~valid,-torch.inf),valid.any(-1)

def select_branch(scores,valid,*,sample):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    any_valid=valid.any(-1);safe=torch.where(any_valid[:,None],scores.masked_fill(~valid,-torch.inf),torch.zeros_like(scores));dist=torch.distributions.Categorical(logits=safe)
    selected=dist.sample() if sample else safe.argmax(-1);logprob=dist.log_prob(selected)
    return torch.where(any_valid,selected,torch.full_like(selected,-1)),logprob*any_valid,any_valid

def fork_prefix(prefix,branch_count):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if not 1<=branch_count<=64:raise ContractError('BudgetExhausted','bounded branch fanout')
    return tuple(prefix.clone() for _ in range(branch_count))
