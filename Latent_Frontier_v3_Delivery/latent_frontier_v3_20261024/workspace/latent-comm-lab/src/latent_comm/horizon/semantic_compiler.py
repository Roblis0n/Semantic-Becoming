"""X12: optimize semantic operations then bind replaceable, policy-locked backends."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c20 import SemanticCompilerInput,LockedBackendPlan
from latent_comm.mechanisms.h35_renormalization.types import ScalePacket,ClosureResidual
from latent_comm.backends.capabilities import BackendCapabilities
from .contracts import bounded_horizon,assumptions,require_complete
ASSUMPTIONS=assumptions('Typed semantic IR, operation-preserving maps, scale contracts and source-bound backend metadata exist.','Backend replacement requires declared operations and compatible role/input-gradient interfaces, not brand or size similarity.','A finite compiler can annotate scale-safe optimization, lowered operations and unresolved capability bindings.','Future learned backends may implement some compiled semantics; arbitrary models are not universal executors.')
@dataclass(frozen=True)
class SemanticCompilationRequest:
    semantics: SemanticCompilerInput
    scale: ScalePacket
    candidate_backends: tuple[BackendCapabilities,...]
    versions: VersionSet
@dataclass(frozen=True)
class BackendBinding:
    model_identity: str
    missing: tuple[str,...]
    status: str
    execution_locked: bool=True
@dataclass(frozen=True)
class SemanticCompilationRecord:
    plan: LockedBackendPlan
    optimized_program: object
    eliminated_nodes: tuple[str,...]
    scale_closure: ClosureResidual
    optimization_passes: tuple[tuple[str,str],...]
    backend_bindings: tuple[BackendBinding,...]
    readable_edges: tuple[tuple[str,str,str],...]
    status: str
def eliminate_dead_pure_nodes(program):
    from latent_comm.mechanisms.h07_legacy.reference import compile_program
    nodes={n.node_id:n for n in program.packet.nodes};required=set();pending=[program.packet.result_id]
    while pending:
        name=pending.pop()
        if name in nodes and name not in required:
            required.add(name);pending.extend(nodes[name].inputs)
    # The current finite ISA returns immutable local values. No host write or
    # authorization side effect can be hidden in a pruned instruction.
    removed=tuple(n.node_id for n in program.packet.nodes if n.node_id not in required)
    packet=replace(program.packet,nodes=tuple(n for n in program.packet.nodes if n.node_id in required))
    return compile_program(packet),removed
@bounded_horizon('X12',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.compositions.c20 import run_reference,build_graph
    from latent_comm.mechanisms.h35_renormalization.reference import closure_report
    q=request
    if q.semantics.versions!=q.versions or q.scale.source_version!=q.versions.state or len(q.candidate_backends)>8:raise ContractError('VersionMismatch','semantic compiler and scale source snapshot must agree')
    plan=require_complete(run_reference(q.semantics));optimized,removed=eliminate_dead_pure_nodes(plan.plan.program);closure=closure_report(q.scale);required=('prefix',)+(('input_gradients',) if q.semantics.mode=='learning' else ());bindings=[]
    for backend in q.candidate_backends:
        meter.consume(steps=1);missing=[]
        for feature in required:
            try:backend.require(feature)
            except ContractError:missing.append(feature)
        bindings.append(BackendBinding(str(backend.identity),tuple(missing),'UnboundBackend' if missing else 'SourceBoundResearchLocked'))
    passes=(('dead_pure_value_elimination',str(len(removed))+' unreachable nodes removed and compiled contracts rechecked'),('immutable_base_macro_lowering','performed by C20/H40'),('operation_preservation','checked numeric and typed graph squares by C20/H30/H25'),('coarse_state_elimination','eligible_under_exact_declared_closure' if closure.closed else 'rejected_retain_detail'),('backend_binding','metadata_only_research_locked'))
    graph=build_graph(q.versions);edges=tuple((ref,node.output,port) for node in graph.nodes for port,ref in node.inputs)
    status='SourceBoundResearchLocked' if any(not b.missing for b in bindings) else 'UnboundBackend'
    return SemanticCompilationRecord(plan,optimized,removed,closure,passes,tuple(bindings),edges,status),('Optimization eligibility is not empirical speedup or model correctness.','No backend is initialized, loaded, executed or trained; missing capabilities remain unbound.')
