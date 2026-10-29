"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_base_execute(expr,inputs):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if not inputs:raise ContractError('LoweringFailure','typed tensor input binding required')
    prototype=next(iter(inputs.values()));steps=[0]
    def visit(node,env):
        steps[0]+=1
        if steps[0]>256:raise ContractError('LoweringFailure','future research expansion budget exceeded')
        if node.op=='const':return torch.full_like(prototype,node.value)
        if node.op=='var':
            if node.name not in env:raise ContractError('LoweringFailure','unbound tensor variable')
            return env[node.name]
        if node.op=='let':return visit(node.args[1],{**env,node.name:visit(node.args[0],env)})
        if node.op=='call':raise ContractError('VersionUnsupported','tensor execution requires immutable base lowering')
        a,b=(visit(c,env) for c in node.args)
        if a.shape!=b.shape:raise ContractError('LoweringFailure','no implicit cross-axis broadcast in macro arithmetic')
        return a+b if node.op=='add' else a*b
    return visit(expr,dict(inputs))

def tensor_fast_polynomial(arguments,powers,coefficients):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if arguments.ndim!=2 or powers.ndim!=2 or powers.shape[1]!=arguments.shape[1] or coefficients.shape!=(powers.shape[0],) or bool((powers<0).any()):raise ContractError('InvalidShape','arguments[B,A], nonnegative monomial powers[M,A], coefficients[M] required')
    features=arguments.unsqueeze(1).pow(powers.unsqueeze(0)).prod(-1)
    return features@coefficients
