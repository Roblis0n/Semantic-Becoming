"""C19: immutable goal, local chart, task quotient, scale closure and authorized detail."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.core.finite import norm,sub,matvec
from latent_comm.mechanisms.h06_legacy.types import Chart
from latent_comm.mechanisms.h12_legacy.types import PersistentCapsule
from latent_comm.mechanisms.h32_perspective.types import ImmutableGoal,ObjectiveFrame,GoalPreservingView
from latent_comm.mechanisms.h35_renormalization.types import ScalePacket,MultiScaleState,ClosureResidual
from latent_comm.mechanisms.h47_quotient.types import StateDomain,FiniteQuery,TaskRelativeQuotient,RefinementMap
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase

@dataclass(frozen=True)
class GoalScaleInput:
    objective: ObjectiveFrame
    current_goal: ImmutableGoal
    chart: Chart
    model_revision: str
    task_family: str
    view_map: tuple
    scale: ScalePacket
    state: tuple[float,...]
    domain: StateDomain
    queries: tuple[FiniteQuery,...]
    added_queries: tuple[FiniteQuery,...]
    source_capsule: PersistentCapsule
    current_dependencies: tuple[tuple[str,str],...]
    withdrawn_sources: frozenset[str]
    retain_detail: bool
    step: int
    versions: VersionSet
@dataclass(frozen=True)
class FrozenExternalGoal:
    request: GoalScaleInput
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class GoalPreservingCoordinates:
    goal: FrozenExternalGoal
    view: GoalPreservingView
    chart_coordinates: tuple[float,...]
    @property
    def versions(self):return self.goal.versions
@dataclass(frozen=True)
class TaskQuotientPlan:
    coordinates: GoalPreservingCoordinates
    quotient: TaskRelativeQuotient
    @property
    def versions(self):return self.coordinates.versions
@dataclass(frozen=True)
class MacroEvolution:
    plan: TaskQuotientPlan
    closure: ClosureResidual
    initial: MultiScaleState
    advanced: MultiScaleState | None
    status: str
    @property
    def versions(self):return self.plan.versions
@dataclass(frozen=True)
class AuthorizedRefinement:
    evolution: MacroEvolution
    quotient_refinement: RefinementMap | None
    refined_state: tuple[float,...] | None
    status: str
    obligations: tuple[str,...]
    @property
    def versions(self):return self.evolution.versions
@dataclass(frozen=True)
class OriginalGoalReadout:
    goal_digest: str
    original_value: float
    transformed_value: float | None
    final_state: tuple[float,...] | None
    hard_constraints_satisfied: bool | None
    refinement: RefinementMap | None
    status: str
    obligations: tuple[str,...]
    versions: VersionSet


def freeze_external_goal(value):
    if value.objective.goal!=value.current_goal:raise ContractError('GoalMutation','the original immutable objective cannot be replaced by internal reparameterization')
    value.versions.require('frame','ontology','world','task','evidence')
    if value.objective.costs!=value.state or value.chart.versions!=value.versions or value.source_capsule.versions!=value.versions:raise ContractError('VersionMismatch','goal cost coordinates, chart and source capsule must describe the same source state/context')
    if len(value.state)!=2 or len(value.domain.state_ids)>4:raise ContractError('BudgetExhausted','C19 fixture has two micro coordinates and at most four source alternatives')
    if value.scale.source_version!=value.versions.frame or value.scale.coarse_map!=value.chart.read_map or value.view_map!=value.scale.coarse_map:raise ContractError('UnboundMap','goal view, chart and coarse map must share the declared coordinate transformation')
    return FrozenExternalGoal(value)


def goal_preserving_view(value):
    from latent_comm.mechanisms.h06_legacy.reference import encode
    from latent_comm.mechanisms.h32_perspective.reference import change_view,assert_commit
    q=value.request;coordinates=encode(q.chart,q.state,task=q.task_family,model_revision=q.model_revision)
    view=change_view(q.objective,q.view_map,q.objective.version+':view');assert_commit(view,q.current_goal)
    if norm(sub(view.transformed_costs,coordinates))>1e-9:raise ContractError('UnboundMap','objective view differs from chart encoding')
    return GoalPreservingCoordinates(value,view,coordinates)


def quotient_plan(value):
    from latent_comm.mechanisms.h47_quotient.reference import form_quotient
    q=value.goal.request
    return TaskQuotientPlan(value,form_quotient(q.domain,q.queries,'quotient:1',retain_source=False,budget=StepBudget(max_steps=16,max_cases=4)))


def macro_evolution(value):
    from latent_comm.mechanisms.h35_renormalization.reference import closure_report,coarsen,step_scale
    q=value.coordinates.goal.request;initial=coarsen(q.scale,q.state,q.retain_detail);closure=closure_report(q.scale)
    if not closure.closed and initial.detail_residual is None:return MacroEvolution(value,closure,initial,None,'NeedsRetainedDetailForClosure')
    return MacroEvolution(value,closure,initial,step_scale(q.scale,initial),'MacroAdvanced')


def authorized_refinement(value):
    from latent_comm.mechanisms.h12_legacy.reference import read_query
    from latent_comm.mechanisms.h47_quotient.reference import refine_quotient
    from latent_comm.mechanisms.h35_renormalization.reference import refine,coarsen,step_scale
    q=value.plan.coordinates.goal.request;obligations=[]
    def lookup(key):
        result=read_query(q.source_capsule,('lookup',key),step=q.step,versions=q.versions,current_dependencies=dict(q.current_dependencies),withdrawn=q.withdrawn_sources)
        if result.value is None:obligations.append(key+':'+result.status)
        return result.value
    source_values=tuple(lookup('domain:'+name) for name in q.domain.state_ids)
    if any(v is None for v in source_values):return AuthorizedRefinement(value,None,None,'NeedsAuthorizedSourceDetail',tuple(obligations))
    if any(not float(v).is_integer() for v in source_values):raise ContractError('RefinementConflict','finite source query values must remain exact integers')
    source=StateDomain(q.domain.state_ids,tuple(int(v) for v in source_values),q.domain.version)
    refinement=refine_quotient(value.plan.quotient,q.added_queries,'quotient:2',source_domain=source,budget=StepBudget(max_steps=32,max_cases=4))
    advanced=value.advanced
    if advanced is None or advanced.detail_residual is None:
        recovered=tuple(lookup('coordinate:'+axis) for axis in q.scale.micro_axes)
        if any(x is None for x in recovered):return AuthorizedRefinement(value,refinement,None,'NeedsAuthorizedSourceDetail',tuple(obligations))
        # Source evidence must recover the original detail, not invent a lift.
        if norm(sub(matvec(q.scale.coarse_map,recovered),value.initial.coarse))>1e-9:raise ContractError('RefinementConflict','source detail contradicts retained macro state')
        advanced=step_scale(q.scale,coarsen(q.scale,recovered,True))
    return AuthorizedRefinement(value,refinement,refine(q.scale,advanced),'RefinedFromAuthorizedSource',())


def recheck_original_goal(value):
    from latent_comm.mechanisms.h32_perspective.reference import change_view,assert_commit
    q=value.evolution.plan.coordinates.goal.request;initial=value.evolution.plan.coordinates.view
    if value.refined_state is None:return OriginalGoalReadout(q.current_goal.digest,initial.original_value,None,None,None,value.quotient_refinement,value.status,value.obligations,q.versions)
    # Apply original weights and hard constraints to actual recovered micro
    # coordinates, never to an arbitrary quotient representative or lifted zero.
    frame=replace(q.objective,costs=value.refined_state);view=change_view(frame,q.view_map,frame.version+':final');assert_commit(view,q.current_goal)
    return OriginalGoalReadout(q.current_goal.digest,view.original_value,view.transformed_value,value.refined_state,view.original_constraints_satisfied,value.quotient_refinement,'OriginalGoalRechecked',(),q.versions)

STAGES=(('freeze_external_goal',('H32',),'GoalScaleInput','FrozenExternalGoal','stop'),('goal_preserving_view',('H06','H32'),'FrozenExternalGoal','GoalPreservingCoordinates','differentiable'),('quotient_plan',('H47',),'GoalPreservingCoordinates','TaskQuotientPlan','enumeration'),('macro_evolution',('H35',),'TaskQuotientPlan','MacroEvolution','differentiable'),('authorized_refinement',('H12','H35','H47'),'MacroEvolution','AuthorizedRefinement','stop'),('recheck_original_goal',('H32',),'AuthorizedRefinement','OriginalGoalReadout','stop'))
def build_graph(versions):return linear_graph('C19',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','frame','ontology','world','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('Neither quotient representative nor lift recovers discarded detail.','Refinement reads only authorized version-bound capsule source fields.','Original immutable goal and hard constraints are rechecked after dynamics.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (GoalScaleInput,FrozenExternalGoal,GoalPreservingCoordinates,TaskQuotientPlan,MacroEvolution,AuthorizedRefinement,OriginalGoalReadout)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h32_perspective.losses import LOSS_SPECS as H32
    from latent_comm.mechanisms.h35_renormalization.losses import LOSS_SPECS as H35
    from latent_comm.mechanisms.h47_quotient.losses import LOSS_SPECS as H47
    return {'recipe':'C19','research_state':'NOT_RUN','phases':[objective_phase('goal_coordinates',(('H32',H32,tuple(s.name for s in H32)),)),objective_phase('closure_and_detail',(('H35',H35,tuple(s.name for s in H35)),)),objective_phase('task_relative_quotient',(('H47',H47,tuple(s.name for s in H47)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'frozen':['external_goal','source_evidence','authorization']}
