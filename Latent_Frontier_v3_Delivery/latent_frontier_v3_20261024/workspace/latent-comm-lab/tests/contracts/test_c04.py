import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c04 import *
from latent_comm.mechanisms.h22_legacy.types import StateCell

def fixture(cut=1):
 v=VersionSet(state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1');actors=frozenset({'source','target'});cell=StateCell('cell','scalar',(3.,),'f1',actors,actors,'source-partition',0);partition=PartitionState((('source-partition',actors),),(cell,),frozenset({'old-cache'}),'s1',v)
 program=(ProgramOperation('double','twice',('mul',('var','x'),('const',2.))),ProgramOperation('increment','result',('add',('var','twice'),('const',1.)),('double','public-ready')));contract=ResumeContract('finite-program','none','float64','named-values','exact_program')
 return AsyncResumeInput(program,(('x',3.),),cut,contract,contract,partition,'cell','source','target','s2','s2',frozenset({'public-ready'}),('e1',),3,v)
class C04Tests(unittest.TestCase):
 def test_suffix_no_replay_at_multiple_cuts(self):
  for cut in (0,1,2):
   r=run_reference(fixture(cut));self.assertEqual(r.status,'Complete');self.assertEqual(dict(r.value.packet.values)['result'],7.);self.assertEqual(r.value.packet.completed_operations,('double','increment'));self.assertEqual(r.value.status,'SuffixCompleted')
 def test_dependency_wait_is_preserved(self):
  r=run_reference(replace(fixture(),available_dependencies=frozenset())).value;self.assertEqual(r.status,'WaitingForDependencies');self.assertEqual(r.packet.program_counter,1)
 def test_stale_receiver_does_not_resume(self):
  r=run_reference(replace(fixture(),actual_receiver_version='old')).value;self.assertEqual(r.status,'StaleReceiverRejected');self.assertEqual(r.packet.program_counter,1)
 def test_contract_change_not_exact(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,target_contract=replace(q.target_contract,model_revision='different')))
 def test_no_authorization_expansion(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),target_actor='intruder'))
if __name__=='__main__':unittest.main()
