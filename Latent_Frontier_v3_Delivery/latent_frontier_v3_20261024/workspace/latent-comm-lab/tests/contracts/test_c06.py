import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,Scope,ContractError
from latent_comm.compositions.c06 import *
from latent_comm.mechanisms.h14_legacy.types import Production,SkillStep

def fixture():
 v=VersionSet(state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1');scope=Scope('skill',frozenset({'receiver'}),frozenset({'Z'}));s=ValueType('state',1,'f1');o=ValueType('operator',1,'f1')
 grammar=SkillGrammar((Production('twice',(('x',s),('op',o)),(SkillStep('y','APPLY_OPERATOR',('x','op'),s),),'y',s),),'g1','i1',frozenset({'multiply'}),v)
 op=OperatorPacket(((1.,),),((1.,),),(0.,),1.,'identity','state','state',v,scope)
 edge=Hyperedge('joint',('a','b'),(((1.,),),((1.,),)),((1.,),),(('a',frozenset({'shared'})),('b',frozenset({'shared'}))),v)
 trace=TeacherTrace('trace','seen-instance','message',('twice',),frozenset({'shared'}),'multiply','teacher1',10,v)
 return JointSkillInput(grammar,'twice',op,(('a',(2.,)),('b',(3.,))),edge,((1.,),),trace,frozenset({'unseen'}),True,0,'multiply',scope,v)
class C06Tests(unittest.TestCase):
 def test_joint_not_sum_and_affine_not_joint(self):
  from latent_comm.mechanisms.h19_legacy.reference import apply_skill
  r=run_reference(fixture());self.assertEqual(r.status,'Complete');self.assertEqual(r.value.observation,(24.,));self.assertEqual(apply_skill(r.value.compiled_local_skill,(2.,)),(4.,));self.assertEqual(r.value.evidence_atoms,frozenset({'shared'}));self.assertEqual(r.value.research_state,'NOT_RUN')
 def test_missing_member_not_zero(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),members=(('a',(2.,)),)))
 def test_trace_split_leakage(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),unseen_instance_ids=frozenset({'seen-instance'})))
 def test_nonlinear_not_affine(self):
  q=fixture();r=run_reference(replace(q,operator=replace(q.operator,nonlinearity='tanh'))).value;self.assertIsNone(r.compiled_local_skill);self.assertEqual(r.status,'NonlinearSkillRequiresFutureDistillation')
 def test_stale_grammar(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,grammar=replace(q.grammar,base_isa='old')))
if __name__=='__main__':unittest.main()
