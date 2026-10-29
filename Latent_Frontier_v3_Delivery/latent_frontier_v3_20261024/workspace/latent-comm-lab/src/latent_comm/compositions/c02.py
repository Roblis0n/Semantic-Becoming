"""C02: response-driven field update with validity and source-specific refresh."""
from dataclasses import dataclass
import json
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.core.finite import matmul,transpose,matvec,sub,add,norm
from latent_comm.mechanisms.h02_legacy.types import QuadraticProgram,ResponseCapsule
from latent_comm.mechanisms.h04_legacy.types import LocalConstraint,ConstraintField,FieldResult
from latent_comm.mechanisms.h23_legacy.types import DiscrepancyReport,RepairPacket,RepairSession
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase
@dataclass(frozen=True)
class ResponseSource:
    source_id: str
    program: QuadraticProgram
    capsule: ResponseCapsule
    target: tuple[float,...]
    temperature: float
    domain: str
    evidence: frozenset[str]
@dataclass(frozen=True)
class SharedResponseInput:
    sources: tuple[ResponseSource,...]
    state: tuple[float,...]
    refresh_authorized: frozenset[str]
    anchor_strength: float
    solver_steps: int
    step_size: float
    versions: VersionSet
@dataclass(frozen=True)
class SourceResponses:
    request: SharedResponseInput
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class ValidatedResponses:
    sources: SourceResponses
    current: tuple[ResponseSource,...]
    refreshed: tuple[str,...]
    missing_refresh: tuple[str,...]
    @property
    def versions(self):return self.sources.versions
@dataclass(frozen=True)
class UpdatedField:
    responses: ValidatedResponses
    field: ConstraintField | None
    result: FieldResult | None
    @property
    def versions(self):return self.responses.versions
@dataclass(frozen=True)
class ResidualRefresh:
    state: tuple[float,...]
    field_result: FieldResult | None
    source_responses: tuple[ResponseSource,...]
    reports: tuple[DiscrepancyReport,...]
    corrected_messages: tuple[RepairSession,...]
    pending_sources: tuple[str,...]
    status: str
    versions: VersionSet

def source_responses(value):
    value.versions.require('state','frame','ontology','world','task','evidence')
    if not 1<=len(value.sources)<=4 or len({s.source_id for s in value.sources})!=len(value.sources) or len(value.state)!=1 or not 1<=value.solver_steps<=16:raise ContractError('BudgetExhausted','C02 finite binding uses one scalar state, four sources and sixteen field steps')
    if len({s.domain for s in value.sources})!=1:raise ContractError('NonCommonDomain','distinct semantic domains require restrictions, not a forced shared vector')
    for source in value.sources:
        if source.capsule.response_kind!='observational' or len(source.target)!=1:raise ContractError('UnknownResponseSemantics','finite local observation residual is not a causal intervention')
    return SourceResponses(value)

def _refresh(source,anchor,versions):
    from latent_comm.mechanisms.h02_legacy.reference import build_capsule
    capsule=build_capsule(source.program,anchor,directions=((1.,),),step=min(.01,source.capsule.radius/2),radius=source.capsule.radius,variables=source.capsule.variables,conditions=source.capsule.observation_conditions,versions=versions)
    return ResponseSource(source.source_id,source.program,capsule,source.target,source.temperature,source.domain,source.evidence)

def validity_check(value):
    from latent_comm.mechanisms.h02_legacy.reference import predict
    q=value.request;current=[];refreshed=[];pending=[]
    for source in q.sources:
        stale=not source.capsule.versions.matches(q.versions,('frame','world','task'))
        outside=predict(source.capsule,q.state).needs_refresh
        if stale or outside:
            if source.source_id not in q.refresh_authorized:pending.append(source.source_id);current.append(source);continue
            source=_refresh(source,q.state,q.versions);refreshed.append(source.source_id)
        current.append(source)
    return ValidatedResponses(value,tuple(current),tuple(refreshed),tuple(pending))

