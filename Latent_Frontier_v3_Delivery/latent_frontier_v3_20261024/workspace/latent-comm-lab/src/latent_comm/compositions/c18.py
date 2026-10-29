"""C18: evidence genealogy and exact-symbol coalition credit, never money."""
from dataclasses import dataclass
from itertools import combinations
from decimal import Decimal
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h10_legacy.types import Hyperedge
from latent_comm.mechanisms.h16_legacy.types import SymbolPacket,Symbol,DualReadout
from latent_comm.mechanisms.h41_coalitions.types import CoalitionContract,CoalitionGame,ContributionRecord
from latent_comm.mechanisms.h48_evidence_genealogy.types import ProvenanceGraph,DependenceModel,CalibratedSupport
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase

@dataclass(frozen=True)
class EvidenceCoalitionInput:
    graph: ProvenanceGraph
    dependence: DependenceModel
    exact_values: SymbolPacket
    proposed_values: tuple[Symbol,...]
    hyperedge: Hyperedge
    member_states: tuple[tuple[str,tuple[float,...]],...]
    coalition: CoalitionContract
    versions: VersionSet
@dataclass(frozen=True)
class BoundEvidenceDAG:
    request: EvidenceCoalitionInput
    exact_readout: DualReadout
    atom_values: tuple[tuple[str,float],...]
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class DeduplicatedSupport:
    evidence: BoundEvidenceDAG
    calibration: CalibratedSupport
    unique_source_count: int
    @property
    def versions(self):return self.evidence.versions
@dataclass(frozen=True)
class CoalitionHyperedge:
    support: DeduplicatedSupport
    joint_effect: tuple[float,...]
    feasible_full_plan: tuple[str,...]
    @property
    def versions(self):return self.support.versions
@dataclass(frozen=True)
class AnalyticCoalitionGame:
    coalition: CoalitionHyperedge
    game: CoalitionGame
    interaction: float
    selected_members: tuple[str,...]
    execution_order: tuple[str,...]
    @property
    def versions(self):return self.coalition.versions
@dataclass(frozen=True)
class InternalCreditAllocation:
    contributions: ContributionRecord
    game: CoalitionGame
    evidence: CalibratedSupport
    exact_symbols: tuple[Symbol,...]
    selected_members: tuple[str,...]
    interaction: float
    unique_source_count: int
    versions: VersionSet
    credit_is_money: bool=False
    competence_status: str='analytic_finite_value_function_not_model_performance'


def bind_evidence(value):
    from latent_comm.mechanisms.h48_evidence_genealogy.reference import validate_graph
    from latent_comm.mechanisms.h16_legacy.reference import fuse
    value.versions.require('ontology','task','evidence')
    if value.exact_values.versions!=value.versions or value.hyperedge.versions!=value.versions or value.graph.version!=value.versions.evidence:raise ContractError('VersionMismatch','exact channel/hyperedge/evidence must bind one snapshot')
    atoms,_,_=validate_graph(value.graph);symbols={s.name:s for s in value.exact_values.symbols}
    if set(symbols)!=set(atoms):raise ContractError('MissingSource','one exact value for each stable original source atom required')
    for identity,symbol in symbols.items():
        if symbol.kind!='decimal' or symbol.unit!='internal_credit_units' or symbol.source.value!=atoms[identity].source_handle:raise ContractError('ExactSourceMismatch','value must be an exact decimal bound to the same original source, not a new copied observation')
        if Decimal(symbol.value)<0:raise ContractError('UndefinedValue','finite analytic source coverage values are nonnegative')
    readout=fuse(value.exact_values,(),value.proposed_values)
    if readout.conflicts:raise ContractError('ExactLatentConflict','latent proposed values cannot overwrite authoritative exact symbols')
    if set(dict(value.hyperedge.evidence_support))!={a.name for a in value.coalition.agents}:raise ContractError('CapabilityUnsatisfied','hyperedge member universe and coalition player universe differ')
    if not set().union(*(s for _,s in value.hyperedge.evidence_support))<=atoms.keys():raise ContractError('MissingSource','member support refers to an absent original evidence atom')
    return BoundEvidenceDAG(value,readout,tuple((k,float(Decimal(s.value))) for k,s in symbols.items()))


