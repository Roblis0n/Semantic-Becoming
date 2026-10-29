"""Explicit layout metadata contracts; no cache tensor constructed."""
import unittest
from dataclasses import replace
from latent_comm.core import ContractError
from latent_comm.backends.hf_kv import *
def layout():return KVLayout(CANONICAL_AXES,2,2,4,8,'none','none',0.,'float32','mrev','trev','legacy_tuple','preserve_live')
class KVContracts(unittest.TestCase):
 def test_axes_and_grouping(self):
  self.assertEqual(layout().canonical_shape(1,3),(1,2,3,8))
  with self.assertRaises(ContractError):replace(layout(),query_heads=3)
 def test_unbound_cache_identity_rejected(self):
  with self.assertRaises(ContractError):replace(layout(),model_revision='')
  with self.assertRaises(ContractError):replace(layout(),dtype='auto')
 def test_unknown_rotary_layout(self):
  with self.assertRaises(ContractError):replace(layout(),position_encoding='rope',rotary_layout='unknown',rotary_fraction=1.)
 def test_exact_transfer_cannot_change_revision(self):
  s=layout()
  with self.assertRaises(ContractError):KVTransferContract(s,replace(s,model_revision='other'),(0,1),(0,1),(0,1),(0,1),'exact_same_backend')
 def test_explicit_layer_head_position_maps(self):
  c=KVTransferContract(layout(),layout(),(0,1),(0,1),(0,1),(0,1),'exact_same_backend');self.assertEqual(c.source_positions,(0,1))
  with self.assertRaises(ContractError):replace(c,head_map=(0,4))
 def test_exact_rejects_any_projection_or_phase_remapping(self):
  c=KVTransferContract(layout(),layout(),(0,1),(0,1),(0,1),(0,1),'exact_same_backend')
  validate_transfer_arguments(c,None,None)
  with self.assertRaises(ContractError):validate_transfer_arguments(c,(((2.,0.),(0.,2.)),)*2,(((1.,0.),(0.,1.)),)*2)
  with self.assertRaises(ContractError):validate_transfer_arguments(c,None,None,source_rope=('cos','sin'))
 def test_exact_identity_branch_source(self):
  import inspect
  text=inspect.getsource(transport_legacy_cache)
  identity=text[text.index("if contract.behavior_mapping_kind=='exact_same_backend':"):text.index('for target_layer,source_layer')]
  self.assertIn('layers.append((key,value))',identity);self.assertNotIn('@',identity);self.assertNotIn('_rotate_interleaved',identity)
 def test_cache_transport_gate(self):
  with self.assertRaises(ContractError):transport_legacy_cache(None,None,key_projections=None,value_projections=None)

def future_integration_contract(cache,contract,key_projections,value_projections):
 from latent_comm.safety.policy import require_research_action
 require_research_action('model_forward')
 result=transport_legacy_cache(cache,contract,key_projections=key_projections,value_projections=value_projections)
 assert len(result)==contract.target.num_layers
 for key,value in result:assert key.shape==value.shape
