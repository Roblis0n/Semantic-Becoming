import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h47_quotient.types import *
from latent_comm.mechanisms.h47_quotient.reference import *
from latent_comm.mechanisms.h47_quotient.serialization import *
import latent_comm.mechanisms.h47_quotient.adapter as adapter

class H47Contracts(unittest.TestCase):
    def test_empty_loss_source_contract(self):
        tree=ast.parse(Path(adapter.__file__).read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='train_quotient_step')
        backward=min(n.lineno for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='backward')
        skips=[n for n in ast.walk(function) if isinstance(n,ast.If) and any(isinstance(x,ast.Return) and "'skipped'" in ast.unparse(x) for x in n.body)]
        self.assertTrue(skips);self.assertLess(min(n.lineno for n in skips),backward)
        self.assertIn('LossValue',ast.unparse(function));self.assertIn('isfinite',ast.unparse(function))
    def domain(self):return StateDomain(('one','two','three','four'),(1,2,3,4),'d1')
    def test_equivalence_and_refinement(self):
        old=form_quotient(self.domain(),(FiniteQuery('parity','parity',0,'q1'),),'v1');self.assertEqual({c.members for c in old.classes},{('one','three'),('two','four')})
        refinement=refine_quotient(old,(FiniteQuery('greater','greater_than',2,'q1'),),'v2');self.assertEqual(len(refinement.quotient.classes),4);self.assertEqual(len(refinement.witnesses),2)
        for c in old.classes:self.assertEqual(len(migrate_class_reference(c.class_id,refinement,'v1')),2)
        self.assertTrue(all(w.response_a!=w.response_b for w in refinement.witnesses))
    def test_source_required_and_preserved(self):
        old=form_quotient(self.domain(),(FiniteQuery('parity','parity',0,'q1'),),'v1',retain_source=False)
        with self.assertRaises(ContractError):refine_quotient(old,(FiniteQuery('greater','greater_than',2,'q1'),),'v2')
        restored=refine_quotient(old,(FiniteQuery('greater','greater_than',2,'q1'),),'v2',source_domain=self.domain());self.assertEqual(len(restored.quotient.classes),4)
        with self.assertRaises(ContractError):refine_quotient(old,(FiniteQuery('parity','greater_than',2,'q1'),),'v2',source_domain=self.domain())
    def test_epsilon_chain_is_not_equivalence(self):
        result=approximate_clusters(((0.,),(.75,),(1.5,)),1.);self.assertFalse(result.threshold_relation_transitive);self.assertIsNotNone(result.nontransitive_witness);self.assertEqual(result.groups,((0,1),(2,)))
        connected=approximate_clusters(((0.,),(.75,),(1.5,)),1.,method='connected_components');self.assertEqual(connected.groups,((0,1,2),));self.assertIn('not_threshold_equivalence',connected.exactness)
    def test_empty_family_schema_migration_budget(self):
        self.assertEqual(len(form_quotient(self.domain(),(),'empty').classes),1)
        payload={'schema_version':3,'domain':{'state_ids':['one'],'values':[1],'version':'d1'},'queries':[],'quotient_version':'v1','retain_source':True,'tolerance_policy':'exact_finite','epsilon':0}
        self.assertEqual(decode_payload(encode_payload(payload)),payload);old=dict(payload,schema_version=2);self.assertEqual(migrate_payload(old,2),payload)
        with self.assertRaises(ContractError):form_quotient(self.domain(),(FiniteQuery('p','parity',0,'v'),),'v',budget=StepBudget(max_steps=2))
    def test_gate(self):
        with self.assertRaises(Exception):adapter.encode_task_relative(None,None,None,None,None)
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
