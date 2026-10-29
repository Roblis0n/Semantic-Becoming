"""W09: bounded expression programs and optimistic transaction conflicts."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode,FixtureBudget
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    argument: float=3.
    conflicting_read: bool=False
    multiplier: float=2.

def signature(p: Parameters) -> StructureSignature:
    return StructureSignature('programs','v1','macro_and_transaction:'+('conflict' if p.conflicting_read else 'commit'),operation_family=('let','add','mul','read_version','commit'))

def sample_parameters(signature_value,rng) -> Parameters:
    return Parameters(float(rng.randint(-3,3)),signature_value.program_template.endswith('conflict'),float(rng.randint(1,3)))

def evaluate(expr: tuple,env: dict[str,float],meter) -> float:
    meter.consume(steps=1);op=expr[0]
    if op=='const':return float(expr[1])
    if op=='var':
        if expr[1] not in env:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'unbound program variable')
        return env[expr[1]]
    if op in {'add','mul'}:
        a=evaluate(expr[1],env,meter);b=evaluate(expr[2],env,meter);return a+b if op=='add' else a*b
    if op=='let':
        bound=evaluate(expr[2],env,meter);return evaluate(expr[3],{**env,expr[1]:bound},meter)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown base instruction')

def build_fixture(p: Parameters=Parameters()):
    # Expansion substitutes into a fresh lexical binding, never into caller names.
    macro=('mul',('var','arg'),('const',p.multiplier));lowered=('let','fresh:arg',('const',p.argument),('add',('mul',('var','fresh:arg'),('const',p.multiplier)),('const',1.)))
    value=evaluate(lowered,{'arg':99.},FixtureBudget().meter())
    snapshot={'concept':1,'reader':1};current={'concept':2 if p.conflicting_read else 1,'reader':1};writes={'concept':('new_predicate',2),'reader':('new_reader',2)}
    conflicts=tuple(k for k,v in snapshot.items() if current[k]!=v);committed=not conflicts
    fields={'task':'lower a lexical macro and commit coordinated versions only if reads remain valid','macro':macro,'caller_argument':p.argument,'snapshot':tuple(snapshot.items()),'current_versions':tuple(current.items()),'write_keys':tuple(writes)}
    targets={'lowered_ast':lowered,'program_output':value,'commit_status':'committed' if committed else 'aborted','conflict_keys':conflicts,'visible_versions':tuple((k,2) for k in current) if committed else tuple(current.items()),'partial_commit':False}
    contract=ProjectionContract(('task','write_keys'),('macro','snapshot'),('caller_argument','current_versions'),(('task','public macro/transaction semantics'),('write_keys','public intended transaction keys, no new host permission')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1'),fixture_name=str(p.conflicting_read))
