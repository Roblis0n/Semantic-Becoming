"""W04: finite equations with separately checked soundness and completeness."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    square: int=4
    domain: tuple[int,...]=(-3,-2,-1,0,1,2,3)
    transform: str='positive_root_only'

def signature(p: Parameters) -> StructureSignature:
    if p.transform not in {'positive_root_only','both_roots','relax_nonnegative'}:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'unknown question transform')
    return StructureSignature('questions','v1','square_equation:'+p.transform,operation_family=('square','solution_transport'))

def sample_parameters(signature_value,rng) -> Parameters:
    n=rng.randint(1,3);return Parameters(n*n,tuple(range(-4,5)),signature_value.program_template.rsplit(':',1)[-1])

def build_fixture(p: Parameters=Parameters()):
    if not 1<=len(p.domain)<=64:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'finite answer domain required')
    original=tuple(x for x in p.domain if x*x==p.square)
    transformed=tuple(x for x in original if x>=0) if p.transform=='positive_root_only' else original if p.transform=='both_roots' else tuple(x for x in p.domain if x>=0)
    sound=set(transformed)<=set(original);complete=set(original)<=set(transformed)
    fields={'task':'rewrite a finite equation while preserving a declared answer relation','equation':('square_equals',p.square),'domain':p.domain,'transform':p.transform}
    targets={'original_solutions':original,'transformed_solutions':transformed,'sound':sound,'complete':complete,'relation':'equivalent' if sound and complete else 'sound_partial' if sound else 'incomplete_or_unsound','missing_answers':tuple(sorted(set(original)-set(transformed))),'unsound_answers':tuple(sorted(set(transformed)-set(original)))}
    contract=ProjectionContract(('task','domain'),('equation',),('transform',),(('task','public rewrite objective'),('domain','declared answer search domain')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1'),fixture_name=p.transform)
