import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h29_questions.types import *
from latent_comm.mechanisms.h29_questions.reference import *
from latent_comm.mechanisms.h29_questions.serialization import *
import latent_comm.mechanisms.h29_questions.adapter as adapter

class H29Contracts(unittest.TestCase):
    def setUp(self):
        self.q=QuestionIR('square',('x',),((-2.,-1.,0.,1.,2.),),(PolynomialConstraint(((1.,(2,)),),'eq',4.),),'1')
    def test_backtranslation_does_not_conflate_close_domain_values(self):
        source=QuestionIR('s',('x',),((0.3,),),(),'1')
        target=QuestionIR('t',('x',),((0.1,),),(),'1')
        mapping=AnswerMap(((3.,),),(0.,),'t','s')
        witness=check_relation(QuestionTransform(source,target,mapping,'heuristic',()))
        self.assertFalse(witness.sound);self.assertFalse(witness.complete)
        self.assertFalse(satisfies(source,(0.1*3,)))
        self.assertEqual(answer_preimages(mapping,(0.3,),target),())
    def test_relation_checks_share_the_declared_budget(self):
        source=QuestionIR('s',('x',),((0.,1.),),(),'1')
        target=QuestionIR('t',('x',),((0.,1.),),(),'1')
        transform=QuestionTransform(source,target,AnswerMap(((1.,),),(0.,),'t','s'),'equivalent',())
        with self.assertRaises(ContractError) as ctx:check_relation(transform,StepBudget(max_steps=3,max_cases=3))
        self.assertEqual(ctx.exception.failure.code,'BudgetExhausted')
        self.assertEqual(check_relation(transform,StepBudget(max_steps=4,max_cases=4)).relation,'equivalent')
    def test_composed_relations_share_one_budget(self):
        first=strengthen(self.q,PolynomialConstraint(((1.,(1,)),),'ge',-2.),'first')
        second=strengthen(first.target,PolynomialConstraint(((1.,(1,)),),'le',2.),'second')
        with self.assertRaises(ContractError) as ctx:compose(first,second,StepBudget(max_steps=14,max_cases=14))
        self.assertEqual(ctx.exception.failure.code,'BudgetExhausted')
    def test_graph_budget_exhaustion_retains_frontier(self):
        question=QuestionIR('initial',('x',),((0.,1.),),(),'1')
        rule=RewriteRule('positive','strengthen',PolynomialConstraint(((1.,(1,)),),'ge',0.))
        graph=build_question_graph(question,TransformLibrary((rule,),'1'),budget=StepBudget(max_steps=5,max_cases=3))
        self.assertEqual(graph.status,'TransformBudget');self.assertEqual(graph.remaining_frontier,(('initial',0),))
        self.assertFalse(graph.edges)
    def test_both_roots_and_partial_detection(self):
        self.assertEqual(solutions(self.q),((-2.,),(2.,)))
        t=strengthen(self.q,PolynomialConstraint(((1.,(1,)),),'ge',0.),'positive')
        w=check_relation(t);self.assertTrue(w.sound);self.assertFalse(w.complete);self.assertEqual(w.lost_solutions,((-2.,),))
        with self.assertRaises(ContractError):check_relation(replace(t,claimed_relation='equivalent'))
    def test_auxiliary_elimination_preserves_solutions(self):
        t=introduce_auxiliary(self.q,'twice',(-4.,4.),(2.,),0.,'expanded');self.assertEqual(check_relation(t).relation,'equivalent')
        self.assertEqual(answer_preimages(t.backtranslation,(-2.,),t.target),((-2.,-4.),))
    def test_necessary_not_sufficient(self):
        target=replace(self.q,question_id='relaxed',constraints=())
        t=QuestionTransform(self.q,target,AnswerMap(((1.,),),(0.,),'relaxed','square'),'necessary',())
        self.assertEqual(check_relation(t).relation,'necessary')
    def test_empty_and_no_fake_inverse(self):
        q=replace(self.q,constraints=(PolynomialConstraint(((1.,(2,)),),'eq',-1.),))
        self.assertEqual(solutions(q),())
        with self.assertRaises(ContractError):introduce_auxiliary(self.q,'a',(4.,),(2.,),0.,'lost')
    def test_composition_and_migration(self):
        t=strengthen(self.q,PolynomialConstraint(((1.,(1,)),),'ge',0.),'pos');u=strengthen(t.target,PolynomialConstraint(((1.,(1,)),),'le',3.),'bounded')
        self.assertEqual(check_relation(compose(t,u)).relation,'sufficient')
        self.assertEqual(migrate_question(self.q,'2',{'x':'y'}).variables,('y',))
    def test_bounded_question_graph_retains_failures_and_transports(self):
        rules=TransformLibrary((RewriteRule('positive','strengthen',PolynomialConstraint(((1.,(1,)),),'ge',0.)),RewriteRule('bad-relax','relax',drop_constraint_index=99)),'library:1')
        graph=build_question_graph(self.q,rules,max_transform_depth=1,candidate_questions=8)
        self.assertEqual(len(graph.nodes),2);self.assertTrue(any(e.rejection for e in graph.edges))
        edge=next(e for e in graph.edges if e.transform is not None)
        self.assertEqual(transport_graph_answer(graph,(edge.edge_id,),(2.,)),(2.,))
        limited=build_question_graph(self.q,rules,candidate_questions=1)
        self.assertEqual(limited.status,'TransformBudget');self.assertTrue(limited.remaining_frontier)
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_transform_policy(None,None,None,None,None)
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
