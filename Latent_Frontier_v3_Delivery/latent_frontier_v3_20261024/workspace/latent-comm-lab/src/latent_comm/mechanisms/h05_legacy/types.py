from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError
@dataclass(frozen=True)
class ResumeContract:
    model_revision: str
    tokenizer_revision: str
    dtype: str
    cache_layout: str
    mode: str
    def __post_init__(self):
        if self.mode not in ('exact_same_model','heterogeneous_approximate','exact_program') or not all((self.model_revision,self.tokenizer_revision,self.dtype,self.cache_layout)):raise ContractError('UnboundResume','complete backend contract required')
@dataclass(frozen=True)
class ProgramOperation:
    operation_id: str
    output: str
    expression: tuple
    dependencies: tuple[str,...]=()
@dataclass(frozen=True)
class ContinuationPacket:
    program: tuple[ProgramOperation,...]
    values: tuple[tuple[str,float],...]
    program_counter: int
    source_clock: int
    completed_operations: tuple[str,...]
    pending_dependencies: tuple[str,...]
    evidence_handles: tuple[str,...]
    public_boundary_conditions: tuple[str,...]
    transaction_version: str
    target_resume_contract: ResumeContract
    versions: VersionSet
    closed: bool=False
    def __post_init__(self):
        self.versions.require('state','isa','task','evidence')
        if not 0<=self.program_counter<=len(self.program)<=64 or self.source_clock<0:raise ContractError('InvalidContinuation','program position bounds')
        if len({op.operation_id for op in self.program})!=len(self.program) or len(dict(self.values))!=len(self.values):raise ContractError('InvalidContinuation','unique operations and variable names')
        if self.completed_operations!=tuple(op.operation_id for op in self.program[:self.program_counter]):raise ContractError('InvalidContinuation','completed prefix cannot skip or replay operations')
        if not self.transaction_version:raise ContractError('UnboundTransaction','snapshot version required')


@dataclass(frozen=True)
class PositionSpec:
    cached_tokens: int
    next_position: int
    pending_token_count: int
    padding_side: str
    position_id_policy: str
    def __post_init__(self):
        if type(self.cached_tokens) is not int or self.cached_tokens<0 or self.next_position!=self.cached_tokens or self.pending_token_count!=1 or self.padding_side not in ('left','right') or self.position_id_policy not in ('explicit','mask_cumsum'):raise ContractError('PositionMismatch','exact continuation consumes one pending token at the cached boundary')

@dataclass(frozen=True)
class ModelContinuation:
    contract: ResumeContract
    position_spec: PositionSpec
    random_state_scope: str
    cpu_rng_state: object
    cuda_rng_states: tuple[tuple[int,object],...]
    cache: object
    attention_mask: object
    pending_token_ids: object
    position_ids: object
    completed_operations: tuple[str,...]
    pending_dependencies: tuple[str,...]
    branch_lineage: tuple[str,...]
    transaction_version: str
    role_origins: tuple[str,...]
    versions: VersionSet
    closed: bool=False
    def __post_init__(self):
        if self.contract.mode!='exact_same_model' or self.random_state_scope not in ('none','cpu','cpu_cuda') or not self.transaction_version:raise ContractError('UnboundResume','exact model snapshot and explicit RNG/snapshot scope required')
        if self.random_state_scope=='none' and (self.cpu_rng_state is not None or self.cuda_rng_states) or self.random_state_scope=='cpu' and self.cuda_rng_states:raise ContractError('RandomStateMismatch','RNG payload must match declared scope')
        if self.random_state_scope!='none' and self.cpu_rng_state is None:raise ContractError('RandomStateMismatch','CPU RNG capture missing')
        if len(set(self.completed_operations))!=len(self.completed_operations) or set(self.completed_operations)&set(self.pending_dependencies):raise ContractError('InvalidContinuation','completed work cannot also be pending')
        self.versions.require('state','isa','task','evidence')
