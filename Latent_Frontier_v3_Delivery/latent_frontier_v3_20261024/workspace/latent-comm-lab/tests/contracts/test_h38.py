import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h38_plasticity.types import *
from latent_comm.mechanisms.h38_plasticity.reference import *
from latent_comm.mechanisms.h38_plasticity.serialization import *
import latent_comm.mechanisms.h38_plasticity.adapter as adapter

class H38Contracts(unittest.TestCase):
    def program(self,estimator='exact_unroll'):
        return PlasticityProgram(RuleNode('scale',(RuleNode('clip',(RuleNode('read',slot='gradient'),),1.),),-.1),('adapter.weight',),1.,2,4,'1',estimator)
    def test_clipped_update_is_1_9(self):
        r=apply_rule(self.program(),(('adapter.weight',(2.,)),),(('adapter.weight',(4.,)),));self.assertEqual(dict(r.parameters)['adapter.weight'],(1.9,))
    def test_running_mean_and_preconditioner(self):
        node=RuleNode('running_mean',(RuleNode('precondition_diagonal',(RuleNode('read',slot='gradient'),RuleNode('read',slot='diagonal')),.001),),.5)
        p=replace(self.program(),ast=node);r=apply_rule(p,(('adapter.weight',(0.,)),),(('adapter.weight',(4.,)),),statistics=(('adapter.weight',(('diagonal',(4.,)),)),));self.assertTrue(r.memory)
    def test_scope_and_query_leak_rejected(self):
        with self.assertRaises(ContractError):replace(self.program(),writable_groups=('policy.permissions',))
        with self.assertRaises(ContractError):validate_rule(RuleNode('read',slot='query_labels'))
        with self.assertRaises(ContractError):validate_partitions(QueryBatch((),(),'q'),QueryBatch((),(),'q'))
        self.assertTrue(validate_partitions(SupportBatch((),(),'s'),QueryBatch((),(),'q')))
    def test_first_order_distinct_and_lifetime(self):
        self.assertNotEqual(self.program().estimator,self.program('first_order').estimator)
        with self.assertRaises(ContractError):apply_rule(self.program(),(('adapter.weight',(2.,)),),(('adapter.weight',(4.,)),),step=4)
    def test_migration_and_unsafe_ast(self):
        p=migrate_rule(self.program(),'2',{'adapter.weight':'reader.weight'});self.assertEqual(p.writable_groups,('reader.weight',))
        with self.assertRaises(ContractError):validate_rule(RuleNode('exec',slot='shell'))
    def test_outer_optimizer_owner_is_exact(self):
        from types import SimpleNamespace
        psi,base=object(),object()
        self.assertTrue(validate_optimizer_ownership(SimpleNamespace(param_groups=[{'params':[psi]}]),{'rule':psi}))
        for parameters in ([psi,base],[base],[],[psi,psi]):
            with self.assertRaises(ContractError):validate_optimizer_ownership(SimpleNamespace(param_groups=[{'params':parameters}]),{'rule':psi})
        source=Path(adapter.__file__).read_text()
        self.assertLess(source.index('validate_optimizer_ownership(optimizer,rule_parameters,initial_parameters)'),source.index('optimizer.zero_grad'))
    def test_outer_owner_alias_and_learned_scalar(self):
        from types import SimpleNamespace
        parameter=object()
        with self.assertRaises(ContractError):validate_optimizer_ownership(SimpleNamespace(param_groups=[{'params':[parameter]}]),{'psi':parameter},{'base.weight':parameter})
        node=RuleNode('running_mean',(RuleNode('read',slot='gradient'),),.5,parameter='beta')
        p=replace(self.program(),ast=node,max_update_norm=10.)
        a=apply_rule(p,(('adapter.weight',(0.,)),),(('adapter.weight',(2.,)),),rule_parameters=(('beta',.1),))
        b=apply_rule(p,(('adapter.weight',(0.,)),),(('adapter.weight',(2.,)),),rule_parameters=(('beta',.9),))
        self.assertAlmostEqual(dict(a.applied_updates)['adapter.weight'][0],1.8)
        self.assertAlmostEqual(dict(b.applied_updates)['adapter.weight'][0],.2)
        with self.assertRaises(ContractError):apply_rule(p,(('adapter.weight',(0.,)),),(('adapter.weight',(2.,)),),rule_parameters=(('beta',1.1),))
    def test_full_first_order_source_and_gate(self):
        source=Path(adapter.__file__).read_text();self.assertIn("create_graph=program.estimator=='exact_unroll'",source);self.assertIn('g.detach()',source)
        with self.assertRaises(Exception):adapter.meta_unroll(None,None,None,None,None,None,None)
    def test_neural_source_is_lazy_and_gated(self):
        tree=ast.parse(Path(adapter.__file__).read_text())
        self.assertFalse(any(isinstance(x,(ast.Import,ast.ImportFrom)) and any(a.name.startswith(('torch','transformers')) for a in x.names) for x in tree.body))
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                imports=[x for x in ast.walk(node) if isinstance(x,ast.Import) and any(a.name=='torch' for a in x.names)]
                if imports:
                    gates=[x for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require_research_action']
                    self.assertTrue(gates)
                    self.assertLess(min(x.lineno for x in gates),min(x.lineno for x in imports))

if __name__=='__main__':unittest.main()
