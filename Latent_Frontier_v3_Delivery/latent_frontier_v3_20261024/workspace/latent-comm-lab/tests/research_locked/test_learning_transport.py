import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.transport.train import describe
from latent_comm.learning.transport import anchor_contract
from latent_comm.core import ContractError,VersionSet,RoleView,Visibility,StepBudget
from latent_comm.core.budgets import aggregate_budget
from latent_comm.core.finite import least_squares
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/transport').glob('*.py'):
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
        cfg=json.loads((ROOT/'configs/learning/transport.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L07')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/transport/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_rank_deficient_minimum_norm(self):
        with aggregate_budget(StepBudget(max_steps=128)):
            result=least_squares(((1.,0.),(0.,0.)),(1.,2.))
            self.assertEqual(result.solution,(1.,0.));self.assertEqual(result.rank,1)
            self.assertFalse(result.unique);self.assertEqual(result.residual,(0.,-2.))
    def test_anchor_identity(self):
        s=RoleView(Visibility.SENDER,{'public_probes':((1.,0.),(0.,1.))},{},VersionSet(task='t1'))
        r=RoleView(Visibility.RECEIVER,{'public_probes':((1.,0.),(0.,1.))},{},VersionSet(task='t1'))
        self.assertEqual(anchor_contract(s,r).coordinate_ids,('probe:0','probe:1'))
        changed=RoleView(Visibility.RECEIVER,{'public_probes':((0.,1.),(1.,0.))},{},VersionSet(task='t1'))
        with self.assertRaises(ContractError):anchor_contract(s,changed)
    def test_jvp_vjp_source_and_no_token_kl(self):
        stage=(ROOT/'src/latent_comm/learning/transport/__init__.py').read_text()
        self.assertIn('tensor_transport(',stage);self.assertIn('functional_behavior(',stage)
        solver=(ROOT/'src/latent_comm/mechanisms/h37_gradient_transport/adapter.py').read_text()
        self.assertIn('jvp',solver);self.assertIn('vjp',solver);self.assertNotIn('no_grad()',stage)

if __name__=='__main__':unittest.main()
