import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c07 import *
def fixture():
 v=VersionSet(state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1');capsule=PersistentCapsule('capsule','doc','d1',None,(('a',2.),('b',4.)),frozenset({'mean','lookup'}),frozenset({'source'}),(('source','v1'),),10,v)
 sender=ProtocolMember('sender','r1','tok1',((2.,),),((1.,),),frozenset({'scalar_query'}),('scalar',),True,v);receiver=ProtocolMember('receiver','r2','tok2',((1.,),),((1.,),),frozenset({'scalar_query'}),('scalar',),True,v)
 grant=CapabilityGrant('cap','reader','session',frozenset({'state:x'}),frozenset({'state:x'}),frozenset({'scalar'}),10,frozenset({'source'}),frozenset(),frozenset(),frozenset(),frozenset({'state:x'}),'fixed-goal',v);cell=ScopedCell('state:x','scalar',(0.,),'session','s1')
 return ScopedMemoryInput(capsule,('mean',''),(('source','v1'),),sender,receiver,(grant,),'cap','reader','session',cell,'s2',frozenset(),frozenset(),0,v)
class C07Tests(unittest.TestCase):
 def test_calibration_residual_scoped_write(self):
  r=run_reference(fixture());self.assertEqual(r.status,'Complete');self.assertEqual(r.value.cell.value,(3.,));self.assertEqual(r.value.repair_report.residual,(3.,));self.assertEqual(r.value.audit.written_slots,('state:x',))
 def test_unknown_retained_detail_no_write(self):
  r=run_reference(replace(fixture(),query=('lookup','missing'))).value;self.assertIsNone(r.audit);self.assertEqual(r.cell.value,(0.,));self.assertEqual(r.status,'SourceLookupRequiredNoWrite')
 def test_source_retraction_future_not_erasure(self):
  r=run_reference(replace(fixture(),withdraw_after=frozenset({'source'}))).value;self.assertEqual(r.revoked_capabilities,('cap',));self.assertEqual(r.invalidated_capsules,(('doc','d1'),));self.assertEqual(r.cell.value,(3.,))
 def test_forged_capability_and_withdrawn_source(self):
  for q in (replace(fixture(),capability_id='forged'),replace(fixture(),withdrawn_before=frozenset({'source'}))):
   with self.assertRaises(ContractError):run_reference(q)
 def test_new_model_is_not_unseen_pair(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,receiver=replace(q.receiver,interface_trained=False)))
 def test_versioned_capsule_with_explicit_lineage(self):
  q=fixture();parent=replace(q.capsule,version='d0');q=replace(q,capsule=replace(q.capsule,parent_version='d0'),capsule_lineage=(parent,));r=run_reference(q).value;self.assertEqual(r.cell.value,(3.,))
 def test_missing_lineage_rejected_before_apply(self):
  q=fixture();q=replace(q,capsule=replace(q.capsule,parent_version='d0'))
  with self.assertRaises(ContractError):scope_check(q)
 def test_stale_capsule_dependency(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),current_dependencies=(('source','old'),)))
if __name__=='__main__':unittest.main()
