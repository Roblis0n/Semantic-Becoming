"""X07: bounded trajectory equivalence and periodic signatures, not forced fixed points."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c15 import MultirateTrajectoryInput,TrajectoryReadout
from .contracts import bounded_horizon,assumptions,require_complete
ASSUMPTIONS=assumptions('Finite coupled dynamics, public terminal boundary and event clocks are bound.','The same terminal state need not imply equal path-integral or event-order semantics.','Finite candidate paths can be compared by endpoint, signed area, mean and recurrence period.','Future models may use trajectory-distributed representations; public backward constraints do not imply retrocausal information.')
@dataclass(frozen=True)
class TrajectoryRequest:
    trajectory: MultirateTrajectoryInput
    versions: VersionSet
@dataclass(frozen=True)
class PathSignature:
    path: tuple[str,...]
    endpoint: tuple[float,...]
    mean: tuple[float,...]
    signed_area: float
    recurrence_period: int | None
@dataclass(frozen=True)
class TrajectoryRecord:
    execution: TrajectoryReadout
    signatures: tuple[PathSignature,...]
    endpoint_collisions: tuple[tuple[int,int],...]
    status: str
@bounded_horizon('X07',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.compositions.c15 import run_reference
    q=request
    if q.trajectory.versions!=q.versions:raise ContractError('VersionMismatch','trajectory context differs')
    result=require_complete(run_reference(q.trajectory));states=dict(q.trajectory.states);paths=tuple(dict.fromkeys((result.path,)+result.alternatives));signatures=[]
    if len(paths)>8:raise ContractError('BudgetExhausted','finite path comparison at most eight alternatives')
    for path in paths:
        if not path:continue
        meter.consume(steps=1,cases=1);values=tuple(states[k] for k in path);mean=tuple(sum(v[d] for v in values)/len(values) for d in (0,1));area=.5*sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(values,values[1:]));period=None
        for p in range(1,len(values)):
            if all(values[i]==values[i%p] for i in range(len(values))) and len(values)>p:period=p;break
        signatures.append(PathSignature(path,values[-1],mean,area,period))
    collisions=tuple((i,j) for i,a in enumerate(signatures) for j,b in enumerate(signatures[i+1:],i+1) if a.endpoint==b.endpoint and (a.mean,a.signed_area,a.path)!=(b.mean,b.signed_area,b.path))
    return TrajectoryRecord(result,tuple(signatures),collisions,'EndpointInsufficientWitness' if collisions else 'FiniteTrajectorySemanticsRetained'),('A finite repeated path is not a proof of global asymptotic stability.','Blocked/delayed receiver events remain in the underlying continuation; no hidden future labels are read.')
