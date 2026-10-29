import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.meta_rules.train import describe
from latent_comm.learning.meta_rules import rule_ast,validate_episode_ids
from latent_comm.mechanisms.h38_plasticity.reference import validate_rule,apply_rule
from latent_comm.mechanisms.h38_plasticity.types import PlasticityProgram
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.budgets import aggregate_budget
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/meta_rules').glob('*.py'):
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
        cfg=json.loads((ROOT/'configs/learning/meta_rules.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L08')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/meta_rules/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_ast_and_partition_isolation(self):
        self.assertEqual(validate_rule(rule_ast()),4)
        self.assertTrue(validate_episode_ids('support:1','query:1'))
        with self.assertRaises(ContractError):validate_episode_ids('same','same')
    def test_bounded_rule_updates(self):
        program=PlasticityProgram(rule_ast(),('adapter.theta',),1.,3,3,'i1','exact_unroll')
        theta=(1.,2.);memory=()
        with aggregate_budget(StepBudget(max_steps=16)):
            for step in range(3):
                result=apply_rule(program,(('adapter.theta',theta),),(('adapter.theta',theta),),memory=memory,rule_parameters=(('rate',-.1),('memory_decay',.5),('clip',1.)),step=step)
                theta=dict(result.parameters)['adapter.theta'];memory=result.memory
        self.assertAlmostEqual(theta[0],.797375);self.assertAlmostEqual(theta[1],1.7)
    def test_first_order_stop_is_explicit(self):
        source=(ROOT/'src/latent_comm/learning/meta_rules/__init__.py').read_text()
        self.assertIn("create_graph=self.estimator=='exact_unroll'",source)
        self.assertIn("if self.estimator=='first_order':gradient=gradient.detach()",source)
        self.assertIn("raw_norms.append(raw_update.norm())",source)
        self.assertIn("'gradient_through_selection':False",source)

if __name__=='__main__':unittest.main()
