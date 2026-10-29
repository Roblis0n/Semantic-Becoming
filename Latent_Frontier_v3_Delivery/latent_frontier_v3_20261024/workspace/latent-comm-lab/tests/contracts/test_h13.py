import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h13_legacy.types import *
from latent_comm.mechanisms.h13_legacy.reference import *
from latent_comm.mechanisms.h13_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h13_legacy'

class BranchTests(unittest.TestCase):
    def root(self):return BranchState('root',(),(('x',(0.,)),('y',(0.,))),(),frozenset(),(),'independent_slots',frozenset({'e'}),'concept1','question1','tx1',V)
    def test_fork_disjoint_merge(self):
        root=self.root();a=write_slot(fork(root,'a'),'x',(1.,),reads=(),operation='setx',commutation_class='independent_slots');b=write_slot(fork(root,'b'),'y',(2.,),reads=(),operation='sety',commutation_class='independent_slots')
        self.assertEqual(common_ancestor(a,b),'root');self.assertEqual(dict(merge(a,b).state),{'x':(1.,),'y':(2.,)});self.assertEqual(dict(root.base)['x'],(0.,))
    def test_read_write_conflict_retained(self):
        root=self.root();a=write_slot(fork(root,'a'),'x',(1.,),reads=(),operation='setx',commutation_class='independent_slots');b=write_slot(fork(root,'b'),'y',(2.,),reads=('x',),operation='readx',commutation_class='independent_slots')
        self.assertIsNone(merge(a,b).state);self.assertEqual(len(merge(a,b).preserved_branches),2)
        with self.assertRaises(ContractError):materialize(release(a))

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


    def test_distinct_roots_do_not_invent_common_ancestry(self):
        from dataclasses import replace
        left=self.root() if hasattr(self,'root') else BranchState('a',(),(('x',(0.,)),),(),frozenset(),(),'independent_slots',frozenset(),'c','q','tx',V)
        right=replace(left,branch_id='other',ancestors=())
        self.assertIsNone(merge(replace(left,ancestors=()),right).state)

    def test_wire_roundtrip_explicit_migration_and_bad_types(self):
        from copy import deepcopy
        from latent_comm.mechanisms.h13_legacy.migration import encode_wire,decode_wire
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

    def test_tensor_merge_metadata_cardinality_is_checked(self):
        source=(ROOT/'adapter.py').read_text();tree=ast.parse(source);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='tensor_merge')
        segment=ast.get_source_segment(source,function)
        self.assertIn('len(structure_ids)!=len(branch_states)',segment)
        self.assertIn('len(commutation_classes)!=len(branch_states)',segment)

    def test_structure_question_and_transaction_branches(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h13_legacy import integration as bind
        from latent_comm.mechanisms.h28_bifurcation.types import StructureTransition
        from latent_comm.mechanisms.h29_questions.types import QuestionIR,QuestionTransform,AnswerMap
        from latent_comm.mechanisms.h39_transactions.types import CommitRecord
        branch=BranchState('root',(),(('x',(1.,)),),(),frozenset(),(),'independent_slots',frozenset({'e'}),'single','q','snapshot',V)
        transition=StructureTransition('s1','s2',((1.,),(2.,)),'single','split',('cache',));child=bind.bifurcate_structure(branch,transition,new_branch_id='child');self.assertEqual(dict(child.base)['x'],(1.,2.));self.assertEqual(branch.concept_structure,'single')
        with self.assertRaises(ContractError):bind.bifurcate_structure(branch,replace(transition,source_version='other'),new_branch_id='bad')
        source=QuestionIR('q',('x',),((0.,1.),),(),'t1');target=replace(source,question_id='q2',version='t2');transform=QuestionTransform(source,target,AnswerMap(((1.,),),(0.,),'q2','q'),'equivalent',())
        rewritten,witness=bind.rewrite_question_branch(branch,transform,new_branch_id='question');self.assertTrue(witness.sound);self.assertEqual(rewritten.question_transform,'q2')
        with self.assertRaises(ContractError):bind.rewrite_question_branch(branch,replace(transform,source=replace(source,version='wrong')),new_branch_id='bad')
        commit=CommitRecord('tx','snapshot','next',('state:x',),'committed');self.assertEqual(bind.advance_transaction_snapshot(branch,commit).transaction_snapshot,'next')
        with self.assertRaises(ContractError):bind.advance_transaction_snapshot(branch,replace(commit,before_digest='wrong'))

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
