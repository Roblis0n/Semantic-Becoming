from dataclasses import replace
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import topological_order,matvec
from latent_comm.compiler.source import SourceDocument
from .types import *
SIGNATURES={'READ_SLOT':(('state',),'state'),'APPLY_OPERATOR':(('state','operator'),'state'),'REFINE_BELIEF':(('belief','likelihoods'),'belief'),'ADD_CONSTRAINT':(('field','constraint'),'field'),'SOLVE_FIELD':(('field',),'state'),'BRANCH':(('state',),'branches'),'MERGE_SCOPED':(('branches',),'state'),'CONTINUE':(('continuation',),'continuation'),'DECODE':(('state','readout'),'observations')}
FRONTIER={'PROPOSE_CONCEPT':'H27','REWRITE_QUESTION':'H29','APPLY_PLASTICITY':'H38','COMPILE_MACRO':'H40'}
def parse(text,*,versions,scope):
    document=SourceDocument(text,'H07');obj=document.value
    if set(obj)!={'nodes','input_types','result_id'}:raise ContractError('InvalidSchema','closed program fields')
    def typ(v):return ValueType(**v)
    nodes=[]
    for i,n in enumerate(obj['nodes']):
        if set(n)-{'node_id','opcode','inputs','output_type','bound'}:raise ContractError('InvalidSchema','unexpected instruction field',path=f'/nodes/{i}')
        nodes.append(Instruction(n['node_id'],n['opcode'],tuple(n['inputs']),typ(n['output_type']),n.get('bound',1)))
    return ProgramPacket(tuple(nodes),tuple((k,typ(v)) for k,v in obj['input_types'].items()),obj['result_id'],versions,scope)
def compile_program(packet,*,actor='receiver',budget=StepBudget()):
    packet.scope.check(actor,writes=frozenset({'Z'}));types=dict(packet.input_types);nodes={n.node_id:n for n in packet.nodes}
    if len(nodes)!=len(packet.nodes) or set(nodes)&set(types):raise ContractError('DuplicateBinding','SSA names must be unique')
    edges=tuple((i,n.node_id) for n in packet.nodes for i in n.inputs if i in nodes)
    order=topological_order(tuple(nodes),edges);steps=0
    for key in order:
        n=nodes[key]
        if n.opcode not in SIGNATURES:raise ContractError('UnsupportedOpcode','frontier nodes must lower through shared compiler; arbitrary system commands forbidden',path=key)
        expected,out=SIGNATURES[n.opcode]
        if any(i not in types for i in n.inputs) or tuple(types[i].kind for i in n.inputs)!=expected or n.output_type.kind!=out:raise ContractError('TypeViolation','instruction signature mismatch',path=key)
        if not 1<=n.bound<=128 or (n.opcode not in ('SOLVE_FIELD','CONTINUE') and n.bound!=1):raise ContractError('UnboundedLoop','only finite field/continuation loops allowed',path=key)
        if out=='state' and n.opcode in ('READ_SLOT','APPLY_OPERATOR') and n.output_type!=types[n.inputs[0]]:raise ContractError('FrameMismatch','no implicit dimension/frame cast',path=key)
        if n.opcode=='APPLY_OPERATOR':
            state_type,operator_type=(types[i] for i in n.inputs)
            if (operator_type.dimension,operator_type.frame)!=(state_type.dimension,state_type.frame):raise ContractError('FrameMismatch','operator and state must share explicit dimension/frame',path=key)
        if n.opcode in ('SOLVE_FIELD','MERGE_SCOPED'):
            source_type=types[n.inputs[0]]
            if source_type.dimension is not None and (source_type.dimension,source_type.frame)!=(n.output_type.dimension,n.output_type.frame):raise ContractError('FrameMismatch','output cannot reinterpret source coordinates',path=key)
        if n.opcode=='ADD_CONSTRAINT':
            a,b=(types[i] for i in n.inputs)
            if a!=n.output_type or (a.dimension,a.frame)!=(b.dimension,b.frame):raise ContractError('FrameMismatch','field/constraint axes differ',path=key)
        types[key]=n.output_type;steps+=n.bound
    if steps>budget.max_steps or packet.result_id not in types:raise ContractError('BudgetExhausted','missing result or excessive worst-case steps')
    return CompiledProgram(packet,order,steps)
