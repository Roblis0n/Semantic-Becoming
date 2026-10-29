"""C10: anchored obstruction → executable counterexample → concept → migration.

The output is a versioned proposal branch. It never upgrades disagreement to
truth or discards the prior ontology/belief merely because a predicate was found.
"""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h03_legacy.types import BeliefPacket
from latent_comm.mechanisms.h26_sheaf.types import SheafPacket,GluingCandidate
from latent_comm.mechanisms.h27_ontology.types import OntologySnapshot,Predicate,DistinctionWitness,OntologyDelta
from latent_comm.mechanisms.h36_disagreement.types import ScopedClaim,Counterexample
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference

@dataclass(frozen=True)
class DisagreementInput:
    belief: BeliefPacket
    local_sections: SheafPacket
    claim: ScopedClaim
    ontology: OntologySnapshot
    records: tuple[tuple[int,dict],...]
    atoms: tuple[Predicate,...]
    next_ontology_version: str
    candidate_limit: int=16
    @property
    def versions(self):return self.belief.versions

@dataclass(frozen=True)
class LocalInterpretations:
    source: DisagreementInput
    normalized_weights: tuple

@dataclass(frozen=True)
class Obstruction:
    interpretations: LocalInterpretations
    gluing: GluingCandidate

@dataclass(frozen=True)
class CounterexamplePair:
    obstruction: Obstruction
    counterexamples: tuple[Counterexample,...]
    pair_indices: tuple[tuple[int,int],...]
    records: tuple[dict,...]
    status: str

@dataclass(frozen=True)
class ConceptProposal:
    challenge: CounterexamplePair
    witness: DistinctionWitness | None
    status: str
    obligation: str

@dataclass(frozen=True)
class MigrationProposal:
    concept: ConceptProposal
    delta: OntologyDelta | None
    status: str

@dataclass(frozen=True)
class MultiDomainBelief:
    historical_belief: BeliefPacket
    proposal_belief: BeliefPacket | None
    prior_ontology: OntologySnapshot
    proposed_ontology: OntologySnapshot | None
    residual_conflicts: tuple
    explanation: str
    reader_migrations: tuple
    status: str
    consensus_claimed: bool=False


def local_interpretations(value):
    from latent_comm.mechanisms.h03_legacy.reference import normalized_logs
    value.versions.require('state','frame','ontology','task','evidence')
    if value.ontology.version!=value.versions.ontology or any(b.ontology_version!=value.ontology.version for b in value.belief.branches if not b.unknown):raise ContractError('VersionMismatch','local belief and ontology readers differ')
    if len(value.records)>16 or not 1<=value.candidate_limit<=32:raise ContractError('BudgetExhausted','C10 declares at most 16 records and 32 concept candidates')
    if len(dict(value.records))!=len(value.records) or set(dict(value.records))!=set(value.claim.domain):raise ContractError('ScopeMismatch','counterexample domain and feature records must coincide exactly')
    return LocalInterpretations(value,normalized_logs(value.belief))


def find_obstruction(value):
    from latent_comm.mechanisms.h26_sheaf.reference import glue
    return Obstruction(value,glue(value.source.local_sections,budget=StepBudget(max_steps=32,max_cases=32)))


def executable_counterexample(value):
    from latent_comm.mechanisms.h36_disagreement.reference import find_counterexamples,execute
    from latent_comm.mechanisms.h27_ontology.reference import evaluate
    q=value.interpretations.source;records=tuple(r for _,r in q.records)
    if value.gluing.status!='NoGlobalSection':return CounterexamplePair(value,(),(),records,'NoObstructionOnDeclaredOverlaps')
    bad,_=find_counterexamples(q.claim,budget=StepBudget(max_steps=16,max_cases=16))
    pairs=[];positions={x:i for i,(x,_) in enumerate(q.records)}
    # Minimality is only within this finite executable critic domain.
    for counterexample in bad:
        a=positions[counterexample.value]
        for x,row in q.records:
            b=positions[x]
            if execute(q.claim.program,x) and all(evaluate(c.predicate,records[a])==evaluate(c.predicate,row) for c in q.ontology.concepts):pairs.append((a,b));break
        if pairs:break
    return CounterexamplePair(value,bad,tuple(pairs),records,'ExpressionGapWitness' if pairs else 'UnresolvedDispute')


