"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_multiscale(state,coarse_map,lift,micro_dynamics,micro_bias,macro_dynamics,macro_bias):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if state.ndim!=2 or coarse_map.ndim!=2 or lift.shape!=coarse_map.transpose(-1,-2).shape or state.shape[1]!=coarse_map.shape[1]:raise ContractError('ScaleMismatch','state[B,micro], coarse[macro,micro], lift[micro,macro] required')
    coarse=state@coarse_map.transpose(-1,-2);detail=state-coarse@lift.transpose(-1,-2)
    true_next=(state@micro_dynamics.transpose(-1,-2)+micro_bias)@coarse_map.transpose(-1,-2)
    macro_next=coarse@macro_dynamics.transpose(-1,-2)+macro_bias
    return coarse,detail,true_next-macro_next

def tensor_memory_step(coarse,detail,lift,micro_dynamics,micro_bias,coarse_map):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    if detail is None:raise ContractError('IrrecoverableDetail','memory closure requires an explicit retained residual tensor')
    micro=coarse@lift.transpose(-1,-2)+detail
    next_micro=micro@micro_dynamics.transpose(-1,-2)+micro_bias
    next_coarse=next_micro@coarse_map.transpose(-1,-2)
    return next_coarse,next_micro-next_coarse@lift.transpose(-1,-2)
