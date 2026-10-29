import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.isa_search.train import describe
from latent_comm.learning.isa_search import parse_world_expression,compiled_world_macro
from latent_comm.mechanisms.h40_instruction_set.reference import execute_base,free_variables
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.budgets import aggregate_budget
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/isa_search').glob('*.py'):
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
        cfg=json.loads((ROOT/'configs/learning/isa_search.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L09')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/isa_search/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_hygienic_base_binding(self):
        with aggregate_budget(StepBudget(max_steps=32)):
            revision,expanded=compiled_world_macro(('mul',('var','arg'),('const',2.)),'i1')
            self.assertEqual(free_variables(expanded),{'caller_argument'})
            self.assertEqual(execute_base(expanded,{'caller_argument':3.,'arg':99.}),7.)
    def test_unknown_instruction_rejected(self):
        with self.assertRaises(ContractError):parse_world_expression(('python','anything'))
    def test_polynomial_is_explicit(self):
        values=[]
        for x,m in ((3.,2.),(-1.,3.),(0.,2.)):
            features=(1.,x,m,x*m);values.append(sum(c*f for c,f in zip((1.,0.,0.,1.),features)))
        self.assertEqual(values,[7.,-2.,1.])
    def test_no_description_gradient(self):
        source=(ROOT/'src/latent_comm/learning/isa_search/__init__.py').read_text()
        self.assertIn("'gradient_through_lowering':False",source)
        self.assertIn('output.exact.detach()',source)

if __name__=='__main__':unittest.main()
