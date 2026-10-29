import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h32_perspective.types import *
from latent_comm.mechanisms.h32_perspective.reference import *
from latent_comm.mechanisms.h32_perspective.serialization import *
import latent_comm.mechanisms.h32_perspective.adapter as adapter

class H32Contracts(unittest.TestCase):
    def frame(self):return ObjectiveFrame(freeze_goal('minimize time and energy'),(2.,3.),(.5,.5),((1.,0.),),(4.,),'1')
    def test_unit_duality_and_counterexample(self):
        f=self.frame();v=change_view(f,((60.,0.),(0.,1.)),'2');self.assertAlmostEqual(v.dual_weights[0],.5/60);self.assertAlmostEqual(v.original_value,v.transformed_value)
        self.assertNotEqual(dot(f.weights,v.transformed_costs),v.original_value)
    def test_lost_preference(self):
        with self.assertRaises(ContractError):change_view(self.frame(),((1.,0.),),'2')
        v=change_view(self.frame(),((1.,0.),),'2',allow_loss=True);self.assertEqual(v.status,'InformationLoss');self.assertGreater(norm(v.preference_residual),0)
    def test_original_goal_and_constraints(self):
        v=change_view(self.frame(),eye(2),'2')
        with self.assertRaises(ContractError):assert_commit(v,freeze_goal('different goal'))
        f=replace(self.frame(),constraint_bounds=(1.,))
        with self.assertRaises(ContractError):assert_commit(change_view(f,eye(2),'2'),f.goal)
    def test_pareto_no_forced_ranking(self):self.assertEqual(pareto_front(((1.,3.),(3.,1.),(4.,4.))),(0,1))
    def test_goal_digest_and_gate(self):
        with self.assertRaises(ContractError):ImmutableGoal('changed','bad')
        with self.assertRaises(Exception):adapter.tensor_view(None,None,None)
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
