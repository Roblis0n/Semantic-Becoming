import unittest
from latent_comm.core import ContractError
from latent_comm.worlds.concepts import *
class ConceptsTests(unittest.TestCase):
 def test_new_distinction(self):
  x=build_fixture();self.assertEqual(x.supervision.targets['predicate_outputs'],(True,False,False));self.assertIn((0,1),x.supervision.targets['distinction_pairs'])
 def test_old_predicate_cannot_distinguish(self):
  x=build_fixture(Parameters('authorized_only'));self.assertEqual(x.supervision.targets['distinction_pairs'],())
 def test_invalid_feature(self):
  with self.assertRaises(ContractError):build_fixture(Parameters(rows=((1,False),)))
