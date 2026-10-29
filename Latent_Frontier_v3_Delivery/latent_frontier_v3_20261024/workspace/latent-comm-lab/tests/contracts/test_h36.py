import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h36_disagreement.types import *
from latent_comm.mechanisms.h36_disagreement.reference import *
from latent_comm.mechanisms.h36_disagreement.serialization import *
import latent_comm.mechanisms.h36_disagreement.adapter as adapter

class H36Contracts(unittest.TestCase):
    def claim(self):
        even=RuleProgram('divisible',2);four=RuleProgram('divisible',4)
        return ScopedClaim('all-even-div4',RuleProgram('implies',children=(even,four)),(0,1,2,3,4,5,6),'1')
    def test_real_counterexample_and_revision(self):
        c=self.claim();e,_=find_counterexamples(c);self.assertEqual(e[0].value,2)
        revised=RuleProgram('implies',children=tuple(reversed(c.program.children)));g=revise_game(c,(revised,));self.assertEqual(g.status,'valid_on_declared_finite_domain_only');self.assertEqual(g.rounds[0].original,c);self.assertEqual(g.rounds[0].revised.program,revised)
    def test_text_not_evidence_and_scope(self):
        with self.assertRaises(ContractError):challenge(self.claim(),'you are wrong')
        with self.assertRaises(ContractError):challenge(self.claim(),100)
    def test_agreement_not_truth(self):
        c=self.claim();e=challenge(c,2,'disagreement_only',c);self.assertEqual(e.status,'agreement_not_truth');self.assertIsNone(e.expected)
    def test_unresolved_and_scope_migration(self):
        self.assertEqual(revise_game(self.claim(),()).status,'UnresolvedDispute')
        c,e=migrate_claim(self.claim(),'2',(0,1,2,3,4,5,6,8));self.assertEqual(c.version,'2');self.assertTrue(e)
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_challenge_policy(None,None,None,None)
    def test_neural_source_is_lazy_and_gated(self):
        tree=ast.parse(Path(adapter.__file__).read_text())
        self.assertFalse(any(isinstance(x,(ast.Import,ast.ImportFrom)) and any(a.name.startswith(('torch','transformers')) for a in x.names) for x in tree.body))
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                imports=[x for x in ast.walk(node) if isinstance(x,ast.Import) and any(a.name=='torch' for a in x.names)]
                if imports:
                    gates=[x for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require_research_action']
                    self.assertTrue(gates)
                    self.assertLess(min(x.lineno for x in gates),min(x.lineno for x in imports))

if __name__=='__main__':unittest.main()
