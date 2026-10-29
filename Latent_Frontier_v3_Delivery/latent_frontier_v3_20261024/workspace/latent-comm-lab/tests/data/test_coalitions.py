import unittest
from latent_comm.worlds.coalitions import *
class CoalitionsTests(unittest.TestCase):
 def test_contribution_efficiency(self):
  t=build_fixture().supervision.targets;self.assertEqual(dict(t['contributions']),{'a':2.,'b':2.,'c':1.});self.assertAlmostEqual(t['efficiency_residual'],0.)
 def test_repeated_source_not_independent(self):
  self.assertAlmostEqual(build_fixture().supervision.targets['support_union_probability'],.8)
  self.assertAlmostEqual(build_fixture(Parameters(shared_source=False)).supervision.targets['support_union_probability'],.96)
 def test_nonmonetary_and_no_source_ids(self):
  r=build_fixture();self.assertFalse(r.sender_view.public_task['credit_is_money']);self.assertNotIn('source_ids',r.sender_view.public_task)
