import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h33_reciprocal.types import *
from latent_comm.mechanisms.h33_reciprocal.reference import *
from latent_comm.mechanisms.h33_reciprocal.serialization import *
import latent_comm.mechanisms.h33_reciprocal.adapter as adapter

class H33Contracts(unittest.TestCase):
    def packet(self,q=0.):return DynamicsPacket(((q,0.),(0.,q)),((0.,-1.),(1.,0.)),(1.,0.),'1',.1,8,(0,9))
    def test_midpoint_norm_and_euler_artifact(self):
        r=integrate(self.packet());self.assertTrue(all(abs(x-1)<1e-10 for x in r.squared_norms));self.assertGreater(euler_artifact(self.packet().skew_coupling,(1.,0.),.1),0.)
        self.assertEqual(r.termination,'bounded_steps_complete');self.assertNotEqual(r.descriptor,'fixed')
    def test_dissipative_condition(self):
        r=integrate(self.packet(1.));self.assertTrue(all(b<a for a,b in zip(r.quadratic_energy,r.quadratic_energy[1:])))
    def test_stale_coupling(self):
        with self.assertRaises(ContractError):integrate(self.packet(),updates=((1,('old','2',((0.,-2.),(2.,0.)))),))
    def test_migration_and_invalid_skew(self):
        p=migrate_state(self.packet(),((0.,1.),(1.,0.)),'2');self.assertAlmostEqual(integrate(p).squared_norms[-1],1)
        with self.assertRaises(ContractError):replace(self.packet(),skew_coupling=((0.,1.),(1.,0.)))
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_integrate(None,None,None,dt=.1,steps=1,readout_weights=None)
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
