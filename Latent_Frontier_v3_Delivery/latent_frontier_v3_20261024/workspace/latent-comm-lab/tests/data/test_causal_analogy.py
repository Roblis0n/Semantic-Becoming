import unittest
from latent_comm.core import ContractError
from latent_comm.worlds.causal_analogy import *
class CausalAnalogyTests(unittest.TestCase):
 def test_commuting_case_and_counterexample(self):
  self.assertEqual(build_fixture(Parameters(2.,2.)).supervision.targets['analogy_commutation_error'],0.)
  self.assertGreater(build_fixture().supervision.targets['analogy_commutation_error'],0.)
 def test_shared_noise_distinct_joint(self):
  self.assertEqual(len(build_fixture().supervision.targets['joint_outputs_after_graft']),2)
  self.assertEqual(len(build_fixture(Parameters(shared_noise=False)).supervision.targets['joint_outputs_after_graft']),4)
 def test_boundary_rejected(self):
  with self.assertRaises(ContractError):build_fixture(Parameters(boundary_scale=0.))
