"""X10: complementary capability plans and dynamic finite coalition membership."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c18 import EvidenceCoalitionInput,InternalCreditAllocation
from latent_comm.mechanisms.h18_legacy.types import GraphCandidate
from .contracts import bounded_horizon,assumptions,require_complete
ASSUMPTIONS=assumptions('Typed agent capabilities, a source-deduplicated value game and an arithmetic dependency graph exist.','Joint value and capability availability depend on the declared membership and shared source identities.','Finite join/leave events update executable plans and explicitly mark missing complementary roles.','Future systems may hold useful capabilities relationally; this is neither cryptographic non-theft nor immunity to distillation.')
@dataclass(frozen=True)
class CommonsRequest:
    coalition: EvidenceCoalitionInput
    computation: GraphCandidate
    input_members: tuple[tuple[str,str],...]
    memberships: tuple[tuple[str,...],...]
    versions: VersionSet
@dataclass(frozen=True)
class MembershipPlan:
    members: tuple[str,...]
    joined: tuple[str,...]
    left: tuple[str,...]
    execution_order: tuple[str,...]
    analytic_value: float
    graph_output: float | None
    joint_factor_available: bool
    status: str
@dataclass(frozen=True)
class CommonsRecord:
    source_corrected_credit: InternalCreditAllocation
    plans: tuple[MembershipPlan,...]
    nonfinancial: bool=True
@bounded_horizon('X10',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.compositions.c18 import run_reference
    from latent_comm.mechanisms.h18_legacy.reference import validate_graph,evaluate_graph
    from latent_comm.mechanisms.h41_coalitions.reference import capability_plan
    q=request
    if q.coalition.versions!=q.versions or q.computation.versions!=q.versions or not 1<=len(q.memberships)<=4:raise ContractError('VersionMismatch','one shared context and at most four membership events')
    base=require_complete(run_reference(q.coalition));validate_graph(q.computation);bindings=dict(q.input_members);states=dict(q.coalition.member_states);players=set(base.game.players)
    if len(bindings)!=len(q.input_members) or set(bindings)!={n.node_id for n in q.computation.nodes if n.operation=='input'} or not set(bindings.values())<=players:raise ContractError('CapabilityExpansion','graph input nodes bind explicit existing coalition members')
    values={frozenset(k):v for k,v in base.game.values};previous=set();plans=[]
    for members in q.memberships:
        meter.consume(steps=1,cases=1);active=set(members)
        if len(active)!=len(members) or not active<=players:raise ContractError('CapabilityExpansion','join event cannot invent an undeclared participant')
        try:order=capability_plan(q.coalition.coalition,members);status='CapabilitiesAvailable'
        except ContractError as e:
            if e.failure.code not in ('CapabilityUnsatisfied','CoalitionBudget','CapabilityMissing','CoalitionInfeasible','NoFeasibleCoalition','MissingCapability','InfeasibleCoalition'):raise
            order=();status='MissingComplementaryCapability'
        output=None
        if order and set(bindings.values())<=active:
            if any(len(states[m])!=1 for m in bindings.values()):raise ContractError('ShapeMismatch','finite arithmetic graph binds scalar member signals')
            output,_=evaluate_graph(q.computation,{node:states[m][0] for node,m in bindings.items()})
        elif order:status='GraphInputsUnavailable'
        plans.append(MembershipPlan(tuple(members),tuple(sorted(active-previous)),tuple(sorted(previous-active)),tuple(order),values[frozenset(active)],output,set(q.coalition.hyperedge.members)<=active,status));previous=active
    return CommonsRecord(base,tuple(plans)),('Value table is a declared finite analytic game, not measured model competence.','Credit remains internal diagnostic quantity, never money, ownership law or secrecy guarantee.')
