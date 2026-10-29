import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h28_bifurcation.types import *
from latent_comm.mechanisms.h28_bifurcation.reference import *
from latent_comm.mechanisms.h28_bifurcation.serialization import *
import latent_comm.mechanisms.h28_bifurcation.adapter as adapter

class H28Contracts(unittest.TestCase):
    def test_analytic_stability(self):
        self.assertEqual(stationary_points(-1)[0].continuous,'stable')
        self.assertEqual([r.continuous for r in stationary_points(1)],['unstable','stable','stable'])
        self.assertIn('nonhyperbolic',stationary_points(0)[0].continuous)
    def test_numerical_artifact_detected(self):
        r=stationary_points(1,2)[1];self.assertEqual(r.continuous,'stable');self.assertEqual(r.discrete,'unstable')
        with self.assertRaises(ContractError):trace_control(PhaseState(1,(1.,),'single','b','1'),(1.,),dt=2)
    def test_structure_event_and_cache_invalidation(self):
        s=PhaseState(-1,(.1,),'single','b','1');event=StructureTransition('1','2',((1.,),(-1.,)),'single','split',('old-cache',))
        r=trace_control(s,(-1.,1.),transitions=((0,event),));self.assertEqual(len(r.states[-1].z),2);self.assertEqual(r.transitions[0].invalidated_cache_keys,('old-cache',))
    def test_branch_bounds_and_schema(self):
        with self.assertRaises(ContractError):equilibrium_branches((1.,1.),StepBudget(max_branches=3))
        p={'schema_version':3,'potential_kind':'quartic_pitchfork','alpha_path':[-1,0,1],'initial_state':[.1],'structure':'s','branch_id':'b','version':'1','dt':.1,'steps_per_control':1}
        self.assertEqual(migrate_payload(dict(p,schema_version=2),2),p)
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_dynamics(None,None,None,dt=.1,steps_per_control=1)
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
