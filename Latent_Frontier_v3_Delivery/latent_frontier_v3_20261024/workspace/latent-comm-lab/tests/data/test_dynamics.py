import unittest
from latent_comm.core import ContractError
from latent_comm.worlds.dynamics import *
class DynamicsTests(unittest.TestCase):
 def test_rotation_retains_path_and_norm(self):
  t=build_fixture().supervision.targets;self.assertEqual(len(t['trajectory']),5)
  for n in t['norms']:self.assertAlmostEqual(n,1.)
 def test_dissipation_and_public_boundary(self):
  t=build_fixture(Parameters(mode='dissipation',damping=.5)).supervision.targets;self.assertLess(t['norms'][-1],t['norms'][0])
  r=build_fixture(Parameters(mode='boundary'));self.assertEqual(r.supervision.targets['terminal_residual'],(0.,0.));self.assertEqual(r.sender_view.public_task['terminal_source'],'public_goal')
 def test_bound(self):
  with self.assertRaises(ContractError):build_fixture(Parameters(steps=129))
