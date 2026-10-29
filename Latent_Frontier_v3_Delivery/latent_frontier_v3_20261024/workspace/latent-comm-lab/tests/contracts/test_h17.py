import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h17_legacy.types import *
from latent_comm.mechanisms.h17_legacy.reference import *
from latent_comm.mechanisms.h17_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h17_legacy'

from dataclasses import replace
class GroundingTests(unittest.TestCase):
    def frames(self):return PhysicalFrame('physical:cm','cm','right','camera1','latent:a'),PhysicalFrame('physical:m','m','left','camera2','latent:b')
    def test_units_handedness_covariance(self):
        a,b=self.frames();t=FrameTransform(a,b,((-1.,0.),(0.,1.)),(1.,0.),.01)
        obj=GroundedObject('object1',(100.,0.),((4.,0.),(0.,4.)),a,0.,'observed',V)
        out=transform_object(obj,t,target_versions=replace(V,frame='f2'));self.assertEqual(out.position,(0.,0.));self.assertAlmostEqual(out.covariance[0][0],.0004)
        self.assertEqual(transform_displacement((100.,0.),t),(-1.,0.))
    def test_occlusion_and_bad_units(self):
        a,b=self.frames();obj=GroundedObject('x',None,None,a,0.,'occluded',V)
        with self.assertRaises(ContractError):apply_synthetic_action(obj,(1.,0.),unit='cm',next_timestamp=1.)
        with self.assertRaises(ContractError):FrameTransform(a,b,((1.,0.),(0.,1.)),(0.,0.),1.)

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
        from latent_comm.mechanisms.h17_legacy.migration import encode_wire,decode_wire
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

    def test_covariance_head_has_explicit_loss_path_source(self):
        tree=ast.parse((ROOT/'losses.py').read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='tensor_losses')
        self.assertIn('aligned_covariances',{a.arg for a in function.args.kwonlyargs})
        self.assertIn('covariance_target',{a.arg for a in function.args.kwonlyargs})
        returned=next(n for n in ast.walk(function) if isinstance(n,ast.Return))
        self.assertIn('covariance',[k.value for k in returned.value.keys])

    def test_physical_and_latent_consumer_boundaries(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h17_legacy import integration as bind
        from latent_comm.mechanisms.h25_gauge.types import FrameSpec
        from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM
        from latent_comm.mechanisms.h43_world_kernels.types import ComposedWorldKernel,SharedNoiseJoint
        frame=PhysicalFrame('physical','m','right','camera','latent:a');obj=GroundedObject('object',(1.,2.),((1.,0.),(0.,1.)),frame,0.,'observed',V);source=FrameSpec('latent:a',1,'GL','f1');target=FrameSpec('latent:b',1,'GL','f2');moved,z=bind.transport_latent_frame_only(obj,(2.,),((3.,),),source,target);self.assertEqual(z,(6.,));self.assertEqual(moved.position,obj.position);self.assertEqual(moved.frame.unit,'m')
        with self.assertRaises(ContractError):bind.transport_latent_frame_only(obj,(2.,),((3.,),),target,source)
        world=TargetSCM((CausalModule('x','m',(),(),(),0.,()),),(),'w1');self.assertEqual(bind.coordinate_intervention(obj,0,world,'x',allowed_variables={'x'}).value,1.)
        with self.assertRaises(ContractError):bind.coordinate_intervention(obj,2,world,'x',allowed_variables={'x'})
        kernel=ComposedWorldKernel(('k',),(('s',),),(('stay','u'),),(('stay',((1.,),)),),(('seen',),),((1.,),),SharedNoiseJoint((),(((),1.),)),(('k',()),),'w1');row,label=bind.predicted_observation_row(obj,kernel,('s',));self.assertEqual(row,(1.,));self.assertEqual(label,'model_prediction_not_real_observation')
        with self.assertRaises(ContractError):bind.predicted_observation_row(obj,kernel,('absent',))

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
