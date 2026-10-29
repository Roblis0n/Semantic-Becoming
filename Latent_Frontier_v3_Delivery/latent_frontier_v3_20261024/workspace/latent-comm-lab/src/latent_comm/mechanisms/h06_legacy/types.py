from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import Matrix,Vector,matrix,vector,finite_scalar
@dataclass(frozen=True)
class Chart:
    chart_id: str
    model_revision: str
    center: Vector
    radius: float
    read_map: Matrix
    write_map: Matrix
    task_family: frozenset[str]
    behavioral_anchor: str
    versions: VersionSet
    invalidated: bool=False
    def __post_init__(self):
        object.__setattr__(self,'center',vector(self.center));object.__setattr__(self,'read_map',matrix(self.read_map));object.__setattr__(self,'write_map',matrix(self.write_map))
        if len(self.read_map[0])!=len(self.center) or len(self.write_map)!=len(self.center) or len(self.write_map[0])!=len(self.read_map):raise ContractError('DimensionMismatch','read [local,model], write [model,local]')
        if finite_scalar(self.radius)<=0 or not self.task_family or not self.behavioral_anchor:raise ContractError('UnboundChart','coverage, task family and semantic anchor required')
        self.versions.require('frame','ontology','task')
@dataclass(frozen=True)
class Transition:
    source_chart: str
    target_chart: str
    mapping: Matrix
    bias: Vector
    source_frame: str
    target_frame: str
    tasks: frozenset[str]
    information_loss: str
    def __post_init__(self):
        object.__setattr__(self,'mapping',matrix(self.mapping));object.__setattr__(self,'bias',vector(self.bias))
        if len(self.mapping)!=len(self.bias) or not self.tasks:raise ContractError('InvalidTransition','explicit target bias and task equivalence scope')
        if len(self.mapping)!=len(self.mapping[0]) and self.information_loss=='none':raise ContractError('FalseInverse','heterogeneous dimensions cannot claim lossless inverse')
