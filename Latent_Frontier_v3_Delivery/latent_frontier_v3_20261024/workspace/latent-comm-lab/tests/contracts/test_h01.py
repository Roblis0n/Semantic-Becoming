import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h01_legacy.types import *
from latent_comm.mechanisms.h01_legacy.reference import *
from latent_comm.mechanisms.h01_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h01_legacy'

from latent_comm.core import Scope
from dataclasses import replace
S=Scope('operator',frozenset({'receiver'}),frozenset({'Z'}))
VSET=V

class OperatorTests(unittest.TestCase):
    def packet(self,U,V,b=(0.,),activation='relu'):
        return OperatorPacket(U,V,b,1.,activation,'state','state',VSET,S)
    def test_order_not_factor_addition(self):
        a=self.packet(((1.,),(0.,)),((0.,),(1.,)))
        b=self.packet(((0.,),(1.,)),((1.,),(0.,)))
        ab=apply((1.,2.),compose(chain(a),chain(b)))[0]
        ba=apply((1.,2.),compose(chain(b),chain(a)))[0]
        self.assertEqual(ab,(3.,5.));self.assertEqual(ba,(4.,3.));self.assertNotEqual(ab,ba)
    def test_identity_immutable_and_budget(self):
        z=(1.,2.);self.assertEqual(apply(z,identity(2,'state',V))[0],z)
        p=self.packet(((1.,),(0.,)),((0.,),(1.,)))
        with self.assertRaises(ContractError):apply(z,compose(chain(p),chain(p)),budget=StepBudget(max_steps=1))
    def test_frame_transport_nonlinear(self):
        p=self.packet(((1.,),(2.,)),((.5,),(1.,)),(.3,),'tanh');g=((0.,1.),(1.,0.))
        q=change_frame(p,g,replace(V,frame='f2'))
        self.assertEqual(tuple(reversed(apply((1.,2.),p)[0])),apply((2.,1.),q)[0])
        with self.assertRaises(ContractError):change_frame(p,((1.,0.),(0.,0.)),replace(V,frame='f2'))
        with self.assertRaises(ContractError):compose(chain(p),chain(q))
    def test_scope_and_migration(self):
        p=self.packet(((1.,),(0.,)),((0.,),(1.,)))
        with self.assertRaises(ContractError):apply((1.,2.),p,actor='other')
        record={'schema_version':2,'U':[[1.]],'V':[[1.]],'bias':[0.],'alpha':1.,'nonlinearity':'relu'}
        out=migrate_legacy(record,bindings={'domain':'state','codomain':'state','scope':{'scope_id':'scope','readers':['receiver'],'writable_components':['Z']},'target':'working_slot'},versions=V)
        self.assertEqual(validate_wire(out),V)

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
        from latent_comm.mechanisms.h01_legacy.migration import encode_wire,decode_wire
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

    def test_explicit_consumers_gauge_analogy_scale_macro(self):
        from dataclasses import replace
        from latent_comm.core import Scope
        from latent_comm.mechanisms.h01_legacy import integration as bind
        from latent_comm.mechanisms.h25_gauge.types import FrameSpec
        from latent_comm.mechanisms.h35_renormalization.types import ScalePacket
        from latent_comm.mechanisms.h40_instruction_set.reference import execute_base
        op=OperatorPacket(((1.,),),((0.,),),(0.,),1.,'identity','scalar','scalar',V,Scope('s',frozenset({'receiver'}),frozenset({'Z'})))
        source=FrameSpec('source',1,'GL','f1');target=FrameSpec('target',1,'GL','f2')
        moved=bind.gauge_operator(op,((2.,),),source,target);self.assertEqual(moved.versions.frame,'f2')
        with self.assertRaises(ContractError):bind.gauge_operator(op,((2.,),),target,source)
        graph=bind.finite_operation_graph(op,(('one',(1.,)),('two',(2.,))),operation_name='identity',version='i1');self.assertEqual(graph.operations[0].table,(('one','one'),('two','two')))
        with self.assertRaises(ContractError):bind.finite_operation_graph(op,(('one',(1.,)),),operation_name='identity',version='wrong')
        scale=ScalePacket(((1.,),),((1.,),),((1.,),),(0.,),((1.,),),(0.,),('x',),('x',),'s1','s2')
        residual,label=bind.coarse_effect_check(op,replace(op,versions=replace(V,state='s2')),scale,((1.,),));self.assertEqual(residual,((0.,),))
        with self.assertRaises(ContractError):bind.coarse_effect_check(op,op,scale,((1.,),))
        macro=bind.scalar_affine_macro(op,name='identity',source_isa='i1');self.assertEqual(execute_base(macro.body,{'x':2.}),2.)
        with self.assertRaises(ContractError):bind.scalar_affine_macro(replace(op,nonlinearity='tanh'),name='nonlinear',source_isa='i1')

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
