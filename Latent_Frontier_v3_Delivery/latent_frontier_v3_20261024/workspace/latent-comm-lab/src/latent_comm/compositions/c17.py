"""C17: scoped exclusions, permission-first finite queries, explicit unknown posterior."""
from dataclasses import dataclass,replace
import math
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h02_legacy.types import QuadraticProgram,ResponseCapsule
from latent_comm.mechanisms.h03_legacy.types import BeliefPacket
from latent_comm.mechanisms.h45_identifiability.types import IdentificationState,QuerySpec,QuerySelection,PosteriorUpdate
from latent_comm.mechanisms.h46_negative_knowledge.types import ExclusionCapsule,ConditionalFeasibleRegion
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase

@dataclass(frozen=True)
class QueryCondition:
    query_id: str
    condition: float
    allowed: bool
    local_only: bool
    cost: float
@dataclass(frozen=True)
class IdentificationInput:
    hypotheses: tuple[tuple[int,QuadraticProgram],...]
    belief: BeliefPacket
    exclusions: tuple[ExclusionCapsule,...]
    assumptions: tuple[str,...]
    retracted: tuple[str,...]
    queries: tuple[QueryCondition,...]
    actual_local_program: QuadraticProgram
    anchor: float
    radius: float
    evidence_id: str
    versions: VersionSet
@dataclass(frozen=True)
class CandidateFamily:
    request: IdentificationInput
    prior: tuple[float,...]
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class ConditionalCandidates:
    family: CandidateFamily
    region: ConditionalFeasibleRegion
    @property
    def versions(self):return self.family.versions
@dataclass(frozen=True)
class AllowedQueryPartition:
    candidates: ConditionalCandidates
    state: IdentificationState | None
    unconditioned_state: IdentificationState | None
    selection: QuerySelection | None
    capsules: tuple[tuple[int,ResponseCapsule],...]
    @property
    def versions(self):return self.candidates.versions
@dataclass(frozen=True)
class FiniteResponsePacket:
    query_id: str
    observation: float
    encoded_response: str
    evidence_id: str
    semantics: str='finite_affine_DSL_observation_not_research_model'
@dataclass(frozen=True)
class QueriedFamily:
    plan: AllowedQueryPartition
    response: FiniteResponsePacket | None
    @property
    def versions(self):return self.plan.versions
@dataclass(frozen=True)
class RefinedIdentification:
    belief: BeliefPacket
    posterior: PosteriorUpdate | None
    response: FiniteResponsePacket | None
    selection: QuerySelection | None
    feasible: tuple[int,...]
    inactive_exclusions: tuple
    status: str
    unknown_hypothesis_possible: bool
    versions: VersionSet
    belief_semantics: str='unconditional_evidence_posterior_with_exclusions_kept_separate'


def candidate_family(value):
    from latent_comm.mechanisms.h03_legacy.reference import normalized_logs
    value.versions.require('frame','world','ontology','task','evidence')
    ids=tuple(str(i) for i,_ in value.hypotheses)
    if not 1<=len(ids)<=8 or len(set(ids))!=len(ids) or tuple(b.branch_id for b in value.belief.branches)!=ids or any(b.unknown for b in value.belief.branches):raise ContractError('HypothesisMismatch','finite integer candidates and branch identities must correspond exactly')
    if value.belief.versions!=value.versions or not value.evidence_id:raise ContractError('VersionMismatch','belief and candidate snapshot/evidence identity required')
    if len(value.queries)>8 or len({q.query_id for q in value.queries})!=len(value.queries):raise ContractError('QueryMismatch','bounded unique local queries required')
    return CandidateFamily(value,tuple(math.exp(x) for x in normalized_logs(value.belief)))


def conditional_exclusions(value):
    from latent_comm.mechanisms.h46_negative_knowledge.reference import apply_exclusions
    q=value.request
    region=apply_exclusions(tuple(i for i,_ in q.hypotheses),q.exclusions,q.assumptions,q.versions.world,retracted=q.retracted,budget=StepBudget(max_steps=48,max_cases=32))
    return ConditionalCandidates(value,region)


def partition_allowed_queries(value):
    from latent_comm.mechanisms.h02_legacy.reference import build_capsule,predict
    from latent_comm.mechanisms.h45_identifiability.reference import select_query
    q=value.family.request
    if not value.region.feasible:return AllowedQueryPartition(value,None,None,None,())
    programs=dict(q.hypotheses);capsules={};specs=[]
    for query in q.queries:
        # Permission and locality are tested BEFORE evaluating a candidate or
        # constructing any likelihood from its response model.
        if not query.allowed or not query.local_only:
            specs.append(QuerySpec(query.query_id,('unqueried',),None,query.cost,query.allowed,query.local_only));continue
        predictions=[];known=True
        for identity in programs:
            program=programs[identity]
            if identity not in capsules:capsules[identity]=build_capsule(program,(q.anchor,),directions=((1.,),),step=min(.01,q.radius/2),radius=q.radius,variables=('public_condition',),conditions=('finite_affine_observational_program',),versions=q.versions)
            prediction=predict(capsules[identity],(query.condition,))
            affine=all(x==0 for matrix in program.quadratic for row in matrix for x in row)
            if prediction.needs_refresh or not affine:known=False;break
            predictions.append(prediction.value[0])
        if not known:specs.append(QuerySpec(query.query_id,('unknown',),None,query.cost,True,True));continue
        responses=tuple(sorted({format(x,'.17g') for x in predictions}))
        likelihood=tuple(tuple(float(format(p,'.17g')==response) for response in responses) for p in predictions)
        specs.append(QuerySpec(query.query_id,responses,likelihood,query.cost,True,True))
    prior_lookup=dict(zip((i for i,_ in q.hypotheses),value.family.prior));mass=sum(prior_lookup[i] for i in value.region.feasible)
    if mass<=0:raise ContractError('ImpossibleEvidence','conditional feasible set has no prior mass; preserve as conflict rather than normalize zero')
    prior=tuple(prior_lookup[i]/mass for i in value.region.feasible)
    all_ids=tuple(programs);positions=tuple(all_ids.index(i) for i in value.region.feasible)
    conditional_specs=tuple(replace(spec,likelihood=tuple(spec.likelihood[i] for i in positions) if spec.likelihood is not None else None) for spec in specs)
    state=IdentificationState(tuple(str(i) for i in value.region.feasible),conditional_specs,prior,q.versions.world,True)
    full_state=IdentificationState(tuple(str(i) for i in all_ids),tuple(specs),value.family.prior,q.versions.world,True)
    return AllowedQueryPartition(value,state,full_state,select_query(state,budget=StepBudget(max_steps=8,max_cases=8)),tuple(capsules.items()))


