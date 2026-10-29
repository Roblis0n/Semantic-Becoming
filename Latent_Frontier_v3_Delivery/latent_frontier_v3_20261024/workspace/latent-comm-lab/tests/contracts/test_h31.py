import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h31_grafting.types import *
from latent_comm.mechanisms.h31_grafting.reference import *
from latent_comm.mechanisms.h31_grafting.serialization import *
import latent_comm.mechanisms.h31_grafting.adapter as adapter

class H31Contracts(unittest.TestCase):
    def setUp(self):
        self.world=TargetSCM((CausalModule('x','u',(),(),(),3.,()),CausalModule('y','u',('x',),('u',),(1.,),0.,()),CausalModule('z','u',('y',),('u',),(1.,),1.,())),('noise:shared',),'1')
        self.source=CausalModule('sy','u',('sx',),('u',),(2.,),0.,())
        self.binding=(BoundaryBinding('sx','x','u','u'),)
    def test_graft_intervention_descendants_rollback(self):
        c=graft(self.source,self.world,'y',self.binding,'2');self.assertEqual(dict(evaluate_scm(c.after,{'noise:shared':0}))['z'],7.)
        self.assertEqual(dict(evaluate_scm(c.after,{'noise:shared':0},(('x',4.),)))['z'],9.)
        self.assertEqual(c.affected_descendants,('y','z'));self.assertEqual(rollback(c,c.after),self.world)
    def test_units_and_cycles_rejected(self):
        with self.assertRaises(ContractError):graft(self.source,self.world,'y',(BoundaryBinding('sx','x','u','seconds'),),'2')
        with self.assertRaises(ContractError):graft(self.source,self.world,'y',(BoundaryBinding('sx','z','u','u'),),'2')
    def test_shared_noise_identity(self):
        source=replace(self.source,coefficients=(0.,),noise_terms=(('noise:shared',1.),));c=graft(source,self.world,'y',self.binding,'2')
        v=dict(evaluate_scm(c.after,{'noise:shared':2.}));self.assertEqual(v['z']-v['y'],1.)
        with self.assertRaises(ContractError):graft(replace(source,noise_terms=(('noise:copy',1.),)),self.world,'y',self.binding,'2')
    def test_recompute_only_affected(self):
        prior=snapshot_scm(self.world,{'noise:shared':0});c=graft(self.source,self.world,'y',self.binding,'2')
        result=evaluate_scm(c.after,{'noise:shared':0},prior_values=prior,budget=StepBudget(max_steps=2));self.assertEqual(dict(result)['z'],7.)
    def test_reuse_detects_changed_noise_and_removed_intervention(self):
        x=replace(self.world.modules[0],noise_terms=(('noise:shared',1.),))
        world=replace(self.world,modules=(x,)+self.world.modules[1:])
        prior=snapshot_scm(world,{'noise:shared':0})
        self.assertEqual(evaluate_scm(world,{'noise:shared':1},prior_values=prior),evaluate_scm(world,{'noise:shared':1}))
        prior=snapshot_scm(world,{'noise:shared':0},(('x',9.),))
        self.assertEqual(evaluate_scm(world,{'noise:shared':0},prior_values=prior),evaluate_scm(world,{'noise:shared':0}))
    def test_bare_values_cannot_be_reused_without_provenance(self):
        values=evaluate_scm(self.world,{'noise:shared':0})
        with self.assertRaises(ContractError):evaluate_scm(self.world,{'noise:shared':0},prior_values=values)
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_scm(None,None,None,batch_size=1)
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
