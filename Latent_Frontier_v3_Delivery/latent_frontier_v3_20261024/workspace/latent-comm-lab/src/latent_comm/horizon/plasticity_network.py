"""X04: scoped tangent updates plus a compiled budget and causal-module boundary."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c13 import LearningProtocolInput,FutureTrainerPlan
from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM,BoundaryBinding,GraftCertificate
from latent_comm.mechanisms.h40_instruction_set.types import Expr,ISARevision
from .contracts import bounded_horizon,assumptions,require_complete
ASSUMPTIONS=assumptions('Source/target public tangent anchors, a bounded learning rule and explicit causal module interfaces exist.','Transport preserves only the reachable linearized behavior; residual and update cost remain visible.','A finite rule/budget compiler and an SCM graft can be connected by a named operational effect contract.','Future neural models may learn transferable plasticity networks; no initialization or training occurs.')
@dataclass(frozen=True)
class PlasticityNetworkRequest:
    learning: LearningProtocolInput
    module: CausalModule
    target_world: TargetSCM
    target_node: str
    boundary: tuple[BoundaryBinding,...]
    next_world_version: str
    noise: tuple[tuple[str,float],...]
    budget_expression: Expr
    isa: ISARevision
    maximum_budget_cost: float
    versions: VersionSet
@dataclass(frozen=True)
class PlasticityNetworkRecord:
    future_plan: FutureTrainerPlan
    compiled_budget: Expr
    budget_cost: float
    causal_graft: GraftCertificate
    finite_world_values: tuple
    transport_residual: tuple[float,...]
    status: str
@bounded_horizon('X04',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.compositions.c13 import run_reference
    from latent_comm.mechanisms.h31_grafting.reference import graft,evaluate_scm
    from latent_comm.mechanisms.h40_instruction_set.reference import lower,execute_base,free_variables
    q=request
    from latent_comm.core.finite import finite_scalar
    limit=finite_scalar(q.maximum_budget_cost)
    if limit<0:raise ContractError('UpdateBudget','nonnegative finite resource contract required')
    if q.learning.versions!=q.versions or q.target_world.version!=q.versions.world or q.isa.version!=q.versions.isa:raise ContractError('VersionMismatch','plasticity, world and instruction interfaces must bind current versions')
    plan=require_complete(run_reference(q.learning));direction=plan.rule.projection.update.delta
    inputs={'delta'+str(i):v for i,v in enumerate(direction)}
    program=lower(q.budget_expression,q.isa)
    if not free_variables(program)<=set(inputs):raise ContractError('UnboundVariable','budget expression may only inspect the explicit transported update')
    cost=execute_base(program,inputs)
    if cost<0 or cost>limit:raise ContractError('UpdateBudget','compiled update cost exceeds declared finite resource contract')
    certificate=graft(q.module,q.target_world,q.target_node,q.boundary,q.next_world_version)
    values=evaluate_scm(certificate.after,dict(q.noise))
    meter.consume(steps=1)
    return PlasticityNetworkRecord(plan,program,cost,certificate,values,plan.rule.realized_residual,'CompiledScopedFiniteLearningNetwork'),('The SCM graft and tangent update are separate named interfaces; no causal efficacy of an unrun neural update is asserted.','Unreachable behavior residual and regularization are retained; learning is not cost-free.')
