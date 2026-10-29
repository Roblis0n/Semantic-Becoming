import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.uncertainty.train import describe
from latent_comm.learning.uncertainty import signed_responses,certified_domain,exact_partition
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.budgets import aggregate_budget
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/uncertainty').glob('*.py'):
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
        cfg=json.loads((ROOT/'configs/learning/uncertainty.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L11')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/uncertainty/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_minimax_without_invented_prior(self):
        self.assertEqual(signed_responses(('y=x','y=-x'),0),(0,0))
        self.assertEqual(signed_responses(('y=x','y=-x'),1),(1,-1))
        source=(ROOT/'src/latent_comm/learning/uncertainty/__init__.py').read_text()
        self.assertIn('verified_partition_reduction',source)
    def test_certificate_and_retraction(self):
        with aggregate_budget(StepBudget(max_steps=64)):
            self.assertEqual(certified_domain('even',True,'w1').feasible,(2,4))
            self.assertEqual(certified_domain('even',False,'w1').feasible,(1,2,3,4))
            self.assertEqual(certified_domain('soft_even_preference',True,'w1').feasible,(1,2,3,4))
    def test_exact_partition_refinement(self):
        with aggregate_budget(StepBudget(max_steps=64)):
            coarse=exact_partition(('parity',));fine=exact_partition(('parity','greater_than_two'))
            self.assertEqual(len(coarse.classes),2);self.assertEqual(len(fine.classes),4)
    def test_hard_mask_not_learned(self):
        source=(ROOT/'src/latent_comm/learning/uncertainty/__init__.py').read_text()
        self.assertIn('x in region.feasible',source);self.assertNotIn('sigmoid()>',source)

if __name__=='__main__':unittest.main()
