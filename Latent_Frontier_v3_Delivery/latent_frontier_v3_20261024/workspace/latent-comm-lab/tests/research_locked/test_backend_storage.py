import ast
from pathlib import Path
import unittest
from latent_comm.core import ContractError,VersionSet
from latent_comm.backends.storage import *
class StorageContracts(unittest.TestCase):
 def test_explicit_device_not_auto(self):
  with self.assertRaises(ContractError):DevicePlan('auto','float32')
  self.assertEqual(DevicePlan('cpu','float32').device,'cpu')
 def test_checkpoint_identity_cannot_escape(self):
  with self.assertRaises(ContractError):CheckpointMetadata('../escape',1,'m','d','c',VersionSet(),('adapter',))
 def test_loading_and_saving_locked(self):
  with self.assertRaises(ContractError):load_tensor_checkpoint(Path('.'),'x','hash',expected_model_digest='m',expected_data_digest='d',device='cpu')
  with self.assertRaises(ContractError):save_tensor_checkpoint(Path('.'),'x',{},None)
 def test_no_pickle_or_torch_load(self):
  import latent_comm.backends.storage as module
  text=Path(module.__file__).read_text();self.assertNotIn('torch.load(',text);self.assertNotIn('pickle',text)
 def test_recompute_boundary_required(self):
  with self.assertRaises(ContractError):CheckpointMetadata('run',1,'m','d','c',VersionSet(),('adapter',),False)

def future_integration_contract(root,tensors,metadata):
 from latent_comm.safety.policy import require_research_action
 require_research_action('model_train')
 saved=save_tensor_checkpoint(root,'checkpoint',tensors,metadata)
 loaded,_,_,_=load_tensor_checkpoint(root,saved['record'],saved['sha256'],expected_model_digest=metadata.model_manifest_digest,expected_data_digest=metadata.data_manifest_digest,device='cpu')
 assert set(loaded)==set(tensors)
 for name in loaded:assert loaded[name].shape==tensors[name].shape
