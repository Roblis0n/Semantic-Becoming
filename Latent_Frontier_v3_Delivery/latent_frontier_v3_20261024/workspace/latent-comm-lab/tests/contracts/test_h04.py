import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h04_legacy.types import *
from latent_comm.mechanisms.h04_legacy.reference import *
from latent_comm.mechanisms.h04_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h04_legacy'

class FieldTests(unittest.TestCase):
    def field(self):
        return ConstraintField((LocalConstraint('a',((1.,),),(1.,),1.,'d','f1','s0',frozenset({'e1'})),LocalConstraint('b',((1.,),),(-1.,),1.,'d','f1','s1',frozenset({'e2'}))),(0.,),.1,'d',V)
    def test_conflict_not_consensus(self):
        f=self.field();r=solve_field(f,steps=8,step_size=.1)
        self.assertEqual(r.state,(0.,));self.assertEqual(set(r.conflicts),{'a','b'});self.assertFalse(exact_compatibility(f)['compatible'])
        self.assertEqual(r.stop_reason,'stationary_not_truth')
    def test_trajectory_and_bad_step(self):
        from dataclasses import replace
        f=replace(self.field(),sources=(self.field().sources[0],));r=solve_field(f,steps=10,step_size=.1)
        self.assertLess(energy(f,r.state),energy(f,f.anchor))
        with self.assertRaises(ContractError):solve_field(f,steps=10,step_size=5.)
        with self.assertRaises(ContractError):replace(f,anchor_strength=0.)
    def test_noncommon_domain(self):
        from dataclasses import replace
        with self.assertRaises(ContractError):replace(self.field(),domain='different')

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
        from latent_comm.mechanisms.h04_legacy.migration import encode_wire,decode_wire
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

    def test_field_sheaf_dynamics_and_public_trajectory(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h04_legacy import integration as bind
        from latent_comm.mechanisms.h26_sheaf.reference import glue
        from latent_comm.mechanisms.h34_boundary_value.types import TrajectoryFactorGraph,PublicTerminalConstraint
        field=ConstraintField((LocalConstraint('source',((1.,),),(2.,),1.,'x','f1','s1',frozenset({'e'})),),(0.,),1.,'x',V)
        sheaf=bind.field_feasibility_sheaf(field);self.assertEqual(glue(sheaf).status,'CompatibleOnDeclaredOverlaps')
        dynamics,center=bind.field_as_centered_dynamics(field,step_size=.1,steps=2);self.assertAlmostEqual(center[0],2/3);self.assertAlmostEqual(dynamics.dissipation[0][0],3.)
        graph=TrajectoryFactorGraph(('a','b'),((('a','b'),),),('a',),PublicTerminalConstraint(('b',),'public_goal','t1'),'s1')
        energies=bind.score_trajectory_states(field,graph,{'a':(0.,),'b':(1.,)});self.assertEqual(len(energies),2)
        with self.assertRaises(ContractError):bind.score_trajectory_states(field,replace(graph,version='wrong'),{'a':(0.,),'b':(1.,)})

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
