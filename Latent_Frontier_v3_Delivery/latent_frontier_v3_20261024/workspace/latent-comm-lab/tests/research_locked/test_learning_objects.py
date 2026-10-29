import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.objects.train import describe
import math
from latent_comm.mechanisms.h03_legacy.reference import logsumexp
from latent_comm.backends.behavior import TokenizerContract
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.budgets import aggregate_budget
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/objects').glob('*.py'):
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
        cfg=json.loads((ROOT/'configs/learning/objects.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L02')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/objects/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_sequence_mixture_is_not_token_mixture(self):
        with aggregate_budget(StepBudget(max_steps=16)) as budget:
            branch=((.9,.1),(.1,.9));budget.consume(steps=4)
            sequence=math.exp(logsumexp(math.log(.5)+sum(math.log(p) for p in row) for row in branch))
            independent_tokens=(.5*.9+.5*.1)**2
            self.assertAlmostEqual(sequence,.09);self.assertAlmostEqual(independent_tokens,.25)
    def test_prefix_posterior_updates(self):
        weights=(.5,.5);token=(.9,.1);normal=sum(w*p for w,p in zip(weights,token));posterior=tuple(w*p/normal for w,p in zip(weights,token));self.assertEqual(posterior,(.9,.1))
    def test_tokenizer_mismatch(self):
        a=TokenizerContract('a','r1','v1','t1');b=TokenizerContract('b','r1','v1','t1')
        with self.assertRaises(ContractError):a.require_same_vocabulary(b)
    def test_locality_masks_task_and_response(self):
        source=(ROOT/'src/latent_comm/learning/objects/__init__.py').read_text()
        self.assertIn('valid=valid&output.locality.unsqueeze(-1)',source)
        self.assertIn('task_mask=task_mask&output.locality.unsqueeze(-1)',source)
        self.assertIn('safe[:,:-1]',source)
    def test_no_total_double_count(self):
        c=json.loads((ROOT/'configs/learning/objects.json').read_text());self.assertTrue(all('total' not in p['loss_weights'] for rows in c['phases'].values() for p in rows))

if __name__=='__main__':unittest.main()
