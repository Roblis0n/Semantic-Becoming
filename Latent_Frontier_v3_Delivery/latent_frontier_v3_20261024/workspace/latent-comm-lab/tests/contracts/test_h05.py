import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h05_legacy.types import *
from latent_comm.mechanisms.h05_legacy.reference import *
from latent_comm.mechanisms.h05_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h05_legacy'

class ContinuationTests(unittest.TestCase):
    def packet(self):
        c=ResumeContract('program:v1','symbols:v1','float64','none','exact_program')
        p=(ProgramOperation('one','x',('add',('var','x'),('const',1.))),ProgramOperation('two','x',('mul',('var','x'),('const',2.)),('external:ready',)))
        return capture(p,{'x':2.},contract=c,versions=V,transaction_version='tx1',evidence=('e1',))
    def test_pause_resume_no_replay(self):
        p=resume(self.packet(),max_operations=2);self.assertEqual(dict(p.values)['x'],3.);self.assertEqual(p.pending_dependencies,('external:ready',))
        q=resume(p,available_dependencies=('external:ready',),max_operations=2);self.assertEqual(dict(q.values)['x'],6.);self.assertEqual(q.source_clock,2)
        self.assertEqual(resume(q),q)
    def test_version_and_close(self):
        p=self.packet()
        with self.assertRaises(ContractError):validate(p,contract=p.target_resume_contract,versions=V,transaction_version='tx2',available_evidence=('e1',))
        with self.assertRaises(ContractError):resume(close(p))
        self.assertEqual(cut_points(4,3),(0,2,4))

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


    def test_exact_model_snapshot_contract_without_tensor_execution(self):
        from dataclasses import replace
        contract=ResumeContract('model','tokenizer','float32','legacy_tuple','exact_same_model')
        position=PositionSpec(3,3,1,'right','explicit')
        snapshot=ModelContinuation(contract,position,'none',None,(),None,None,None,None,('prefix',),('evidence_ready',),('root',),'tx',('receiver',),V)
        self.assertEqual(validate_model_snapshot(snapshot,contract=contract,versions=V,transaction_version='tx',available_dependencies={'evidence_ready'}),position)
        with self.assertRaises(ContractError):validate_model_snapshot(snapshot,contract=contract,versions=V,transaction_version='tx',available_dependencies=set())
        with self.assertRaises(ContractError):PositionSpec(3,2,1,'right','explicit')
        with self.assertRaises(ContractError):replace(snapshot,random_state_scope='cpu')

    def test_wire_roundtrip_explicit_migration_and_bad_types(self):
        from copy import deepcopy
        from latent_comm.mechanisms.h05_legacy.migration import encode_wire,decode_wire
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

    def test_public_boundary_transaction_and_evidence_lifecycle(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h05_legacy import integration as bind
        from latent_comm.mechanisms.h34_boundary_value.types import PublicTerminalConstraint
        from latent_comm.mechanisms.h39_transactions.types import CommitRecord
        from latent_comm.mechanisms.h48_evidence_genealogy.types import InvalidationSet
        packet=capture((),{},contract=ResumeContract('program','none','float64','none','exact_program'),versions=V,transaction_version='tx0',evidence=('e',))
        bound=bind.bind_public_terminal(packet,PublicTerminalConstraint(('goal',),'public_goal','t1'));self.assertIn('terminal:goal',bound.public_boundary_conditions)
        with self.assertRaises(ContractError):bind.bind_public_terminal(packet,PublicTerminalConstraint(('goal',),'public_goal','other'))
        pending=replace(packet,pending_dependencies=('commit',));commit=CommitRecord('commit','before','after',('state:x',),'committed')
        resumed=bind.after_transaction_commit(pending,commit,expected_snapshot='tx0',new_snapshot='tx1');self.assertEqual(resumed.pending_dependencies,())
        with self.assertRaises(ContractError):bind.after_transaction_commit(packet,commit,expected_snapshot='tx0',new_snapshot='tx1')
        self.assertTrue(bind.retract_continuation_evidence(packet,InvalidationSet(('e',),('root',),True,'e1')).closed)
        with self.assertRaises(ContractError):bind.retract_continuation_evidence(packet,InvalidationSet(('e',),('root',),True,'other'))

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
