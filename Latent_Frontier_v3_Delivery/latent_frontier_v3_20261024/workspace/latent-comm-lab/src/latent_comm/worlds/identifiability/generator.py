"""W12: distinguishable hypotheses, conditional exclusions and retraction."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    allowed_queries: tuple[int,...]=(0,1)
    hard_even_constraint: bool=True
    retract_even: bool=False

def signature(p: Parameters) -> StructureSignature:
    return StructureSignature('identifiability','v1','signed_linear:'+('distinguishable' if any(x!=0 for x in p.allowed_queries) else 'unidentifiable'),operation_family=('query_partition','conditional_exclude','retract'))

def sample_parameters(signature_value,rng) -> Parameters:
    return Parameters((0,) if signature_value.program_template.endswith('unidentifiable') else (0,rng.choice((-1,1))),True,bool(rng.randint(0,1)))

def build_fixture(p: Parameters=Parameters()):
    if not p.allowed_queries or len(p.allowed_queries)>64:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'finite allowed query set required')
    response={q:(q,-q) for q in p.allowed_queries};worst={q:2 if a==b else 1 for q,(a,b) in response.items()};selected=min(p.allowed_queries,key=lambda q:(worst[q],abs(q),q))
    domain=(1,2,3,4);excluded=(1,3) if p.hard_even_constraint and not p.retract_even else ();remaining=tuple(x for x in domain if x not in excluded)
    fields={'task':'request distinguishing evidence only within allowed local queries','hypothesis_programs':('y=x','y=-x'),'allowed_queries':p.allowed_queries,'current_observation':(0,0),'constraint':'even' if p.hard_even_constraint else 'soft_even_preference','assumption_active':not p.retract_even}
    targets={'query_response_table':tuple(response.items()),'selected_query':selected,'remaining_worst_case':worst[selected],'identifiable':worst[selected]==1,'excluded_domain':excluded,'remaining_domain':remaining,'selection_rule':'minimax_partition_no_prior','external_action_executed':False}
    contract=ProjectionContract(('task','allowed_queries','current_observation'),('hypothesis_programs',),('constraint','assumption_active'),(('task','public identification question'),('allowed_queries','host-authorized finite local query domain'),('current_observation','shared observation, not hidden solution')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',world='w1',task='t1',evidence='e1'),fixture_name=str(p))
