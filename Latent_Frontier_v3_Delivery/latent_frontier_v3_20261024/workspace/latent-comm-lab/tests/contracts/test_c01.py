import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,Scope,ContractError
from latent_comm.compositions.c01 import *
from latent_comm.mechanisms.h22_legacy.types import StateCell

def fixture():
 v=VersionSet(state='s1',frame='f1',ontology='o1',isa='i1',task='t1',evidence='e1');targetv=replace(v,frame='f2');actors=frozenset({'source','receiver'})
 cell=StateCell('cell','state',(1.,2.),'f1',actors,actors,'both',0);partition=PartitionState((('both',actors),),(cell,),frozenset({'old-cache'}),'s1',v)
 source=Chart('s','model-s',(0.,0.),10.,((1.,0.),(0.,1.)),((1.,0.),(0.,1.)),frozenset({'sum'}),'sum',v);target=Chart('t','model-t',(0.,),10.,((1.,),),((1.,),),frozenset({'sum'}),'sum',targetv)
 edge=Transition('s','t',((1.,1.),),(0.,),'f1','f2',frozenset({'sum'}),'task-relative projection loses difference')
 op=OperatorPacket(((1.,),),((1.,),),(0.,),1.,'identity','state','state',targetv,Scope('operator',frozenset({'receiver'}),frozenset({'Z'})))
 return TemporaryComputationInput(partition,'cell','source','receiver',source,target,edge,'sum',op,((1.,),),v)
class C01Tests(unittest.TestCase):
 def test_heterogeneous_typed_computation(self):
  q=fixture();r=run_reference(q);self.assertEqual(r.value.observations,(6.,));self.assertEqual(r.value.partition_transition.after.cells[0].value,(3.,));self.assertEqual(q.partition.cells[0].value,(1.,2.));self.assertEqual(len(r.audit),4)
 def test_no_access_expansion(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),target_actor='intruder'))
 def test_wrong_operator_frame(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,operator=replace(q.operator,versions=q.versions)))
 def test_chart_coverage(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,target_chart=replace(q.target_chart,radius=.1)))
 def test_target_ontology_cannot_change_with_frame(self):
  q=fixture();other=replace(q.target_chart.versions,ontology='other-ontology')
  with self.assertRaises(ContractError):run_reference(replace(q,target_chart=replace(q.target_chart,versions=other),operator=replace(q.operator,versions=other)))
 def test_no_false_inverse(self):
  q=fixture()
  with self.assertRaises(ContractError):replace(q.chart_edge,information_loss='none')
if __name__=='__main__':unittest.main()
