import ast
from pathlib import Path
import unittest
from latent_comm.core import ContractError,VersionSet
from latent_comm.learning.concept_questions import build_stage,select_concept_structure,search_question_structure
from latent_comm.learning.concept_questions.train import describe
from latent_comm.mechanisms.h27_ontology.types import Predicate,ConceptDefinition,OntologySnapshot
from latent_comm.mechanisms.h27_ontology.reference import search_concept,evaluate
from latent_comm.mechanisms.h29_questions.types import QuestionIR,PolynomialConstraint
from latent_comm.mechanisms.h29_questions.reference import strengthen,check_relation
class LearningConceptQuestions(unittest.TestCase):
    def test_variant_versions_bind_actual_world_records(self):
        import json
        from latent_comm.learning.concept_questions.train import resolve_versions
        from latent_comm.worlds.concepts.generator import build_fixture as concept_fixture
        from latent_comm.worlds.questions.generator import build_fixture as question_fixture
        root=Path(__file__).resolve().parents[2];config=json.loads((root/'configs/learning/concept_questions.json').read_text())
        for variant,builder in (('concept',concept_fixture),('questions',question_fixture)):
            versions=resolve_versions(dict(config,variant=variant));record=builder()
            self.assertEqual(versions,record.sender_view.versions)
            self.assertIsNone(versions.frame)
        self.assertIsNone(resolve_versions(dict(config,variant='concept')).isa)
        self.assertEqual(resolve_versions(dict(config,variant='questions')).isa,'i1')
    def test_describe(self):self.assertEqual(describe()['stage'],'L04')
    def test_build_locked(self):
        with self.assertRaises(ContractError):build_stage('concept',VersionSet())
    def test_structural_train_locked(self):
        with self.assertRaises(ContractError):select_concept_structure(None,None,None,None,concept_id='x',evidence=())
        with self.assertRaises(ContractError):search_question_structure(None,None)
    def test_actual_distinction_and_length(self):
        atom=Predicate('eq','authorized',True);other=Predicate('eq','expired',True)
        old=OntologySnapshot('o1',(ConceptDefinition('authorized',atom,(),('public',),('authorized',)),))
        records=({'authorized':True,'expired':False},{'authorized':True,'expired':True})
        found=search_concept(old,records,((0,1),),(atom,other),concept_id='new',evidence=('public',),candidate_limit=8)
        self.assertNotEqual(found.values[0],found.values[1]);self.assertGreater(found.definition.predicate.description_length,0)
    def test_three_valued_unknown(self):self.assertIsNone(evaluate(Predicate('eq','authorized',True),{}))
    def test_positive_root_not_equivalence(self):
        q=QuestionIR('q',('x',),((-2.,2.),),(PolynomialConstraint(((1.,(2,)),),'eq',4.),),'v1')
        tx=strengthen(q,PolynomialConstraint(((1.,(1,)),),'ge',0.),'p');w=check_relation(tx)
        self.assertTrue(w.sound);self.assertFalse(w.complete);self.assertEqual(w.lost_solutions,((-2.,),))
    def test_no_eager_models(self):
        root=Path(__file__).resolve().parents[2]/'src/latent_comm/learning/concept_questions'
        for path in root.glob('*.py'):
            tree=ast.parse(path.read_text())
            for n in tree.body:
                if isinstance(n,ast.Import):self.assertFalse(any(a.name in ('torch','transformers') for a in n.names))
            for n in ast.walk(tree):
                if isinstance(n,ast.FunctionDef) and n.name in {'forward_roles','losses','build_stage','select_concept_structure','search_question_structure','run'}:
                    first=n.body[1] if isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Constant) else n.body[0]
                    self.assertEqual(getattr(getattr(first,'value',None),'func',None).id,'require_research_action')
    def test_no_query_supervision_forward(self):
        tree=ast.parse((Path(__file__).resolve().parents[2]/'src/latent_comm/learning/concept_questions/__init__.py').read_text())
        for n in ast.walk(tree):
            if isinstance(n,ast.FunctionDef) and n.name=='forward_roles':
                self.assertFalse(any(isinstance(x,ast.Name) and x.id=='supervision' for x in ast.walk(n)))
if __name__=='__main__':unittest.main()
