"""Shared graph contracts for concrete composition programs, not generic agents."""
from dataclasses import dataclass,asdict,is_dataclass
from collections.abc import Mapping
from enum import Enum
import hashlib
import json
import math
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.compiler import Compiler
from latent_comm.compiler.types import NodeCapability

@dataclass(frozen=True)
class ObjectContract:
    object_id: str
    type_name: str
    versions: VersionSet
    required_axes: tuple[str,...]
    visibility: str
    scope: frozenset[str]
    def __post_init__(self):
        self.versions.require(*self.required_axes)
        if not self.object_id or not self.type_name or self.visibility not in {'public','sender','receiver','supervision'}:raise ContractError('InvalidCompositionContract','explicit object identity, semantic type and role required')

@dataclass(frozen=True)
class FlowNode:
    node_id: str
    mechanisms: tuple[str,...]
    inputs: tuple[tuple[str,str],...]
    output: str
    implementation: str
    read_set: frozenset[str]
    write_set: frozenset[str]
    differentiability: str
    gradient_edges: tuple[tuple[str,str],...]
    role: str='public'
    budget_cost: int=1

@dataclass(frozen=True)
class CompositionGraph:
    recipe_id: str
    objects: tuple[ObjectContract,...]
    nodes: tuple[FlowNode,...]
    maximum_steps: int
    obligations: tuple[str,...]=()

@dataclass(frozen=True)
class ReferenceResult:
    value: object
    objects: Mapping[str,object]
    audit: tuple[dict,...]
    obligations: tuple[str,...]
    research_state: str='NOT_RUN'
    status: str='Complete'
    pending_nodes: tuple[str,...]=()
    consumed_steps: int=0
    consumed_cases: int=0
    consumed_branches: int=0


def infer_contracts(graph):
    objects={o.object_id:o for o in graph.objects};producers={};known=set(objects)
    if len(objects)!=len(graph.objects):raise ContractError('InvalidCompositionContract','duplicate object identity')
    for node in graph.nodes:
        if not node.implementation.startswith('latent_comm.compositions.'):raise ContractError('UnboundImplementation','composition must bind an actual local stage implementation')
        if node.output not in known or node.output in producers:raise ContractError('MultipleWriters','exactly one output producer required')
        producers[node.output]=node.node_id
        if not dict(node.inputs) or any(ref not in known for _,ref in node.inputs):raise ContractError('UnboundReference','concrete input object is missing')
        for port,ref in node.inputs:
            obj=objects[ref]
            if node.role!='supervision' and obj.visibility not in {'public',node.role}:raise ContractError('RoleLeakage','composition node cannot widen an object role')
            if not node.read_set<=obj.scope:raise ContractError('ScopeViolation','invalid scope')
        if not set(dict(node.gradient_edges))<=set(dict(node.inputs)):raise ContractError('GradientPort','unknown input gradient port')
    return {'objects':objects,'producers':producers,'edges':tuple((producers[ref],n.node_id,port,ref) for n in graph.nodes for port,ref in n.inputs if ref in producers)}


def lower_plan(graph):
    bound=infer_contracts(graph);objects=bound['objects'];caps={};nodes=[]
    for n in graph.nodes:
        key=graph.recipe_id+'.'+n.node_id
        axes=tuple(sorted({a for _,r in n.inputs for a in objects[r].required_axes}))
        caps[key]=NodeCapability(key,key,tuple((p,objects[r].type_name) for p,r in n.inputs),(('out',objects[n.output].type_name),),n.read_set,n.write_set,n.differentiability,'deterministic_given_inputs',tuple(n.mechanisms),axes,n.implementation,'composition:'+graph.recipe_id)
        nodes.append({'id':n.node_id,'operation':key,'inputs':dict(n.inputs),'outputs':{'out':n.output},'role':n.role,'gradient_edges':dict(n.gradient_edges),'budget_cost':n.budget_cost})
    declarations={o.object_id:{'type':o.type_name,'versions':o.versions.as_dict(),'visibility':o.visibility,'scope':sorted(o.scope),'bound':True} for o in graph.objects}
    recipe={'schema_version':3,'id':graph.recipe_id,'kind':'combination','design_only':True,'research_execution_authorized':False,'nodes':nodes,'objects':declarations,'runtime_budget':{'max_steps':graph.maximum_steps},'parameters':{'obligations':list(graph.obligations)}}
    return Compiler(caps).compile(recipe,source=graph.recipe_id+'.bound.json')