def finite_local_response(value):
    q=value.candidates.family.request
    if value.selection is None or value.selection.query_id is None or q.evidence_id in q.belief.consumed_evidence:return QueriedFamily(value,None)
    selected=next(c for c in q.queries if c.query_id==value.selection.query_id)
    if not selected.allowed or not selected.local_only:raise ContractError('NoAllowedQuery','selected response is not an authorized local finite query')
    if not isinstance(q.actual_local_program,QuadraticProgram):raise ContractError('UnsupportedFixture','no external or model callback can answer this finite query')
    observation=q.actual_local_program.evaluate((selected.condition,))[0]
    return QueriedFamily(value,FiniteResponsePacket(selected.query_id,observation,format(observation,'.17g'),q.evidence_id))


def refine_belief(value):
    from latent_comm.mechanisms.h45_identifiability.reference import update_posterior
    q=value.plan.candidates.family.request;region=value.plan.candidates.region
    if value.plan.state is None:return RefinedIdentification(q.belief,None,None,None,region.feasible,region.inactive,'EmptyDomainConflict',True,q.versions)
    if value.response is None:
        status='RepeatedEvidenceNotReapplied' if q.evidence_id in q.belief.consumed_evidence else value.plan.selection.status
        return RefinedIdentification(q.belief,None,None,value.plan.selection,region.feasible,region.inactive,status,True,q.versions)
    update=update_posterior(value.plan.state,value.response.query_id,value.response.encoded_response)
    unconditional=update_posterior(value.plan.unconditioned_state,value.response.query_id,value.response.encoded_response)
    if unconditional.posterior is None:return RefinedIdentification(q.belief,update,value.response,value.plan.selection,region.feasible,region.inactive,unconditional.status,True,q.versions)
    # Persist only the evidence likelihood update over the original family.
    # Temporary conditional exclusions never become irreversible -inf priors.
    # The separately returned conditional posterior applies only to this region.
    posterior=dict(zip(unconditional.hypotheses,unconditional.posterior));branches=tuple(replace(b,log_weight=math.log(posterior[b.branch_id]) if posterior.get(b.branch_id,0)>0 else -math.inf,evidence_support=b.evidence_support|{q.evidence_id}) for b in q.belief.branches)
    belief=replace(q.belief,branches=branches,consumed_evidence=q.belief.consumed_evidence|{q.evidence_id},probability_semantics='specified_generative_posterior')
    status=update.status if update.posterior is not None else 'ExclusionAssumptionConflict'
    return RefinedIdentification(belief,update,value.response,value.plan.selection,region.feasible,region.inactive,status,True,q.versions)

STAGES=(('candidate_family',('H03',),'IdentificationInput','CandidateFamily','stop'),('conditional_exclusions',('H46',),'CandidateFamily','ConditionalCandidates','enumeration'),('partition_allowed_queries',('H02','H45'),'ConditionalCandidates','AllowedQueryPartition','enumeration'),('finite_local_response',('H02',),'AllowedQueryPartition','QueriedFamily','stop'),('refine_belief',('H03','H45'),'QueriedFamily','RefinedIdentification','stop'))
def build_graph(versions):return linear_graph('C17',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','frame','world','ontology','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('Permission filtering precedes information gain and query evaluation.','A nonlinear local response capsule does not establish an exact likelihood.','Posterior identification is conditional on the candidate family; unknown hypotheses remain possible.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (IdentificationInput,CandidateFamily,ConditionalCandidates,AllowedQueryPartition,QueriedFamily,RefinedIdentification)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h02_legacy.losses import LEDGER as H02
    from latent_comm.mechanisms.h45_identifiability.losses import LOSS_SPECS as H45
    from latent_comm.mechanisms.h46_negative_knowledge.losses import LOSS_SPECS as H46
    return {'recipe':'C17','research_state':'NOT_RUN','phases':[objective_phase('local_response',(('H02',H02,tuple(s.name for s in H02)),)),objective_phase('query_policy',(('H45',H45,tuple(s.name for s in H45)),)),objective_phase('scoped_exclusions',(('H46',H46,tuple(s.name for s in H46)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'permissions':'not learned and never optimized away'}
