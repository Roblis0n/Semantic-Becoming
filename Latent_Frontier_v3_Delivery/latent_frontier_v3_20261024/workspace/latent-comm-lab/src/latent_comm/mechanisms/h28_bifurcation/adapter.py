"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_dynamics(initial,control,coefficient,*,dt,steps_per_control,max_unroll=128):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if initial.ndim!=2 or control.ndim!=1 or coefficient.shape!=(initial.shape[1],):raise ContractError('InvalidShape','z[B,d], alpha[T], positive cubic coefficient[d] required')
    if dt<=0 or steps_per_control<1 or len(control)*steps_per_control>max_unroll or bool((coefficient<=0).any()):raise ContractError('UnstableIntegrator','invalid integrator bounds or potential coefficient')
    state=initial;trajectory=[state]
    for alpha in control:
        for _ in range(steps_per_control):
            state=state+dt*(alpha*state-coefficient*state.pow(3));trajectory.append(state)
    return torch.stack(trajectory,dim=1)

def tensor_migrate(state,mapping):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if state.ndim!=2 or mapping.ndim!=2 or mapping.shape[1]!=state.shape[1]:raise ContractError('InvalidShape','migration[out,in] must match state[B,in]')
    return state@mapping.transpose(-1,-2)
