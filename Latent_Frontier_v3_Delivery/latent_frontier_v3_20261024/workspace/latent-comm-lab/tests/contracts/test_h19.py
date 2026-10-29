import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h19_legacy.types import *
from latent_comm.mechanisms.h19_legacy.reference import *
from latent_comm.mechanisms.h19_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h19_legacy'

from dataclasses import replace
import tempfile
from latent_comm.runtime.files import AtomicWorkspace
class TestConsolidation(unittest.TestCase):
    def artifact(self,version,parent=None):return ConsolidatedAdapter('a',version,parent,'sha256:fixed',frozenset({'trace'}),frozenset({'instance'}),frozenset({'source'}),frozenset({'adapter.weight'}),'family','base',V)
    def test_ordered_compilation_and_no_message(self):
        skill=compile_affine_operations((('scale',((2.,),),(0.,)),('shift',((1.,),),(3.,))))
        self.assertEqual(apply_skill(skill,(4.,)),(11.,));self.assertEqual(skill.source_operations,('scale','shift'))
    def test_persistent_rollback_retraction(self):
        store=AdapterHistory();store.register(self.artifact('1'));store.register(self.artifact('2','1'));store.activate('a','2',base_revision='base',versions=V)
        with tempfile.TemporaryDirectory() as tmp:
            with AtomicWorkspace(tmp) as ws:store.persist(ws);restored=AdapterHistory.restore(ws)
        self.assertEqual(restored.rollback('a',base_revision='base',versions=V).version,'1');restored.withdraw({'source'})
        with self.assertRaises(ContractError):restored.activate('a','1',base_revision='base',versions=V)
    def test_sources_and_connections(self):
        trace=TeacherTrace('trace','instance','message',('op',),frozenset({'source'}),'family','base',10,V)
        self.assertEqual(validate_training_partition((trace,),{'new'},step=2,versions=V),frozenset({'trace'}))
        with self.assertRaises(ContractError):validate_training_partition((trace,),{'instance'},step=2,versions=V)
        from latent_comm.mechanisms.h37_gradient_transport.types import BehaviorAnchorSet,Linearization
        lin=Linearization(((1.,),),BehaviorAnchorSet(('p',),'t1'),('adapter.weight',),'1')
        self.assertIs(bind_learning_effect(self.artifact('1'),lin),lin)
        with self.assertRaises(ContractError):bind_learning_effect(self.artifact('2'),lin)
        from latent_comm.mechanisms.h38_plasticity.types import PlasticityProgram,RuleNode
        rule=PlasticityProgram(RuleNode('read',slot='gradient'),('adapter.weight',),1.,1,1,'rule','first_order')
        self.assertIs(bind_update_rule(self.artifact('1'),rule),rule)
        self.assertEqual(macro_provenance(self.artifact('1'),'macro',source_trace_ids={'trace'},isa_version='i1')['adapter_version'],'1')
        with self.assertRaises(ContractError):macro_provenance(self.artifact('1'),'macro',source_trace_ids={'other'},isa_version='i1')

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
        from latent_comm.mechanisms.h19_legacy.migration import encode_wire,decode_wire
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

    def test_rule_binding_validates_actual_ast(self):
        from latent_comm.mechanisms.h38_plasticity.types import PlasticityProgram,RuleNode
        for ast_node,groups in ((RuleNode('read',slot='query_labels'),('adapter.weight',)),(RuleNode('read',slot='gradient'),('adapter.other',))):
            rule=PlasticityProgram(ast_node,groups,1.,1,1,'r','first_order')
            with self.assertRaises(ContractError):bind_update_rule(self.artifact('1'),rule)

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
