"""W03: executable predicates whose old concept fails to distinguish cases."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    rule: str='authorized_and_not_expired'
    rows: tuple[tuple[bool,bool],...]=((True,False),(True,True),(False,False))

def signature(p: Parameters) -> StructureSignature:
    if p.rule not in {'authorized_and_not_expired','authorized_only'}:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'unknown predicate program')
    return StructureSignature('concepts','v1',p.rule,concept_combination=('authorized','expired'),operation_family=('predicate','distinguish'))

def sample_parameters(signature_value,rng) -> Parameters:
    rows=[(True,False),(True,True),(False,bool(rng.randint(0,1)))];rng.shuffle(rows)
    return Parameters(signature_value.program_template,tuple(rows))

def build_fixture(p: Parameters=Parameters()):
    if not 1<=len(p.rows)<=64 or any(len(row)!=2 or any(type(v) is not bool for v in row) for row in p.rows):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'bounded Boolean feature rows required')
    labels=tuple(a and not e if p.rule=='authorized_and_not_expired' else a for a,e in p.rows)
    witness=tuple((i,j) for i in range(len(p.rows)) for j in range(i+1,len(p.rows)) if p.rows[i][0]==p.rows[j][0] and labels[i]!=labels[j])
    fields={'task':'find an executable distinction without altering the goal','old_feature':'authorized','observations':p.rows,'query_indices':tuple(range(len(p.rows)))}
    targets={'predicate_outputs':labels,'distinction_pairs':witness,'predicate_ast':('and',('feature','authorized'),('not',('feature','expired'))) if p.rule=='authorized_and_not_expired' else ('feature','authorized')}
    contract=ProjectionContract(('task','old_feature'),('observations',),('query_indices',),(('task','public concept distinction objective'),('old_feature','public previous ontology definition')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',ontology='o1',world='w1',task='t1',evidence='e1'),fixture_name=p.rule)
