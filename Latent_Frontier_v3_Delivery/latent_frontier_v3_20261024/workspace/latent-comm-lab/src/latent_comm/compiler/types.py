"""Source-localized, immutable compiler IR. No runtime or model imports."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from latent_comm.core import TensorSpec, VersionSet

@dataclass(frozen=True)
class SourceLocation:
    source: str
    path: str
    line: int = 1
    column: int = 1

@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    location: SourceLocation
    pass_number: int
    severity: str = 'error'

class CompilationError(ValueError):
    def __init__(self, diagnostics: tuple[Diagnostic, ...]):
        self.diagnostics = diagnostics
        super().__init__('\n'.join(f'{d.location.source}:{d.location.line}:{d.location.column} {d.location.path}: {d.code}: {d.message}' for d in diagnostics))

@dataclass(frozen=True)
class TypeSpec:
    name: str
    versions: VersionSet
    visibility: str = 'public'
    tensor: TensorSpec | None = None
    fields: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    scope: frozenset[str] = frozenset()
    bound: bool = True

@dataclass(frozen=True)
class NodeCapability:
    key: str
    operation: str
    inputs: tuple[tuple[str, str], ...]
    outputs: tuple[tuple[str, str], ...]
    read_set: frozenset[str]
    write_set: frozenset[str]
    differentiability: str
    determinism: str
    required_capabilities: tuple[str, ...]
    required_version_axes: tuple[str, ...]
    implementation: str
    source_spec: str

@dataclass(frozen=True)
class IRNode:
    node_id: str
    operation: str
    mechanism: str | None
    inputs: tuple[tuple[str, str], ...]
    outputs: tuple[tuple[str, str], ...]
    input_types: tuple[tuple[str, TypeSpec], ...]
    output_types: tuple[tuple[str, TypeSpec], ...]
    read_set: frozenset[str]
    write_set: frozenset[str]
    differentiability: str
    determinism: str
    budget_cost: int
    required_capabilities: tuple[str, ...]
    implementation: str
    location: SourceLocation
    gradient_edges: tuple[tuple[str, str], ...] = ()
    gate_action: str | None = None

@dataclass(frozen=True)
class BoundedLoop:
    loop_id: str
    body: tuple[str, ...]
    max_iterations: int
    carried: tuple[tuple[str, str], ...]
    location: SourceLocation

@dataclass(frozen=True)
class CompiledIR:
    recipe_id: str
    nodes: tuple[IRNode, ...]
    objects: tuple[tuple[str, TypeSpec], ...]
    edges: tuple[tuple[str, str], ...]
    schedule: tuple[str, ...]
    loops: tuple[BoundedLoop, ...]
    diagnostics: tuple[Diagnostic, ...]
    pass_trace: tuple[str, ...]
    worst_case_steps: int
    max_steps: int
    input_digest: str
    declared_parameters: dict[str, Any] = field(default_factory=dict)
    declared_runtime_budget: dict[str, Any] = field(default_factory=dict)
    research_state: str = 'NOT_RUN'
    research_execution_authorized: bool = False
    gate: str = 'latent_comm.safety.policy.require_research_action'

    def to_dict(self) -> dict[str, Any]:
        def plain(x: Any) -> Any:
            if isinstance(x, Enum): return x.value
            if isinstance(x, dict): return {k: plain(v) for k, v in x.items()}
            if isinstance(x, (tuple, list)): return [plain(v) for v in x]
            if isinstance(x, (set, frozenset)): return [plain(v) for v in sorted(x)]
            return x
        return plain(asdict(self))
