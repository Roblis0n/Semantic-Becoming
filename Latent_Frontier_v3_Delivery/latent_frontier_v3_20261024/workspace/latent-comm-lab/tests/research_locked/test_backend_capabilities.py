"""Source/declaration checks only; no backend integration is executed."""
import ast
from pathlib import Path
import unittest
from latent_comm.core import ContractError
from latent_comm.backends.capabilities import *
class BackendCapabilitiesContracts(unittest.TestCase):
 def test_unknown_capability_not_guessed(self):
  c=unbound_capabilities()
  for feature in ('prefix','residual','kv','input_gradients'):
   with self.assertRaises(ContractError):c.require(feature)
 def test_identity_needs_revision(self):
  with self.assertRaises(ContractError):ModelIdentity('model','','tokenizer','rev','digest','https://example.test/source')
 def test_loading_locked(self):
  with self.assertRaises(ContractError):bind_hf(None,unbound_capabilities(),device='cpu',dtype_name='float32')
 def test_freeze_does_not_disable_input_graph(self):
  text=Path(__import__('latent_comm.backends.capabilities',fromlist=['x']).__file__).read_text();tree=ast.parse(text)
  self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='no_grad' for n in ast.walk(tree)))
 def test_model_input_cannot_smuggle_labels(self):
  from latent_comm.core import RoleView,Visibility,VersionSet
  class ShapeDescriptor:
   shape=(1,2)
  origin=(RoleView(Visibility.SENDER,{}, {'tokens':(1,2)},VersionSet()),)
  with self.assertRaises(ContractError):ModelInputs(origin,{'input_ids':ShapeDescriptor(),'labels':ShapeDescriptor()})
  batch=ModelInputs(origin,{'input_ids':ShapeDescriptor()});self.assertEqual(tuple(batch.tensors),('input_ids',))
 def test_neural_integration_is_not_run(self):
  import sys
  self.assertNotIn('torch',sys.modules);self.assertNotIn('transformers',sys.modules)

def future_integration_contract(model,capabilities):
 from latent_comm.safety.policy import require_research_action
 require_research_action('model_forward')
 assert model.get_input_embeddings().embedding_dim==capabilities.hidden_size
 assert capabilities.binding_status!='unbound'
