from dataclasses import dataclass
from latent_comm.core import ContractError, VersionSet, Scope
from latent_comm.core.finite import Vector, Matrix, vector, matrix, finite_scalar
@dataclass(frozen=True)
class OperatorPacket:
    U: Matrix
    V: Matrix
    bias: Vector
    alpha: float
    nonlinearity: str
    domain: str
    codomain: str
    versions: VersionSet
    scope: Scope
    target: str = 'working_slot'
    def __post_init__(self):
        object.__setattr__(self,'U',matrix(self.U));object.__setattr__(self,'V',matrix(self.V));object.__setattr__(self,'bias',vector(self.bias))
        d,r=len(self.U),len(self.U[0])
        if len(self.V)!=d or len(self.V[0])!=r or len(self.bias)!=r:raise ContractError('DimensionMismatch','U,V [d,r], bias [r]')
        finite_scalar(self.alpha);self.versions.require('frame','ontology','isa')
        if not self.domain or self.domain!=self.codomain:raise ContractError('TypeViolation','residual operator requires one declared state type')
        if self.nonlinearity not in ('identity','tanh','relu'):raise ContractError('UnsupportedNonlinearity','explicit activation enum required')
        if self.target not in ('working_slot','residual'):raise ContractError('UnsupportedTarget','read/write injection target required')
@dataclass(frozen=True)
class OperatorChain:
    operators: tuple[OperatorPacket,...]
    dimension: int
    domain: str
    codomain: str
    versions: VersionSet
    def __post_init__(self):
        if not 0<self.dimension<=64 or len(self.operators)>64:raise ContractError('BudgetExhausted','finite chain bound')
        self.versions.require('frame','ontology','isa')
        current=self.domain
        for op in self.operators:
            if op.domain!=current or len(op.U)!=self.dimension or not op.versions.matches(self.versions,('frame','ontology','isa')):raise ContractError('TypeViolation','compose requires explicit compatible types and coordinates')
            current=op.codomain
        if current!=self.codomain:raise ContractError('TypeViolation','chain output type mismatch')