def deduplicate_evidence(value):
    from latent_comm.mechanisms.h48_evidence_genealogy.reference import calibrate_support
    from latent_comm.mechanisms.h10_legacy.reference import independent_support_count
    q=value.request
    return DeduplicatedSupport(value,calibrate_support(q.graph,q.dependence,budget=StepBudget(max_steps=32,max_cases=32)),independent_support_count(q.hyperedge))


def form_coalition(value):
    from latent_comm.mechanisms.h10_legacy.reference import compose_hyperedge
    from latent_comm.mechanisms.h41_coalitions.reference import capability_plan
    q=value.evidence.request
    if len(q.hyperedge.members)>4:raise ContractError('CoalitionBudget','C18 executes exact mathematical games on at most four members')
    plan=capability_plan(q.coalition,q.hyperedge.members)
    return CoalitionHyperedge(value,compose_hyperedge(q.hyperedge,dict(q.member_states)),plan)


def analytic_value_function(value):
    from latent_comm.mechanisms.h10_legacy.reference import subset_interaction
    from latent_comm.mechanisms.h41_coalitions.reference import unique_evidence_value,choose_coalition
    q=value.support.evidence.request;players=q.hyperedge.members;supports=dict(q.hyperedge.evidence_support);values=[]
    # The counterfactual value function is DEFINED for every subset: union
    # coverage plus a joint factor only when every required member is present.
    # This is not an absent empirical measurement filled with zero.
    for size in range(len(players)+1):
        for members in combinations(players,size):
            coverage=unique_evidence_value(tuple(supports[p] for p in members),value.support.evidence.atom_values)
            synergy=sum(value.joint_effect) if set(players)<=set(members) else 0.
            values.append((members,coverage+synergy))
    game=CoalitionGame(players,tuple(values),q.versions.task+':analytic-game')
    interaction=subset_interaction(players,{frozenset(s):-v for s,v in values},budget=StepBudget(max_steps=16,max_cases=16))
    _,selected,plan=choose_coalition(game,q.coalition,budget=StepBudget(max_steps=16,max_cases=16))
    return AnalyticCoalitionGame(value,game,interaction,selected,plan)


def allocate_internal_credit(value):
    from latent_comm.mechanisms.h41_coalitions.reference import exact_shapley
    support=value.coalition.support
    record=exact_shapley(value.game,budget=StepBudget(max_steps=32,max_cases=16))
    if record.efficiency_residual is not None and abs(record.efficiency_residual)>1e-9:raise ContractError('CreditConflict','finite contribution efficiency identity failed')
    return InternalCreditAllocation(record,value.game,support.calibration,support.evidence.exact_readout.exact_symbols,value.selected_members,value.interaction,support.unique_source_count,value.versions)

STAGES=(('bind_evidence',('H16','H48'),'EvidenceCoalitionInput','BoundEvidenceDAG','stop'),('deduplicate_evidence',('H10','H48'),'BoundEvidenceDAG','DeduplicatedSupport','enumeration'),('form_coalition',('H10','H41'),'DeduplicatedSupport','CoalitionHyperedge','stop'),('analytic_value_function',('H10','H41'),'CoalitionHyperedge','AnalyticCoalitionGame','enumeration'),('allocate_internal_credit',('H41',),'AnalyticCoalitionGame','InternalCreditAllocation','stop'))
def build_graph(versions):return linear_graph('C18',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','ontology','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('Credit is an analytic internal attribution, not currency or measured competence.','Unknown evidence dependence remains unknown; allocation does not calibrate truth.','Repeated source handles cannot become independent atom copies.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (EvidenceCoalitionInput,BoundEvidenceDAG,DeduplicatedSupport,CoalitionHyperedge,AnalyticCoalitionGame,InternalCreditAllocation)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h10_legacy.losses import LEDGER as H10
    from latent_comm.mechanisms.h41_coalitions.losses import LOSS_SPECS as H41
    from latent_comm.mechanisms.h48_evidence_genealogy.losses import LOSS_SPECS as H48
    return {'recipe':'C18','research_state':'NOT_RUN','phases':[objective_phase('joint_factor',(('H10',H10,tuple(s.name for s in H10)),)),objective_phase('coalition_selector',(('H41',H41,tuple(s.name for s in H41)),)),objective_phase('dependence_calibration',(('H48',H48,tuple(s.name for s in H48)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'exact_fields':'not overwritten by learned readout','credit_is_money':False}
