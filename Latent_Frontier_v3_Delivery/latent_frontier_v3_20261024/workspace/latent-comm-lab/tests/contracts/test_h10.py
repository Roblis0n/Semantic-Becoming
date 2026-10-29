import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h10_legacy.types import *
from latent_comm.mechanisms.h10_legacy.reference import *
from latent_comm.mechanisms.h10_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h10_legacy'

class HyperedgeTests(unittest.TestCase):
    def test_xor_synergy(self):
        losses={frozenset():.5,frozenset({'a'}):.5,frozenset({'b'}):.5,frozenset({'a','b'}):0.}
        self.assertEqual(subset_interaction(('a','b'),losses),.5)
        estimate=sampled_interaction(('a','b'),losses,samples=16,seed=3);self.assertFalse(estimate['exact']);self.assertIsNotNone(estimate['sample_variance'])
    def test_joint_not_additive(self):
        e=Hyperedge('h',('a','b'),(((1.,),),((1.,),)),((1.,),),(('a',frozenset({'same'})),('b',frozenset({'same'}))),V)
        self.assertEqual(compose_hyperedge(e,{'a':(-1.,),'b':(-1.,)}),(1.,));self.assertEqual(independent_support_count(e),1)
        with self.assertRaises(ContractError):compose_hyperedge(e,{'a':(-1.,)})
    def test_unknown_subset(self):
        with self.assertRaises(ContractError):subset_interaction(('a','b'),{})

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
        from latent_comm.mechanisms.h10_legacy.migration import encode_wire,decode_wire
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

    def test_coalition_ecology_and_evidence_consumers(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h10_legacy import integration as bind
        from latent_comm.mechanisms.h41_coalitions.reference import exact_shapley
        from latent_comm.mechanisms.h42_ecology.types import TaskGenome,ProtocolGenome
        from latent_comm.mechanisms.h48_evidence_genealogy.types import EvidenceAtom
        edge=Hyperedge('edge',('a','b'),(((1.,),),((1.,),)),((1.,),),(('a',frozenset({'e'})),('b',frozenset({'e'}))),V)
        game=bind.coalition_from_subset_losses(edge,{frozenset():1.,frozenset({'a'}):1.,frozenset({'b'}):1.,frozenset({'a','b'}):0.},value_version='v');credit=exact_shapley(game);self.assertAlmostEqual(sum(v for _,v in credit.contributions),1.)
        with self.assertRaises(ContractError):bind.coalition_from_subset_losses(edge,{frozenset({'c'}):0.},value_version='v')
        protocols=(ProtocolGenome('a',('add',),(),(),'p'),ProtocolGenome('b',('inverse',),(),(),'p'));task=TaskGenome('t','add',1.,False,0.,True,(),'t1')
        self.assertEqual(bind.population_expressibility(edge,protocols,task)[0],())
        with self.assertRaises(ContractError):bind.population_expressibility(edge,protocols,replace(task,version='other'))
        graph=bind.hyperedge_provenance(edge,(EvidenceAtom('e','source','observed',None),));self.assertEqual(len(graph.atoms),1)
        with self.assertRaises(ContractError):bind.hyperedge_provenance(edge,())

    def test_typed_hyperedge_wire_matrix_and_atom_identity(self):
        from latent_comm.mechanisms.h10_legacy.migration import encode_hyperedge,decode_hyperedge
        edge=Hyperedge('h',('a','b'),(((1.,),),((2.,),)),((3.,),),(('a',frozenset({'e'})),('b',frozenset({'e'}))),V)
        restored,kind=decode_hyperedge(encode_hyperedge(edge,value_function='negative_task_loss'),edge_id='h')
        self.assertEqual(restored,edge);self.assertEqual(kind,'negative_task_loss');self.assertEqual(unique_support_count(restored),1)

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
