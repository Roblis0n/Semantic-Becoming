import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h02_legacy.types import *
from latent_comm.mechanisms.h02_legacy.reference import *
from latent_comm.mechanisms.h02_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h02_legacy'

class ResponseTests(unittest.TestCase):
    def capsule(self):
        program=QuadraticProgram(((0.,0.),),(((2.,0.),(0.,2.)),),(0.,))
        return build_capsule(program,(1.,2.),directions=((1.,0.),(0.,1.)),step=.01,radius=.5,variables=('x','y'),conditions=('public variables only',),versions=V)
    def test_derivative_and_radius(self):
        c=self.capsule();self.assertAlmostEqual(c.A[0][0],2.,places=8);self.assertAlmostEqual(c.A[0][1],4.,places=8)
        self.assertAlmostEqual(predict_delta(c,(.1,.1)).value[0],5.6)
        self.assertTrue(predict_delta(c,(1.,0.)).needs_refresh);self.assertIsNone(predict_delta(c,(1.,0.)).value)
    def test_chain_and_invalid_basis(self):
        c=self.capsule();second=ResponseCapsule(c.base,(10.,),((2.,),),((1.,),),1.,('z',),('local',),'observational',V)
        self.assertIn('error_unbounded',compose_response(c,second).approximation)
        with self.assertRaises(ContractError):build_capsule(QuadraticProgram(((1.,),),(((0.,),),),(0.,)),(0.,),directions=((2.,),),step=.1,radius=1.,variables=('x',),conditions=(),versions=V)
    def test_no_causal_inference(self):
        from dataclasses import replace
        with self.assertRaises(ContractError):replace(self.capsule(),response_kind='structural_intervention',observation_conditions=())
        self.assertEqual(self.capsule().response_kind,'observational')

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
        from latent_comm.mechanisms.h02_legacy.migration import encode_wire,decode_wire
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

    def test_scm_kernel_and_identification_consumers(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h02_legacy import integration as bind
        from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM
        from latent_comm.mechanisms.h43_world_kernels.types import ComposedWorldKernel,SharedNoiseJoint
        world=TargetSCM((CausalModule('x','u',(),(),(),0.,()),CausalModule('y','u',('x',),('u',),(2.,),0.,())),(),'w1')
        capsule=bind.response_from_scm(world,{},('x',),(1.,),('y',),radius=1.,versions=V);self.assertEqual(predict(capsule,(1.5,)).value,(3.,))
        with self.assertRaises(ContractError):bind.response_from_scm(world,{},('x',),(1.,),('y',),radius=1.,versions=replace(V,world='wrong'))
        kernel=ComposedWorldKernel(('k',),(('a',),('b',)),(('stay','none'),),(('stay',((1.,0.),(0.,1.))),),(('a',),('b',)),((1.,0.),(0.,1.)),SharedNoiseJoint((),(((),1.),)),(),'w1')
        response=bind.response_from_kernel(kernel,'stay',(.5,.5),radius=1.,versions=V);self.assertEqual(predict(response,(.75,.25)).value,(.75,.25))
        with self.assertRaises(ContractError):bind.response_from_kernel(kernel,'missing',(.5,.5),radius=1.,versions=V)
        query=bind.query_likelihood_from_responses((response,),(.75,.25),query_id='query',responses=('a','b'),cost=1.);self.assertEqual(query.likelihood,((.75,.25),))
        with self.assertRaises(ContractError):bind.query_likelihood_from_responses((response,),(3.,-2.),query_id='query',responses=('a','b'),cost=1.)

    def test_tensor_basis_guard_is_present_without_tensor_import(self):
        tree=ast.parse((ROOT/'adapter.py').read_text());acquire=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='acquire_response')
        checks=[n for n in ast.walk(acquire) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='allclose']
        self.assertEqual(len(checks),1)
        self.assertIn('orthonormal',ast.get_source_segment((ROOT/'adapter.py').read_text(),acquire))

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
