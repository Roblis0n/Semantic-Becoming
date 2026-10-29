from __future__ import annotations
import copy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import frontierctl as ctl
import math_reference as mathref

class PathsAndJson(unittest.TestCase):
    def test_valid_path(self):self.assertEqual(str(ctl.relative('a/b.json')),'a/b.json')
    def test_parent_escape(self):
        with self.assertRaises(ctl.PlanError):ctl.relative('a/../secret')
    def test_windows_drive(self):
        with self.assertRaises(ctl.PlanError):ctl.relative('C:/secret')
    def test_backslash(self):
        with self.assertRaises(ctl.PlanError):ctl.relative('a\\secret')
    def test_absolute(self):
        with self.assertRaises(ctl.PlanError):ctl.relative('/tmp/secret')
    def test_empty_segment(self):
        with self.assertRaises(ctl.PlanError):ctl.relative('a//b')
    def test_duplicate_json(self):
        with self.assertRaises(ctl.PlanError):ctl.loads('{"x":1,"x":2}')
    def test_nan(self):
        with self.assertRaises(ctl.PlanError):ctl.loads('{"x":NaN}')
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'actual').write_text('x');(r/'alias').symlink_to(r/'actual')
            with self.assertRaises(ctl.PlanError):ctl.within(r,'alias',True)
    def test_atomic_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';ctl.atomic_json(p,{'value':1});ctl.atomic_json(p,{'value':2})
            self.assertEqual(ctl.load(p),{'value':2});self.assertEqual(len(list(Path(d).iterdir())),1)

