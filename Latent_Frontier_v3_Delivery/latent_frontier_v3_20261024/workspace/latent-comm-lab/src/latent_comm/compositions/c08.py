"""C08: protocol-as-language with real macro lowering and graph equivalence checks."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet,StepBudget,Scope
from latent_comm.core.finite import norm,sub
from latent_comm.mechanisms.h01_legacy.types import OperatorPacket
from latent_comm.mechanisms.h07_legacy.types import ValueType,CompiledProgram
from latent_comm.mechanisms.h14_legacy.types import SkillGrammar
from latent_comm.mechanisms.h18_legacy.types import GraphCandidate
from latent_comm.mechanisms.h22_legacy.types import PartitionState,StateReference
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase
@dataclass(frozen=True)
class ProtocolLanguageInput:
    grammar: SkillGrammar
    skill_name: str
    arguments: tuple[str,...]
    input_types: tuple[tuple[str,ValueType],...]
    operators: tuple[tuple[str,OperatorPacket],...]
    graph: GraphCandidate
    graph_input_node: str
    partition: PartitionState
    state_reference: StateReference
    actor: str
    task_family: str
    scope: Scope
    versions: VersionSet
@dataclass(frozen=True)
class CompiledLanguage:
    request: ProtocolLanguageInput
    graph_schedule: tuple[str,...]
    graph_cost: int
    input_state: tuple[float,...]
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class ExpandedLanguage:
    source: CompiledLanguage
    program: CompiledProgram
    affine_witness: tuple[float,float]
    @property
    def versions(self):return self.source.versions
@dataclass(frozen=True)
class BudgetedLanguage:
    expanded: ExpandedLanguage
    declared_execution_cost: int
    @property
    def versions(self):return self.expanded.versions
@dataclass(frozen=True)
class LanguageExecution:
    budgeted: BudgetedLanguage
    program_value: tuple[float,...]
    graph_value: float
    trace: tuple
    @property
    def versions(self):return self.budgeted.versions
@dataclass(frozen=True)
class ProtocolLanguageReadout:
    observation: tuple[float,...]
    affine_witness: tuple[float,float]
    lowered_opcodes: tuple[str,...]
    graph_cost: int
    program_steps: int
    owner: str
    status: str
    versions: VersionSet

def compile(value):
    from latent_comm.mechanisms.h18_legacy.reference import validate_graph
    from latent_comm.mechanisms.h22_legacy.reference import resolve_reference
    value.versions.require('state','frame','ontology','isa','world','task','evidence')
    if any(x.versions!=value.versions for x in (value.grammar,value.graph,value.partition)):raise ContractError('VersionMismatch','compiler, topology and ownership must share one semantic snapshot')
    if value.grammar.base_isa!=value.versions.isa or value.graph.semantic_changes:raise ContractError('UnboundMigration','topology cannot quietly change ontology, ISA or learning rule')
    order,cost=validate_graph(value.graph);state=resolve_reference(value.partition,value.state_reference,actor=value.actor,write=True)
    if len(state)!=1 or {n.node_id for n in value.graph.nodes if n.operation=='input'}!={value.graph_input_node}:raise ContractError('TypeViolation','C08 affine certificate uses one explicitly owned scalar input')
    if len(value.graph.nodes)>16:raise ContractError('BudgetExhausted','finite composition graph certificate limited to sixteen nodes')
    return CompiledLanguage(value,order,cost,state)
def expand_macro(value):
    from latent_comm.mechanisms.h14_legacy.reference import expand
    q=value.request;program=expand(q.grammar,q.skill_name,q.arguments,q.input_types,scope=q.scope,task=q.task_family)
    # Prove agreement of the declared affine sublanguage by propagating exact
    # symbolic coefficient/bias pairs, not by fitting a few numeric probes.
    types=dict(q.input_types);ops=dict(q.operators)
    if len(ops)!=len(q.operators) or set(types)!={'state'}|set(ops) or types['state']!=ValueType('state',1,q.versions.frame):raise ContractError('UnboundReference','one state and explicit operator bindings only')
    forms={'state':(1.,0.)};meter=StepBudget().meter()
    for name,op in ops.items():
        if len(op.U)!=1 or op.nonlinearity!='identity' or op.versions!=q.versions or types[name]!=ValueType('operator',1,q.versions.frame):raise ContractError('UnsupportedCertificate','affine proof does not establish nonlinear or cross-frame equivalence')
        op.scope.check(q.actor,writes=frozenset({'Z'}))
    for node in program.packet.nodes:
        meter.consume(steps=1)
        if node.opcode!='APPLY_OPERATOR' or node.inputs[0] not in forms or node.inputs[1] not in ops:raise ContractError('UnsupportedCertificate','only typed affine operator terms can be certified here')
        op=ops[node.inputs[1]];a=1+op.alpha*sum(u*v for u,v in zip(op.U[0],op.V[0]));b=op.alpha*sum(u*c for u,c in zip(op.U[0],op.bias));x,y=forms[node.inputs[0]];forms[node.node_id]=(a*x,a*y+b)
    if program.packet.result_id not in forms:raise ContractError('UnboundReference','program result must be an affine state')
    graph_forms={};nodes={n.node_id:n for n in q.graph.nodes}
    for name in value.graph_schedule:
        meter.consume(steps=1);op=nodes[name].operation;args=[graph_forms[a] for a,b,_ in sorted(q.graph.edges,key=lambda e:e[2]) if b==name]
        if op=='input':form=(1.,0.)
        elif op=='identity':form=args[0]
        elif op=='negate':form=tuple(-v for v in args[0])
        elif op=='sum':form=tuple(a+b for a,b in zip(*args))
        elif op=='product':
            (a,b),(c,d)=args
            if a*c!=0:raise ContractError('UnsupportedCertificate','nonlinear graph product is not an affine macro certificate')
            form=(a*d+b*c,b*d)
        graph_forms[name]=form
    form=forms[program.packet.result_id]
    if norm(sub(form,graph_forms[q.graph.output_node]))>1e-12:raise ContractError('NoncommutingProgram','macro and topology have different affine functions')
    return ExpandedLanguage(value,program,form)
def budget_check(value):
    cost=value.source.graph_cost+value.program.worst_case_steps+len(value.program.packet.nodes)
    if cost>128:raise ContractError('BudgetExhausted','macro expansion must count both DSL nodes and nested operator work')
    return BudgetedLanguage(value,cost)
def execute(value):
    from latent_comm.mechanisms.h07_legacy.reference import execute as execute_program
    from latent_comm.mechanisms.h18_legacy.reference import evaluate_graph
    q=value.expanded.source.request;bindings={'state':value.expanded.source.input_state,**dict(q.operators)}
    result,trace=execute_program(value.expanded.program,bindings,actor=q.actor)
    graph_result,_=evaluate_graph(q.graph,{q.graph_input_node:value.expanded.source.input_state[0]})
    if abs(result[0]-graph_result)>1e-9:raise ContractError('NoncommutingProgram','runtime result violates compiled affine witness')
    return LanguageExecution(value,result,graph_result,trace)
def decode(value):
    q=value.budgeted.expanded.source.request
    return ProtocolLanguageReadout(value.program_value,value.budgeted.expanded.affine_witness,tuple(op for _,op in value.trace),value.budgeted.expanded.source.graph_cost,value.budgeted.expanded.program.worst_case_steps,q.actor,'AffineSubLanguageProvedAndExecuted',q.versions)
STAGES=(('compile',('H18','H22'),'ProtocolLanguageInput','CompiledLanguage','stop'),('expand_macro',('H07','H14'),'CompiledLanguage','ExpandedLanguage','stop'),('budget_check',('H07','H18'),'ExpandedLanguage','BudgetedLanguage','stop'),('execute',('H07','H18'),'BudgetedLanguage','LanguageExecution','differentiable'),('decode',('H07',),'LanguageExecution','ProtocolLanguageReadout','differentiable'))
def build_graph(versions):return linear_graph('C08',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','isa','task'),scope=('Z','F','O','P','Q','V','K','W','U','E'),obligations=('Finite affine sublanguage equivalence is not arbitrary-program equivalence.','Macro expansion and topology cannot grant new state ownership or edit base ISA.','Aggregate execution meter includes nested primitive work.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (ProtocolLanguageInput,CompiledLanguage,ExpandedLanguage,BudgetedLanguage,LanguageExecution,ProtocolLanguageReadout)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h07_legacy.losses import LEDGER as H07
    from latent_comm.mechanisms.h14_legacy.losses import LEDGER as H14
    from latent_comm.mechanisms.h18_legacy.losses import LEDGER as H18
    from latent_comm.mechanisms.h22_legacy.losses import LEDGER as H22
    return {'recipe':'C08','research_state':'NOT_RUN','phases':[objective_phase('typed_program',(('H07',H07,tuple(s.name for s in H07)),('H14',H14,tuple(s.name for s in H14)))),objective_phase('graph_discovery',(('H18',H18,tuple(s.name for s in H18)),)),objective_phase('ownership_policy',(('H22',H22,tuple(s.name for s in H22)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES}}
