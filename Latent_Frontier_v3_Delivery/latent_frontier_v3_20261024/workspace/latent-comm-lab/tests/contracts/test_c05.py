import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c05 import *
from latent_comm.mechanisms.h08_legacy.types import RelationNode,RelationEdge
from latent_comm.mechanisms.h17_legacy.types import PhysicalFrame

def fixture():
 v=VersionSet(frame='lf1',ontology='o1',world='w1',task='t1',evidence='e1');tv=replace(v,frame='lf2');sf=PhysicalFrame('cm','cm','right','public_position','lf1');tf=PhysicalFrame('m','m','right','public_position','lf2')
 sources=tuple(GroundedObject(n,(x,0.),((1.,0.),(0.,1.)),sf,0.,'observed',v) for n,x in (('a',0.),('b',100.)));targets=tuple(GroundedObject(n,(x,0.),((.0001,0.),(0.,.0001)),tf,0.,'observed',tv) for n,x in (('A',0.),('B',1.)))
 sg=RelationPacket((RelationNode('a','object',(0.,),'left'),RelationNode('b','object',(1.,),'right')),(RelationEdge('a','b','right','spatial'),),v);tg=RelationPacket((RelationNode('A','object',(0.,),'left'),RelationNode('B','object',(1.,),'right')),(RelationEdge('A','B','right','spatial'),),tv)
 sc=Chart('sc','s',(0.,0.),200.,((1.,0.),(0.,1.)),((1.,0.),(0.,1.)),frozenset({'move'}),'public-displacement',v);tc=replace(sc,chart_id='tc',model_revision='t',radius=2.,versions=tv)
 edge=Transition('sc','tc',((.01,0.),(0.,.01)),(0.,0.),'lf1','lf2',frozenset({'move'}),'none');physical=FrameTransform(sf,tf,((1.,0.),(0.,1.)),(0.,0.),.01)
 return RelationalGroundingInput(sg,tg,sources,targets,physical,sc,tc,edge,(20.,0.),((1.,0.),(0.,1.)),((1.,0.),(0.,1.)),'a','move',1.,v)
class C05Tests(unittest.TestCase):
 def test_physical_latent_maps_commute(self):
  r=run_reference(fixture());self.assertEqual(r.value.changed_object.position,(.2,0.));self.assertEqual(r.value.changed_object.status,'predicted');self.assertEqual(r.value.after_relations[0][2],('right',.8));self.assertEqual(len(r.audit),4)
 def test_units_cannot_be_substituted_by_latent_shape(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,latent_transition=replace(q.latent_transition,mapping=((1.,0.),(0.,1.)))))
 def test_ambiguous_mapping_is_not_action(self):
  q=fixture();sg=replace(q.source_relations,nodes=tuple(replace(n,anchor=None) for n in q.source_relations.nodes),edges=());tg=replace(q.target_relations,nodes=tuple(replace(n,anchor=None) for n in q.target_relations.nodes),edges=());r=run_reference(replace(q,source_relations=sg,target_relations=tg)).value;self.assertIsNone(r.changed_object);self.assertEqual(len(r.mapping_candidates),2)
 def test_physical_anchor_mismatch_rejected(self):
  q=fixture();objects=(replace(q.target_objects[0],position=(.1,0.)),q.target_objects[1])
  with self.assertRaises(ContractError):run_reference(replace(q,target_objects=objects))
 def test_stale_physical_world_rejected(self):
  q=fixture();old=lambda items:tuple(replace(o,versions=replace(o.versions,world='old-world')) for o in items)
  with self.assertRaises(ContractError):run_reference(replace(q,source_objects=old(q.source_objects),target_objects=old(q.target_objects)))
 def test_target_chart_invalidation(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,target_chart=replace(q.target_chart,invalidated=True)))
if __name__=='__main__':unittest.main()
