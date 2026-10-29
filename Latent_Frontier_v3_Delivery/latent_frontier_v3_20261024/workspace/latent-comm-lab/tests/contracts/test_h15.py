import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h15_legacy.types import *
from latent_comm.mechanisms.h15_legacy.reference import *
from latent_comm.mechanisms.h15_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h15_legacy'

class PopulationTests(unittest.TestCase):
    def member(self,name,trained=True):return ProtocolMember(name,'rev1','tok:'+name,((1.,0.),),((1.,),(2.,)),frozenset({'operator'}),('action1',),trained,V)
    def test_heldout_and_dropout(self):
        members=tuple(self.member(x) for x in 'abc');plan=sample_pairs(members,held_out_pairs={('a','b')},required={'operator'},count=8,seed=3,receiver_dropout={'c'})
        self.assertNotIn(('a','b'),plan.pairs);self.assertTrue(all(b!='c' for a,b in plan.pairs))
    def test_heterogeneous_tokenizers_not_logits(self):
        self.assertEqual(transmit(self.member('a'),self.member('b'),(3.,4.),required={'operator'}),(3.,6.))
        with self.assertRaises(ContractError):transmit(self.member('a'),self.member('new',False),(3.,4.),required={'operator'})
        self.assertEqual(coverage((self.member('a'),self.member('b')),())['unseen_pairs'],(('a','b'),('b','a')))

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
        from latent_comm.mechanisms.h15_legacy.migration import encode_wire,decode_wire
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

    def test_gauge_learning_and_quotient_boundaries(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h15_legacy import integration as bind
        from latent_comm.mechanisms.h25_gauge.types import FrameSpec
        from latent_comm.mechanisms.h37_gradient_transport.types import Linearization,BehaviorAnchorSet
        from latent_comm.mechanisms.h47_quotient.types import StateDomain,FiniteQuery
        from latent_comm.mechanisms.h47_quotient.reference import form_quotient
        member=ProtocolMember('m','rev','token',((2.,),),((3.,),),frozenset({'prefix'}),('behavior',),True,V);source=FrameSpec('a',1,'GL','f1');target=FrameSpec('b',1,'GL','f2');moved=bind.gauge_protocol_member(member,((2.,),),source,target);self.assertEqual(moved.writer,((4.,),));self.assertEqual(moved.reader,((1.5,),))
        with self.assertRaises(ContractError):bind.gauge_protocol_member(member,((2.,),),target,source)
        linearization=Linearization(((1.,),),BehaviorAnchorSet(('behavior',),'t1'),('adapter.w',),'rev');self.assertIs(bind.learning_effect_boundary(member,linearization),linearization)
        with self.assertRaises(ContractError):bind.learning_effect_boundary(member,replace(linearization,parameter_version='wrong'))
        quotient=form_quotient(StateDomain(('one','three'),(1,3),'s1'),(FiniteQuery('parity','parity',0,'t1'),),'q1');self.assertEqual(bind.quotient_protocol_boundary(member,quotient,supported_queries={'parity'}),((1,),))
        with self.assertRaises(ContractError):bind.quotient_protocol_boundary(member,quotient,supported_queries=set())

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
