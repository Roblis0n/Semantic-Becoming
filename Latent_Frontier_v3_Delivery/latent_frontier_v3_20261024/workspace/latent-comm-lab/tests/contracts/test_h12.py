import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h12_legacy.types import *
from latent_comm.mechanisms.h12_legacy.reference import *
from latent_comm.mechanisms.h12_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h12_legacy'

class CapsuleTests(unittest.TestCase):
    def capsule(self):return build_capsule({'a':1.,'b':3.},capsule_id='c1',document_id='d',version='1',query_family=('sum','lookup'),evidence=('e',),dependencies={'source':'1'},expires_step=5,versions=V)
    def test_future_queries_and_unknown(self):
        c=self.capsule();args={'step':0,'versions':V,'current_dependencies':{'source':'1'}}
        self.assertEqual(read_query(c,('sum',None),**args).value,4.)
        self.assertEqual(read_query(c,('lookup','a'),**args).value,1.)
        self.assertTrue(read_query(c,('variance',None),**args).source_lookup_required)
        with self.assertRaises(ContractError):read_query(c,('sum',None),step=6,versions=V,current_dependencies={'source':'1'})
    def test_retraction_and_atomic_persistence(self):
        from tempfile import TemporaryDirectory
        from latent_comm.runtime.files import AtomicWorkspace
        store=CapsuleStore();store.add(self.capsule())
        with TemporaryDirectory() as root:
            with AtomicWorkspace(root) as work:store.persist(work);restored=CapsuleStore.restore(work);self.assertEqual(restored.get('d','1'),self.capsule())
        store.withdraw({'e'})
        with self.assertRaises(ContractError):store.get('d','1')
    def test_version_is_immutable(self):
        store=CapsuleStore();store.add(self.capsule())
        with self.assertRaises(ContractError):store.add(self.capsule())

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


    def test_wire_roundtrip_explicit_migration_and_bad_types(self):
        from copy import deepcopy
        from latent_comm.mechanisms.h12_legacy.migration import encode_wire,decode_wire
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

    def test_dependency_retraction_propagates_and_restore_rejects_cycle(self):
        from dataclasses import replace
        from tempfile import TemporaryDirectory
        from latent_comm.runtime.files import AtomicWorkspace
        store=CapsuleStore();base=self.capsule();store.add(base)
        derived=replace(base,capsule_id='c2',document_id='derived',version='2',evidence_handles=frozenset({'other'}),capsule_dependencies=(('d','1'),));store.add(derived)
        self.assertIn(('derived','2'),store.withdraw({'e'}))
        with self.assertRaises(ContractError):store.get('derived','2')
        with TemporaryDirectory() as root:
            with AtomicWorkspace(root) as work:
                store.persist(work);restored=CapsuleStore.restore(work)
                with self.assertRaises(ContractError):restored.get('derived','2')

    def test_ontology_transaction_and_genealogy_consumers(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h12_legacy import integration as bind
        from latent_comm.mechanisms.h27_ontology.types import OntologySnapshot,OntologyDelta,ConceptDefinition,Predicate
        from latent_comm.mechanisms.h48_evidence_genealogy.types import InvalidationSet
        capsule=self.capsule()
        concepts=tuple(ConceptDefinition(name,Predicate('eq','observable',i),(),('e',),('observable',)) for i,name in enumerate(('a','b')))
        targets=tuple(replace(c,concept_id='new_'+c.concept_id) for c in concepts)
        delta=OntologyDelta(OntologySnapshot('o1',concepts),OntologySnapshot('o2',targets),(('c1','a','new_a'),('c1','b','new_b')),())
        migrated=bind.migrate_capsule_ontology(capsule,delta,new_version='2');self.assertEqual(migrated.versions.ontology,'o2');self.assertEqual(migrated.capsule_dependencies,(('d','1'),))
        with self.assertRaises(ContractError):bind.migrate_capsule_ontology(capsule,replace(delta,reader_migrations=()),new_version='2')
        tx=bind.capsule_transaction(capsule,previous_cell_version=0);self.assertEqual(tx.writes[0].version,1)
        store=CapsuleStore();store.add(capsule);self.assertIn(('d','1'),bind.retract_capsule_sources(store,InvalidationSet(('e',),('root',),True,'e1'),evidence_version='e1'))
        with self.assertRaises(ContractError):bind.retract_capsule_sources(store,InvalidationSet(('e',),('root',),True,'wrong'),evidence_version='e1')

    def test_dependency_identity_is_in_cache_key(self):
        from dataclasses import replace
        capsule=self.capsule()
        self.assertNotEqual(cache_key(capsule,'sum'),cache_key(replace(capsule,capsule_dependencies=(('source-doc','1'),)),'sum'))

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
