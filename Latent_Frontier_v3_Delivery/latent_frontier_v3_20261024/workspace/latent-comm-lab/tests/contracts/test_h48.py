import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h48_evidence_genealogy.types import *
from latent_comm.mechanisms.h48_evidence_genealogy.reference import *
from latent_comm.mechanisms.h48_evidence_genealogy.serialization import *
import latent_comm.mechanisms.h48_evidence_genealogy.adapter as adapter

class H48Contracts(unittest.TestCase):
    def test_empty_loss_source_contract(self):
        tree=ast.parse(Path(adapter.__file__).read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='train_link_step')
        backward=min(n.lineno for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='backward')
        skips=[n for n in ast.walk(function) if isinstance(n,ast.If) and any(isinstance(x,ast.Return) and "'skipped'" in ast.unparse(x) for x in n.body)]
        self.assertTrue(skips);self.assertLess(min(n.lineno for n in skips),backward)
        self.assertIn('LossValue',ast.unparse(function));self.assertIn('isfinite',ast.unparse(function))
    def graph(self,duplicate=False):
        atoms=(EvidenceAtom('e','original:e','observed',.8),) if duplicate else (EvidenceAtom('e','original:e','observed',.8),EvidenceAtom('f','original:f','observed',.8))
        return ProvenanceGraph(atoms,(SupportNode('A','atom',(),'e'),SupportNode('B','atom',(),'e' if duplicate else 'f'),SupportNode('claim','or',('A','B'))),'claim','v1')
    def test_duplicate_is_point8_not_point96(self):
        graph=self.graph(True);result=calibrate_support(graph,DependenceModel('unknown',('e',)));self.assertEqual(result.normalized_expression,('atom','e'));self.assertEqual(result.probability,.8);self.assertEqual(result.atom_coverage,('e',));self.assertIn('e',result.shared_ancestors)
        independent=calibrate_support(graph,DependenceModel('declared_independent',('e',),declaration_id='one-source'));self.assertAlmostEqual(independent.probability,.8)
    def test_independent_vs_correlated_joint_and_unknown(self):
        graph=self.graph();ind=calibrate_support(graph,DependenceModel('declared_independent',('e','f'),declaration_id='explicit-assumption'));self.assertAlmostEqual(ind.probability,.96)
        correlated=DependenceModel('explicit_joint',('e','f'),(JointAssignment((False,False),.2),JointAssignment((True,True),.8)),'joint-proof');self.assertAlmostEqual(calibrate_support(graph,correlated).probability,.8)
        unknown=calibrate_support(graph,DependenceModel('unknown',('e','f')));self.assertIsNone(unknown.probability);self.assertEqual((unknown.lower_bound,unknown.upper_bound),(.8,1.));self.assertEqual(unknown.status,'UnknownDependence')
    def test_retraction_cycle_and_missing(self):
        graph=self.graph();result=retract_sources(graph,('e',));self.assertTrue(result.root_invalidated);self.assertEqual(set(result.invalidated_nodes),{'A','claim'})
        cycle=ProvenanceGraph(graph.atoms,(SupportNode('a','or',('b',)),SupportNode('b','and',('a',))),'a','v')
        with self.assertRaises(ContractError):normalize_support(cycle)
        with self.assertRaises(ContractError):calibrate_support(graph,DependenceModel('declared_independent',('e',),declaration_id='not-enough'))
        duplicate_source=ProvenanceGraph((graph.atoms[0],EvidenceAtom('f','original:e','observed',.8)),graph.nodes,'claim','v')
        with self.assertRaises(ContractError):validate_graph(duplicate_source)
    def test_migration_truth_table_and_synthetic_lineage(self):
        graph=self.graph();migrated=migrate_graph(graph,{'A':'AA','B':'BB','claim':'CC'},'v2');self.assertEqual(normalize_support(graph),normalize_support(migrated));self.assertEqual(migrated.atoms,graph.atoms)
        rows,truth=compile_truth_table(graph,('e','f'));self.assertEqual(truth,(False,True,True,True));self.assertEqual(len(rows),4)
        synthetic=ProvenanceGraph((EvidenceAtom('e','dream:e','synthetic',.8,('dream-world',)),),(SupportNode('A','atom',(),'e'),),'A','v');self.assertIn('not_independent_real',calibrate_support(synthetic,DependenceModel('unknown',('e',))).evidence_scope)
        with self.assertRaises(ContractError):compile_truth_table(graph,('e','f'),budget=StepBudget(max_cases=2))
    def test_schema_rejects_uncovered_dependence(self):
        payload={'schema_version':3,'atoms':[{'atom_id':'e','source_handle':'source:e','source_kind':'observed','marginal':.8,'world_lineage':[]}],'nodes':[{'node_id':'n','op':'atom','inputs':[],'atom_id':'e'}],'root':'n','version':'v1','dependence':{'mode':'declared_independent','atom_ids':[],'joint':[],'declaration_id':'false-coverage'}}
        with self.assertRaises(ContractError):validate_payload(payload)
    def test_schema_roundtrip_and_gate(self):
        payload={'schema_version':3,'atoms':[{'atom_id':'e','source_handle':'source:e','source_kind':'observed','marginal':.8,'world_lineage':[]}],'nodes':[{'node_id':'n','op':'atom','inputs':[],'atom_id':'e'}],'root':'n','version':'v1','dependence':{'mode':'unknown','atom_ids':['e'],'joint':[],'declaration_id':None}}
        self.assertEqual(decode_payload(encode_payload(payload)),payload);self.assertEqual(migrate_payload(dict(payload,schema_version=2),2),payload)
        with self.assertRaises(Exception):adapter.exact_support_tensor(None,None,None,dependence_mode='unknown',declaration_id=None)
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
