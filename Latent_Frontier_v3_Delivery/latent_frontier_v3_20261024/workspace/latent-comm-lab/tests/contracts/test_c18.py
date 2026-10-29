import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError,ObjectRef
from latent_comm.compositions.c18 import *
from latent_comm.mechanisms.h48_evidence_genealogy.types import EvidenceAtom,SupportNode
from latent_comm.mechanisms.h41_coalitions.types import AgentCapability

def fixture():
 v=VersionSet(ontology='o1',task='t1',evidence='e1');atom=EvidenceAtom('a','evidence:source1','observed',.8)
 graph=ProvenanceGraph((atom,),(SupportNode('one','atom',(),'a'),SupportNode('two','atom',(),'a'),SupportNode('root','or',('one','two'))),'root','e1')
 symbol=Symbol('a','decimal','0.8','internal_credit_units',ObjectRef(atom.source_handle),'public');packet=SymbolPacket((symbol,),ObjectRef('state:latent'),v)
 edge=Hyperedge('joint',('reader','writer'),(((1.,),),((1.,),)),((2.,),),(('reader',frozenset({'a'})),('writer',frozenset({'a'}))),v)
 coalition=CoalitionContract((AgentCapability('reader',('parsed',),('input',),1.),AgentCapability('writer',('answer',),('parsed',),1.)),('answer',),('input',),2.)
 return EvidenceCoalitionInput(graph,DependenceModel('unknown',('a',)),packet,(),edge,(('reader',(1.,)),('writer',(1.,))),coalition,v)
class C18Tests(unittest.TestCase):
 def test_duplicate_evidence_not_96_and_exact_credit(self):
  r=run_reference(fixture());self.assertEqual(r.value.evidence.probability,.8);self.assertEqual(r.value.unique_source_count,1);self.assertAlmostEqual(dict(r.value.contributions.contributions)['reader'],1.4);self.assertAlmostEqual(dict(r.value.contributions.contributions)['writer'],1.4);self.assertFalse(r.value.credit_is_money);self.assertEqual(len(r.audit),5)
 def test_duplicate_atom_handles_rejected(self):
  q=fixture();atom=replace(q.graph.atoms[0],atom_id='copy')
  with self.assertRaises(ContractError):run_reference(replace(q,graph=replace(q.graph,atoms=q.graph.atoms+(atom,))))
 def test_exact_symbol_not_overwritten(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,proposed_values=(replace(q.exact_values.symbols[0],value='0.96'),)))
 def test_capability_budget_is_real(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,coalition=replace(q.coalition,resource_budget=1.)))
 def test_missing_member_not_zero(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),member_states=(('reader',(1.,)),)))
if __name__=='__main__':unittest.main()
