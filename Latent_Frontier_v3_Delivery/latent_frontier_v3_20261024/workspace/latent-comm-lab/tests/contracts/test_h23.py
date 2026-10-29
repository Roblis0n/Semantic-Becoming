import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h23_legacy.types import *
from latent_comm.mechanisms.h23_legacy.reference import *
from latent_comm.mechanisms.h23_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h23_legacy'

from dataclasses import replace
class TestRepair(unittest.TestCase):
    def report(self,**kw):
        args=dict(report_id='r',payload=b'message',expected_digest=integrity_digest(b'message'),probe_ids=('p',),observed=(3.,),expected=(2.,),allowed_fields={'probe_ids','residual','missing_variables','conflicting_domains','evidence_errors'},versions=V);args.update(kw);return diagnose(**args)
    def test_numeric_repair_and_accounting(self):
        report=self.report();repair=build_repair(report,((2.,),));self.assertEqual(repair.delta,(-.5,));self.assertEqual(repair.remaining_residual,(0.,))
        s=RepairSession((1.5,),report.message_digest,frozenset(),0,0,0,frozenset({'e'}),V);r=apply_repair(s,report,repair,max_rounds=2)
        self.assertEqual(r.state,(1.,));self.assertGreater(r.feedback_bytes,0);self.assertGreater(r.repair_bytes,0)
        duplicate=apply_repair(r,report,repair,max_rounds=2);self.assertEqual(duplicate.state,r.state);self.assertGreater(duplicate.repair_bytes,r.repair_bytes)
    def test_byte_corruption_is_not_semantic_repair(self):
        with self.assertRaises(ContractError):self.report(payload=b'corrupted')
        with self.assertRaises(ContractError):self.report(allowed_fields={'private_text'})
    def test_conflict_missing_evidence_are_not_noise(self):
        report=self.report(domains=('temperature','distance'));packet=build_repair(report);self.assertEqual(packet.delta,());self.assertEqual(packet.kind,'semantic_domain')
        missing=self.report(missing=('velocity',));self.assertEqual(build_repair(missing).required_action,'explicit_variable_and_ontology_binding')
        bound=bind_ontology_repair(missing,source_ontology='o1',target_ontology='o2',variable_bindings={'velocity':'m/s'});self.assertEqual(bound['target_ontology'],'o2')
        with self.assertRaises(ContractError):bind_ontology_repair(missing,source_ontology='o1',target_ontology='o2',variable_bindings={})
        evidence=self.report(evidence_errors={'e'});self.assertEqual(build_repair(evidence).evidence_retractions,frozenset({'e'}))
    def test_unreachable_residual_preserved_and_no_repair(self):
        packet=build_repair(self.report(),((0.,),));self.assertEqual(packet.remaining_residual,(1.,));self.assertEqual(packet.required_action,'unreachable_residual_preserved')
        self.assertEqual(build_repair(self.report(observed=(2.,))).kind,'none')

    def test_source_gate_and_schema(self):
        schema=json.loads((ROOT/'schema.json').read_text())
        self.assertFalse(schema['additionalProperties'])
        for name in ('adapter.py','losses.py'):
            tree=ast.parse((ROOT/name).read_text())
            for node in tree.body:
                self.assertFalse(isinstance(node,(ast.Import,ast.ImportFrom)) and any(a.name.split('.')[0] in {'torch','transformers'} for a in node.names))
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    calls=[x for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require_research_action']
                    self.assertTrue(calls,node.name)
                    imports=[x for x in ast.walk(node) if isinstance(x,ast.Import) and any(a.name=='torch' for a in x.names)]
                    for imp in imports:self.assertLess(min(x.lineno for x in calls),imp.lineno)
        with self.assertRaises(ContractError):migrate_legacy({'schema_version':2},bindings={},versions=V)

    def test_reply_binding_prevents_semantic_coercion(self):
        report=self.report(domains=('a','b'));session=RepairSession((1.,),report.message_digest,frozenset(),0,0,0,frozenset({'e'}),V)
        forged=RepairPacket(report.report_id,report.message_digest,'numeric',(1.,),(),'f1',frozenset(),None,V)
        with self.assertRaises(ContractError):apply_repair(session,report,forged,max_rounds=2)
        evidence=self.report(evidence_errors={'e'});packet=replace(build_repair(evidence),evidence_retractions=frozenset({'other'}))
        with self.assertRaises(ContractError):apply_repair(session,evidence,packet,max_rounds=2)
    def test_single_sheaf_edge_is_two_domains(self):
        from latent_comm.mechanisms.h26_sheaf.types import LocalDomain,AffineRestriction,SheafPacket,GluingCandidate
        sheaf=SheafPacket((LocalDomain('a',1),LocalDomain('b',1)),(AffineRestriction('edge','a','b',((1.,),),((1.,),),(0.,),('source',)),),(),'s1')
        gluing=GluingCandidate((),(('edge',(1.,)),),('edge',),'conflict',(),1,1)
        report=sheaf_conflict_report(gluing,sheaf,report_id='r',digest='hash',versions=V)
        self.assertEqual(report.conflicting_domains,('a','b'));self.assertEqual(report.conflict_edge_witness,('edge',))

    def test_wire_roundtrip_explicit_migration_and_bad_types(self):
        from copy import deepcopy
        from latent_comm.mechanisms.h23_legacy.migration import encode_wire,decode_wire
        example=json.loads((ROOT/'wire_example.json').read_text())
        self.assertEqual(decode_wire(encode_wire(example)),example)
        legacy={k:v for k,v in example.items() if k not in ('schema_version','versions')};legacy['schema_version']=2
        migrated=migrate_legacy(legacy,bindings={},versions=V);self.assertEqual(migrated,example)
        malformed=deepcopy(example);malformed['versions']['state']=float('inf')
        with self.assertRaises(ContractError):validate_wire(malformed)
        malformed=deepcopy(example);malformed['unexpected']=True
        with self.assertRaises(ContractError):validate_wire(malformed)
        key=next(k for k in example if k not in ('schema_version','versions'));malformed=deepcopy(example);malformed[key]=object()
        with self.assertRaises(ContractError):validate_wire(malformed)
        with self.assertRaises(ContractError):decode_wire(b'{"schema_version":3,"schema_version":3}')

    def test_static_loss_ledger_and_empty_mask_contract(self):
        allowed={'EXACT','SECOND_ORDER','FIRST_ORDER','POLICY_GRADIENT','STRAIGHT_THROUGH','ENUMERATION','NONDIFFERENTIABLE'}
        tree=ast.parse((ROOT/'losses.py').read_text())
        aliases={'masked_tensor_mean'}
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                aliases.update(alias.asname or alias.name for alias in node.names if alias.name=='masked_tensor_mean')
            if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='GradientEstimator':self.assertIn(node.attr,allowed)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in aliases:
                self.assertTrue(any(k.arg=='zero_valid_policy' and isinstance(k.value,ast.Constant) and k.value.value=='differentiable_zero' for k in node.keywords))

    def test_exclusion_and_provenance_are_typed_repairs(self):
        from latent_comm.mechanisms.h46_negative_knowledge.types import DomainPredicate,NegativeWitness,ExclusionCapsule
        predicate=DomainPredicate('eq',0);witness=NegativeWitness('program_exhaustive',predicate,(0,1),None,'complete')
        capsule=ExclusionCapsule('c',predicate,(),witness,1.,'hard',(),(),'o1')
        report=self.report(domains=('a','b'));self.assertIs(exclusion_for_repair(report,capsule),capsule)
        with self.assertRaises(ContractError):exclusion_for_repair(self.report(),capsule)
        with self.assertRaises(ContractError):exclusion_for_repair(report,replace(capsule,domain_version='o2'))
        from latent_comm.mechanisms.h48_evidence_genealogy.types import InvalidationSet
        invalidation=InvalidationSet(('e',),('dependent',),True,'e1');evidence=self.report(evidence_errors={'e'})
        self.assertEqual(provenance_retraction(evidence,invalidation),('dependent',))
        with self.assertRaises(ContractError):provenance_retraction(evidence,replace(invalidation,retracted_atoms=('other',)))

    def test_recipe_api_loss_names_and_owner_edges(self):
        api=json.loads((ROOT/'training_api.json').read_text())
        adapter=ast.parse((ROOT/'adapter.py').read_text());loss_tree=ast.parse((ROOT/'losses.py').read_text())
        functions={f.name:f for f in adapter.body if isinstance(f,ast.FunctionDef) and not f.name.startswith('_')}
        self.assertEqual(set(api['forward_entries']),set(functions))
        for name,f in functions.items():
            self.assertEqual(api['forward_entries'][name]['arguments'],[a.arg for a in f.args.posonlyargs+f.args.args+f.args.kwonlyargs])
        loss_fn=next(f for f in loss_tree.body if isinstance(f,ast.FunctionDef) and f.name=='tensor_losses')
        args={a.arg for a in loss_fn.args.posonlyargs+loss_fn.args.args+loss_fn.args.kwonlyargs}
        self.assertEqual(set(api['loss_input_bindings']),args)
        returned={k.value for node in ast.walk(loss_fn) if isinstance(node,ast.Return) and isinstance(node.value,ast.Dict) for k in node.value.keys if isinstance(k,ast.Constant) and isinstance(k.value,str)}
        ledger=next(n.value for n in loss_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LEDGER' for t in n.targets))
        names={ast.literal_eval(call.args[0]) for call in ledger.elts}
        self.assertEqual(names,{row['name'] for row in api['loss_specs']});self.assertTrue(names<=returned)
        for row in api['loss_specs']:
            self.assertTrue(set(row['requires_grad_inputs'])<=args)
            self.assertTrue({edge[0] for edge in row['stop_gradient_edges']}<=args)
            self.assertTrue(set(row['parameter_owners'])<=set(api['parameter_bindings']))
            self.assertEqual(row['zero_valid_policy'],'differentiable_zero')
        config=json.loads((ROOT.parents[3]/'configs/mechanisms'/('H'+ROOT.name[1:3]+'.json')).read_text())
        self.assertEqual(config['training_integration']['forward_entry'],api['forward_entry'])
        self.assertEqual(config['training_integration']['loss_input_bindings'],api['loss_input_bindings'])
        self.assertFalse(config['research_execution_authorized'])
