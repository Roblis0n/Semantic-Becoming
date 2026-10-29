import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h44_dreaming.types import *
from latent_comm.mechanisms.h44_dreaming.reference import *
from latent_comm.mechanisms.h44_dreaming.serialization import *
import latent_comm.mechanisms.h44_dreaming.adapter as adapter

class H44Contracts(unittest.TestCase):
    def test_duplicate_parent_identity_rejected_before_edit(self):
        pool,noise=self.pool();left=pool[0];right=replace(left,state_port='other')
        with self.assertRaises(ContractError):construct_dream((left,right),noise,(CounterfactualEdit('door','closed','go',(),(0.,1.)),))
    def pool(self):
        from latent_comm.mechanisms.h43_world_kernels.types import ConditionalRow
        k=WorldKernel('door','door',('closed','open'),(('go','try-door'),),(),(ConditionalRow('closed','go',(),(1.,0.)),ConditionalRow('open','go',(),(0.,1.))),('closed','open'),eye(2),'1','public:world')
        return (k,),SharedNoiseJoint((),(((),1.),))
    def test_counterfactual_world_is_executable_and_new(self):
        pool,noise=self.pool();edit=CounterfactualEdit('door','closed','go',(),(0.,1.));world=construct_dream(pool,noise,(edit,));baseline=compose_kernels(pool,noise)
        evidence=observe_dream(world,(1.,0.),('go',));self.assertEqual(evidence.observation_distributions,((0.,1.),));self.assertTrue(evidence.synthetic);self.assertIn('door',evidence.parents)
        questions=question_candidates(world,baseline,(('closed',),));self.assertTrue(questions);self.assertEqual(answer_question(world,next(q for q in questions if q.target_state==('open',))),1.)
        self.assertEqual(pool[0].transition_rows[0].probabilities,(1.,0.))
    def test_synthetic_not_real_and_cycle(self):
        pool,noise=self.pool();w=construct_dream(pool,noise,());e=observe_dream(w,(1.,0.),('go',))
        with self.assertRaises(ContractError):assert_evidence_use(e,'claim:real','real_world_fact')
        with self.assertRaises(ContractError):assert_evidence_use(e,'door','synthetic_consequence')
    def test_incompatible_edits_and_holdout(self):
        pool,noise=self.pool()
        with self.assertRaises(ContractError):construct_dream(pool,noise,(CounterfactualEdit('door','absent','go',(),(0.,1.)),))
        with self.assertRaises(ContractError):independent_holdout(('door',),('door',),independence_assumed=True)
        with self.assertRaises(ContractError):independent_holdout(('door',),('other',))
        self.assertTrue(independent_holdout(('door',),('other',),independence_assumed=True))
    def test_role_projection_and_gate(self):
        from latent_comm.core.refs import Visibility
        pool,noise=self.pool();w=construct_dream(pool,noise,());v=local_role_view(w,Visibility.SENDER,(0,));self.assertTrue(v.public_task['synthetic']);self.assertNotIn('noise',v.features)
        with self.assertRaises(Exception):adapter.tensor_world_proposal(None,None,None)
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
