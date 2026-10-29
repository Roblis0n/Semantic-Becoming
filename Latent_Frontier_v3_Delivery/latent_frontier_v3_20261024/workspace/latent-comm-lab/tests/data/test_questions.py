import unittest
from latent_comm.worlds.questions import *
class QuestionsTests(unittest.TestCase):
 def test_positive_root_is_sound_not_complete(self):
  t=build_fixture().supervision.targets;self.assertTrue(t['sound']);self.assertFalse(t['complete']);self.assertEqual(t['missing_answers'],(-2,))
 def test_both_roots_equivalent(self):
  self.assertEqual(build_fixture(Parameters(transform='both_roots')).supervision.targets['relation'],'equivalent')
 def test_relaxation_not_equivalent(self):
  t=build_fixture(Parameters(transform='relax_nonnegative')).supervision.targets;self.assertFalse(t['sound']);self.assertIn(0,t['unsound_answers'])
