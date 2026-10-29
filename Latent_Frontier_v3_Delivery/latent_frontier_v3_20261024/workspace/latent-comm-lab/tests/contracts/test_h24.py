import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h24_legacy.types import *
from latent_comm.mechanisms.h24_legacy.reference import *
from latent_comm.mechanisms.h24_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h24_legacy'

from dataclasses import replace
class TestCapabilities(unittest.TestCase):
    def grant(self):return CapabilityGrant('cap','actor','session',frozenset({'state:x'}),frozenset({'state:x'}),frozenset({'scalar'}),5,frozenset({'e'}),frozenset({'view'}),frozenset({'adapter.w'}),frozenset({'macro'}),frozenset({'state:x'}),'goalhash',V)
    def store(self):return ScopedStateStore((ScopedCell('state:x','scalar',(2.,),'session','s1'),ScopedCell('state:secret','scalar',(9.,),'session','s1')),(('alias','state:secret'),))
    def effect(self,read='state:x',write='state:x'):return ScopedEffect('cap','add_affine',(read,),(write,),((2.,),),(1.,),'scalar')
    def test_effect_and_protected_identity(self):
        store=self.store();authority=CapabilityAuthority((self.grant(),),session_id='session');audit=store.apply(self.effect(),authority,principal='actor',step=1,versions=V,new_version='s2')
        self.assertEqual(store.cells['state:x'].value,(7.,));self.assertEqual(store.cells['state:secret'].value,(9.,));self.assertEqual(audit.written_slots,('state:x',))
    def test_alias_expiry_cross_session_and_forged_header(self):
        for effect,step in ((self.effect(read='alias'),1),(self.effect(),6),(replace(self.effect(),capability_id='forged'),1)):
            store=self.store();authority=CapabilityAuthority((self.grant(),),session_id='session')
            with self.assertRaises(ContractError):store.apply(effect,authority,principal='actor',step=step,versions=V,new_version='s2')
            self.assertEqual(store.cells['state:x'].value,(2.,))
        with self.assertRaises(ContractError):CapabilityAuthority((self.grant(),),session_id='other')
        with self.assertRaises(ContractError):ScopedStateStore(tuple(self.store().cells.values()),(('a','b'),('b','a')))
    def test_narrowing_and_integration_scopes(self):
        authority=CapabilityAuthority((self.grant(),),session_id='session');child=replace(self.grant(),capability_id='child',writable_slots=frozenset(),expires_step=3);authority.narrow('cap',child)
        with self.assertRaises(ContractError):authority.narrow('cap',replace(child,capability_id='bad',readable_slots=child.readable_slots|{'state:secret'}))
        self.assertTrue(check_macro(self.grant(),required_capabilities={'macro'},expanded_read_slots={'state:x'},expanded_write_slots={'state:x'}))
        with self.assertRaises(ContractError):check_macro(self.grant(),required_capabilities={'macro'},expanded_read_slots={'state:secret'},expanded_write_slots=())
        from latent_comm.mechanisms.h39_transactions.types import CognitiveTransaction,VersionedCell
        tx=CognitiveTransaction('t',(('state:x',0),),(VersionedCell('state:x','scalar',1,'2'),));self.assertIs(check_transaction(self.grant(),tx),tx)
        with self.assertRaises(ContractError):check_transaction(replace(self.grant(),transaction_writes=frozenset()),tx)

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

    def test_parent_revocation_reaches_derived_grants(self):
        authority=CapabilityAuthority((self.grant(),),session_id='session')
        child=replace(self.grant(),capability_id='child');grandchild=replace(child,capability_id='grandchild')
        authority.narrow('cap',child);authority.narrow('child',grandchild);authority.revoke('cap')
        for capability in ('cap','child','grandchild'):
            with self.assertRaises(ContractError):authority.resolve(capability,principal='actor',step=1,versions=V)

    def test_wire_roundtrip_explicit_migration_and_bad_types(self):
        from copy import deepcopy
        from latent_comm.mechanisms.h24_legacy.migration import encode_wire,decode_wire
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

    def test_goal_view_and_update_rule_grants(self):
        from latent_comm.mechanisms.h32_perspective.types import GoalPreservingView
        view=GoalPreservingView('goalhash',(1.,),(1.,),(0.,),1.,1.,'preserved',True,'v1','v2')
        self.assertIs(check_objective_view(self.grant(),view,view_id='view'),view)
        with self.assertRaises(ContractError):check_objective_view(self.grant(),replace(view,goal_digest='other'),view_id='view')
        from latent_comm.mechanisms.h38_plasticity.types import RuleNode,PlasticityProgram
        rule=PlasticityProgram(RuleNode('read',slot='gradient'),('adapter.w',),1.,1,1,'r','first_order')
        self.assertIs(check_update_rule(self.grant(),rule),rule)
        with self.assertRaises(ContractError):check_update_rule(self.grant(),replace(rule,writable_groups=('adapter.other',)))
        with self.assertRaises(ContractError):check_update_rule(self.grant(),replace(rule,ast=RuleNode('read',slot='query_labels')))

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
