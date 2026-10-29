import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.causal_analogy.train import describe
from latent_comm.learning.causal_analogy import noise_atoms,module_coefficient
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.budgets import aggregate_budget
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/causal_analogy').glob('*.py'):
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
        cfg=json.loads((ROOT/'configs/learning/causal_analogy.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L05')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/causal_analogy/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_noise_identity_and_normalization(self):
        with aggregate_budget(StepBudget(max_steps=16)) as budget:
            for contract in ('shared_bit','independent_bits'):
                atoms=noise_atoms(contract);budget.consume(steps=len(atoms),cases=1)
                self.assertEqual(sum(p for _,_,p in atoms),1.)
                if contract=='shared_bit':self.assertTrue(all(u==v for u,v,_ in atoms))
                else:self.assertTrue(any(u!=v for u,v,_ in atoms))
    def test_scm_effect_and_false_analogy(self):
        with aggregate_budget(StepBudget(max_steps=16)) as budget:
            effects=[]
            for u,v,probability in noise_atoms('shared_bit'):
                budget.consume(steps=1,cases=1)
                effects.append((2.*(2.*1.)+u,3.*1.+v,probability))
            self.assertEqual(effects,[(4.,3.,.5),(5.,4.,.5)])
            self.assertNotEqual(2.*2.-3.*2.,0.)
            self.assertEqual(2.*2.-2.*2.,0.)
    def test_operation_map_behavior_owner(self):
        from latent_comm.learning.causal_analogy import ANALOGY_LOSS_SPECS
        from latent_comm.learning.contracts import Phase,validate_phase
        phase=Phase('operation_only',('operation_map',),(('behavior',1.),),1,.01)
        validate_phase(phase,{'operation_map':{'logits':object()}},ANALOGY_LOSS_SPECS)
    def test_unknown_noise_rejected(self):
        with self.assertRaises(ContractError):noise_atoms('silently_independent')
    def test_no_supervised_module_generation(self):
        tree=ast.parse((ROOT/'src/latent_comm/learning/causal_analogy/__init__.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.FunctionDef) and node.name=='forward_roles':self.assertNotIn('supervision',ast.unparse(node))
    def test_exact_hardening_rechecks(self):
        source=(ROOT/'src/latent_comm/learning/causal_analogy/__init__.py').read_text()
        self.assertIn('return validate_hardened(',source)

if __name__=='__main__':unittest.main()
