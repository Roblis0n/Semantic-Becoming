import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h09_legacy.types import *
from latent_comm.mechanisms.h09_legacy.reference import *
from latent_comm.mechanisms.h09_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h09_legacy'

from dataclasses import replace
class CausalTests(unittest.TestCase):
    def world(self):return TargetSCM((CausalModule('X','u',(),(),(),0.,(('U',1.),)),CausalModule('Y','u',(),(),(),0.,(('U',1.),))),('U',),'w1')
    def test_condition_not_do(self):
        w=self.world();noise=(((('U',0.),),.5),((('U',1.),),.5))
        conditioned=query_distribution(w,noise,CausalQuery('condition',(('X',1.),),'Y',V))
        intervened=query_distribution(w,noise,CausalQuery('do',(('X',1.),),'Y',V))
        self.assertEqual(conditioned,((1.,1.),));self.assertEqual(intervened,((0.,.5),(1.,.5)))
    def test_overwrite_and_scope(self):
        a=Intervention('X',1.,'u',frozenset({'X'}),'w1');b=replace(a,value=2.)
        self.assertEqual(compose_interventions((a,b)),(b,));self.assertFalse(may_commute(self.world(),a,b))
        with self.assertRaises(ContractError):replace(a,allowed_variables=frozenset())
    def test_budget(self):
        with self.assertRaises(ContractError):query_distribution(self.world(),(((('U',0.),),1.),),CausalQuery('observe',(),'Y',V),budget=StepBudget(max_steps=1))

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
        from latent_comm.mechanisms.h09_legacy.migration import encode_wire,decode_wire
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

    def test_graft_kernel_and_intervention_query_boundaries(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h09_legacy import integration as bind
        from latent_comm.mechanisms.h31_grafting.types import GraftCertificate
        from latent_comm.mechanisms.h43_world_kernels.types import ComposedWorldKernel,SharedNoiseJoint
        world=TargetSCM((CausalModule('x','u',(),(),(),0.,()),),(),'w1');after=replace(world,version='w2');certificate=GraftCertificate(world,after,'x',(),(('x','x'),),(),('same structural variable',))
        op=Intervention('x',1.,'u',frozenset({'x'}),'w1');self.assertEqual(bind.intervention_after_graft(op,certificate).world_version,'w2')
        with self.assertRaises(ContractError):bind.intervention_after_graft(replace(op,world_version='other'),certificate)
        kernel=ComposedWorldKernel(('k',),(('a',),),(('set_x','u'),),(('set_x',((1.,),)),),(('o',),),((1.,),),SharedNoiseJoint((),(((),1.),)),(('k',()),),'w1')
        self.assertEqual(bind.kernel_action_for_intervention(op,kernel,{('x',1.,'u'):'set_x'}),'set_x')
        with self.assertRaises(ContractError):bind.kernel_action_for_intervention(op,kernel,{})
        query=CausalQuery('do',(('x',1.),),'x',V);ident=bind.intervention_identification_query((world,),(( ((),1.), ),),query,(0.,1.),query_id='test',cost=1.)
        self.assertEqual(ident.likelihood,((0.,1.),))
        with self.assertRaises(ContractError):bind.intervention_identification_query((world,),(( ((),1.), ),),replace(query,semantics='condition'),(0.,1.),query_id='test',cost=1.)

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
