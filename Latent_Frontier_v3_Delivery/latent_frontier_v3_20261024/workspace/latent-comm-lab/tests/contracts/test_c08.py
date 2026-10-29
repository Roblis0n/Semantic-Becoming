import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,Scope,ContractError,StepBudget
from latent_comm.compositions.c08 import *
from latent_comm.mechanisms.h14_legacy.types import Production,SkillStep
from latent_comm.mechanisms.h18_legacy.types import PrimitiveNode
from latent_comm.mechanisms.h22_legacy.types import StateCell

def fixture():
 v=VersionSet(state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1');scope=Scope('program',frozenset({'receiver'}),frozenset({'Z'}));s=ValueType('state',1,'f1');o=ValueType('operator',1,'f1')
 grammar=SkillGrammar((Production('double',(('x',s),('op',o)),(SkillStep('y','APPLY_OPERATOR',('x','op'),s),),'y',s),),'g1','i1',frozenset({'double'}),v);op=OperatorPacket(((1.,),),((1.,),),(0.,),1.,'identity','state','state',v,scope)
 graph=GraphCandidate('double',(PrimitiveNode('x','input'),PrimitiveNode('y','sum')),(('x','y',0),('x','y',1)),'y',(),v);actors=frozenset({'receiver'});cell=StateCell('cell','scalar',(3.,),'f1',actors,actors,'p',0);partition=PartitionState((('p',actors),),(cell,),frozenset(),'s1',v)
 return ProtocolLanguageInput(grammar,'double',('state','operator'),(('state',s),('operator',o)),(('operator',op),),graph,'x',partition,StateReference('cell',0,'s1','f1'),'receiver','double',scope,v)
class C08Tests(unittest.TestCase):
 def test_macro_graph_owned_execution(self):
  r=run_reference(fixture());self.assertEqual(r.status,'Complete');self.assertEqual(r.value.observation,(6.,));self.assertEqual(r.value.affine_witness,(2.,0.));self.assertEqual(r.value.lowered_opcodes,('APPLY_OPERATOR',))
 def test_noncommuting_graph_rejected_not_probe_fitted(self):
  q=fixture();bad=replace(q.graph,nodes=(PrimitiveNode('x','input'),PrimitiveNode('y','negate')),edges=(('x','y',0),))
  with self.assertRaises(ContractError):run_reference(replace(q,graph=bad))
 def test_nonlinear_graph_requires_different_certificate(self):
  q=fixture();bad=replace(q.graph,nodes=(PrimitiveNode('x','input'),PrimitiveNode('y','product')))
  with self.assertRaises(ContractError):run_reference(replace(q,graph=bad))
 def test_stale_ownership_reference(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,state_reference=replace(q.state_reference,revision=1)))
 def test_end_to_end_budget_preserves_partial(self):
  r=run_reference(fixture(),budget=StepBudget(max_steps=8));self.assertNotEqual(r.status,'Complete');self.assertTrue(r.pending_nodes);self.assertLessEqual(r.consumed_steps,8)
if __name__=='__main__':unittest.main()
