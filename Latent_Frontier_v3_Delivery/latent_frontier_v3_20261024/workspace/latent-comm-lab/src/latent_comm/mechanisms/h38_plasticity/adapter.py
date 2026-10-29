"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def tensor_interpret(node,environment,rule_parameters,memory_out):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from .reference import validate_rule
    validate_rule(node)
    if node.op=='read':
        if node.slot not in environment:raise ContractError('RuleTypeError','local statistic not bound')
        return environment[node.slot]
    values=[tensor_interpret(c,environment,rule_parameters,memory_out) for c in node.children]
    scalar=node.scalar if node.parameter is None else rule_parameters[node.parameter]
    scalar_value=float(scalar.detach()) if hasattr(scalar,'detach') else scalar
    if node.op in ('clip','precondition_diagonal') and scalar_value<=0 or node.op=='running_mean' and not 0<=scalar_value<1:raise ContractError('RuleTypeError','learned scalar violates operator domain')
    if node.op=='scale':return scalar*values[0]
    if node.op=='clip':return values[0].clamp(-scalar,scalar)
    if node.op=='running_mean':
        result=scalar*environment['memory']+(1-scalar)*values[0];memory_out['memory']=result;return result
    if node.op=='precondition_diagonal':
        if bool((values[1]<0).any()):raise ContractError('RuleTypeError','diagonal must be nonnegative')
        return values[0]/(values[1].sqrt()+scalar)
    if bool(((values[2]!=0)&(values[2]!=1)).any()):raise ContractError('WriteScopeViolation','coordinate mask must be binary')
    return values[0]+values[2]*values[1]

def meta_unroll(program,initial_parameters,rule_parameters,support,query,support_loss,query_loss,*,initial_memory=None):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from .reference import validate_rule,validate_partitions
    validate_rule(program.ast);validate_partitions(support,query)
    names=program.writable_groups
    if not set(names)<=initial_parameters.keys():raise ContractError('WriteScopeViolation','authorized parameter group absent')
    parameters=dict(initial_parameters);memory={} if initial_memory is None else dict(initial_memory);trajectory=[]
    for step in range(program.inner_steps):
        # Query inputs/labels never reach this support-only call or local AST environment.
        loss=support_loss(parameters,support.inputs,support.targets)
        gradients=torch.autograd.grad(loss,tuple(parameters[n] for n in names),create_graph=program.estimator=='exact_unroll',allow_unused=False)
        if program.estimator=='first_order':gradients=tuple(g.detach() for g in gradients)
        updated=dict(parameters)
        for name,gradient in zip(names,gradients):
            parameter=parameters[name];env={'gradient':gradient,'theta':parameter,'memory':memory.get(name,torch.zeros_like(parameter)),'diagonal':gradient.square(),'mask':torch.ones_like(parameter)};out={}
            delta=tensor_interpret(program.ast,env,rule_parameters,out)
            if delta.shape!=parameter.shape:raise ContractError('RuleTypeError','AST update shape changed')
            scale=(program.max_update_norm/delta.norm().clamp_min(1e-12)).clamp(max=1.)
            updated[name]=parameter+delta*scale
            if 'memory' in out:memory[name]=out['memory']
        parameters=updated;trajectory.append(parameters)
    outer_loss=query_loss(parameters,query.inputs,query.targets)
    return {'parameters':parameters,'memory':memory,'trajectory':tuple(trajectory),'query_loss':outer_loss,'estimator':program.estimator,'stop_gradient_edges':(('support_gradient','inner_update'),) if program.estimator=='first_order' else ()}

def meta_train_step(program,initial_parameters,rule_parameters,support,query,support_loss,query_loss,optimizer,*,gradient_clip=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    if gradient_clip<=0:raise ContractError('RuleTypeError','positive outer clipping bound required')
    from .reference import validate_optimizer_ownership
    validate_optimizer_ownership(optimizer,rule_parameters,initial_parameters)
    optimizer.zero_grad(set_to_none=True)
    result=meta_unroll(program,initial_parameters,rule_parameters,support,query,support_loss,query_loss)
    result['query_loss'].backward()
    torch.nn.utils.clip_grad_norm_(tuple(rule_parameters.values()),gradient_clip)
    optimizer.step()
    return {'query_loss':float(result['query_loss'].detach()),'estimator':program.estimator,'rule_version':program.version,'optimizer_state':optimizer.state_dict()}
