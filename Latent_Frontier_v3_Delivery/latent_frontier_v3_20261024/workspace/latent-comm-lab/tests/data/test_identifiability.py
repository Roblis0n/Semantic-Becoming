import unittest
from latent_comm.worlds.identifiability import *
class IdentifiabilityTests(unittest.TestCase):
 def test_nonzero_query_distinguishes(self):
  t=build_fixture().supervision.targets;self.assertEqual(t['selected_query'],1);self.assertTrue(t['identifiable'])
 def test_restricted_domain_cannot_identify(self):
  t=build_fixture(Parameters(allowed_queries=(0,))).supervision.targets;self.assertFalse(t['identifiable']);self.assertFalse(t['external_action_executed'])
 def test_retraction_and_soft_exclusion(self):
  self.assertEqual(build_fixture(Parameters(retract_even=True)).supervision.targets['remaining_domain'],(1,2,3,4))
  self.assertEqual(build_fixture(Parameters(hard_even_constraint=False)).supervision.targets['excluded_domain'],())
