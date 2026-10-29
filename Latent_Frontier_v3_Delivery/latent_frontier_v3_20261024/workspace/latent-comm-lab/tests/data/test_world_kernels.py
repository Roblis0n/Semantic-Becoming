import unittest
from latent_comm.worlds.world_kernels import *
class WorldKernelsTests(unittest.TestCase):
 def test_shared_noise_not_independent(self):
  self.assertEqual(build_fixture().supervision.targets['probability_equal'],1.)
  self.assertEqual(build_fixture(Parameters(shared_noise=False)).supervision.targets['probability_equal'],.5)
 def test_counterfactual_is_synthetic(self):
  r=build_fixture(Parameters(invert_second=True));self.assertEqual(r.supervision.targets['probability_equal'],0.);self.assertTrue(r.sender_view.public_task['synthetic'])
 def test_normalization_and_finite_path(self):
  t=build_fixture().supervision.targets
  for _,row in t['joint_transition_rows']:self.assertAlmostEqual(sum(p for _,p in row),1.)
  self.assertEqual(len(t['illustrative_path']),4)
