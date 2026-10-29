from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import Matrix,matrix
@dataclass(frozen=True)
class Hyperedge:
    edge_id: str
    members: tuple[str,...]
    projections: tuple[Matrix,...]
    readout: Matrix
    evidence_support: tuple[tuple[str,frozenset[str]],...]
    versions: VersionSet
    credit_is_money: bool=False
    def __post_init__(self):
        if not 2<=len(self.members)<=6 or len(set(self.members))!=len(self.members) or len(self.projections)!=len(self.members):raise ContractError('InvalidHyperedge','2..6 unique members and role-specific projections')
        object.__setattr__(self,'projections',tuple(matrix(p) for p in self.projections));object.__setattr__(self,'readout',matrix(self.readout))
        if len({len(p) for p in self.projections})!=1 or len(self.readout[0])!=len(self.projections[0]):raise ContractError('DimensionMismatch','shared multilinear rank')
        if self.credit_is_money:raise ContractError('ScopeViolation','internal diagnostic credit is never currency')
        if len(self.evidence_support)!=len(self.members) or set(dict(self.evidence_support))!=set(self.members):raise ContractError('MissingSource','explicit evidence support per member')
        self.versions.require('task','evidence')
