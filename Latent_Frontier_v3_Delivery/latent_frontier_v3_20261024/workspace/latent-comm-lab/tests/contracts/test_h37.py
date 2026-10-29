import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h37_gradient_transport.types import *
from latent_comm.mechanisms.h37_gradient_transport.reference import *
from latent_comm.mechanisms.h37_gradient_transport.serialization import *
import latent_comm.mechanisms.h37_gradient_transport.adapter as adapter

class H37Contracts(unittest.TestCase):
    def lin(self,j,names=None):
        return Linearization(tuple(tuple(r) for r in j),BehaviorAnchorSet(tuple(f'behavior:{i}' for i in range(len(j))),'1'),names or tuple(f'adapter.{i}' for i in range(len(j[0]))),'1')
    def test_scalar_and_ridge(self):
        a=self.lin(((2.,),));b=self.lin(((4.,),));u=transport_direction(a,b,(.5,));self.assertAlmostEqual(u.delta[0],.25)
        r=transport_direction(a,b,(.5,),ridge=1);self.assertAlmostEqual(r.delta[0],4/17);self.assertNotEqual(r.projection_residual,(0.,));self.assertAlmostEqual(norm(r.unreachable_residual),0.)
    def test_rank_and_unreachable(self):
        a=self.lin(((1.,0.),(0.,1.)));b=self.lin(((1.,1.),(0.,0.)));u=transport_direction(a,b,(1.,2.))
        self.assertEqual(u.rank,1);self.assertFalse(u.unique);self.assertTrue(u.minimum_norm);self.assertAlmostEqual(u.delta[0],.5);self.assertAlmostEqual(u.delta[1],.5);self.assertAlmostEqual(u.unreachable_residual[1],-2.)
    def test_anchor_scope_and_expiration(self):
        with self.assertRaises(ContractError):BehaviorAnchorSet(('token:1',),'1','token_logits')
        with self.assertRaises(ContractError):self.lin(((1.,),),('base.weight',))
        with self.assertRaises(ContractError):transport_direction(self.lin(((1.,),)),self.lin(((1.,),)),(1.,),current_target_version='2')
    def test_bounded_solver_and_migration(self):
        x,it,res,ok=cgls(lambda x:(x[0],2*x[1]),lambda y:(y[0],2*y[1]),(1.,1.),2,max_steps=1);self.assertFalse(ok)
        a=self.lin(((1.,),(2.,)));anchors=BehaviorAnchorSet(tuple(reversed(a.anchors.coordinate_ids)),'2');self.assertEqual(migrate_anchors(a,anchors,(1,0)).jacobian,((2.,),(1.,)))
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_transport(None,None,None,None,None,source_anchors=None,target_anchors=None,parameter_names=())
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
