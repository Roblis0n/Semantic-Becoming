"""X06: coarse dynamics, retained detail, local response and query-relative quotient."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import matvec,matmul,add,sub,norm,eye
from latent_comm.mechanisms.h35_renormalization.types import ScalePacket,MultiScaleState,ClosureResidual
from latent_comm.mechanisms.h25_gauge.types import FrameSpec,GaugePacket
from latent_comm.mechanisms.h47_quotient.types import FiniteQuery,TaskRelativeQuotient
from .contracts import bounded_horizon,assumptions
ASSUMPTIONS=assumptions('Explicit micro/macro dynamics, coarse and lift maps, a gauge and finite queries exist.','Closed macro dynamics require equality of the induced next coarse state on every fiber; a lift alone is not an inverse.','Retained detail and an error ledger support finite advance and re-refinement without inventing lost information.','Future models may learn scale-changing interfaces; the material metaphor implies no physical substance or conservation law.')
@dataclass(frozen=True)
class MultiscaleRequest:
    scale: ScalePacket
    initial: tuple[float,...]
    steps: int
    retain_detail: bool
    source_frame: FrameSpec
    target_frame: FrameSpec
    gauge: tuple[tuple[float,...],...]
    queries: tuple[FiniteQuery,...]
    response_radius: float
    versions: VersionSet
@dataclass(frozen=True)
class ScaleError:
    step: int
    reconstruction: float | None
    macro_prediction: float
    gauge_residual: float
    local_response_status: str
@dataclass(frozen=True)
class MultiscaleRecord:
    final: MultiScaleState
    closure: ClosureResidual
    error_ledger: tuple[ScaleError,...]
    quotient: TaskRelativeQuotient
    exact_micro_history: tuple[tuple[float,...],...]
@bounded_horizon('X06',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.mechanisms.h35_renormalization.reference import closure_report,coarsen,step_scale,refine
    from latent_comm.mechanisms.h25_gauge.reference import transport
    from latent_comm.mechanisms.h02_legacy.reference import build_capsule,predict
    from latent_comm.mechanisms.h02_legacy.types import QuadraticProgram
    from latent_comm.mechanisms.h47_quotient.reference import form_quotient
    from latent_comm.mechanisms.h47_quotient.types import StateDomain
    q=request;p=q.scale
    if not 1<=q.steps<=4 or len(q.initial)>8 or len(p.coarse_map)!=1 or q.source_frame.dimension!=1 or q.target_frame.dimension!=1 or p.source_version!=q.versions.state:raise ContractError('ScaleMismatch','finite scalar macro with at most eight micro axes and four steps')
    closure=closure_report(p);state=coarsen(p,q.initial,q.retain_detail);micro=q.initial;history=[micro];errors=[];macro_values=[]
    n=len(micro);linear=matmul(p.coarse_map,p.micro_dynamics);quadratic=(tuple((0.,)*n for _ in range(n)),);bias=matvec(p.coarse_map,p.micro_bias)
    capsule=build_capsule(QuadraticProgram(linear,quadratic,bias),micro,directions=eye(n),step=1e-3,radius=q.response_radius,variables=p.micro_axes,conditions=('explicit deterministic micro program',),versions=q.versions)
    for step in range(q.steps):
        meter.consume(steps=1,cases=1);coarse=state.coarse
        packet=GaugePacket(q.source_frame,coarse,p.macro_dynamics,((1.,),));gauge=transport(packet,q.gauge,q.target_frame)
        prediction=predict(capsule,micro);macro_pred=add(matvec(p.macro_dynamics,coarse),p.macro_bias)
        micro=add(matvec(p.micro_dynamics,micro),p.micro_bias);state=step_scale(p,state);history.append(micro)
        reconstruction=norm(sub(refine(p,state),micro)) if state.detail_residual is not None else None
        errors.append(ScaleError(step+1,reconstruction,norm(sub(state.coarse,macro_pred)),norm(gauge.residual),prediction.reason))
        value=state.coarse[0]
        if not float(value).is_integer():raise ContractError('QueryFamilyUndefined','integer finite quotient cannot silently round a real macro value')
        macro_values.append(int(value))
    domain=StateDomain(tuple('step:'+str(i+1) for i in range(q.steps)),tuple(macro_values),p.target_version)
    quotient=form_quotient(domain,q.queries,'quotient:'+p.target_version)
    return MultiscaleRecord(state,closure,tuple(errors),quotient,tuple(history)),('Query equivalence is relative to the declared finite query family.','Response outside its radius requests refresh; nonclosed scales require retained detail or added statistics.')
