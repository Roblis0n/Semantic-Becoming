import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h39_transactions.types import *
from latent_comm.mechanisms.h39_transactions.reference import *
from latent_comm.mechanisms.h39_transactions.serialization import *
import latent_comm.mechanisms.h39_transactions.adapter as adapter

class H39Contracts(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp=tempfile.TemporaryDirectory();self.store=VersionedStore(self.tmp.name)
        self.store.commit(CognitiveTransaction('initial',(('state:x',-1),),(VersionedCell('state:x','scalar',0,'0'),)))
    def tearDown(self):self.tmp.cleanup()
    def tx(self,name,value=1):return CognitiveTransaction(name,(('state:x',0),),(VersionedCell('state:x','scalar',1,str(value)),))
    def test_commit_conflict_and_compensation(self):
        self.store.commit(self.tx('a'))
        with self.assertRaises(ContractError):self.store.commit(self.tx('b',2))
        self.store.rollback('a','undo-a');self.assertEqual(self.store.snapshot()[0].payload_json,'0');self.assertEqual(self.store.snapshot()[0].version,2)
    def test_read_dependency_even_disjoint_write(self):
        self.store.commit(self.tx('a'))
        t=CognitiveTransaction('other',(('state:x',0),('state:y',-1)),(VersionedCell('state:y','scalar',0,'2'),))
        with self.assertRaises(ContractError):self.store.commit(t)
    def test_crash_before_publish_aborts(self):
        with self.assertRaises(ContractError):self.store.commit(self.tx('crash'),crash_at='after_prepare')
        self.assertEqual(self.store.recover(),(('crash','abort'),));self.assertEqual(self.store.snapshot()[0].version,0)
    def test_crash_after_publish_rolls_forward(self):
        with self.assertRaises(ContractError):self.store.commit(self.tx('crash'),crash_at='after_publish')
        self.assertEqual(VersionedStore(self.tmp.name).recover(),(('crash','commit'),));self.assertEqual(self.store.snapshot()[0].version,1)
    def test_external_and_gate(self):
        with self.assertRaises(ContractError):CognitiveTransaction('email',(),(),external_effects=True)
        with self.assertRaises(Exception):adapter.tensor_commit_policy(None,None,None,None)
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
