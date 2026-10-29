import unittest,math
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c03 import *
from latent_comm.mechanisms.h03_legacy.types import BeliefBranch

def fixture(disjoint=False):
 v=VersionSet(state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1');root=BranchState('root',(),(('x',(0.,)),('y',(0.,))),(),frozenset(),(),'independent_slots',frozenset(),'o1','question','snapshot',v)
 belief=BeliefPacket((BeliefBranch('a',(1.,),0.,'domain',frozenset(),'o1'),BeliefBranch('b',(-1.,),0.,'domain',frozenset(),'o1')),'sequence_mixture',v)
 nodes=tuple(PortfolioNode(n,(('x',x),),(),None,None,(),'answer','question','world','declared_finite_hypothesis',frozenset(),v) for n,x in (('a',1.),('b',-1.)))
 return BeliefTreeInput(belief,root,nodes,(('a',(('x',(1.,)),)),('b',((('y' if disjoint else 'x'),(-1.,)),))),(.8,.2),'e:new',((math.log(.9),math.log(.9)),(math.log(.1),math.log(.1))),v)
class C03Tests(unittest.TestCase):
 def test_conflict_not_vector_average(self):
  r=run_reference(fixture());self.assertIsNone(r.value.shared_state);self.assertEqual(len(r.value.preserved_branches),2);self.assertEqual(len(r.value.belief.branches),2);self.assertAlmostEqual(r.value.sequence_mixture_nll,-math.log(.8*.81+.2*.01));self.assertEqual(len(r.audit),5)
 def test_disjoint_computation_merges_not_beliefs(self):
  q=fixture(True);r=run_reference(q).value;self.assertEqual(dict(r.shared_state),{'x':(1.,),'y':(-1.,)});self.assertEqual(len(r.belief.branches),2);self.assertEqual(dict(q.root.base)['x'],(0.,))
 def test_all_contradicted_preserves_unknown(self):
  q=fixture();r=run_reference(replace(q,likelihood=(0.,0.))).value;self.assertEqual(r.belief,q.belief);self.assertTrue(r.unknown_alternatives_possible);self.assertIn('EvidenceConflict',r.status)
 def test_repeat_evidence_does_not_reweight(self):
  q=fixture();first=run_reference(q).value;second=run_reference(replace(q,belief=first.belief)).value;self.assertEqual(second.belief,first.belief)
 def test_synthetic_worlds_not_merged(self):
  q=fixture(True);q=replace(q,semantic_nodes=(q.semantic_nodes[0],replace(q.semantic_nodes[1],synthetic=True)));self.assertIsNone(run_reference(q).value.shared_state)
if __name__=='__main__':unittest.main()
