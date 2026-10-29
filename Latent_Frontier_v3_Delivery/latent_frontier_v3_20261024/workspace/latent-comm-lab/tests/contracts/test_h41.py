import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h41_coalitions.types import *
from latent_comm.mechanisms.h41_coalitions.reference import *
from latent_comm.mechanisms.h41_coalitions.serialization import *
import latent_comm.mechanisms.h41_coalitions.adapter as adapter

class H41Contracts(unittest.TestCase):
    def test_resource_budget_is_finite(self):
        for value in (float('nan'),float('inf'),float('-inf')):
            with self.assertRaises(ContractError):CoalitionContract((AgentCapability('a',('answer',),(),10.),),('answer',),(),value)
        self.assertEqual(CoalitionContract((),(),(),0.).resource_budget,0.)
    def game(self):return CoalitionGame(('a','b'),(((),0.),(('a',),0.),(('b',),0.),(('a','b'),1.)),'1')
    def test_complementarity_and_efficiency(self):
        r=exact_shapley(self.game());self.assertEqual(dict(r.contributions),{'a':.5,'b':.5});self.assertAlmostEqual(r.efficiency_residual,0.)
    def test_dummy_and_nonzero_empty_value(self):
        from itertools import combinations
        players=('a','b','dummy');table=tuple((s,2.+float('a' in s and 'b' in s)) for n in range(4) for s in combinations(players,n));r=exact_shapley(CoalitionGame(players,table,'1'))
        self.assertEqual(dict(r.contributions)['dummy'],0.);self.assertAlmostEqual(sum(dict(r.contributions).values()),1.)
    def test_unknown_is_not_zero(self):
        r=exact_shapley(replace(self.game(),values=(((),0.),)));self.assertEqual(r.status,'UndefinedValue');self.assertIsNone(dict(r.contributions)['a'])
    def test_sampling_budget_and_unique_source(self):
        r=sampled_shapley(self.game(),samples=20,seed=2,budget=StepBudget(max_steps=4));self.assertEqual(r.status,'budget_limited_estimate');self.assertEqual(r.samples,2)
        self.assertEqual(unique_evidence_value((('source',),('source',)),(('source',.8),)),.8)
    def test_capability_dependency_and_gate(self):
        c=CoalitionContract((AgentCapability('a',('intermediate',),(),1),AgentCapability('b',('answer',),('intermediate',),1)),('answer',),(),2)
        self.assertEqual(choose_coalition(self.game(),c)[1],('a','b'))
        with self.assertRaises(Exception):adapter.tensor_coalition_value(None,None,None,None)
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
