from dataclasses import dataclass
from latent_comm.core import ContractError, VersionSet
from latent_comm.core.finite import Vector,Matrix,vector,matrix,finite_scalar
@dataclass(frozen=True)
class ResponseCapsule:
    anchor: Vector
    base: Vector
    A: Matrix
    B: Matrix
    radius: float
    variables: tuple[str,...]
    observation_conditions: tuple[str,...]
    response_kind: str
    versions: VersionSet
    approximation: str='local_linear'
    def __post_init__(self):
        for name in ('anchor','base'):object.__setattr__(self,name,vector(getattr(self,name)))
        for name in ('A','B'):object.__setattr__(self,name,matrix(getattr(self,name)))
        if len(self.A)!=len(self.base) or len(self.B)!=len(self.anchor) or len(self.A[0])!=len(self.B[0]):raise ContractError('DimensionMismatch','A [output,rank], B [condition,rank]')
        if finite_scalar(self.radius)<=0 or len(self.variables)!=len(self.anchor) or len(set(self.variables))!=len(self.variables):raise ContractError('OutOfDomain','positive radius and unique public variables')
        if self.response_kind not in ('observational','structural_intervention'):raise ContractError('UnknownResponseSemantics','must not infer causality from a derivative')
        if self.response_kind=='structural_intervention' and not self.observation_conditions:raise ContractError('MissingCausalAssumptions','explicit structural context required')
        self.versions.require('frame','world','task')
@dataclass(frozen=True)
class ResponsePrediction:
    value: Vector | None
    needs_refresh: bool
    distance: float
    reason: str
@dataclass(frozen=True)
class QuadraticProgram:
    linear: Matrix
    quadratic: tuple[Matrix,...]
    bias: Vector
    def evaluate(self,x):
        from latent_comm.core.finite import matvec,dot,add
        x=vector(x);linear=matvec(self.linear,x)
        if len(self.quadratic)!=len(linear) or len(self.bias)!=len(linear):raise ContractError('DimensionMismatch','one quadratic form per output')
        return add(add(linear,tuple(.5*dot(x,matvec(q,x)) for q in self.quadratic)),self.bias)
