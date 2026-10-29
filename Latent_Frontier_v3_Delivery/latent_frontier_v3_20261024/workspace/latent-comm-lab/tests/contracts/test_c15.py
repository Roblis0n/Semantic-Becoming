import unittest
from dataclasses import replace
from latent_comm.core import Visibility,RoleView,VersionSet,ContractError
from latent_comm.compositions.c15 import *

def fixture():
 v=VersionSet(state='d1',ontology='o1',isa='i1',frame='f1',world='w1',task='t1',evidence='e1')
 view=RoleView(Visibility.RECEIVER, {'terminal_states':['W'],'terminal_source':'public_goal'},{},v)
 fast=DynamicsPacket(((0.,0.),(0.,0.)),((0.,-1.),(1.,0.)),(1.,0.),'d1',2.,1,(0,2))
 slow=replace(fast,step_size=.5)
 return MultirateTrajectoryInput(view,(('E',(1.,0.)),('N',(0.,1.)),('W',(-1.,0.)),('S',(0.,-1.))),'E',(('fast',fast),('slow',slow)),2,.6,(('fast',1),('slow',2)),'d1',8,v)
class C15Tests(unittest.TestCase):
 def test_public_boundary_actual_midpoint_continuation(self):
  r=run_reference(fixture());self.assertEqual(r.value.path,('E','N','W'));self.assertEqual(r.value.states,((1.,0.),(0.,1.),(-1.,0.)));self.assertEqual(r.value.status,'Completed');self.assertEqual(r.value.signed_area,1.);self.assertEqual(r.value.endpoint_residual,0.);self.assertEqual(len(r.audit),5)
 def test_stale_receiver_does_not_advance(self):
  r=run_reference(replace(fixture(),current_receiver_version='old')).value;self.assertEqual(r.status,'StaleOrUnresolvedContinuation');self.assertEqual(len(r.states),1)
 def test_hidden_terminal_rejected(self):
  q=fixture();view=RoleView(Visibility.RECEIVER, {'terminal_states':['W'],'terminal_source':'hidden_label'},{},q.versions)
  with self.assertRaises(ContractError):run_reference(replace(q,public_boundary=view))
 def test_numerical_non_psd_rejected(self):
  q=fixture();bad=replace(q.dynamics[0][1],dissipation=((-1.,0.),(0.,0.)))
  with self.assertRaises(ContractError):run_reference(replace(q,dynamics=(('fast',bad),('slow',q.dynamics[1][1]))))
 def test_publicly_infeasible_not_future_answer(self):
  q=fixture();view=RoleView(Visibility.RECEIVER, {'terminal_states':['S'],'terminal_source':'public_goal'},{},q.versions)
  r=run_reference(replace(q,public_boundary=view)).value;self.assertEqual(r.status,'BoundaryInfeasible');self.assertFalse(r.states)
 def test_schedule_not_causal_path_index(self):
  q=replace(fixture(),schedule_delays=(('fast',3),('slow',2)));r=run_reference(q).value
  self.assertEqual([d.physical_step for d in r.schedule],[3,6]);self.assertEqual([d.source_path[1] for d in r.schedule],[1,2])
if __name__=='__main__':unittest.main()
