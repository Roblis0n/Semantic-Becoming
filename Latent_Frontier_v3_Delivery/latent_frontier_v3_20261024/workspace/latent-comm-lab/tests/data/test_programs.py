import unittest
from latent_comm.core import ContractError,FixtureBudget
from latent_comm.worlds.programs import *
from latent_comm.worlds.programs.generator import evaluate
class ProgramsTests(unittest.TestCase):
 def test_macro_binding(self):
  self.assertEqual(build_fixture().supervision.targets['program_output'],7.)
 def test_atomic_conflict(self):
  t=build_fixture(Parameters(conflicting_read=True)).supervision.targets;self.assertEqual(t['commit_status'],'aborted');self.assertFalse(t['partial_commit']);self.assertIn('concept',t['conflict_keys'])
 def test_unknown_instruction(self):
  with self.assertRaises(ContractError):evaluate(('shell','anything'),{},FixtureBudget().meter())
