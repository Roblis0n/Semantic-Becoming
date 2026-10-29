"""Bounded horizon envelopes and explicit, non-circular assumption dependencies."""
from dataclasses import dataclass
from functools import wraps
import hashlib,json
from latent_comm.core import ContractError,StepBudget,VersionSet,ObjectRef,ObjectRegistry,RegisteredObject,Visibility,Scope
from latent_comm.core.budgets import aggregate_budget
from latent_comm.core.finite import topological_order
from latent_comm.compositions.contracts import _plain
@dataclass(frozen=True)
class Assumption:
    identity: str
    statement: str
    depends_on: tuple[str,...]
    status: str
    def __post_init__(self):
        if self.status not in ('definition','finite_derived','conditional_bridge','unrun_learning_hypothesis'):raise ContractError('InvalidAssumption','separate definition, derivation, bridge and future learning')
@dataclass(frozen=True)
class SerializedHorizonObject:
    type_name: str
    payload_json: str
    content_digest: str
    reference_semantics: str='wire transcript only; embedded names do not grant registry access or resolve external objects'
@dataclass(frozen=True)
class HorizonExecution:
    horizon_id: str
    value: object | None
    status: str
    obligations: tuple[str,...]
    assumptions: tuple[Assumption,...]
    object_reference: str | None
    object_digest: str | None
    consumed_steps: int
    consumed_cases: int
    research_state: str='NOT_RUN'
    finite_execution_kind: str='stdlib_math_DSL_not_model_experiment'
    def export_json(self):return json.dumps(_plain(self),ensure_ascii=False,sort_keys=True,allow_nan=False)
def assumption_graph(items):
    names=tuple(a.identity for a in items)
    if len(set(names))!=len(names) or any(d not in names for a in items for d in a.depends_on):raise ContractError('UnboundAssumption','unique named assumptions and complete dependency edges required')
    order=topological_order(names,tuple((d,a.identity) for a in items for d in a.depends_on))
    return order

def assumptions(objects,operation,representation,learning):
    return (Assumption('A1',objects,(),'definition'),Assumption('A2',operation,('A1',),'conditional_bridge'),Assumption('A3',representation,('A1','A2'),'finite_derived'),Assumption('H1',learning,('A3',),'unrun_learning_hypothesis'))
def bounded_horizon(identity,assumption_items):
    assumption_graph(assumption_items)
    def decorate(fn):
        @wraps(fn)
        def run(request,*,budget=StepBudget()):
            with aggregate_budget(budget) as meter:
                try:
                    value,obligations=fn(request,meter)
                    if meter.exhausted:
                        return HorizonExecution(identity,value,'PartialBudgetExhausted',tuple(obligations)+('Only an explicitly completed prefix is retained; no final object is registered.',),assumption_items,None,None,meter.steps,meter.cases)
                    encoded=json.dumps(_plain(value),sort_keys=True,allow_nan=False).encode();digest=hashlib.sha256(encoded).hexdigest();ref=ObjectRef('horizon:'+identity+':'+digest[:20])
                    versions=request.versions;axes=tuple(k for k,v in versions.as_dict().items() if v is not None)
                    wire=SerializedHorizonObject(type(value).__name__,encoded.decode(),digest)
                    registry=ObjectRegistry();registry.register(RegisteredObject(ref,'SerializedHorizonObject',wire,versions,axes,Scope(identity,frozenset({'orchestrator'}),frozenset()),Visibility.PUBLIC))
                    return HorizonExecution(identity,value,'FiniteComplete',tuple(obligations),assumption_items,ref.value,digest,meter.steps,meter.cases)
                except ContractError as error:
                    if error.failure.code!='BudgetExhausted':raise
                    return HorizonExecution(identity,None,'PartialBudgetExhausted',(str(error),'No final object is exposed; restart or explicitly resume from a returned domain capsule, never treat a prior stage as final.'),assumption_items,None,None,meter.steps,meter.cases)
        return run
    return decorate

def require_complete(result):
    if result.status!='Complete':raise ContractError('BudgetExhausted','nested composition remains partial: '+','.join(result.pending_nodes))
    return result.value
