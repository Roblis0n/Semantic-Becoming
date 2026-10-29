"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_shared_noise_compose(left_logits,right_logits,joint_noise_probabilities,*,conditional_independence):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if not conditional_independence:raise ContractError('NoiseAliasConflict','stochastic residual factors require explicit conditional independence given the same shared noise')
    if left_logits.ndim!=3 or right_logits.ndim!=3 or left_logits.shape[:2]!=right_logits.shape[:2] or joint_noise_probabilities.shape!=(left_logits.shape[1],):raise ContractError('InvalidShape','conditional logits[B,U,S_i] and joint noise probability[U] required')
    if bool((joint_noise_probabilities<0).any()) or not torch.allclose(joint_noise_probabilities.sum(),joint_noise_probabilities.new_tensor(1.)):raise ContractError('KernelNotNormalized','noise probabilities not normalized')
    left=torch.softmax(left_logits,dim=-1);right=torch.softmax(right_logits,dim=-1)
    # The same U index is summed once, never independently sampled twice.
    return torch.einsum('u,bui,buj->bij',joint_noise_probabilities,left,right).flatten(1)

def tensor_rollout(initial,transition_logits,action_indices,observation_logits):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if initial.ndim!=2 or transition_logits.ndim!=4 or transition_logits.shape[0]!=initial.shape[0] or transition_logits.shape[-2:]!=(initial.shape[1],initial.shape[1]):raise ContractError('InvalidShape','initial[B,S] and transitions[B,A,S,S] required')
    if len(action_indices)>128:raise ContractError('WorldCycle','rollout horizon exceeds explicit bound')
    transition=torch.softmax(transition_logits,dim=-1);observation=torch.softmax(observation_logits,dim=-1);state=initial;states=[state];outputs=[]
    for action in action_indices:
        state=torch.einsum('bi,bij->bj',state,transition[:,action]);states.append(state);outputs.append(torch.einsum('bi,bio->bo',state,observation))
    return torch.stack(states,dim=1),tuple(outputs)
