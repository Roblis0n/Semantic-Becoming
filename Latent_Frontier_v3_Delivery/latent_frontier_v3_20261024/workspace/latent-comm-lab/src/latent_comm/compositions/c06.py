"""C06: typed skill expansion, nonlinear joint messages and optional exact compilation."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet,StepBudget,Scope
from latent_comm.core.finite import matvec,matmul,transpose,eye,add,scale
from latent_comm.mechanisms.h01_legacy.types import OperatorPacket
from latent_comm.mechanisms.h14_legacy.types import SkillGrammar
from latent_comm.mechanisms.h07_legacy.types import ValueType,CompiledProgram
from latent_comm.mechanisms.h10_legacy.types import Hyperedge
from latent_comm.mechanisms.h19_legacy.types import TeacherTrace,AffineSkill
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase
@dataclass(frozen=True)
class JointSkillInput:
    grammar: SkillGrammar
    skill_name: str
    operator: OperatorPacket
    members: tuple[tuple[str,tuple[float,...]],...]
    hyperedge: Hyperedge
    readout: tuple[tuple[float,...],...]
    trace: TeacherTrace
    unseen_instance_ids: frozenset[str]
    consolidate: bool
    step: int
    task_family: str
    scope: Scope
    versions: VersionSet
@dataclass(frozen=True)
class ParsedSkill:
    request: JointSkillInput
    compiled: CompiledProgram
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class BoundSkills:
    parsed: ParsedSkill
    member_states: tuple[tuple[str,tuple[float,...]],...]
    execution_traces: tuple
    @property
    def versions(self):return self.parsed.versions
@dataclass(frozen=True)
class JointMessage:
    bound: BoundSkills
    message: tuple[float,...]
    evidence_atoms: frozenset[str]
    @property
    def versions(self):return self.bound.versions
@dataclass(frozen=True)
class JointDecoded:
    joint: JointMessage
    observation: tuple[float,...]
    @property
    def versions(self):return self.joint.versions
@dataclass(frozen=True)
class JointSkillReadout:
    observation: tuple[float,...]
    joint_message: tuple[float,...]
    compiled_local_skill: AffineSkill | None
    trace_id: str
    evidence_atoms: frozenset[str]
    status: str
    versions: VersionSet
    research_state: str='NOT_RUN'

def skill_parse(value):
    from latent_comm.mechanisms.h14_legacy.reference import expand,lower_for_reader
    from latent_comm.mechanisms.h07_legacy.reference import SIGNATURES
    value.versions.require('state','frame','ontology','isa','world','task','evidence')
    if any(obj.versions!=value.versions for obj in (value.grammar,value.operator,value.hyperedge,value.trace)):raise ContractError('VersionMismatch','skill, operator, joint factor and teacher must share semantic versions')
    if value.grammar.base_isa!=value.versions.isa:raise ContractError('VersionMismatch','macro expansion cannot silently replace the base ISA')
    if len(value.members)>6 or len(dict(value.members))!=len(value.members) or set(dict(value.members))!=set(value.hyperedge.members):raise ContractError('MissingMember','bind each declared hyperedge role exactly once')
    if value.trace.task_family!=value.task_family or value.trace.operation_ids!=(value.skill_name,):raise ContractError('MissingProvenance','teacher trace must name this skill and task')
    d=len(value.operator.U);inputs=(('state',ValueType('state',d,value.versions.frame)),('operator',ValueType('operator',d,value.versions.frame)))
    compiled=expand(value.grammar,value.skill_name,('state','operator'),inputs,scope=value.scope,task=value.task_family)
    compiled=lower_for_reader(value.grammar,compiled,supported_isa=value.versions.isa,supported_opcodes=frozenset(SIGNATURES))
    if any(n.opcode!='APPLY_OPERATOR' or n.inputs[1]!='operator' for n in compiled.packet.nodes):raise ContractError('UnsupportedLocalSkill','C06 local finite path accepts typed repeated operator actions; other grammars remain separate recipes')
    previous='state'
    for node in compiled.packet.nodes:
        if node.inputs[0]!=previous:raise ContractError('UnsupportedLocalSkill','optional affine compilation requires a linear state chain, not discarded DAG branches')
        previous=node.node_id
    if compiled.packet.result_id!=previous:raise ContractError('UnsupportedLocalSkill','declared result must retain the entire local chain')
    return ParsedSkill(value,compiled)
def bind(value):
    from latent_comm.mechanisms.h07_legacy.reference import execute
    q=value.request;states=[];traces=[]
    for name,state in q.members:
        result,trace=execute(value.compiled,{'state':state,'operator':q.operator});states.append((name,result));traces.append((name,trace))
    return BoundSkills(value,tuple(states),tuple(traces))
def hyperedge_apply(value):
    from latent_comm.mechanisms.h10_legacy.reference import compose_hyperedge
    q=value.parsed.request
    atoms=frozenset().union(*(s for _,s in q.hyperedge.evidence_support))
    if not atoms<=q.trace.evidence_sources:raise ContractError('MissingProvenance','joint teacher must preserve each member evidence atom')
    return JointMessage(value,compose_hyperedge(q.hyperedge,dict(value.member_states)),atoms)
def decode(value):return JointDecoded(value,matvec(value.bound.parsed.request.readout,value.message))
def optional_consolidate(value):
    from latent_comm.mechanisms.h19_legacy.reference import validate_training_partition,compile_affine_operations
    q=value.joint.bound.parsed.request;skill=None;status='JointMessageOnly'
    if q.consolidate:
        validate_training_partition((q.trace,),q.unseen_instance_ids,step=q.step,versions=q.versions)
        if q.operator.nonlinearity!='identity':status='NonlinearSkillRequiresFutureDistillation'
        else:
            # Only the local affine grammar is compiled. The multilinear joint
            # interaction is not falsely represented as an affine skill.
            op=q.operator;product=matmul(op.U,transpose(op.V));a=tuple(tuple(x+op.alpha*y for x,y in zip(row,p)) for row,p in zip(eye(len(op.U)),product));b=scale(matvec(op.U,op.bias),op.alpha)
            operations=tuple((node.node_id,a,b) for node in value.joint.bound.parsed.compiled.packet.nodes)
            if not operations:raise ContractError('EmptyOperations','cannot consolidate an empty computation')
            skill=compile_affine_operations(operations);status='LocalAffineCompiledJointFactorRetained'
    return JointSkillReadout(value.observation,value.joint.message,skill,q.trace.trace_id,value.joint.evidence_atoms,status,q.versions)
STAGES=(('skill_parse',('H14',),'JointSkillInput','ParsedSkill','stop'),('bind',('H01','H14'),'ParsedSkill','BoundSkills','differentiable'),('hyperedge_apply',('H10',),'BoundSkills','JointMessage','differentiable'),('decode',('H01','H10'),'JointMessage','JointDecoded','differentiable'),('optional_consolidate',('H19',),'JointDecoded','JointSkillReadout','stop'))
def build_graph(versions):return linear_graph('C06',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','isa','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),obligations=('Joint effects remain separate from individual affine skills.','Finite affine compilation is not distillation or unseen-instance transfer evidence.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (JointSkillInput,ParsedSkill,BoundSkills,JointMessage,JointDecoded,JointSkillReadout)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h01_legacy.losses import LEDGER as H01
    from latent_comm.mechanisms.h10_legacy.losses import LEDGER as H10
    from latent_comm.mechanisms.h14_legacy.losses import LEDGER as H14
    from latent_comm.mechanisms.h19_legacy.losses import LEDGER as H19
    return {'recipe':'C06','research_state':'NOT_RUN','phases':[objective_phase('typed_local_skill',(('H01',H01,tuple(s.name for s in H01)),('H14',H14,tuple(s.name for s in H14)))),objective_phase('joint_message',(('H10',H10,tuple(s.name for s in H10)),)),objective_phase('trace_distillation',(('H19',H19,tuple(s.name for s in H19)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES}}
