"""Bounded execution of explicitly supplied, non-neural reference operations.

The compiler's implementation strings are never imported. This interpreter only
accepts trusted, explicitly registered stdlib fixture functions. Real research
execution is a different, permanently gated entrypoint in this task.
"""
from dataclasses import dataclass
from copy import deepcopy
from collections.abc import Callable
from latent_comm.core import ContractError, StepBudget
from .transactions import VersionedStore
from .journal import canonical, sha256

@dataclass(frozen=True)
class FixtureOperation:
    function: Callable[[dict],dict]
    action: str = 'stdlib_math_fixture'

@dataclass(frozen=True)
class LoopExecution:
    objects: dict
    steps: int
    audit: tuple[dict,...]
    termination_reason: str
    research_state: str = 'NOT_RUN'


def execute_fixture_ir(ir,bindings,operations, *, budget=StepBudget()):
    meter=budget.meter();objects=deepcopy(bindings);nodes={n.node_id:n for n in ir.nodes};loops={l.loop_id:l for l in ir.loops};audit=[]
    specs=dict(ir.objects)
    def validate(spec,value):
        VersionedStore._validate_value(value)
        def shape(v):
            if isinstance(v,(tuple,list)):
                meter.dimension(len(v));children=[shape(x) for x in v]
                if children and any(x!=children[0] for x in children):raise ContractError('InvalidShape','ragged fixture tensors are not permitted')
                return (len(v),)+(children[0] if children else ())
            if isinstance(v,dict):
                for child in v.values():shape(child)
            return ()
        actual=shape(value)
        if spec.tensor is not None:spec.tensor.check_shape(actual)
    for key,value in objects.items():
        if key not in specs or not specs[key].bound:raise ContractError('UnboundFixture','fixture requires explicit bound object contracts',key)
        validate(specs[key],value)
    if ir.worst_case_steps>budget.max_steps:raise ContractError('BudgetExhausted','IR exceeds authorized finite fixture steps')
    def execute(node_id,iteration):
        node=nodes[node_id]
        if any(not spec.bound for _,spec in node.input_types+node.output_types):raise ContractError('UnboundFixture','all fixture contracts must be bound',node_id)
        if node.gate_action is not None:
            from latent_comm.safety.policy import require_research_action
            require_research_action(node.gate_action)
        if node_id not in operations:raise ContractError('UnboundFixture','explicit fixture operation missing',node_id)
        op=operations[node_id]
        if op.action!='stdlib_math_fixture':
            from latent_comm.safety.policy import require_research_action
            require_research_action(op.action)
        meter.consume(steps=node.budget_cost)
        if any(ref not in objects for _,ref in node.inputs):raise ContractError('UnboundReference','fixture input missing',node_id)
        inputs={port:deepcopy(objects[ref]) for port,ref in node.inputs};before=sha256(canonical(inputs));result=op.function(inputs)
        if not isinstance(result,dict) or set(result)!={p for p,_ in node.outputs}:raise ContractError('OutputContract','fixture output ports do not match IR',node_id)
        for port,ref in node.outputs:
            validate(specs[ref],result[port]);objects[ref]=deepcopy(result[port])
        audit.append({'node_id':node_id,'iteration':iteration,'input_digest':before,'output_digest':sha256(canonical(result)),'steps_used':meter.steps})
    for block in ir.schedule:
        if block in loops:
            loop=loops[block]
            if loop.max_iterations>budget.max_steps:raise ContractError('BudgetExhausted','loop exceeds fixture step bound')
            for iteration in range(loop.max_iterations):
                for node_id in loop.body:execute(node_id,iteration)
                carried={target:deepcopy(objects[source]) for source,target in loop.carried}
                objects.update(carried)
        else:execute(block,0)
    return LoopExecution(objects,meter.steps,tuple(audit),'bounded_schedule_complete')


def execute_research_ir(ir,*args,**kwargs):
    from latent_comm.safety.policy import require_research_action
    require_research_action('research_execution')
    raise ContractError('ResearchForbidden','current IR remains NOT_RUN')
