import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c02 import *
from latent_comm.mechanisms.h02_legacy.reference import build_capsule

def fixture(nonlinear=False):
 v=VersionSet(state='s1',frame='f1',ontology='o1',world='w1',task='t1',evidence='e1');p=QuadraticProgram(((1.,),),(((2. if nonlinear else 0.,),),),(0.,));c=build_capsule(p,(0.,),directions=((1.,),),step=.01,radius=2.,variables=('x',),conditions=('public polynomial',),versions=v)
 return SharedResponseInput((ResponseSource('one',p,c,(1.,),1.,'scalar',frozenset({'e1'})),),(0.,),frozenset({'one'}),.1,8,.1,v)
class C02Tests(unittest.TestCase):
 def test_linear_response_field_and_repair(self):
  r=run_reference(fixture());self.assertGreater(r.value.state[0],0.);self.assertEqual(r.value.status,'FiniteApproximateFieldUpdateNotTruth');self.assertEqual(r.value.reports[0].kind,'none');self.assertEqual(len(r.audit),4)
 def test_nonlinear_residual_requires_resolve(self):
  r=run_reference(fixture(True)).value;self.assertEqual(r.status,'ResponseRefreshedFieldNeedsResolve');self.assertEqual(r.reports[0].kind,'numeric');self.assertEqual(r.source_responses[0].capsule.anchor,r.state);self.assertAlmostEqual(r.corrected_messages[0].state[0],r.state[0]+r.state[0]**2)
 def test_unauthorized_refresh_not_skipped(self):
  q=fixture();q=replace(q,state=(3.,),refresh_authorized=frozenset());r=run_reference(q).value;self.assertEqual(r.status,'AwaitingAuthorizedRefresh');self.assertEqual(r.pending_sources,('one',));self.assertIsNone(r.field_result)
 def test_stale_response_refreshes_exact_context(self):
  q=fixture();old=replace(q.sources[0],capsule=replace(q.sources[0].capsule,versions=replace(q.versions,world='old')));r=run_reference(replace(q,sources=(old,))).value;self.assertEqual(r.source_responses[0].capsule.versions.world,'w1')
 def test_unstable_solver_rejected(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),step_size=10.))
if __name__=='__main__':unittest.main()
