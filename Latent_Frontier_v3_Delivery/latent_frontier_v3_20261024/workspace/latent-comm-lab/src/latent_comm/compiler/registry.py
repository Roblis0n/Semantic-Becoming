"""Data-only capability lookup: importing this module never loads a mechanism."""
import json
from pathlib import Path
from .types import NodeCapability

def mechanism_registry() -> dict[str, NodeCapability]:
    rows = json.loads(Path(__file__).with_name('mechanism_registry.json').read_text(encoding='utf-8'))
    result = {}
    for row in rows:
        for k in ('inputs', 'outputs'): row[k] = tuple(tuple(p) for p in row[k])
        for k in ('read_set', 'write_set'): row[k] = frozenset(row[k])
        for k in ('required_capabilities', 'required_version_axes'): row[k] = tuple(row[k])
        entry = NodeCapability(**row)
        if entry.key in result: raise ValueError('duplicate capability ' + entry.key)
        result[entry.key] = entry
    if set(result) != {f'H{i:02d}' for i in range(1,49)}: raise ValueError('mechanism registry must cover H01 through H48')
    return result

def builtin_registry() -> dict[str, NodeCapability]:
    signatures = {
        'ReadEvidence': ('EvidenceAtoms', 'EvidenceRecord', 'E'),
        'EncodeView': ('RoleView', 'EncodedView', 'Z'),
        'ConstructObject': ('ObjectSpec', 'TypedObject', 'Z'),
        'TransformFrame': ('FrameSpec', 'TransportedObject', 'F'),
        'ProposeConcept': ('OntologySnapshot', 'OntologyDelta', 'O'),
        'RewriteQuestion': ('QuestionIR', 'QuestionGraph', 'Q'),
        'MapAnalogy': ('TypedOperationGraph', 'CompiledAnalogy', 'P'),
        'GraftMechanism': ('TargetSCM', 'GraftedSCM', 'W'),
        'IntegrateTrajectory': ('Dynamics', 'TrajectoryObject', 'Z'),
        'CoarseGrain': ('MicroState', 'MultiScaleState', 'Z'),
        'TransportUpdate': ('SourceDirection', 'TransportedUpdate', 'U'),
        'ApplyPlasticity': ('PlasticityAST', 'UpdateRule', 'U'),
        'CompileMacro': ('TypedProgram', 'ExecutableProgram', 'P'),
        'StepWorld': ('TransitionKernel', 'WorldState', 'W'),
        'SelectQuery': ('QuestionIR', 'QuerySelection', 'Q'),
        'AccumulateProvenance': ('EvidenceAtoms', 'ProvenanceGraph', 'E'),
        'CommitTransaction': ('Transaction', 'CommitRecord', 'K'),
    }
    return {op: NodeCapability(op, op, (('in0', a),), (('out0', b),), frozenset(w), frozenset(w), 'exact', 'deterministic_given_inputs', ('ir:'+op,), ('schema',), 'unbound:'+op, 'docs/07_编译器与可执行流水线.md') for op,(a,b,w) in signatures.items()}
