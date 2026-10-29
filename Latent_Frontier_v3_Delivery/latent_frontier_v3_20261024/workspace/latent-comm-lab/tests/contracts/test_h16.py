import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h16_legacy.types import *
from latent_comm.mechanisms.h16_legacy.reference import *
from latent_comm.mechanisms.h16_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h16_legacy'

from latent_comm.core import ObjectRef
class SymbolTests(unittest.TestCase):
    def symbol(self,value='0.10'):return Symbol('amount','decimal',value,'USD',ObjectRef('source:1'),'public')
    def test_decimal_and_authority(self):
        p=SymbolPacket((self.symbol(),),ObjectRef('latent:1'),V)
        result=fuse(p,(1.,),(self.symbol('0.11'),));self.assertEqual(result.exact_symbols[0].value,'0.10');self.assertTrue(result.conflicts)
        self.assertFalse(fuse(p,(1.,),(self.symbol('0.100'),)).conflicts);self.assertGreater(wire_size(p,8),8)
    def test_supervision_and_bad_symbol(self):
        with self.assertRaises(ContractError):Symbol('label','decimal','1','unit',ObjectRef('source:1'),'public')
        with self.assertRaises(ContractError):self.symbol('NaN')
        with self.assertRaises(Exception):parse_symbols('{"symbols":[],"symbols":[],"latent_handle":"latent:1","versions":{}}')
        with self.assertRaises(ContractError):parse_symbols(b'\xff')

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
        from latent_comm.mechanisms.h16_legacy.migration import encode_wire,decode_wire
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

    def test_entity_target_is_a_recursive_typed_reference(self):
        from latent_comm.core import ObjectRegistry,RegisteredObject,ObjectRef,Scope,Visibility
        scope=Scope('symbols',frozenset({'reader'}),frozenset())
        registry=ObjectRegistry();source=ObjectRef('source:registered');target=ObjectRef('entity:missing')
        registry.register(RegisteredObject(source,'source','evidence',V,('evidence',),scope,Visibility.PUBLIC))
        symbol=Symbol('entity','entity',target.value,'',source,'public');self.assertEqual(symbol.target_ref,target)
        with self.assertRaises(ContractError):registry.register(RegisteredObject(ObjectRef('symbol:bad'),'symbol',symbol,V,('evidence',),scope,Visibility.PUBLIC,(source,)))
        registry.register(RegisteredObject(target,'entity','object',V,('ontology',),scope,Visibility.PUBLIC))
        registry.register(RegisteredObject(ObjectRef('symbol:good'),'symbol',symbol,V,('evidence',),scope,Visibility.PUBLIC,(source,target)))
        self.assertEqual(registry.resolve(ObjectRef('symbol:good'),expected_type='symbol',versions=V,actor='reader',role=Visibility.RECEIVER),symbol)

    def test_exact_relation_intervention_and_source_bindings(self):
        from dataclasses import replace
        from latent_comm.core import ObjectRef
        from latent_comm.mechanisms.h16_legacy import integration as bind
        from latent_comm.mechanisms.h29_questions.types import RelationWitness
        from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM
        from latent_comm.mechanisms.h48_evidence_genealogy.types import EvidenceAtom,SupportNode,ProvenanceGraph
        symbol=Symbol('relation','relation','equivalent','',ObjectRef('source:e'),'public');witness=RelationWitness('equivalent',True,True,(),(),(),(),());self.assertEqual(bind.checked_answer_relation(symbol,witness),'equivalent')
        with self.assertRaises(ContractError):bind.checked_answer_relation(symbol,replace(witness,sound=False))
        decimal=Symbol('x','decimal','0.5','m',ObjectRef('source:e'),'public');world=TargetSCM((CausalModule('x','m',(),(),(),0.,()),),(),'w1');self.assertEqual(bind.exact_symbol_intervention(decimal,world,allowed_variables={'x'}).value,.5)
        with self.assertRaises(ContractError):bind.exact_symbol_intervention(replace(decimal,value='0.1'),world,allowed_variables={'x'})
        graph=ProvenanceGraph((EvidenceAtom('e','source:e','observed',None),),(SupportNode('n','atom',(),'e'),),'n','e1');self.assertEqual(len(bind.symbol_source_atoms(decimal,graph)),1)
        with self.assertRaises(ContractError):bind.symbol_source_atoms(replace(decimal,source=ObjectRef('source:other')),graph)

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
