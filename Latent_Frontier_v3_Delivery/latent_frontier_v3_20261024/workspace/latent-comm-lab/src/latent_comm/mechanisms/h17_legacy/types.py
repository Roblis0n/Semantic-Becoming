from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import Matrix,Vector,matrix,vector,finite_scalar
@dataclass(frozen=True)
class PhysicalFrame:
    frame_id: str
    unit: str
    handedness: str
    observation_model: str
    latent_frame_id: str
    def __post_init__(self):
        if self.handedness not in ('left','right') or not all((self.frame_id,self.unit,self.observation_model,self.latent_frame_id)) or self.frame_id==self.latent_frame_id:raise ContractError('FrameConflation','physical units/handedness/observation and latent coordinates are separate')
@dataclass(frozen=True)
class FrameTransform:
    source: PhysicalFrame
    target: PhysicalFrame
    linear: Matrix
    translation: Vector
    unit_scale: float
    def __post_init__(self):
        object.__setattr__(self,'linear',matrix(self.linear));object.__setattr__(self,'translation',vector(self.translation))
        if len(self.linear)!=2 or len(self.linear[0])!=2 or len(self.translation)!=2 or finite_scalar(self.unit_scale)<=0:raise ContractError('DimensionMismatch','2D finite affine transform with unit scale')
        det=self.linear[0][0]*self.linear[1][1]-self.linear[0][1]*self.linear[1][0]
        if abs(det)<1e-12 or (det>0)!=(self.source.handedness==self.target.handedness):raise ContractError('HandednessMismatch','orientation map must agree with declared frame handedness')
@dataclass(frozen=True)
class GroundedObject:
    object_id: str
    position: Vector | None
    covariance: Matrix | None
    frame: PhysicalFrame
    timestamp: float
    status: str
    versions: VersionSet
    def __post_init__(self):
        finite_scalar(self.timestamp);self.versions.require('frame','world')
        if self.status not in ('observed','occluded','predicted') or not self.object_id:raise ContractError('InvalidObject','identity/observation status required')
        if self.position is None:
            if self.status!='occluded' or self.covariance is not None:raise ContractError('InvalidUnknown','missing position is explicit occlusion, not zero')
        else:
            p=vector(self.position);c=matrix(self.covariance)
            if len(p)!=2 or len(c)!=2 or len(c[0])!=2 or abs(c[0][1]-c[1][0])>1e-10 or min(c[0][0],c[1][1])<0 or c[0][0]*c[1][1]-c[0][1]**2< -1e-10:raise ContractError('InvalidUncertainty','2D positive semidefinite covariance')
            object.__setattr__(self,'position',p);object.__setattr__(self,'covariance',c)
