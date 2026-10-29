import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c20 import *
from latent_comm.mechanisms.h27_ontology.types import ConceptDefinition,Predicate
from latent_comm.mechanisms.h29_questions.types import QuestionIR,PolynomialConstraint,AnswerMap
from latent_comm.mechanisms.h30_analogy.types import TypedObject,FiniteOperation
from latent_comm.mechanisms.h38_plasticity.types import RuleNode
from latent_comm.backends.capabilities import unbound_capabilities

def fixture(mode='inference'):
 v=VersionSet(state='s1',ontology='o1',isa='i1',frame='f1',task='t1',evidence='e1');ontology=OntologySnapshot('o1',(ConceptDefinition('enabled',Predicate('eq','enabled',True),(),('public-task',),('enabled',)),))
 question=QuestionIR('source',('x',),((1.,2.),),(PolynomialConstraint(((1.,(1,)),),'eq',2.),),'t1');target=replace(question,question_id='target');transform=QuestionTransform(question,target,AnswerMap(((1.,),),(0.,),'target','source'),'equivalent',())
 source=TypedOperationGraph((TypedObject('a','S'),TypedObject('b','S')),(FiniteOperation('next','S','S',(('a','b'),)),),'g1');targetgraph=TypedOperationGraph((TypedObject('A','T'),TypedObject('B','T')),(FiniteOperation('advance','T','T',(('A','B'),)),),'g2');morphism=AnalogyMorphism((('a','A'),('b','B')),(('next','advance'),),(('S','T'),),('a','b'))
 rule=PlasticityProgram(RuleNode('scale',(RuleNode('read',slot='gradient'),),-.1),('adapter.offset',),1.,1,2,'rule1','exact_unroll')
 return SemanticCompilerInput(ontology,'enabled',(('enabled',True),),transform,source,targetgraph,morphism,'next','a',(('a',1.),('b',2.)),TaskGenome('add1','add',1.,False,0.,False,(),'task1'),ProtocolGenome('add-protocol',('add',),(),(),'p1'),MutationGrammar(('inverse',),('add_inverse',)),FrameSpec('source',2,'GL','f1'),FrameSpec('target',2,'GL','f2'),((2.,1.),(0.,1.)),rule,SupportBatch((),(),'support'),QueryBatch((),(),'query'),mode,unbound_capabilities(),v)
class C20Tests(unittest.TestCase):
 def test_all_stages_have_actual_effect_and_locked_binding(self):
  r=run_reference(fixture());self.assertEqual(r.value.plan.original_answer,(2.,));self.assertEqual(r.value.backend_status,'UnboundBackend');self.assertFalse(r.value.research_execution_authorized);self.assertEqual(len(r.audit),6);self.assertTrue(r.value.plan.transported.macro.operations.ecology.transfer_graph)
 def test_learning_owner_and_support_query_plan(self):
  r=run_reference(fixture('learning')).value;self.assertEqual(r.plan.partitions,('support','query'));self.assertEqual(r.plan.phase_owners[0][1],('adapter.offset',));self.assertIsNotNone(r.plan.rule)
 def test_unknown_concept_does_not_become_true(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),public_record=()))
 def test_wrong_numeric_edge_rejected(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),object_scalars=(('a',1.),('b',3.))))
 def test_singular_coordinate_map(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),gauge=((0.,0.),(0.,1.))))
 def test_meta_partition_and_owner(self):
  q=fixture('learning')
  with self.assertRaises(ContractError):run_reference(replace(q,query=replace(q.query,partition_id='support')))
  with self.assertRaises(ContractError):run_reference(replace(q,rule=replace(q.rule,writable_groups=('adapter.unowned',))))
if __name__=='__main__':unittest.main()
