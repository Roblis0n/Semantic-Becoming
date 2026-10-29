import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h20_legacy.types import *
from latent_comm.mechanisms.h20_legacy.reference import *
from latent_comm.mechanisms.h20_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h20_legacy'

from dataclasses import replace
class TestClocks(unittest.TestCase):
    def event(self,name,clock,deps=frozenset(),policy='reject'):return CognitiveEvent(name,'evidence_ready','a',clock,deps,'s1',(('state:x','1'),),0,4,policy,'payload',V)
    def test_causal_not_wall_time(self):
        a=CognitiveClock(9,'refine',0,'p',0,(('a',1),));b=CognitiveClock(1,'search',4,'q',3,(('b',1),))
        self.assertFalse(happens_before(a,b));self.assertFalse(happens_before(b,a))
        joined=tick(b,'b',physical_step=2,received=a);self.assertTrue(happens_before(a,joined))
        self.assertEqual(joined.path_index,3)
    def test_out_of_order_duplicate_and_replay(self):
        a=self.event('a',CognitiveClock(0,'refine',0,'p',0,(('x',1),)))
        b=self.event('b',CognitiveClock(0,'refine',1,'p',1,(('x',2),)),frozenset({'a'}))
        scheduler=EventScheduler(max_steps=4);scheduler.deliver(b);self.assertEqual(scheduler.advance({'state:x':'1'})[0],())
        scheduler.deliver(a);self.assertEqual(scheduler.deliver(a),'duplicate_ignored');decisions,status=scheduler.advance({'state:x':'1'})
        self.assertEqual([d.event_id for d in decisions],['a','b']);self.assertEqual(status,'complete')
        with self.assertRaises(ContractError):scheduler.deliver(replace(a,payload_ref='different'))
    def test_stale_and_never_trigger_bound(self):
        e=self.event('a',CognitiveClock(0,'refine',0,'p',0,(('x',1),)),policy='remap')
        self.assertEqual(staleness(e,{'state:x':'2'},1)[0],'remap_required')
        remap=VersionRemap('map',e.receiver_versions,(('state:x','2'),),'payload','new','certificate')
        self.assertEqual(staleness(e,{'state:x':'2'},1,(remap,)),('remapped','new'))
        scheduler=EventScheduler(max_steps=1);scheduler.deliver(replace(e,dependencies=frozenset({'missing'})))
        self.assertEqual(scheduler.advance({'state:x':'1'})[1],'schedule_budget_exhausted')
    def test_new_consumer_versions(self):
        from latent_comm.mechanisms.h39_transactions.types import CognitiveTransaction
        e=self.event('a',CognitiveClock(0,'refine',0,'p',1,(('x',1),)))
        tx=CognitiveTransaction('tx',(('state:x',1),),())
        self.assertIs(bind_transaction(e,tx),tx);self.assertEqual(bind_path_event(e,('a','b'),trajectory_version='s1'),'b')
        with self.assertRaises(ContractError):bind_path_event(e,('a','b'),trajectory_version='s2')
        with self.assertRaises(ContractError):bind_transaction(replace(e,receiver_versions=(('state:x','2'),)),tx)

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
        from latent_comm.mechanisms.h20_legacy.migration import encode_wire,decode_wire
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

    def test_dynamics_readout_is_not_wall_clock(self):
        from latent_comm.mechanisms.h33_reciprocal.types import DynamicsPacket
        packet=DynamicsPacket(((1.,),),((0.,),),(2.,),'s1',.1,2,(0,3))
        event=self.event('a',CognitiveClock(90,'settle',0,'p',0,(('x',1),)))
        self.assertEqual(bind_dynamics_event(event,packet,readout_index=1),('settle',1,'s1'))
        with self.assertRaises(ContractError):bind_dynamics_event(event,packet,readout_index=90)

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
