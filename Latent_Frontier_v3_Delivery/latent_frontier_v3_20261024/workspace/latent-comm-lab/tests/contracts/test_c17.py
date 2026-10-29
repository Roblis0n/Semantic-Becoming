import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c17 import *
from latent_comm.mechanisms.h03_legacy.types import BeliefBranch
from latent_comm.mechanisms.h46_negative_knowledge.types import DomainPredicate,NegativeWitness

def fixture():
 v=VersionSet(frame='f1',world='w1',ontology='o1',task='t1',evidence='e1');programs=tuple((i,QuadraticProgram(((float(i),),),(((0.,),),),(0.,))) for i in (0,1,2))
 belief=BeliefPacket(tuple(BeliefBranch(str(i),(float(i),),0.,'slopes',frozenset(),'o1') for i,_ in programs),'sequence_mixture',v)
 witness=NegativeWitness('program_exhaustive',DomainPredicate('ge',1),(0,1,2),None,'complete');capsule=ExclusionCapsule('nonzero',DomainPredicate('eq',0),('positive_slope',),witness,1.,'hard',(),('positive_slope',),'w1')
 return IdentificationInput(programs,belief,(capsule,),('positive_slope',),(),(QueryCondition('at1',1.,True,True,0.),QueryCondition('forbidden',2.,False,False,0.)),programs[1][1],0.,2.,'query-evidence',v)
class C17Tests(unittest.TestCase):
 def test_conditional_query_refines_real_finite_response(self):
  r=run_reference(fixture());self.assertEqual(r.value.feasible,(1,2));self.assertEqual(r.value.response.observation,1.);self.assertEqual(r.value.posterior.posterior,(1.,0.));self.assertTrue(r.value.unknown_hypothesis_possible);self.assertEqual(len(r.audit),5)
 def test_permissions_before_query(self):
  q=fixture();q=replace(q,queries=tuple(replace(x,allowed=False) for x in q.queries));r=run_reference(q).value;self.assertEqual(r.status,'NoAllowedQuery');self.assertIsNone(r.response)
 def test_same_response_nonidentifiable(self):
  q=fixture();r=run_reference(replace(q,queries=(QueryCondition('at0',0.,True,True,0.),))).value;self.assertEqual(r.status,'NonIdentifiable');self.assertIsNone(r.response)
 def test_retracted_assumption_restores_candidates(self):
  r=run_reference(replace(fixture(),retracted=('positive_slope',))).value;self.assertEqual(r.feasible,(0,1,2));self.assertTrue(r.inactive_exclusions)
 def test_nonlinear_response_does_not_fabricate_likelihood(self):
  q=fixture();programs=tuple((i,replace(p,quadratic=(((1.,),),))) for i,p in q.hypotheses);r=run_reference(replace(q,hypotheses=programs)).value;self.assertEqual(r.status,'UnknownLikelihood');self.assertIsNone(r.response)
 def test_repeated_evidence_not_squared(self):
  q=fixture();first=run_reference(q).value;second=run_reference(replace(q,belief=first.belief)).value;self.assertEqual(second.status,'RepeatedEvidenceNotReapplied');self.assertEqual(second.belief,first.belief)
 def test_sequential_retraction_restores_conditional_mass(self):
  from latent_comm.mechanisms.h03_legacy.reference import normalized_logs
  import math
  q=fixture();programs=((0,q.hypotheses[1][1]),)+q.hypotheses[1:];q=replace(q,hypotheses=programs)
  first=run_reference(q).value;self.assertEqual(first.posterior.posterior,(1.,0.))
  second=run_reference(replace(q,belief=first.belief,retracted=('positive_slope',))).value
  self.assertEqual(second.feasible,(0,1,2));self.assertEqual(second.status,'RepeatedEvidenceNotReapplied')
  weights=tuple(math.exp(x) for x in normalized_logs(second.belief));self.assertEqual(weights,(.5,.5,0.))
  fresh=run_reference(replace(q,retracted=('positive_slope',))).value
  self.assertEqual(second.belief,fresh.belief)
 def test_outside_candidate_family_unknown(self):
  q=fixture();actual=QuadraticProgram(((3.,),),(((0.,),),),(0.,));r=run_reference(replace(q,actual_local_program=actual)).value;self.assertEqual(r.status,'model_mismatch_unknown');self.assertEqual(r.belief,q.belief)
if __name__=='__main__':unittest.main()
