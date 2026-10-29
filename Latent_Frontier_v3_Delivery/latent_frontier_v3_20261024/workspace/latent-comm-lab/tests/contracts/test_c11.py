import unittest
from dataclasses import replace
from latent_comm.core import ContractError,VersionSet,Scope
from latent_comm.compositions.c11 import *
from latent_comm.mechanisms.h29_questions.types import QuestionIR,PolynomialConstraint,AnswerMap
from latent_comm.mechanisms.h30_analogy.types import TypedObject,FiniteOperation

def fixture():
 v=VersionSet(state='s1',frame='f1',ontology='o1',isa='i1',task='t1',evidence='e1')
 source=TypedOperationGraph((TypedObject('a','S'),TypedObject('b','S')),(FiniteOperation('next','S','S',(('a','b'),)),),'g1')
 target=TypedOperationGraph((TypedObject('x','T'),TypedObject('y','T')),(FiniteOperation('advance','T','T',(('x','y'),)),),'g2')
 morphism=AnalogyMorphism((('a','x'),('b','y')),(('next','advance'),),(('S','T'),),('a','b'))
 original=QuestionIR('original',('x',),((-2.,2.),),(PolynomialConstraint(((1.,(2,)),),'eq',4.),),'q1')
 changed=QuestionIR('positive',('x',),((-2.,2.),),original.constraints+(PolynomialConstraint(((1.,(1,)),),'ge',0.),),'q1')
 rewrite=QuestionTransform(original,changed,AnswerMap(((1.,),),(0.,),'positive','original'),'partial',('same finite domain',))
 op=OperatorPacket(((1.,),),((0.,),),(1.,),1.,'identity','state','state',v,Scope('op',frozenset({'receiver'}),frozenset({'Z'})))
 return ProblemMigrationInput(rewrite,StateDomain(('a','b'),(1,2),'d1'),(FiniteQuery('parity','parity',0,'q1'),),source,target,morphism,('next',),'a',(('x',(1.,)),('y',(2.,))),(('advance',op),),v)
class C11Tests(unittest.TestCase):
 def test_actual_compiled_program(self):
  r=run_reference(fixture());self.assertEqual(r.value.original_answer,(2.,));self.assertEqual(r.value.relation,'partial');self.assertFalse(r.value.complete);self.assertEqual(r.value.execution_trace,(('step:0','APPLY_OPERATOR'),));self.assertEqual(len(r.audit),6)
 def test_heuristic_not_certified(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,question_transform=replace(q.question_transform,claimed_relation='heuristic')))
 def test_broken_numeric_implementation(self):
  q=fixture();op=replace(q.target_operators[0][1],alpha=2.)
  with self.assertRaises(ContractError):run_reference(replace(q,target_operators=(('advance',op),)))
 def test_unmapped_operation(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,target_operators=()))
 def test_quotient_keeps_source_and_does_not_guess(self):
  q=fixture();q=replace(q,queries=());r=run_reference(q);self.assertEqual(r.value.erased_distinctions,(('a','b'),));self.assertEqual(r.value.original_answer,(2.,))
 def test_bound_ir(self):self.assertEqual(len(lower_plan(build_graph(fixture().versions)).edges),5)
if __name__=='__main__':unittest.main()
