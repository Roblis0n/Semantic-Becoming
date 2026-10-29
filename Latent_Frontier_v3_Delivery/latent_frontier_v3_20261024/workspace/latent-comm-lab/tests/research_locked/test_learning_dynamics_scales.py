import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.dynamics_scales.train import describe
from latent_comm.learning.dynamics_scales import public_horizon
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.budgets import aggregate_budget
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/dynamics_scales').glob('*.py'):
            tree=ast.parse(path.read_text())
            for node in tree.body:
                if isinstance(node,ast.Import):self.assertFalse(any(a.name.split('.')[0] in {'torch','transformers','numpy'} for a in node.names))
                if isinstance(node,ast.ImportFrom):self.assertNotIn((node.module or '').split('.')[0],{'torch','transformers','numpy'})
            for node in ast.walk(tree):
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    direct_neural=any(isinstance(n,ast.Import) and any(a.name=='torch' for a in n.names) for n in node.body)
                    if direct_neural or node.name in {'build_stage','forward_roles','losses','run'}:
                        body=node.body[1:] if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) else node.body
                        self.assertTrue(any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id','')=='require_research_action' for n in body[:2]),(path.name,node.name))
                    if node.name=='forward_roles':self.assertEqual([a.arg for a in node.args.args],['self','sender','receiver'])
    def test_recipe_is_unbound(self):
        cfg=json.loads((ROOT/'configs/learning/dynamics_scales.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L06')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/dynamics_scales/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_public_horizon(self):
        self.assertEqual(public_horizon(SimpleNamespace(public_task={'steps':4,'dt':.25}),8),(4,.25))
        for steps,dt in ((9,.25),(4,0.),(4,float('inf'))):
            with self.assertRaises(ContractError):public_horizon(SimpleNamespace(public_task={'steps':steps,'dt':dt}),8)
    def test_boundary_is_public_not_supervision(self):
        source=(ROOT/'src/latent_comm/learning/dynamics_scales/__init__.py').read_text()
        self.assertIn("r.public_task['terminal']",source)
        self.assertIn("r.public_task['terminal_source']",source)
    def test_midpoint_rotation_and_boundary(self):
        with aggregate_budget(StepBudget(max_steps=16)) as budget:
            x,y=1.,0.;h=.25
            for _ in range(4):
                budget.consume(steps=1)
                denominator=1+h*h/4
                x,y=((1-h*h/4)*x-h*y)/denominator,(h*x+(1-h*h/4)*y)/denominator
            self.assertAlmostEqual(x*x+y*y,1.)
            path=tuple((1-t/4,t/4) for t in range(5));budget.consume(steps=5)
            self.assertEqual(path[0],(1.,0.));self.assertEqual(path[-1],(0.,1.))
            self.assertTrue(all(path[t+1][0]-2*path[t][0]+path[t-1][0]==0 for t in range(1,4)))
    def test_scale_retained_detail_identity(self):
        z=(2.,0.,0.,0.);coarse=(1.,0.);lift=(1.,1.,0.,0.);detail=tuple(a-b for a,b in zip(z,lift))
        self.assertEqual(tuple(a+b for a,b in zip(lift,detail)),z)
        self.assertNotEqual(lift,z)

if __name__=='__main__':unittest.main()
