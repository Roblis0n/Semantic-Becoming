import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h45_identifiability.types import *
from latent_comm.mechanisms.h45_identifiability.reference import *
from latent_comm.mechanisms.h45_identifiability.serialization import *
import latent_comm.mechanisms.h45_identifiability.adapter as adapter

class H45Contracts(unittest.TestCase):
    def state(self,prior=(.5,.5)):
        return IdentificationState(('plus','minus'),(QuerySpec('x0',('0',),((1.,),(1.,)),0.,True,True),QuerySpec('x1',('1','-1'),((1.,0.),(0.,1.)),0.,True,True)),prior,'1')
    def test_identify_and_no_prior(self):
        self.assertEqual(select_query(self.state()).query_id,'x1');self.assertAlmostEqual(select_query(self.state()).information_gain,math.log(2))
        r=select_query(self.state(None));self.assertEqual(r.query_id,'x1');self.assertIsNone(r.information_gain)
    def test_no_allowed_information(self):
        s=replace(self.state(),queries=(self.state().queries[0],));self.assertEqual(select_query(s).status,'NonIdentifiable')
        s=replace(self.state(),queries=tuple(replace(q,local_only=False) for q in self.state().queries));self.assertEqual(select_query(s).status,'NoAllowedQuery')
    def test_noise_and_model_mismatch(self):
        q=QuerySpec('noisy',('yes','no'),((.9,.1),(.2,.8)),0.,True,True);s=replace(self.state(),queries=(q,));r=update_posterior(s,'noisy','yes');self.assertAlmostEqual(r.posterior[0],.9/1.1)
        self.assertEqual(update_posterior(s,'noisy','unknown').status,'model_mismatch_unknown')
    def test_migration_and_unknown(self):
        s=migrate_hypotheses(self.state(),'2',(1,0));self.assertEqual(update_posterior(s,'x1','1').posterior,(0.,1.))
        q=QuerySpec('unknown',('yes',),None,0.,True,True);self.assertEqual(select_query(replace(s,queries=(q,))).status,'UnknownLikelihood')
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_information_gain(None,None,None,None)
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