class GraphAndState(unittest.TestCase):
    def setUp(self):
        self.g={'tasks':[{'id':'A00','dependencies':[],'outputs':['a.txt']},
                         {'id':'A01','dependencies':['A00'],'outputs':['b.txt']},
                         {'id':'Z01','dependencies':['A01'],'outputs':['result/']}],
                'terminal_task':'Z01','task_count':3}
    def test_topological_order(self):self.assertEqual(ctl.graph_order(self.g),['A00','A01','Z01'])
    def test_cycle(self):
        self.g['tasks'][0]['dependencies']=['Z01']
        with self.assertRaises(ctl.PlanError):ctl.graph_order(self.g)
    def test_missing_dependency(self):
        self.g['tasks'][1]['dependencies']=['X99']
        with self.assertRaises(ctl.PlanError):ctl.graph_order(self.g)
    def test_duplicate_id(self):
        self.g['tasks'][1]['id']='A00'
        with self.assertRaises(ctl.PlanError):ctl.graph_order(self.g)
    def test_output_owner_overlap(self):
        self.g['tasks'][0]['outputs']=['result/sub.py']
        with self.assertRaises(ctl.PlanError):ctl.graph_order(self.g)
    def test_orphan(self):
        self.g['tasks'].append({'id':'X01','dependencies':[],'outputs':['orphan.md']});self.g['task_count']=4
        with self.assertRaises(ctl.PlanError):ctl.graph_order(self.g)
    def test_count_mismatch(self):
        self.g['task_count']=4
        with self.assertRaises(ctl.PlanError):ctl.graph_order(self.g)
    def test_ready_dependency(self):
        s=ctl.initial_state(self.g,'test');self.assertEqual(ctl.ready_tasks(self.g,s),['A00'])
        s['tasks']['A00']['status']='done';self.assertEqual(ctl.ready_tasks(self.g,s),['A01'])
    def test_core_blocker_blocks(self):
        s=ctl.initial_state(self.g,'test');s['tasks']['A00']['status']='blocked'
        self.assertEqual(ctl.ready_tasks(self.g,s),[])
    def test_optional_blocker_is_terminal(self):
        self.g['tasks'][0]['external_optional']=True
        s=ctl.initial_state(self.g,'test');s['tasks']['A00']['status']='blocked'
        self.assertEqual(ctl.ready_tasks(self.g,s),['A01'])
    def test_invalidate_descendants(self):
        s=ctl.initial_state(self.g,'test')
        for t in s['tasks'].values():t['status']='done'
        self.assertEqual(ctl.invalidate(self.g,s,'A01'),['A01','Z01'])
        self.assertEqual(s['tasks']['A00']['status'],'done')
    def test_state_ids_must_match(self):
        s=ctl.initial_state(self.g,'test');s['tasks'].pop('A00')
        with self.assertRaises(ctl.PlanError):ctl.ready_tasks(self.g,s)
    def test_outputs_nonempty(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a.txt').touch()
            with self.assertRaises(ctl.PlanError):ctl.verify_outputs(root,self.g['tasks'][0])
    def test_output_hashes_real_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a.txt').write_text('real source')
            out=ctl.verify_outputs(root,self.g['tasks'][0]);self.assertEqual(out[0]['sha256'],ctl.digest(root/'a.txt'))

class PolicyAndPackage(unittest.TestCase):
    def setUp(self):self.policy=ctl.load(ROOT/'specs/execution_policy.json')
    def test_model_action_denied(self):
        with self.assertRaises(ctl.PlanError):ctl.gate(self.policy,'model_forward')
    def test_unknown_action_denied(self):
        with self.assertRaises(ctl.PlanError):ctl.gate(self.policy,'do_whatever')
    def test_public_read_allowed_not_executed(self):self.assertIs(ctl.gate(self.policy,'public_read')['executed'],False)
    def test_media_requires_authorization(self):
        with self.assertRaises(ctl.PlanError):ctl.gate(self.policy,'authorized_zero_new_cost_media')
    def test_media_requires_no_cost(self):
        with self.assertRaises(ctl.PlanError):ctl.gate(self.policy,'authorized_zero_new_cost_media',authorized=True)
    def test_media_both_flags(self):self.assertTrue(ctl.gate(self.policy,'authorized_zero_new_cost_media',authorized=True,zero_new_cost=True)['allowed_by_plan'])
    def test_tampered_model_policy(self):
        self.policy['models']['initialize']=True
        with self.assertRaises(ctl.PlanError):ctl.check_policy(self.policy)
    def test_tampered_allowed_actions(self):
        self.policy['allowed_actions'].append('purchase')
        with self.assertRaises(ctl.PlanError):ctl.check_policy(self.policy)
    def test_bool_not_zero_budget(self):
        self.policy['external_effects']['new_spend']=False
        with self.assertRaises(ctl.PlanError):ctl.check_policy(self.policy)
    def test_full_package(self):
        report=ctl.validate(ROOT);self.assertTrue(report['ok']);self.assertEqual(report['scientific_claims_validated'],0)
    def test_compile_is_plan_only(self):
        plan=ctl.compile_recipe(ROOT,'C13');self.assertTrue(plan['plan_compilation_only']);self.assertFalse(plan['research_execution'])
    def test_recipe_path_escape(self):
        with self.assertRaises(ctl.PlanError):ctl.compile_recipe(ROOT,'../secret')
    def test_scan_does_not_execute(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'not_run.py';p.write_text('raise RuntimeError("must not execute")\ndef empty():\n    pass\n')
            report=ctl.scan_python(p);self.assertFalse(report['executed']);self.assertEqual(len(report['warnings']),1)

class ExactMathematics(unittest.TestCase):
    def test_gauge(self):
        out=mathref.covariant_apply([[0,1],[1,0]],[[2,0],[0,3]],[[1],[2]])
        self.assertEqual(out['left'],out['right']);self.assertEqual(out['left'],[[F(6)],[F(2)]])
    def test_singular(self):
        with self.assertRaises(ValueError):mathref.inverse2([[1,2],[2,4]])
    def test_dimension_mismatch(self):
        with self.assertRaises(ValueError):mathref.matmul([[1,2]],[[1]])
    def test_ragged(self):
        with self.assertRaises(ValueError):mathref.matmul([[1,2],[3]],[[1],[2]])
    def test_transport(self):self.assertEqual(mathref.scalar_transport(4,1),F(1,4))
    def test_regularized_transport(self):self.assertEqual(mathref.scalar_transport(4,1,1),F(4,17))
    def test_unidentifiable_transport(self):
        with self.assertRaises(ValueError):mathref.scalar_transport(0,1)
    def test_negative_regularization(self):
        with self.assertRaises(ValueError):mathref.scalar_transport(4,1,-1)
    def test_partition_refines(self):
        coarse=mathref.question_partition([1,2,3,4],[lambda x:x%2])
        fine=mathref.question_partition([1,2,3,4],[lambda x:x%2,lambda x:x>2])
        self.assertTrue(mathref.is_refinement(coarse,fine));self.assertFalse(mathref.is_refinement(fine,coarse))
    def test_repeated_evidence(self):self.assertEqual(mathref.independent_probability(('or','e','e'),{'e':F(4,5)},independence_declared=True),F(4,5))
    def test_independent_evidence(self):self.assertEqual(mathref.independent_probability(('or','e','f'),{'e':F(4,5),'f':F(4,5)},independence_declared=True),F(24,25))
    def test_unknown_dependence(self):
        with self.assertRaises(ValueError):mathref.independent_probability(('or','e','f'),{'e':F(4,5),'f':F(4,5)})
    def test_missing_atom(self):
        with self.assertRaises(ValueError):mathref.evaluate_boolean(('or','e','missing'),{'e':True})
    def test_shapley_complementarity(self):
        values=mathref.shapley(['a','b'],lambda s:F(len(s)==2))
        self.assertEqual(values,{'a':F(1,2),'b':F(1,2)})
    def test_shapley_efficiency_nonzero_baseline(self):
        values=mathref.shapley(['a','b','c'],lambda s:F(7+len(s)))
        self.assertEqual(sum(values.values()),F(3))
    def test_fixture_status(self):self.assertIs(mathref.fixture_report()['scientific_effectiveness_tested'],False)

if __name__=='__main__':unittest.main(verbosity=2)
