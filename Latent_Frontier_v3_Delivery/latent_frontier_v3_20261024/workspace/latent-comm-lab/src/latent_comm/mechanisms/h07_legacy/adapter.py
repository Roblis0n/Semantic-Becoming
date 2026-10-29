from latent_comm.core import ContractError

def tensor_execute(compiled,inputs,operator_parameters):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from .reference import compile_program
    from latent_comm.mechanisms.h01_legacy.adapter import tensor_operator
    from dataclasses import replace
    from .types import TensorFieldBinding,TensorConstraintBinding,TensorProgramContinuation
    from latent_comm.mechanisms.h04_legacy.adapter import tensor_field
    checked=compile_program(compiled.packet);values=dict(inputs)
    if set(values)!=set(dict(checked.packet.input_types)):raise ContractError('UnboundReference','exact declared tensor inputs required')
    for name,typ in checked.packet.input_types:
        value=values[name]
        if typ.kind=='state' and (value.ndim!=2 or value.shape[-1]!=typ.dimension):raise ContractError('DimensionMismatch','tensor state must match declared frame dimension')
        if typ.kind=='operator':
            from .reference import validate_bound_input
            validate_bound_input(value,typ,checked.packet.versions)
            if name not in operator_parameters:raise ContractError('UnboundReference','operator factors absent')
    nodes={n.node_id:n for n in checked.packet.nodes}
    for key in checked.schedule:
        n=nodes[key];v=[values[x] for x in n.inputs]
        if n.opcode=='READ_SLOT':out=v[0]
        elif n.opcode=='APPLY_OPERATOR':out=tensor_operator(v[0],*operator_parameters[n.inputs[1]])
        elif n.opcode=='DECODE':out=v[0]@v[1].T
        elif n.opcode=='BRANCH':out=(v[0],v[0])
        elif n.opcode=='MERGE_SCOPED':
            if len(v[0])!=2 or not torch.equal(v[0][0],v[0][1]):raise ContractError('Conflict','tensor merge requires matching explicit branch states')
            out=v[0][0]
        elif n.opcode=='REFINE_BELIEF':
            from latent_comm.mechanisms.h03_legacy.adapter import tensor_prefix_update
            out=tensor_prefix_update(v[0],v[1])
        elif n.opcode=='ADD_CONSTRAINT':
            field,constraint=v
            if not isinstance(field,TensorFieldBinding) or not isinstance(constraint,TensorConstraintBinding) or field.frame!=constraint.frame:raise ContractError('FrameMismatch','typed tensor field/constraint bindings required')
            out=replace(field,matrices=torch.cat((field.matrices,constraint.matrix[:,None]),1),targets=torch.cat((field.targets,constraint.target[:,None]),1),temperatures=torch.cat((field.temperatures,constraint.temperature[:,None]),1))
        elif n.opcode=='SOLVE_FIELD':
            field=v[0]
            if not isinstance(field,TensorFieldBinding) or field.frame!=n.output_type.frame:raise ContractError('FrameMismatch','typed tensor field output frame')
            out=tensor_field(field.anchor,field.matrices,field.targets,field.temperatures,field.anchor_strength,steps=n.bound,step_size=field.step_size,nonlinear=field.nonlinear)[0]
        elif n.opcode=='CONTINUE':out=tensor_continue_program(v[0],max_steps=n.bound)
        else:raise ContractError('UnsupportedOpcode','closed compiled tensor opcode set')
        values[key]=out
    return values[checked.packet.result_id]


def tensor_continue_program(continuation,*,max_steps):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    from dataclasses import replace
    from latent_comm.core import StepBudget
    from .types import TensorProgramContinuation
    if not isinstance(continuation,TensorProgramContinuation) or not 1<=max_steps<=128:raise ContractError('InvalidContinuation','typed bounded differentiable program continuation required')
    meter=StepBudget(max_steps=max_steps).meter();values=dict(continuation.values);pc=continuation.program_counter;completed=list(continuation.completed_operations)
    if completed!=[op.operation_id for op in continuation.program[:pc]]:raise ContractError('InvalidContinuation','completed tensor program must be exact prefix')
    def evaluate(expr,env):
        meter.consume(steps=1);opcode=expr[0]
        if opcode=='const':return expr[1]
        if opcode=='var':
            if expr[1] not in env:raise ContractError('UnboundReference','tensor program variable absent')
            return env[expr[1]]
        if opcode=='add':return evaluate(expr[1],env)+evaluate(expr[2],env)
        if opcode=='mul':return evaluate(expr[1],env)*evaluate(expr[2],env)
        if opcode=='let':return evaluate(expr[3],dict(env,**{expr[1]:evaluate(expr[2],env)}))
        raise ContractError('UnsupportedOpcode','closed differentiable expression AST')
    while pc<len(continuation.program):
        op=continuation.program[pc];missing=set(op.dependencies)-continuation.available_dependencies-set(completed)
        if missing:return replace(continuation,values=tuple(values.items()),program_counter=pc,completed_operations=tuple(completed),pending_dependencies=tuple(sorted(missing)))
        meter.consume(steps=1);values[op.output]=evaluate(op.expression,values);completed.append(op.operation_id);pc+=1
    return replace(continuation,values=tuple(values.items()),program_counter=pc,completed_operations=tuple(completed),pending_dependencies=())
