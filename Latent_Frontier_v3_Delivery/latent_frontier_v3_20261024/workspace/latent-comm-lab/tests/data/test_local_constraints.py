import unittest
from latent_comm.worlds.local_constraints import *
class LocalConstraintsTests(unittest.TestCase):
 def test_consistent_hard_anchor(self):
  x=build_fixture();self.assertTrue(x.supervision.targets['exactly_gluable']);self.assertEqual(x.supervision.targets['global_section'][0],1.);self.assertAlmostEqual(x.supervision.targets['obstruction_norm'],0.)
 def test_irreducible_obstruction(self):
  x=build_fixture(Parameters((1.,1.,-1.),1.,True));self.assertFalse(x.supervision.targets['exactly_gluable']);self.assertGreater(x.supervision.targets['obstruction_norm'],.1);self.assertEqual(x.supervision.targets['global_section'][0],1.)
 def test_source_separation(self):
  r=build_fixture();self.assertNotIn('edge_ca',r.sender_view.features);self.assertNotIn('global_section',r.receiver_view.features)
