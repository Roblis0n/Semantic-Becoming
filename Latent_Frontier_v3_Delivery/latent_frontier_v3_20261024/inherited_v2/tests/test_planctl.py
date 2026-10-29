"""Tests of the planning tools only; not tests of the proposed algorithms."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('planctl',ROOT/'tools/planctl.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class PlanTests(unittest.TestCase):
    def setUp(self):
        self.policy=m.read_json(ROOT/'specs/execution_policy.json')
    def test_full_bundle(self):
        self.assertEqual(m.validate(ROOT)['status'],'passed')
    def test_dag(self):
        self.assertEqual(m.topological_order([{'id':'b','depends_on':['a']},{'id':'a','depends_on':[]}]),['a','b'])
    def test_cycle(self):
        with self.assertRaises(m.PlanError):
            m.topological_order([{'id':'a','depends_on':['b']},{'id':'b','depends_on':['a']}])
    def test_missing(self):
        with self.assertRaises(m.PlanError):
            m.topological_order([{'id':'a','depends_on':['b']}])
    def test_duplicate(self):
        with self.assertRaises(m.PlanError):
            m.topological_order([{'id':'a','depends_on':[]},{'id':'a','depends_on':[]}])
    def test_unknown_action(self):
        with self.assertRaises(m.PlanError):m.authorize('shell_arbitrary',self.policy)
    def test_research_actions_denied(self):
        for action in self.policy['banned_actions']:
            with self.subTest(action=action):
                with self.assertRaises(m.PlanError):m.authorize(action,self.policy)
    def test_media_allowed(self):
        self.assertTrue(m.authorize('authorized_media_creation',self.policy))
    def test_math_allowed(self):
        self.assertTrue(m.authorize('fixed_tensor_math',self.policy))
    def test_design_allowed(self):
        self.assertTrue(m.authorize('compile_pipeline',self.policy))
    def test_no_empirical_gate(self):
        self.assertTrue(self.policy['no_empirical_gate_for_hypothesis_implementation'])
    def test_future_software_not_claimed_done(self):
        tasks=m.read_json(ROOT/'specs/task_graph.json')['tasks']
        self.assertTrue(all(t['status']=='planned_for_dot' for t in tasks))
    def test_sources_unique(self):
        sources=m.read_json(ROOT/'specs/sources.json')
        self.assertEqual(len({s['id'] for s in sources}),18)
    def test_per_hypothesis_recipe(self):
        recipes=[m.read_json(p) for p in (ROOT/'recipes').glob('H*.json')]
        self.assertEqual({r['hypothesis_id'] for r in recipes},{f'H{i:02d}' for i in range(1,25)})
    def test_task_covers_each_hypothesis(self):
        tasks=m.read_json(ROOT/'specs/task_graph.json')['tasks']
        covered={h for t in tasks for h in t['hypotheses']}
        self.assertEqual(covered,{f'H{i:02d}' for i in range(1,25)})
    def test_no_models_in_bundle(self):
        forbidden={'.safetensors','.gguf','.pt','.pth','.bin','.ckpt'}
        self.assertFalse([p for p in ROOT.rglob('*') if p.is_file() and p.suffix in forbidden])

if __name__=='__main__':unittest.main()
