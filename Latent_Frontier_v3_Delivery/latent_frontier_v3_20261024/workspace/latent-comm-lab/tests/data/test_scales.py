import unittest
from latent_comm.worlds.scales import *
class ScalesTests(unittest.TestCase):
 def test_closed_dynamics(self):
  t=build_fixture().supervision.targets;self.assertEqual(t['closure_residual'],(0.,0.));self.assertNotEqual(t['lifting_residual'],(0.,0.,0.,0.))
 def test_equal_coarse_different_next(self):
  a,b,fa,fb=build_fixture(Parameters(closed=False)).supervision.targets['closure_counterexample'];self.assertEqual(a,b);self.assertNotEqual(fa,fb)
 def test_partition_refines(self):
  coarse=build_fixture(Parameters(refined_query=False)).supervision.targets['task_partition'];fine=build_fixture().supervision.targets['task_partition'];self.assertEqual(len(coarse),2);self.assertEqual(len(fine),4)
