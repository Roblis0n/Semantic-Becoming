import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c10 import *
from latent_comm.mechanisms.h03_legacy.types import BeliefBranch
from latent_comm.mechanisms.h26_sheaf.types import LocalDomain,AffineRestriction,Anchor
from latent_comm.mechanisms.h27_ontology.types import ConceptDefinition
from latent_comm.mechanisms.h36_disagreement.types import RuleProgram

def fixture():
    v=VersionSet(state='s1',frame='f1',ontology='o1',task='t1',evidence='e1')
    belief=BeliefPacket((BeliefBranch('a',(0.,),0.,'local-a',frozenset({'e:1'}),'o1'),BeliefBranch('b',(1.,),0.,'local-b',frozenset({'e:2'}),'o1')),'sequence_mixture',v)
    edges=(AffineRestriction('xy','x','y',((1.,),),((1.,),),(0.,),('e:1',)),AffineRestriction('yz','y','z',((1.,),),((1.,),),(0.,),('e:2',)),AffineRestriction('zx','z','x',((1.,),),((1.,),),(1.,),('e:3',)))
    sheaf=SheafPacket(tuple(LocalDomain(n,1) for n in 'xyz'),edges,(Anchor('x',0,0.),),'f1')
    old=Predicate('eq','authorized',True);new=Predicate('eq','expired',True)
    ontology=OntologySnapshot('o1',(ConceptDefinition('old',old,(),('e:public',),('authorized',)),),(('reader','old'),))
    return DisagreementInput(belief,sheaf,ScopedClaim('all-even',RuleProgram('divisible',2),(2,3),'claim1'),ontology,((2,{'authorized':True,'expired':False}),(3,{'authorized':True,'expired':True})),(old,new),'o2')

class C10Tests(unittest.TestCase):
    def test_real_object_flow_preserves_disagreement(self):
        q=fixture();r=run_reference(q)
        self.assertEqual(len(r.audit),6);self.assertEqual(r.value.status,'VersionedBranchPrepared');self.assertFalse(r.value.consensus_claimed)
        self.assertEqual(r.value.prior_ontology.version,'o1');self.assertEqual(r.value.proposed_ontology.version,'o2')
        self.assertEqual(len(r.value.proposal_belief.branches),2);self.assertEqual(r.value.historical_belief,q.belief);self.assertTrue(any(abs(x)>0 for _,v in r.value.residual_conflicts for x in v))
    def test_no_candidate_keeps_old_world(self):
        q=fixture();q=replace(q,atoms=(q.atoms[0],),candidate_limit=4);r=run_reference(q)
        self.assertEqual(r.value.status,'NoCandidateWithinGrammar');self.assertIsNone(r.value.proposal_belief);self.assertEqual(r.value.historical_belief,q.belief)
    def test_agreement_not_concept_birth(self):
        q=fixture();edges=tuple(replace(e,bias=(0.,)) for e in q.local_sections.restrictions);q=replace(q,local_sections=replace(q.local_sections,restrictions=edges))
        r=run_reference(q);self.assertEqual(r.value.status,'NoObstructionOnDeclaredOverlaps');self.assertIsNone(r.value.proposed_ontology)
    def test_domain_mismatch(self):
        with self.assertRaises(ContractError):run_reference(replace(fixture(),records=((2,{'authorized':True}),)))
    def test_old_reader_and_weights(self):
        q=fixture();r=run_reference(q).value
        self.assertEqual(r.reader_migrations,(('reader','old','old'),));self.assertEqual({b.evidence_support for b in r.proposal_belief.branches},{b.evidence_support for b in q.belief.branches})
        self.assertEqual(r.proposal_belief.consumed_evidence,q.belief.consumed_evidence)
    def test_compiler_all_edges_bound(self):
        ir=lower_plan(build_graph(fixture().versions));self.assertEqual(len(ir.edges),5);self.assertFalse(ir.diagnostics)
if __name__=='__main__':unittest.main()
