import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h27_ontology.types import *
from latent_comm.mechanisms.h27_ontology.reference import *
from latent_comm.mechanisms.h27_ontology.serialization import *
import latent_comm.mechanisms.h27_ontology.adapter as adapter

class H27Contracts(unittest.TestCase):
    def setUp(self):
        self.old=OntologySnapshot('0.1',(ConceptDefinition('key',Predicate('eq','shape','key'),(),('e:shape',),('shape',)),),(('reader','key'),))
        self.records=({'shape':'key','expires':1},{'shape':'key','expires':10})
    def test_new_executable_concept_and_old_reader(self):
        w=search_concept(self.old,self.records,((0,1),),(Predicate('le','expires',5),),concept_id='validity',evidence=('e:expiry',),candidate_limit=6)
        self.assertEqual(w.values,(True,False));d=revise_ontology(self.old,'0.2',(w.definition,))
        self.assertTrue(read_concept((d.before,d.after),'0.1','key',self.records[0]))
        self.assertFalse(read_concept((d.before,d.after),'0.2','validity',self.records[1]))
    def test_unknown_not_false_and_forbidden_label(self):
        self.assertIsNone(evaluate(Predicate('le','expires',5),{'shape':'key'}))
        with self.assertRaises(ContractError):Predicate('eq','label',1)
    def test_extensional_duplicate_provenance(self):
        w=search_concept(self.old,self.records,((0,1),),(Predicate('le','expires',5),Predicate('le','expires',6)),concept_id='new',evidence=('e:1',),candidate_limit=2)
        self.assertEqual(len(w.equivalent_sources),2)
    def test_unexpressible_counterexample(self):
        with self.assertRaises(ContractError):search_concept(self.old,self.records,((0,1),),(Predicate('eq','shape','key'),),concept_id='empty',evidence=('e:1',),candidate_limit=8)
    def test_retirement_requires_consumer_migration(self):
        c=ConceptDefinition('new',Predicate('le','expires',5),('key',),('e:1',),('expires',))
        with self.assertRaises(ContractError):revise_ontology(self.old,'2',(c,),retire=('key',))
        d=revise_ontology(self.old,'2',(c,),retire=('key',),consumer_targets=(('reader','new'),));self.assertEqual(d.reader_migrations,(('reader','key','new'),))
    def test_schema_and_migration(self):
        p={'schema_version':3,'ontology_version':'1','concept_id':'c','predicate':{'op':'le','field':'expires','constant':5,'children':[]},'parents':[],'evidence':['e:1'],'domain':['expires'],'preserve_old_readers':True}
        self.assertEqual(migrate_payload(dict(p,schema_version=2),2),p)
        with self.assertRaises(ContractError):predicate_from_dict(dict(p['predicate'],op='exec'))
    def test_nested_atom_domain_is_enforced(self):
        atom=Predicate('le','undeclared',5);nested=Predicate('not',children=(atom,))
        with self.assertRaises(ContractError):ConceptDefinition('bad',nested,(),('e:1',),('expires',))
        p={'schema_version':3,'ontology_version':'1','concept_id':'c','predicate':{'op':'not','field':None,'constant':None,'children':[{'op':'le','field':'undeclared','constant':5,'children':[]}]},'parents':[],'evidence':['e:1'],'domain':['expires'],'preserve_old_readers':True}
        with self.assertRaises(ContractError):validate_payload(p)
    def test_gate(self):
        with self.assertRaises(Exception):adapter.soft_predicate(None,None,None,None)
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
