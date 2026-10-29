"""Explicit authoring audit; stdlib/AST only, never invokes a model entry point."""
import ast
import importlib.abc
import json
from pathlib import Path
import sys
import unittest

NEURAL_PREFIXES=frozenset({'torch','transformers','tensorflow','jax','numpy','safetensors'})
class NoNeuralImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in NEURAL_PREFIXES:raise RuntimeError('Authoring audit forbids neural/numeric backend import: '+fullname)
        return None

def audit(root):
    """Run only explicit safe L-stage tests; guard-entry calls are excluded."""
    blocker=NoNeuralImports();sys.meta_path.insert(0,blocker)
    try:
        test_root=root/'tests/research_locked';suite=unittest.TestSuite();loader=unittest.TestLoader()
        # L03/L04 predate the no-guard-invocation tightening. Their two legacy
        # guard-entry tests are excluded explicitly, not run to prove denial.
        excluded={'test_gate_before_model','test_gate_before_training','test_build_locked','test_structural_train_locked'}
        def selected(item):
            if isinstance(item,unittest.TestSuite):
                for child in item:yield from selected(child)
            elif item._testMethodName not in excluded:yield item
        for path in sorted(test_root.glob('test_learning_*.py')):
            if path.name not in {'test_learning_views.py','test_learning_objects.py','test_learning_frames.py','test_learning_concept_questions.py','test_learning_causal_analogy.py','test_learning_dynamics_scales.py','test_learning_transport.py','test_learning_meta_rules.py','test_learning_isa_search.py','test_learning_worlds.py','test_learning_uncertainty.py','test_learning_evidence.py','test_learning_joint.py'}:continue
            tree=ast.parse(path.read_text(encoding='utf-8'))
            forbidden_calls={'build_stage','train','run','select_concept_structure','search_question_structure'}
            for node in ast.walk(tree):
                if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
                    invokes_entry=any(isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id in forbidden_calls for call in ast.walk(node))
                    if invokes_entry and node.name not in excluded:raise RuntimeError('Unapproved model-entry test must be reviewed before audit: '+path.name+':'+node.name)
            suite.addTests(selected(loader.discover(str(test_root),pattern=path.name)))
        for path in sorted((root/'src/latent_comm/learning').rglob('*.py')):ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        loaded=sorted(m for m in sys.modules if m.split('.')[0] in NEURAL_PREFIXES)
        print(json.dumps({'research_state':'NOT_RUN','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'neural_modules_loaded':loaded,'legacy_model_entry_tests_excluded':sorted(excluded)},sort_keys=True))
        return result.wasSuccessful() and not loaded
    finally:sys.meta_path.remove(blocker)

if __name__=='__main__':raise SystemExit(0 if audit(Path(__file__).resolve().parents[4]) else 1)
