from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet,Scope
@dataclass(frozen=True)
class ValueType:
    kind: str
    dimension: int | None
    frame: str | None
    def __post_init__(self):
        if self.dimension is not None and not 1<=self.dimension<=64:raise ContractError('DimensionMismatch','finite state dimension')
        if self.kind=='state' and (self.dimension is None or not self.frame):raise ContractError('UnboundState','state dimension and frame required')
@dataclass(frozen=True)
class Instruction:
    node_id: str
    opcode: str
    inputs: tuple[str,...]
    output_type: ValueType
    bound: int=1
@dataclass(frozen=True)
class ProgramPacket:
    nodes: tuple[Instruction,...]
    input_types: tuple[tuple[str,ValueType],...]
    result_id: str
    versions: VersionSet
    scope: Scope
    def __post_init__(self):
        self.versions.require('frame','ontology','isa')
        if len(self.nodes)>64 or len(self.input_types)>64:raise ContractError('BudgetExhausted','bounded program graph')
@dataclass(frozen=True)
class CompiledProgram:
    packet: ProgramPacket
    schedule: tuple[str,...]
    worst_case_steps: int


@dataclass(frozen=True)
class TensorFieldBinding:
    anchor: object
    matrices: object
    targets: object
    temperatures: object
    anchor_strength: float
    frame: str
    step_size: float=.01
    nonlinear: bool=False

@dataclass(frozen=True)
class TensorConstraintBinding:
    matrix: object
    target: object
    temperature: object
    frame: str

@dataclass(frozen=True)
class TensorProgramContinuation:
    program: tuple
    values: tuple[tuple[str,object],...]
    program_counter: int
    completed_operations: tuple[str,...]
    available_dependencies: frozenset[str]
    pending_dependencies: tuple[str,...]
    versions: VersionSet
