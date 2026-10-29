import unittest
from latent_comm.core import ContractError
from latent_comm.backends.behavior import *
class BehaviorContracts(unittest.TestCase):
 def test_tokenizer_kl_rejects_mismatch(self):
  a=TokenizerContract('a','r','v','rules');b=TokenizerContract('b','r','v2','rules2')
  with self.assertRaises(ContractError):a.require_same_vocabulary(b)
 def test_common_space_requires_explicit_correspondence(self):
  a=BehaviorSpace('actions','v1',('left','right'),'public_probe','probability');b=BehaviorSpace('actions','v1',('right','left'),'public_probe','probability')
  with self.assertRaises(ContractError):a.require_same(b)
 def test_public_anchor_only(self):
  with self.assertRaises(ContractError):BehaviorSpace('x','v1',('a',),'hidden_solution','probability')
 def test_parameter_scope_disjoint(self):
  with self.assertRaises(ContractError):ParameterScope(('adapter',),('adapter',))
 def test_functional_binding_locked(self):
  with self.assertRaises(ContractError):FunctionalBehaviorAdapter(None,None,None,None)

def future_integration_contract(adapter,parameters,direction,inputs,cotangent):
 from latent_comm.safety.policy import require_research_action
 require_research_action('model_forward')
 value,jv=adapter.jvp(parameters,direction,inputs)
 _,pullback=adapter.vjp(parameters,cotangent,inputs)
 assert value.shape==jv.shape
 assert set(pullback)==set(parameters)
