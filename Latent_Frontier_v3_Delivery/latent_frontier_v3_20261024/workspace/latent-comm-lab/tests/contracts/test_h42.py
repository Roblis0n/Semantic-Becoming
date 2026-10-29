import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h42_ecology.types import *
from latent_comm.mechanisms.h42_ecology.reference import *
from latent_comm.mechanisms.h42_ecology.serialization import *
import latent_comm.mechanisms.h42_ecology.adapter as adapter

class H42Contracts(unittest.TestCase):
    def test_generated_identity_collision_preserves_acyclic_lineage(self):
        tasks=(TaskGenome('task:1:0','add',1.,False,0.,False,(),'v1'),)
        protocols=(ProtocolGenome('protocol:1:0',('add',),(),(),'p1'),)
        result=evolve(tasks,protocols,MutationGrammar(('shift',),('add_compare',)),generations=1)
        identities=[identity for identity,_ in result.lineage]
        self.assertEqual(len(identities),len(set(identities)))
        self.assertTrue(all(identity not in parents for identity,parents in result.lineage))
        self.assertEqual(len(result.tasks),2);self.assertEqual(len(result.protocols),2)
    def setup_ecology(self):return (TaskGenome('root','add',1.,False,0.,False,(),'1'),),(ProtocolGenome('proto',('add',),(),(),'1'),),MutationGrammar(('condition','inverse'),('add_compare','add_inverse'))
    def test_joint_mutation_lineage_and_archive(self):
        r=evolve(*self.setup_ecology(),generations=1);self.assertGreater(len(r.tasks),1);self.assertGreater(len(r.protocols),1);self.assertTrue(any(parents for _,parents in r.lineage));self.assertGreater(len(r.archive),1)
        self.assertTrue(all(t.competence is None for t in r.transfer_graph))
    def test_dedup_and_budget(self):
        r=evolve(*self.setup_ecology(),generations=4,budget=StepBudget(max_steps=6,max_cases=6));self.assertEqual(r.termination,'ResourceExhausted');self.assertEqual(len({task_signature(t) for t in r.tasks}),len(r.tasks))
    def test_executable_program_and_type(self):
        tasks,protocols,_=self.setup_ecology();self.assertEqual(execute_program(tasks[0],protocols[0],2.),3.)
        with self.assertRaises(ContractError):execute_program(mutate_task(tasks[0],'inverse','new'),protocols[0],2.)
        with self.assertRaises(ContractError):mutate_task(tasks[0],'shell','new')
    def test_transfer_graph_consumes_shared_budget(self):
        result=evolve(*self.setup_ecology(),generations=1,budget=StepBudget(max_steps=5,max_cases=5))
        self.assertEqual(result.consumed_cases,5);self.assertEqual(len(result.transfer_graph),1);self.assertFalse(result.transfer_complete);self.assertEqual(result.termination,'ResourceExhausted')
        result=evolve(*self.setup_ecology(),generations=1);self.assertTrue(result.transfer_complete);self.assertEqual(len(result.transfer_graph),len(result.tasks)*len(result.protocols))
        tree=ast.parse(Path(adapter.__file__).read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='alternating_train')
        self.assertTrue(any(isinstance(n,ast.BinOp) and isinstance(n.op,ast.BitAnd) for n in ast.walk(function)))
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_niche_policy(None,None,None,None,None)
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
