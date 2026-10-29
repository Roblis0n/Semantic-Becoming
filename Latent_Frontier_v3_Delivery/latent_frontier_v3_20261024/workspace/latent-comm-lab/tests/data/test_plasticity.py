import unittest
from latent_comm.core import ContractError
from latent_comm.worlds.plasticity import *
class PlasticityTests(unittest.TestCase):
 def test_rank_residual(self):
  t=build_fixture().supervision.targets;self.assertEqual(t['rank'],1);self.assertEqual(t['unreachable_residual'],(0.,-2.));self.assertFalse(t['unique'])
 def test_full_rank_and_scoped_rule(self):
  t=build_fixture(Parameters(rank_deficient=False)).supervision.targets;self.assertEqual(t['transported_update'],(1.,1.));self.assertEqual(len(t['inner_trajectory']),4);self.assertLess(t['query_loss'],5.)
 def test_bound(self):
  with self.assertRaises(ContractError):build_fixture(Parameters(inner_steps=129))
