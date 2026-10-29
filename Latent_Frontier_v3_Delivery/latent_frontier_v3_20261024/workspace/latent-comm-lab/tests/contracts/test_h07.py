import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h07_legacy.types import *
from latent_comm.mechanisms.h07_legacy.reference import *
from latent_comm.mechanisms.h07_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h07_legacy'

from latent_comm.core import Scope
S=Scope('dsl',frozenset({'receiver'}),frozenset({'Z'}))
T=ValueType('state',1,'f1')
class DSLTests(unittest.TestCase):
    def test_branch_and_merge(self):
        p=ProgramPacket((Instruction('b','BRANCH',('x',),ValueType('branches',None,None)),Instruction('m','MERGE_SCOPED',('b',),T)),(('x',T),),'m',V,S)
        self.assertEqual(execute(compile_program(p),{'x':(2.,)})[0],(2.,))
    def test_cycle_command_and_types(self):
        for opcode in ('shell','eval','__import__'):
            p=ProgramPacket((Instruction('o',opcode,('x',),T),),(('x',T),),'o',V,S)
            with self.assertRaises(ContractError):compile_program(p)
        p=ProgramPacket((Instruction('a','READ_SLOT',('b',),T),Instruction('b','READ_SLOT',('a',),T)),(),'a',V,S)
        with self.assertRaises(ContractError):compile_program(p)
    def test_scope_rejected(self):
        p=ProgramPacket((),(('x',T),),'x',V,S)
        with self.assertRaises(ContractError):compile_program(p,actor='outsider')

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


    def test_operator_frame_and_bound_packet(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h01_legacy.types import OperatorPacket
        op=OperatorPacket(((1.,),),((1.,),),(0.,),1.,'identity','d','d',V,S)
        packet=ProgramPacket((Instruction('o','APPLY_OPERATOR',('x','op'),T),),(('x',T),('op',ValueType('operator',1,'f1'))),'o',V,S)
        self.assertEqual(execute(compile_program(packet),{'x':(2.,),'op':op})[0],(4.,))
        with self.assertRaises(ContractError):compile_program(replace(packet,input_types=(('x',T),('op',ValueType('operator',1,'other')))))
        with self.assertRaises(ContractError):execute(compile_program(packet),{'x':(2.,),'op':replace(op,versions=replace(V,frame='other'))})
    def test_field_and_continuation_positive_and_budget(self):
        from latent_comm.mechanisms.h04_legacy.types import LocalConstraint,ConstraintField
        field=ConstraintField((LocalConstraint('c',((1.,),),(2.,),1.,'d','f1','s1',frozenset({'e'})),),(0.,),1.,'d',V)
        packet=ProgramPacket((Instruction('z','SOLVE_FIELD',('field',),T,3),),(('field',ValueType('field',1,'f1')),),'z',V,S)
        self.assertGreater(execute(compile_program(packet),{'field':field})[0][0],0.)
        from latent_comm.mechanisms.h05_legacy.types import ProgramOperation,ResumeContract
        from latent_comm.mechanisms.h05_legacy.reference import capture
        continuation=capture((ProgramOperation('one','x',('const',1.)),),{},contract=ResumeContract('program','none','float64','none','exact_program'),versions=V,transaction_version='tx')
        packet=ProgramPacket((Instruction('next','CONTINUE',('c',),ValueType('continuation',None,None),2),),(('c',ValueType('continuation',None,None)),),'next',V,S)
        self.assertEqual(execute(compile_program(packet),{'c':continuation})[0].program_counter,1)
        with self.assertRaises(ContractError):execute(compile_program(packet),{'c':continuation},budget=StepBudget(max_steps=1))

    def test_wire_roundtrip_explicit_migration_and_bad_types(self):
        from copy import deepcopy
        from latent_comm.mechanisms.h07_legacy.migration import encode_wire,decode_wire
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

    def test_typed_belief_refinement_uses_ordered_log_likelihoods(self):
        from latent_comm.mechanisms.h03_legacy.types import BeliefBranch,BeliefPacket
        belief=BeliefPacket((BeliefBranch('a',(1.,),0.,'d',frozenset({'e'}),'o1'),BeliefBranch('b',(2.,),0.,'d',frozenset({'e'}),'o1')),'sequence_mixture',V)
        typ=ValueType('belief',None,None);packet=ProgramPacket((Instruction('out','REFINE_BELIEF',('b','l'),typ),),(('b',typ),('l',ValueType('likelihoods',None,None))),'out',V,S)
        out,_=execute(compile_program(packet),{'b':belief,'l':(0.,-math.inf)});self.assertEqual(out.branches[0].log_weight,0.)
        with self.assertRaises(ContractError):execute(compile_program(packet),{'b':belief,'l':{'a':0.,'b':-1.}})

    def test_frontier_consumer_bindings(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h07_legacy import integration as bind
        from latent_comm.mechanisms.h27_ontology.types import Predicate,ConceptDefinition,OntologySnapshot
        from latent_comm.mechanisms.h29_questions.types import QuestionIR,AnswerMap,QuestionTransform
        from latent_comm.mechanisms.h38_plasticity.types import PlasticityProgram,RuleNode
        from latent_comm.mechanisms.h40_instruction_set.types import Expr,ISARevision
        program=compile_program(ProgramPacket((),(('x',T),),'x',V,Scope('s',frozenset({'receiver'}),frozenset({'Z','U'}))))
        ontology=OntologySnapshot('o1',(ConceptDefinition('c',Predicate('eq','x',1),(),('e',),('x',)),));self.assertTrue(bind.execute_concept_binding(program,ontology,'c',{'x':1}))
        with self.assertRaises(ContractError):bind.execute_concept_binding(program,replace(ontology,version='other'),'c',{'x':1})
        source=QuestionIR('q',('x',),((0.,1.),),(),'t1');target=replace(source,question_id='q2',version='t2');transform=QuestionTransform(source,target,AnswerMap(((1.,),),(0.,),'q2','q'),'equivalent',())
        self.assertTrue(bind.verify_question_binding(program,transform).sound)
        with self.assertRaises(ContractError):bind.verify_question_binding(program,replace(transform,source=replace(source,version='other')))
        rule=PlasticityProgram(RuleNode('read',slot='gradient'),('adapter.w',),1.,1,1,'rule','first_order');self.assertEqual(bind.validate_plasticity_binding(program,rule,allowed_parameters={'adapter.w'}),1)
        with self.assertRaises(ContractError):bind.validate_plasticity_binding(program,rule,allowed_parameters=set())
        expr=Expr('const',value=1.);self.assertEqual(bind.lower_macro_binding(program,expr,ISARevision('i1',())),expr)
        with self.assertRaises(ContractError):bind.lower_macro_binding(program,expr,ISARevision('other',()))

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
