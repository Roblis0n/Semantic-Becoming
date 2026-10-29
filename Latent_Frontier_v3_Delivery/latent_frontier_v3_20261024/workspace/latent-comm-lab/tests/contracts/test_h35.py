import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h35_renormalization.types import *
from latent_comm.mechanisms.h35_renormalization.reference import *
from latent_comm.mechanisms.h35_renormalization.serialization import *
import latent_comm.mechanisms.h35_renormalization.adapter as adapter

class H35Contracts(unittest.TestCase):
    def packet(self,nonclosed=False):
        f=((1.,1.),(0.,1.)) if nonclosed else eye(2);bias=(0.,0.) if nonclosed else (1.,1.);c=((1.,1.),);g,b=fit_linear_closure(c,f,bias)
        return ScalePacket(c,((.5,),(.5,)),f,bias,g,b,('a','b'),('sum',),'micro:1','macro:1')
    def test_sum_closes_and_steps_by_two(self):
        p=self.packet();self.assertTrue(closure_report(p).closed);self.assertEqual(step_scale(p,coarsen(p,(1.,2.),False)).coarse,(5.,))
    def test_nonclosure_witness_and_memory_repair(self):
        p=self.packet(True);self.assertFalse(closure_report(p).closed);self.assertTrue(closure_counterexamples(p,((0.,2.),(1.,1.))))
        s=coarsen(p,(0.,2.));self.assertEqual(refine(p,step_scale(p,s)),(2.,2.))
        with self.assertRaises(ContractError):step_scale(p,coarsen(p,(0.,2.),False))
    def test_no_detail_invention(self):
        p=self.packet()
        with self.assertRaises(ContractError):refine(p,coarsen(p,(1.,3.),False))
    def test_migration_and_gate(self):
        p=self.packet();q=replace(p,target_version='macro:2');s=migrate_scale(p,q,coarsen(p,(1.,3.)));self.assertEqual(refine(q,s),(1.,3.))
        with self.assertRaises(Exception):adapter.tensor_multiscale(None,None,None,None,None,None,None)
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