def execute(program,inputs,*,actor='receiver',budget=StepBudget()):
    program=compile_program(program.packet,actor=actor,budget=budget);p=program.packet;values=dict(inputs);trace=[];meter=budget.meter();nodes={n.node_id:n for n in p.nodes}
    if set(values)!=set(dict(p.input_types)):raise ContractError('UnboundReference','exact declared program inputs required')
    from latent_comm.mechanisms.h01_legacy.reference import apply
    from latent_comm.mechanisms.h03_legacy.reference import prefix_posterior_update
    from latent_comm.mechanisms.h04_legacy.reference import solve_field
    from latent_comm.mechanisms.h05_legacy.reference import resume
    for name,typ in p.input_types:validate_bound_input(values[name],typ,p.versions)
    for key in program.schedule:
        n=nodes[key];meter.consume(steps=n.bound);v=[values[x] for x in n.inputs];local_budget=StepBudget(max_steps=n.bound,max_dimension=budget.max_dimension,max_cases=budget.max_cases,max_branches=budget.max_branches)
        if n.opcode=='READ_SLOT':out=v[0]
        elif n.opcode=='APPLY_OPERATOR':out=apply(v[0],v[1],actor=actor,budget=local_budget)[0]
        elif n.opcode=='REFINE_BELIEF':out=prefix_posterior_update(*v)
        elif n.opcode=='ADD_CONSTRAINT':out=replace(v[0],sources=v[0].sources+(v[1],))
        elif n.opcode=='SOLVE_FIELD':out=solve_field(v[0],steps=n.bound,step_size=.01,budget=local_budget).state
        elif n.opcode=='BRANCH':out=(v[0],v[0])
        elif n.opcode=='MERGE_SCOPED':
            if not v[0] or any(x!=v[0][0] for x in v[0]):raise ContractError('Conflict','distinct branches retained; no silent average')
            out=v[0][0]
        elif n.opcode=='CONTINUE':out=resume(v[0],max_operations=n.bound,budget=local_budget)
        elif n.opcode=='DECODE':out=matvec(v[1],v[0])
        values[key]=out;trace.append((key,n.opcode))
    return values[p.result_id],tuple(trace)
def lower_frontier(opcode,recipe):
    from latent_comm.compiler.pipeline import compile_recipe
    if opcode not in FRONTIER or FRONTIER[opcode] not in recipe.get('mechanisms',[]):raise ContractError('LoweringFailure','frontier extension needs its own typed recipe and mechanism')
    return compile_recipe(recipe,source='H07:'+opcode)


def validate_bound_input(value,typ,versions):
    from latent_comm.core.finite import vector,matrix
    from latent_comm.mechanisms.h01_legacy.types import OperatorPacket
    from latent_comm.mechanisms.h03_legacy.types import BeliefPacket
    from latent_comm.mechanisms.h04_legacy.types import ConstraintField,LocalConstraint
    from latent_comm.mechanisms.h05_legacy.types import ContinuationPacket
    if typ.kind=='state':
        if len(vector(value))!=typ.dimension:raise ContractError('DimensionMismatch','bound state differs from declared coordinate dimension')
    elif typ.kind=='operator':
        if not isinstance(value,OperatorPacket) or len(value.U)!=typ.dimension or value.versions.frame!=typ.frame or not value.versions.matches(versions,('frame','ontology','isa')):raise ContractError('FrameMismatch','actual bound operator must match declared type and program versions')
    elif typ.kind=='field':
        if not isinstance(value,ConstraintField) or len(value.anchor)!=typ.dimension or value.versions.frame!=typ.frame:raise ContractError('FrameMismatch','actual field coordinate binding')
    elif typ.kind=='constraint':
        if not isinstance(value,LocalConstraint) or len(value.A[0])!=typ.dimension or value.frame!=typ.frame:raise ContractError('FrameMismatch','actual constraint coordinate binding')
    elif typ.kind=='belief':
        if not isinstance(value,BeliefPacket) or not value.versions.matches(versions,('task','evidence')):raise ContractError('VersionMismatch','belief semantics differ')
    elif typ.kind=='continuation':
        if not isinstance(value,ContinuationPacket) or not value.versions.matches(versions,('state','isa','task','evidence')):raise ContractError('VersionMismatch','continuation snapshot differs')
    elif typ.kind=='readout':matrix(value)
    elif typ.kind=='likelihoods':
        import math
        if not isinstance(value,(tuple,list)) or not 1<=len(value)<=64 or any(type(x) not in (int,float) or math.isnan(x) or x>0 for x in value):raise ContractError('TypeViolation','ordered finite or negative-infinity branch log-likelihood vector required')
    elif typ.kind=='branches':
        if not 1<=len(value)<=64:raise ContractError('BudgetExhausted','bounded branch input')
        for state in value:vector(state)
    else:raise ContractError('TypeViolation','unsupported input type')
