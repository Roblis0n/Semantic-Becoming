"""No fake neural module: hook runtime is AST-checked and future-locked."""
import ast
from pathlib import Path
import unittest
from latent_comm.core import ContractError,TensorSpec
from latent_comm.backends.hf_hooks import *
class HookContracts(unittest.TestCase):
 def test_context_gate_precedes_registration(self):
  with self.assertRaises(ContractError):
   with residual_injections(None,(),capabilities=None):self.fail('must not enter')
 def test_cleanup_has_finally(self):
  import latent_comm.backends.hf_hooks as module
  tree=ast.parse(Path(module.__file__).read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='residual_injections')
  self.assertTrue(any(isinstance(n,ast.Try) and n.finalbody for n in ast.walk(function)))
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='remove' for n in ast.walk(function)))
 def test_no_implicit_broadcast_source(self):
  import latent_comm.backends.hf_hooks as module
  text=Path(module.__file__).read_text();self.assertIn('injection.spec.check_shape(tuple(injection.tensor.shape))',text)
 def test_nested_policy_is_explicit(self):
  import latent_comm.backends.hf_hooks as module
  self.assertIn('nested injection into the same model is explicitly unsupported',Path(module.__file__).read_text())
 def test_forward_locked(self):
  with self.assertRaises(ContractError):forward_with_residuals(None,(),{},capabilities=None)

def future_integration_contract(model,injections,inputs,capabilities):
 from latent_comm.safety.policy import require_research_action
 require_research_action('model_forward')
 before={name:len(module._forward_hooks) for name,module in model.named_modules()}
 try:
  with residual_injections(model,injections,capabilities=capabilities):
   model(**inputs.kwargs())
   raise RuntimeError('intentional cleanup check')
 except RuntimeError as error:
  assert str(error)=='intentional cleanup check'
 after={name:len(module._forward_hooks) for name,module in model.named_modules()}
 assert before==after
