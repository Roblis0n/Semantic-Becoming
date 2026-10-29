import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c16 import *
from latent_comm.mechanisms.h43_world_kernels.types import ConditionalRow

def fixture():
 v=VersionSet(world='w1',task='t1',isa='i1',evidence='e1');k=WorldKernel('door','door',('closed','open'),(('go','try-door'),),(),(ConditionalRow('closed','go',(),(1.,0.)),ConditionalRow('open','go',(),(0.,1.))),('closed','open'),((1.,0.),(0.,1.)),'w1','public:world')
 return CounterfactualEcologyInput((k,),SharedNoiseJoint((),(((),1.),)),(CounterfactualEdit('door','closed','go',(),(0.,1.)),),('closed',),'go',MutationGrammar(('condition',),('add_compare',)),ProtocolGenome('protocol-root',('add',),(),(),'p1'),'synthetic_consequence',v)
class C16Tests(unittest.TestCase):
 def test_actual_synthetic_question_and_macro_ecology(self):
  q=fixture();r=run_reference(q);self.assertTrue(r.value.evidence.synthetic);self.assertEqual(len(r.value.question_relations),2);self.assertTrue(all(w.sound and w.complete for w in r.value.question_relations));self.assertTrue(r.value.compiled_examples);self.assertTrue(r.value.obligations);self.assertEqual(q.kernels[0].transition_rows[0].probabilities,(1.,0.));self.assertEqual(len(r.audit),5)
 def test_no_real_fact_claim(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),claim_kind='real_world_fact'))
 def test_non_normalized_edit(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,edits=(replace(q.edits[0],probabilities=(.8,.8)),)))
 def test_no_changed_world_no_fabricated_novelty(self):
  r=run_reference(replace(fixture(),edits=())).value;self.assertIsNone(r.population);self.assertFalse(r.question_relations);self.assertIn('no changed questions',r.obligations[0][1])
 def test_nested_budget_returns_partial_before_policy_limit(self):
  q=fixture();q=replace(q,grammar=MutationGrammar(('inverse','shift'),('add_inverse','add_threshold_concept')))
  r=run_reference(q);self.assertEqual(r.status,'BudgetExhausted');self.assertLessEqual(r.consumed_steps,128);self.assertLessEqual(r.consumed_cases,64);self.assertTrue(r.pending_nodes);self.assertTrue(r.obligations)
 def test_caller_budget_is_end_to_end(self):
  from latent_comm.core import StepBudget
  r=run_reference(fixture(),budget=StepBudget(max_steps=10));self.assertEqual(r.status,'BudgetExhausted');self.assertLessEqual(r.consumed_steps,10)
 def test_scope_retains_static_status(self):
  r=run_reference(fixture()).value;self.assertTrue(all(a.competence is None for a in r.population.transfer_graph));self.assertEqual(r.research_state,'NOT_RUN');self.assertTrue(any(parent=='door' for parent,child in r.lineage_edges))
if __name__=='__main__':unittest.main()