def _plain(value):
    if is_dataclass(value):return {name:_plain(getattr(value,name)) for name in value.__dataclass_fields__}
    if isinstance(value,Enum):return value.value
    if isinstance(value,Mapping):return {str(k):_plain(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):
        if len(value)>64:raise ContractError('BudgetExhausted','finite composition sequence dimension exceeds 64')
        return [_plain(v) for v in value]
    if isinstance(value,(set,frozenset)):return sorted((_plain(v) for v in value),key=repr)
    if isinstance(value,float):
        if math.isnan(value) or value==math.inf:raise ContractError('NonfiniteComposition','NaN/positive infinity cannot enter finite object flow')
        return '-inf_log_weight' if value==-math.inf else value
    if value is None or isinstance(value,(str,int,bool)):return value
    raise ContractError('OpaqueCompositionValue','finite reference accepts typed stdlib objects only, never live neural tensors')


def execute_reference(graph,bindings,functions,types,*,budget=StepBudget()):
    from latent_comm.core.budgets import aggregate_budget
    with aggregate_budget(budget) as aggregate:
        return _execute_reference(graph,bindings,functions,types,budget=budget,aggregate=aggregate)

def _execute_reference(graph,bindings,functions,types,*,budget,aggregate):
    """Execute actual stage functions in the compiler schedule with typed inputs.

    Function bindings are supplied by source, not resolved from untrusted strings.
    Each mechanism retains its own finite contract; outer stage counts are also
    bounded. A research tensor dispatcher is deliberately not this interpreter.
    """
    ir=lower_plan(graph);contracts={o.object_id:o for o in graph.objects};nodes={n.node_id:n for n in graph.nodes};values=dict(bindings);audit=[];meter=budget.meter()
    if ir.worst_case_steps>budget.max_steps:raise ContractError('BudgetExhausted','composition exceeds current finite fixture budget')
    def check(ref,value):
        expected=types.get(contracts[ref].type_name)
        if expected is None or not isinstance(value,expected):raise ContractError('TypeMismatch','wrong finite object for '+ref)
        actual_versions=getattr(value,'versions',None)
        if actual_versions is not None and not actual_versions.matches(contracts[ref].versions,contracts[ref].required_axes):raise ContractError('VersionMismatch','bound object semantic versions do not match '+ref)
        _plain(value)
    for ref,value in values.items():
        if ref not in contracts:raise ContractError('UnboundReference','unknown binding')
        check(ref,value)
    for index,node_id in enumerate(ir.schedule):
        n=nodes[node_id]
        if node_id not in functions:raise ContractError('UnboundImplementation','missing concrete stage '+node_id)
        if any(ref not in values for _,ref in n.inputs):raise ContractError('UnboundReference','missing stage input')
        inputs={p:values[r] for p,r in n.inputs}
        try:
            meter.consume(steps=n.budget_cost)
            out=functions[node_id](**inputs)
        except ContractError:
            if not aggregate.exhausted:raise
            prior=values[graph.nodes[index-1].output] if index else None
            pending=tuple(ir.schedule[index:])
            return ReferenceResult(prior,values,tuple(audit),graph.obligations+('Aggregate finite budget exhausted before further work; pending stages: '+', '.join(pending),),status='BudgetExhausted',pending_nodes=pending,consumed_steps=aggregate.steps,consumed_cases=aggregate.cases,consumed_branches=aggregate.branches)
        check(n.output,out);values[n.output]=out
        digest=lambda x:hashlib.sha256(json.dumps(_plain(x),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        audit.append({'node':node_id,'mechanisms':n.mechanisms,'input_sha256':digest(inputs),'output_sha256':digest(out),'steps':aggregate.steps,'cases':aggregate.cases,'branches':aggregate.branches,'stage_steps':meter.steps})
    return ReferenceResult(values[graph.nodes[-1].output],values,tuple(audit),graph.obligations,consumed_steps=aggregate.steps,consumed_cases=aggregate.cases,consumed_branches=aggregate.branches)


def linear_graph(recipe_id,stage_definitions,versions,*,required_axes,scope,maximum_steps=64,obligations=()):
    """Construct explicit stage-specific types, not mechanism-name placeholders."""
    from latent_comm.compiler.registry import mechanism_registry
    registry=mechanism_registry()
    nodes=[];objects=[];prior='input'
    for index,(name,mechanisms,input_type,output_type,implementation,gradient) in enumerate(stage_definitions):
        if index==0:objects.append(ObjectContract(prior,input_type,versions,required_axes,'public',frozenset(scope)))
        elif objects[-1].type_name!=input_type:raise ContractError('TypeMismatch','adjacent composition types do not match')
        out=name+':out';objects.append(ObjectContract(out,output_type,versions,required_axes,'public',frozenset(scope)))
        reads=frozenset().union(*(registry[h].read_set for h in mechanisms));writes=frozenset().union(*(registry[h].write_set for h in mechanisms))
        nodes.append(FlowNode(name,tuple(mechanisms),(('value',prior),),out,implementation,reads,writes,'differentiable' if gradient=='differentiable' else 'discrete' if gradient in {'enumeration','score_function'} else 'exact',(('value',gradient),)))
        prior=out
    return CompositionGraph(recipe_id,tuple(objects),tuple(nodes),maximum_steps,tuple(obligations))


def objective_phase(name, bindings, **settings):
    """Bind exact source ledgers, retaining every denominator and gradient edge.

    This is a phase description, not permission to sum all mechanisms' losses.
    A future trainer must bind phase-specific differentiable parameter paths.
    """
    objectives=[]
    for mechanism,ledger,names in bindings:
        by_name={spec.name:spec for spec in ledger}
        for loss_name in names:
            if loss_name not in by_name:raise ContractError('UnknownLoss',mechanism+'.'+loss_name)
            record=asdict(by_name[loss_name]);record['id']=mechanism+'.'+loss_name
            objectives.append(record)
    return {'name':name,'objectives':objectives,'losses':[o['id'] for o in objectives],'owners':sorted({owner for o in objectives for owner in o['parameter_owners']}),'aggregation':'separately normalized phase objectives; explicit per-run weights required','source_graph_revalidation':'each selected owner must have a live path in the concrete stage',**settings}
