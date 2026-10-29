"""Prefix layout contracts and AST-only future tensor checks."""
import unittest
from latent_comm.core import ContractError
from latent_comm.backends.hf_prefix import *
class PrefixContracts(unittest.TestCase):
 def test_left_padding_positions(self):
  p=plan_layout(((False,True,True),),2,padding_side='left');self.assertEqual(p.attention_mask,((True,True,False,True,True),));self.assertEqual(p.position_ids,((0,1,0,2,3),));self.assertEqual(p.loss_ignore_prefix,2)
 def test_right_padding_positions(self):
  self.assertEqual(plan_layout(((True,False,False),),1,padding_side='right').position_ids,((0,1,0,0),))
 def test_padding_mismatch_and_empty(self):
  for mask in [((True,False,True),),((False,False,False),)]:
   with self.assertRaises(ContractError):plan_layout(mask,0,padding_side='left')
 def test_future_length_not_clipped(self):
  # Metadata-only length declaration; no model or iterative fixture is run.
  self.assertEqual(PrefixDecodeState(256,512,(),None,'rev').prefix_length,256)
 def test_left_padding_visible_causal_target(self):
  layout=plan_layout(((False,True),),1,padding_side='left')
  self.assertEqual(visible_predecessors(layout),((-1,0),))
  # Token y is scored at prefix logit 0, never masked-pad logit 1.
  logits=((.8,.2),(.1,.9),(.6,.4));target=0;index=visible_predecessors(layout)[0][1]
  self.assertEqual(logits[index][target],.8);self.assertNotEqual(logits[index][target],logits[1][target])
 def test_predecessors_without_prefix_or_right_padding(self):
  self.assertEqual(visible_predecessors(plan_layout(((False,True,True),),0,padding_side='left')),((-1,-1,1),))
  self.assertEqual(visible_predecessors(plan_layout(((True,True,False),),1,padding_side='right')),((0,1,-1),))
 def test_backend_does_not_shift_labels(self):
  import inspect
  text=inspect.getsource(forward_with_prefix)
  self.assertNotIn("kwargs['labels']",text);self.assertIn('aligned_prefix_loss(raw.logits,labels,layout)',text)
 def test_forward_gate_before_inputs(self):
  with self.assertRaises(ContractError):forward_with_prefix(None,None,None,None,capabilities=None,prefix_spec=None,padding_side='left')

def future_integration_contract(model,input_ids,mask,prefix,spec,capabilities,role_origins):
 from latent_comm.safety.policy import require_research_action
 require_research_action('model_forward')
 outputs,_=forward_with_prefix(model,input_ids,mask,prefix,capabilities=capabilities,prefix_spec=spec,padding_side='left',role_origins=role_origins,labels=input_ids,use_cache=False)
 outputs.loss.backward()
 assert prefix.grad is not None
 assert outputs.logits.shape[1]==input_ids.shape[1]+prefix.shape[1]
