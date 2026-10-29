import unittest
from latent_comm.core import ContractError,Visibility
from latent_comm.worlds.matrix_frames import *
class MatrixFramesTests(unittest.TestCase):
 def test_transport(self):
  x=build_fixture();self.assertEqual(x.supervision.targets['source_result'],(7.,));self.assertTrue(x.supervision.targets['invertible'])
 def test_singular_and_dimensional(self):
  for kind in ('singular','dimensional'):
   x=build_fixture(Parameters(kind));self.assertEqual(x.supervision.targets['failure_kind'],'NonInvertibleFrame')
 def test_roles_and_locked_sampling(self):
  p=Parameters();r=build_fixture(p);self.assertNotIn('source_result',r.sender_view.features)
  self.assertEqual(collate_role((r,),Visibility.RECEIVER).role,Visibility.RECEIVER)
  m=manifest_for((p,),salt='test')
  with self.assertRaises(ContractError):next(iter_records(m,instances_per_template=2,seed=1))
