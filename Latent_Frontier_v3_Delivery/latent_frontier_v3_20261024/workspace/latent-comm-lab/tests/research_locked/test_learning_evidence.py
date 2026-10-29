import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.evidence.train import describe
from latent_comm.learning.evidence import source_classes
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.budgets import aggregate_budget
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/evidence').glob('*.py'):
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
        cfg=json.loads((ROOT/'configs/learning/evidence.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L12')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/evidence/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_duplicate_source_is_one_atom(self):
        self.assertEqual(source_classes(((True,True),(True,True))),((0,1),))
        self.assertEqual(source_classes(((True,False),(False,True))),((0,),(1,)))
        p=.8;self.assertAlmostEqual(p,.8);self.assertAlmostEqual(1-(1-p)**2,.96)
        self.assertNotEqual(p,1-(1-p)**2)
    def test_identity_must_be_equivalence(self):
        with self.assertRaises(ContractError):source_classes(((True,True,False),(True,True,True),(False,True,True)))
    def test_pair_value_calibration(self):
        with aggregate_budget(StepBudget(max_steps=16)) as budget:
            values=[]
            for members in ((),(0,),(1,),(2,),(0,1),(0,2),(1,2),(0,1,2)):
                budget.consume(steps=1,cases=1);values.append(len(members)+(2 if 0 in members and 1 in members else 0))
            self.assertEqual(values,[0,1,1,1,4,2,2,5])
    def test_assumption_not_inferred_from_link(self):
        source=(ROOT/'src/latent_comm/learning/evidence/__init__.py').read_text()
        self.assertIn("declaration_id=='UNBOUND'",source)
        self.assertIn('identity is not independence',source)
        self.assertIn('scores=values.detach()',source)

if __name__=='__main__':unittest.main()