def propose_concept(value):
    from latent_comm.mechanisms.h27_ontology.reference import search_concept
    q=value.obstruction.interpretations.source
    if not value.pair_indices:return ConceptProposal(value,None,value.status,'No verified old-language-equivalent pair; preserve the original domains.')
    support=tuple(dict.fromkeys(s for edge in q.local_sections.restrictions for s in edge.support))
    try:witness=search_concept(q.ontology,value.records,value.pair_indices,q.atoms,concept_id='concept:'+q.next_ontology_version,evidence=support,candidate_limit=q.candidate_limit,description_weight=.001,budget=StepBudget(max_steps=32,max_cases=32))
    except ContractError as error:
        if error.failure.code not in {'GrammarExhausted','BudgetExhausted'}:raise
        return ConceptProposal(value,None,'NoCandidateWithinGrammar',str(error))
    return ConceptProposal(value,witness,'ExecutableConceptProposed','A separating predicate explains this distinction; it does not prove the cause of all conflicts.')


def prepare_migration(value):
    from latent_comm.mechanisms.h27_ontology.reference import revise_ontology
    q=value.challenge.obstruction.interpretations.source
    if value.witness is None:return MigrationProposal(value,None,value.status)
    # Existing readers continue to read their original definitions. The new
    # definition is additive; retirement would require an explicit consumer map.
    delta=revise_ontology(q.ontology,q.next_ontology_version,(value.witness.definition,))
    return MigrationProposal(value,delta,'VersionedBranchPrepared')


def retain_disagreement(value):
    from latent_comm.mechanisms.h03_legacy.reference import normalized_logs
    q=value.concept.challenge.obstruction.interpretations.source;gluing=value.concept.challenge.obstruction.gluing
    proposal=None
    if value.delta is not None:
        weights=normalized_logs(q.belief)
        # Preserve branch identity, support and normalized mass; no artificial
        # likelihood boost from inventing a predicate on the same observations.
        branches=tuple(replace(b,log_weight=w,ontology_version=value.delta.after.version) if not b.unknown else replace(b,log_weight=w) for b,w in zip(q.belief.branches,weights))
        proposal=replace(q.belief,branches=branches,versions=replace(q.versions,ontology=value.delta.after.version))
    return MultiDomainBelief(q.belief,proposal,q.ontology,None if value.delta is None else value.delta.after,gluing.residuals,value.concept.obligation,() if value.delta is None else value.delta.reader_migrations,value.status)


STAGES=(('local_interpretations',('H03',),'DisagreementInput','LocalInterpretations','stop'),('find_obstruction',('H26',),'LocalInterpretations','Obstruction','stop'),('executable_counterexample',('H36',),'Obstruction','CounterexamplePair','enumeration'),('propose_concept',('H27',),'CounterexamplePair','ConceptProposal','enumeration'),('prepare_migration',('H27',),'ConceptProposal','MigrationProposal','stop'),('retain_disagreement',('H03','H26'),'MigrationProposal','MultiDomainBelief','stop'))

def build_graph(versions):
    return linear_graph('C10',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('IR versions identify the prior snapshot; MigrationProposal carries explicit before/after ontology alternatives.','No candidate is a grammar-relative result, not global impossibility.','A prepared ontology branch requires an explicit later commit; disagreement remains available.'))


def run_reference(request,*,budget=StepBudget()):
    types={c.__name__:c for c in (DisagreementInput,LocalInterpretations,Obstruction,CounterexamplePair,ConceptProposal,MigrationProposal,MultiDomainBelief)}
    return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},types,budget=budget)


def describe_training():
    from .contracts import objective_phase
    from latent_comm.mechanisms.h26_sheaf.losses import LOSS_SPECS as H26
    from latent_comm.mechanisms.h27_ontology.losses import LOSS_SPECS as H27
    return {'recipe':'C10','research_state':'NOT_RUN','phases':[
        objective_phase('local_restrictions',(('H26',H26,('local', 'overlap', 'obstruction')),)),
        objective_phase('predicate_structure_search',(('H27',H27,('description',)),)),
        objective_phase('concept_behavior',(('H27',H27,('distinction', 'behavior', 'drift')),)),
    ],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'frozen':['base_models','immutable_source_definitions'],'structure_search':'enumeration is distinct from differentiable phases','execution':'unified gated runner only; no joint global loss by default'}
