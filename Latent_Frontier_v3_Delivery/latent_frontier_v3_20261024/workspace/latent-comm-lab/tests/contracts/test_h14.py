import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h14_legacy.types import *
from latent_comm.mechanisms.h14_legacy.reference import *
from latent_comm.mechanisms.h14_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h14_legacy'

from latent_comm.core import Scope
from latent_comm.mechanisms.h07_legacy.reference import execute,SIGNATURES
S=Scope('grammar',frozenset({'receiver'}),frozenset({'Z'}));T=ValueType('state',1,'f1')
class GrammarTests(unittest.TestCase):
    def grammar(self):return SkillGrammar((Production('copy',(('arg',T),),(SkillStep('tmp','READ_SLOT',('arg',),T),),'tmp',T),),'g1','i1',frozenset({'task'}),V)
    def test_hygiene_and_old_reader(self):
        p=expand(self.grammar(),'copy',('tmp',),(('tmp',T),),scope=S,task='task')
        self.assertNotEqual(p.packet.nodes[0].node_id,'tmp');self.assertEqual(execute(p,{'tmp':(4.,)})[0],(4.,))
        self.assertEqual(lower_for_reader(self.grammar(),p,supported_isa='i1',supported_opcodes=set(SIGNATURES)),p)
    def test_recursion_and_capture(self):
        p=Production('loop',(('arg',T),),(SkillStep('x','loop',('arg',),T),),'x',T)
        with self.assertRaises(ContractError):validate_grammar(SkillGrammar((p,),'g1','i1',frozenset({'task'}),V))
        p=Production('bad',(('arg',T),),(SkillStep('x','READ_SLOT',('private_caller',),T),),'x',T)
        with self.assertRaises(ContractError):expand(SkillGrammar((p,),'g1','i1',frozenset({'task'}),V),'bad',('x',),(('x',T),),scope=S,task='task')

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
        from latent_comm.mechanisms.h14_legacy.migration import encode_wire,decode_wire
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

    def test_concept_analogy_and_macro_consumers(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h14_legacy import integration as bind
        from latent_comm.mechanisms.h27_ontology.types import Predicate,ConceptDefinition,OntologySnapshot
        from latent_comm.mechanisms.h30_analogy.types import TypedObject,FiniteOperation,TypedOperationGraph,AnalogyMorphism
        from latent_comm.mechanisms.h30_analogy.reference import check_morphism
        from latent_comm.mechanisms.h40_instruction_set.types import Expr,MacroDefinition,ISARevision
        from latent_comm.mechanisms.h40_instruction_set.reference import lower,execute_base
        typ=ValueType('state',1,'f1');production=Production('skill',(('x',typ),),(SkillStep('y','READ_SLOT',('x',),typ),),'y',typ);grammar=SkillGrammar((production,),'grammar','base',frozenset({'task'}),V)
        ontology=OntologySnapshot('o1',(ConceptDefinition('guard',Predicate('eq','x',1),(),('e',),('x',)),));self.assertTrue(bind.concept_guard(grammar,ontology,'guard',{'x':1}))
        with self.assertRaises(ContractError):bind.concept_guard(grammar,replace(ontology,version='wrong'),'guard',{'x':1})
        source=TypedOperationGraph((TypedObject('x','scalar'),),(FiniteOperation('READ_SLOT','scalar','scalar',(('x','x'),)),),'i1');target=replace(source,version='i2');morphism=AnalogyMorphism((('x','x'),),(('READ_SLOT','READ_SLOT'),),(('scalar','scalar'),),('x',));checked=check_morphism(source,target,morphism)
        self.assertEqual(bind.transport_skill_operations(grammar,'skill',checked),(('y','READ_SLOT',('x',)),))
        with self.assertRaises(ContractError):bind.transport_skill_operations(grammar,'skill',replace(checked,source_version='wrong'))
        primitive=MacroDefinition('read_scalar',('x',),Expr('var',name='x'),('scalar',));macro=bind.scalar_macro_from_production(grammar,'skill',{'READ_SLOT':primitive},target_isa='i1');revision=ISARevision('i1',(primitive,macro));program=lower(Expr('call',(Expr('const',value=2.),),name='skill'),revision);self.assertEqual(execute_base(program,{}),2.)
        with self.assertRaises(ContractError):bind.scalar_macro_from_production(grammar,'skill',{},target_isa='i1')

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
