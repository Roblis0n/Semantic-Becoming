import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.worlds.train import describe
from latent_comm.learning.worlds import binary_component,lineage_contract
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.budgets import aggregate_budget
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/worlds').glob('*.py'):
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
        cfg=json.loads((ROOT/'configs/learning/worlds.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L10')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/worlds/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_shared_noise_cannot_be_independent(self):
        with aggregate_budget(StepBudget(max_steps=16)) as budget:
            shared=[0.]*4;independent=[0.]*4
            for u,v,p in ((0,0,.5),(1,1,.5)):
                budget.consume(steps=1);shared[2*binary_component(('copy_noise','shared'),u)+binary_component(('copy_noise','shared'),v)]+=p
            for u,v,p in ((0,0,.25),(0,1,.25),(1,0,.25),(1,1,.25)):
                budget.consume(steps=1);independent[2*u+v]+=p
            self.assertEqual(shared,[.5,0.,0.,.5]);self.assertEqual(independent,[.25]*4)
    def test_holdout_ids_and_independence_assumption_are_separate(self):
        self.assertTrue(lineage_contract({'synthetic':True,'parent_sources':['world:a'],'holdout_sources':['external:b'],'holdout_independence_assumed':True}))
        for public in ({'synthetic':False,'parent_sources':['world:a'],'holdout_sources':['external:b'],'holdout_independence_assumed':True},{'synthetic':True,'parent_sources':['world:a'],'holdout_sources':['world:a'],'holdout_independence_assumed':True},{'synthetic':True,'parent_sources':['world:a'],'holdout_sources':['external:b']}):
            with self.assertRaises(ContractError):lineage_contract(public)
    def test_alternating_phases_are_disjoint(self):
        c=json.loads((ROOT/'configs/learning/worlds.json').read_text())
        for variant in ('dream','ecology'):
            a,b=c['phases'][variant];self.assertFalse(set(a['parameter_owners'])&set(b['parameter_owners']))
    def test_independent_holdout_credit_is_stopped(self):
        source=(ROOT/'src/latent_comm/mechanisms/h44_dreaming/losses.py').read_text()
        self.assertIn('holdout_errors.detach()',source)
        stage=(ROOT/'src/latent_comm/learning/worlds/__init__.py').read_text()
        self.assertIn('adapted=theta-self.adaptation_rate*gradient',stage)

if __name__=='__main__':unittest.main()
