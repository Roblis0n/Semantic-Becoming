"""W10: exact finite cooperative value and correlated-source support."""
from dataclasses import dataclass
from itertools import combinations
import math
from latent_comm.core import VersionSet,ContractError,ErrorCode
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    members: tuple[str,...]=('a','b','c')
    synergy: float=2.
    shared_source: bool=True
    source_probability: float=.8

def signature(p: Parameters) -> StructureSignature:
    return StructureSignature('coalitions','v1','pair_synergy:'+('shared_source' if p.shared_source else 'independent_sources'),operation_family=('coalition_value','shapley','support_union'))

def sample_parameters(signature_value,rng) -> Parameters:
    return Parameters(('a','b','c'),float(rng.randint(1,3)),signature_value.program_template.endswith('shared_source'),.8)

def build_fixture(p: Parameters=Parameters()):
    n=len(p.members)
    if not 2<=n<=6 or len(set(p.members))!=n or not 0<=p.source_probability<=1:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'finite coalition or probability invalid')
    subsets=[frozenset(s) for k in range(n+1) for s in combinations(p.members,k)]
    values={s:float(len(s))+(p.synergy if {p.members[0],p.members[1]}<=s else 0.) for s in subsets}
    contribution={}
    for member in p.members:
        phi=0.
        for s in subsets:
            if member in s:continue
            weight=math.factorial(len(s))*math.factorial(n-len(s)-1)/math.factorial(n)
            phi+=weight*(values[s|{member}]-values[s])
        contribution[member]=phi
    probability=p.source_probability if p.shared_source else 1-(1-p.source_probability)**2
    rows=tuple((tuple(sorted(s)),v) for s,v in values.items());fields={'task':'allocate internal task credit without duplicating evidence','players':p.members,'credit_is_money':False,'sender_values':rows[::2],'receiver_values':rows[1::2],'source_equivalence':((True,True),(True,True)) if p.shared_source else ((True,False),(False,True))}
    targets={'contributions':tuple(contribution.items()),'efficiency_residual':sum(contribution.values())-values[frozenset(p.members)],'support_union_probability':probability,'coalition_values':rows,'dependence':'identical_atom' if p.shared_source else 'explicit_independence'}
    contract=ProjectionContract(('task','players','credit_is_money','source_equivalence'),('sender_values',),('receiver_values',),(('task','public coalition allocation goal'),('players','public coalition membership'),('credit_is_money','explicit nonmonetary interpretation'),('source_equivalence','anonymized known shared-source relation, not source IDs or assumed independence')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',world='w1',task='t1',evidence='e1'),fixture_name=str(p.shared_source))
