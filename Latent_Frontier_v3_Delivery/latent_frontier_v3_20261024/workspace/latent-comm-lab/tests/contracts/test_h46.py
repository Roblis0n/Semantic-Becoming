import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h46_negative_knowledge.types import *
from latent_comm.mechanisms.h46_negative_knowledge.reference import *
from latent_comm.mechanisms.h46_negative_knowledge.serialization import *
import latent_comm.mechanisms.h46_negative_knowledge.adapter as adapter

class H46Contracts(unittest.TestCase):
    def test_empty_loss_source_contract(self):
        tree=ast.parse(Path(adapter.__file__).read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='train_exclusion_step')
        backward=min(n.lineno for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='backward')
        skips=[n for n in ast.walk(function) if isinstance(n,ast.If) and any(isinstance(x,ast.Return) and "'skipped'" in ast.unparse(x) for x in n.body)]
        self.assertTrue(skips);self.assertLess(min(n.lineno for n in skips),backward)
        self.assertIn('LossValue',ast.unparse(function));self.assertIn('isfinite',ast.unparse(function))
        source=ast.unparse(function)
        self.assertIn("model_inputs['predicate_weights']",source);self.assertIn("model_inputs['scope_weights']",source)
        checks=[n for n in function.body if isinstance(n,ast.If) and 'bound.items()' in ast.unparse(n.test)]
        forward=min(n.lineno for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='propose_exclusions')
        self.assertEqual(len(checks),1);self.assertLess(checks[0].lineno,forward)
    def capsule(self,key,excluded,required,assumption='a',dependencies=()):
        return ExclusionCapsule(key,excluded,(assumption,),NegativeWitness('program_exhaustive',required,(1,2,3,4),None,'complete'),1.,'hard',dependencies,(), 'v1')
    def test_hard_intersection_and_empty(self):
        even=self.capsule('even',DomainPredicate('not_divisible',2),DomainPredicate('divisible',2));greater=self.capsule('greater',DomainPredicate('le',3),DomainPredicate('gt',3));less=self.capsule('less',DomainPredicate('ge',4),DomainPredicate('lt',4))
        self.assertEqual(apply_exclusions((1,2,3,4),(even,greater),('a',),'v1').feasible,(4,))
        result=apply_exclusions((1,2,3,4),(even,greater,less),('a',),'v1');self.assertEqual(result.status,'EmptyDomainConflict');self.assertEqual(len(result.conflicts),3)
    def test_timeout_and_soft_never_hard(self):
        witness=NegativeWitness('search_failed_in_grammar',None,(), 'depth2','search_exhausted_within_budget')
        with self.assertRaises(ContractError):ExclusionCapsule('timeout',DomainPredicate('eq',1),(),witness,.99,'hard',(),(),'v1')
        soft=ExclusionCapsule('soft',DomainPredicate('gt',0),(),NegativeWitness('soft_empirical',None,(),None,'estimate'),.9,'soft',(),(),'v1')
        result=apply_exclusions((1,2,3,4),(soft,),(),'v1');self.assertEqual(result.feasible,(1,2,3,4));self.assertAlmostEqual(dict(result.soft_penalties)[1],.9)
    def test_retraction_dependency_and_scope(self):
        even=self.capsule('even',DomainPredicate('not_divisible',2),DomainPredicate('divisible',2));greater=self.capsule('greater',DomainPredicate('le',3),DomainPredicate('gt',3),'b',('even',))
        before=apply_exclusions((1,2,3,4),(even,greater),('a','b'),'v1');event=retract_exclusions(before,(even,greater),('a','b'),('a',))
        self.assertEqual(event.invalidated_capsules,('even','greater'));self.assertEqual(event.region.feasible,(1,2,3,4));self.assertEqual(event.restored_candidates,(1,2,3))
        self.assertEqual(apply_exclusions((1,2,3,4),(even,),('a',),'v2').inactive,(('even','ScopeExpired'),))
    def test_overgeneralization_migration_budget(self):
        bad=self.capsule('bad',DomainPredicate('lt',4),DomainPredicate('divisible',2))
        self.assertEqual(generalization_counterexamples(bad.excluded,bad.witness.required_predicate,(1,2,3,4)),(2,))
        with self.assertRaises(ContractError):apply_exclusions((1,2,3,4),(bad,),('a',),'v1')
        valid=self.capsule('valid',DomainPredicate('not_divisible',2),DomainPredicate('divisible',2));self.assertEqual(migrate_capsule(valid,'v2',(1,2,3,4)).domain_version,'v2')
        with self.assertRaises(ContractError):migrate_capsule(valid,'v2',(1,2,3,4,5))
        with self.assertRaises(ContractError):apply_exclusions((1,2,3,4),(valid,),('a',),'v1',budget=StepBudget(max_steps=2))
    def test_gate(self):
        with self.assertRaises(Exception):adapter.apply_tensor_exclusions(None,None,None)
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
