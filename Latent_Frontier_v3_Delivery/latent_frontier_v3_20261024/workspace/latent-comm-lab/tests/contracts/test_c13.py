import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c13 import *
from latent_comm.mechanisms.h37_gradient_transport.types import BehaviorAnchorSet

def fixture():
 v=VersionSet(state='s1',ontology='o1',isa='i1',frame='f1',task='t1',evidence='e1');anchors=BehaviorAnchorSet(('a','b'),'t1')
 source=Linearization(((1.,0.),(0.,1.)),anchors,('adapter.x','adapter.y'),'a1');target=Linearization(((1.,),(0.,)),anchors,('adapter.z',),'b1')
 a=ConsolidatedAdapter('source','a1',None,'finite-metadata-only',frozenset({'trace'}),frozenset({'seen'}),frozenset({'teacher'}),frozenset(source.parameter_names),'family','base-source',v,origin='finite_affine_compilation')
 b=replace(a,adapter_id='target',version='b1',writable_groups=frozenset(target.parameter_names),base_revision='base-target')
 trace=TeacherTrace('trace','seen','public-example',('affine',),frozenset({'teacher'}),'family','base-source',3,v)
 return LearningProtocolInput(source,target,(1.,1.),((2.,0.),(0.,3.)),a,b,(trace,),frozenset({'unseen'}),(('adapter.z',(0.,)),),SupportBatch((),(),'support'),QueryBatch((),(),'query'),2.,0.,0,v)
class C13Tests(unittest.TestCase):
 def test_unreachable_is_preserved(self):
  r=run_reference(fixture());u=r.value.rule.projection.update
  self.assertEqual(u.delta,(1.,));self.assertEqual(u.unreachable_residual,(0.,-1.));self.assertEqual(u.rank,1);self.assertEqual(r.value.rule.realized_residual,(0.,-1.));self.assertEqual(r.value.research_state,'NOT_RUN');self.assertEqual(len(r.audit),5)
 def test_basis_covariance(self):
  q=fixture();a=run_reference(q).value;b=run_reference(replace(q,source_basis=((1.,0.),(0.,1.)))).value
  self.assertEqual(a.rule.projection.update.behavior_direction,b.rule.projection.update.behavior_direction)
 def test_stale_parameter(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,target=replace(q.target,parameter_version='old')))
 def test_token_coordinates_not_anchors(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,target=replace(q.target,anchors=BehaviorAnchorSet(('token0','token1'),'t1'))))
 def test_support_query_leak(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,query=replace(q.query,partition_id='support')))
 def test_unseen_trace_not_training(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),unseen_instance_ids=frozenset({'seen'})))
 def test_singular_source_basis(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),source_basis=((0.,0.),(0.,1.))))
if __name__=='__main__':unittest.main()