def field_update(value):
    q=value.sources.request
    if value.missing_refresh:return UpdatedField(value,None,None)
    constraints=[]
    for source in value.current:
        capsule=source.capsule;jac=matmul(capsule.A,transpose(capsule.B));rhs=add(sub(source.target,capsule.base),matvec(jac,capsule.anchor))
        constraints.append(LocalConstraint(source.source_id,jac,rhs,source.temperature,source.domain,q.versions.frame,q.versions.state,source.evidence))
    field=ConstraintField(tuple(constraints),q.state,q.anchor_strength,value.current[0].domain,q.versions)
    from latent_comm.mechanisms.h04_legacy.reference import solve_field
    result=solve_field(field,steps=q.solver_steps,step_size=q.step_size,budget=StepBudget(max_steps=16))
    return UpdatedField(value,field,result)

def residual_refresh(value):
    from latent_comm.mechanisms.h02_legacy.reference import predict
    from latent_comm.mechanisms.h23_legacy.reference import diagnose,integrity_digest,build_repair,apply_repair
    q=value.responses.sources.request
    if value.result is None:return ResidualRefresh(q.state,None,value.responses.current,(),(),value.responses.missing_refresh,'AwaitingAuthorizedRefresh',q.versions)
    reports=[];sessions=[];sources=[];pending=[];needs=False
    for source in value.responses.current:
        predicted=predict(source.capsule,value.result.state)
        if predicted.needs_refresh:
            needs=True
            if source.source_id in q.refresh_authorized:sources.append(_refresh(source,value.result.state,q.versions))
            else:pending.append(source.source_id);sources.append(source)
            continue
        if source.source_id not in q.refresh_authorized:
            pending.append(source.source_id);sources.append(source);continue
        actual=source.program.evaluate(value.result.state)
        payload=json.dumps({'source':source.source_id,'state':value.result.state,'response':predicted.value},sort_keys=True).encode();digest=integrity_digest(payload)
        report=diagnose(report_id='refresh:'+source.source_id,payload=payload,expected_digest=digest,probe_ids=('public_response',),observed=predicted.value,expected=actual,allowed_fields=('probe_ids','residual'),versions=q.versions)
        reports.append(report);repair=build_repair(report,((1.,),))
        session=RepairSession(predicted.value,digest,frozenset(),0,0,0,source.evidence,q.versions)
        sessions.append(apply_repair(session,report,repair,max_rounds=1))
        if report.kind=='numeric':needs=True;sources.append(_refresh(source,value.result.state,q.versions))
        else:sources.append(source)
    status='AwaitingAuthorizedRefresh' if pending else 'ResponseRefreshedFieldNeedsResolve' if needs else 'FiniteApproximateFieldUpdateNotTruth'
    return ResidualRefresh(value.result.state,value.result,tuple(sources),tuple(reports),tuple(sessions),tuple(pending),status,q.versions)

STAGES=(('source_responses',('H02',),'SharedResponseInput','SourceResponses','stop'),('validity_check',('H02',),'SourceResponses','ValidatedResponses','stop'),('field_update',('H02','H04'),'ValidatedResponses','UpdatedField','differentiable'),('residual_refresh',('H02','H23'),'UpdatedField','ResidualRefresh','stop'))
def build_graph(versions):return linear_graph('C02',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','world','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),obligations=('Local linear response validity is checked before use and again after field motion.','Correcting a response message does not silently correct or solve the shared field.','Unreachable or unauthorized source refresh remains a partial object.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (SharedResponseInput,SourceResponses,ValidatedResponses,UpdatedField,ResidualRefresh)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h02_legacy.losses import LEDGER as H02
    from latent_comm.mechanisms.h04_legacy.losses import LEDGER as H04
    from latent_comm.mechanisms.h23_legacy.losses import LEDGER as H23
    return {'recipe':'C02','research_state':'NOT_RUN','phases':[objective_phase('local_response',(('H02',H02,tuple(s.name for s in H02)),)),objective_phase('field',(('H04',H04,tuple(s.name for s in H04)),)),objective_phase('refresh',(('H23',H23,tuple(s.name for s in H23)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'solver':'finite differentiable field unroll; refresh selection is a separate discrete boundary'}
