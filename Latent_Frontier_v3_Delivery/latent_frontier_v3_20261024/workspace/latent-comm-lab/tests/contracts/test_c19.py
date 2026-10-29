import unittest
from dataclasses import replace
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c19 import *
from latent_comm.mechanisms.h32_perspective.reference import freeze_goal
from latent_comm.mechanisms.h12_legacy.reference import build_capsule

def fixture():
 v=VersionSet(frame='f1',ontology='o1',world='w1',task='t1',evidence='e1');goal=freeze_goal('Preserve the original mean cost and keep each cost under ten')
 objective=ObjectiveFrame(goal,(1.,3.),(.5,.5),((1.,0.),(0.,1.)),(10.,10.),'objective1');c=((.5,.5),)
 chart=Chart('mean-chart','finite-model',(0.,0.),10.,c,((1.,),(1.,)),frozenset({'mean'}),'public:mean',v)
 scale=ScalePacket(c,((1.,),(1.,)),((1.,1.),(0.,1.)),(0.,0.),((1.,),),(0.,),('x','y'),('mean',),'f1','coarse1')
 domain=StateDomain(('a','b'),(0,2),'domain1');query=FiniteQuery('parity','parity',0,'q1');new=FiniteQuery('gt1','greater_than',1,'q1')
 capsule=build_capsule({'domain:a':0.,'domain:b':2.,'coordinate:x':1.,'coordinate:y':3.},capsule_id='detail',document_id='doc',version='c1',query_family=('lookup',),evidence=('source1',),dependencies={'source':'rev1'},expires_step=5,versions=v)
 return GoalScaleInput(objective,goal,chart,'finite-model','mean',c,scale,(1.,3.),domain,(query,),(new,),capsule,(('source','rev1'),),frozenset(),False,0,v)
class C19Tests(unittest.TestCase):
 def test_nonclosed_macro_recovers_real_detail(self):
  r=run_reference(fixture());self.assertEqual(r.value.final_state,(4.,3.));self.assertEqual(r.value.original_value,3.5);self.assertAlmostEqual(r.value.transformed_value,3.5);self.assertEqual(r.value.status,'OriginalGoalRechecked');self.assertTrue(r.value.refinement.witnesses);self.assertEqual(len(r.audit),6)
 def test_missing_source_does_not_invent_inverse(self):
  q=fixture();capsule=replace(q.source_capsule,observations=tuple((k,v) for k,v in q.source_capsule.observations if k!='coordinate:y'))
  r=run_reference(replace(q,source_capsule=capsule)).value;self.assertEqual(r.status,'NeedsAuthorizedSourceDetail');self.assertIsNone(r.final_state);self.assertTrue(r.obligations)
 def test_goal_cannot_change(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),current_goal=freeze_goal('optimize a different goal')))
 def test_original_hard_constraint_is_rechecked(self):
  q=fixture();q=replace(q,objective=replace(q.objective,constraint_bounds=(3.,4.)))
  with self.assertRaises(ContractError):run_reference(q)
 def test_retracted_source_blocks_refinement(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),withdrawn_sources=frozenset({'source1'})))
 def test_chart_does_not_extrapolate(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,chart=replace(q.chart,radius=.1)))
 def test_source_cannot_replace_old_distinctions(self):
  q=fixture();capsule=replace(q.source_capsule,observations=tuple((k,1. if k=='domain:b' else v) for k,v in q.source_capsule.observations))
  with self.assertRaises(ContractError):run_reference(replace(q,source_capsule=capsule))
if __name__=='__main__':unittest.main()
