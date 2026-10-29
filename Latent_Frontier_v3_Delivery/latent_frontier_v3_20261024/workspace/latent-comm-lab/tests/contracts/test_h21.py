import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h21_legacy.types import *
from latent_comm.mechanisms.h21_legacy.reference import *
from latent_comm.mechanisms.h21_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h21_legacy'

from dataclasses import replace
from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM
class TestPortfolios(unittest.TestCase):
    def root(self):return PortfolioNode('root',(('x',0.),('y',0.)),(),None,None,(),'answer','q','w','public',frozenset({'e'}),V)
    def world(self):return TargetSCM((CausalModule('x','u',(),(),(),0.,()),CausalModule('y','u',('x',),('u',),(2.,),0.,())),(),'w1')
    def test_causal_search_preserves_prefix(self):
        root=self.root();result=search_counterfactuals(self.world(),{},root,(('x',(1.,2.)),),PublicGoal('y',4.),max_depth=2)
        self.assertEqual(dict(next(n for n in result.nodes if n.node_id==result.best_id).anchor_state)['y'],4.);self.assertEqual(dict(root.anchor_state)['y'],0.)
        self.assertGreater(result.reused,0);self.assertFalse(result.impossibility_proven)
    def test_timeout_not_proof_and_semantic_dedup(self):
        result=search_counterfactuals(self.world(),{},self.root(),(('x',(1.,2.)),),PublicGoal('y',9.),max_depth=2,budget=StepBudget(max_steps=2))
        self.assertEqual(result.status,'search_exhausted_within_budget');self.assertTrue(result.frontier);self.assertFalse(result.impossibility_proven)
        self.assertNotEqual(semantic_key(self.root()),semantic_key(replace(self.root(),intervention=(('x',0.),))))
        with self.assertRaises(ContractError):PublicGoal('y',1.,'supervision')
    def test_evidence_update_idempotence_and_identification(self):
        nodes=(self.root(),replace(self.root(),node_id='other',intervention=(('x',1.),)))
        p,seen=update_evidence_weights(nodes,(.5,.5),(1.,.5),evidence_id='new',seen=set());self.assertAlmostEqual(p[0],2/3)
        self.assertEqual(update_evidence_weights(nodes,p,(0.,1.),evidence_id='new',seen=seen)[0],p)
        state=identification_state(nodes,(),p,version='id1');self.assertTrue(state.unknown_hypothesis_possible)
        with self.assertRaises(ContractError):update_evidence_weights(nodes,p,(0.,0.),evidence_id='conflict',seen=seen)

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
        from latent_comm.mechanisms.h21_legacy.migration import encode_wire,decode_wire
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

    def test_question_counterexample_concept_and_synthetic_branches(self):
        from latent_comm.mechanisms.h29_questions.types import QuestionIR,QuestionTransform,AnswerMap
        from latent_comm.mechanisms.h29_questions.reference import check_relation
        q=QuestionIR('q',('x',),((0.,1.),),(),'t1');q2=replace(q,question_id='q2',version='t2')
        transform=QuestionTransform(q,q2,AnswerMap(((1.,),),(0.,),'q2','q'),'equivalent',())
        witness=check_relation(transform);branch=question_branch(self.root(),transform,witness,node_id='question')
        self.assertEqual(branch.question_id,'q2')
        with self.assertRaises(ContractError):question_branch(self.root(),transform,replace(witness,sound=False),node_id='bad')
        from latent_comm.mechanisms.h36_disagreement.types import Counterexample
        counter=Counterexample('c',2,False,True,'executable','verified_counterexample')
        self.assertIn('c:2',counterexample_branch(self.root(),counter,claim_id='c').evidence)
        with self.assertRaises(ContractError):counterexample_branch(self.root(),replace(counter,status='timeout'),claim_id='c')
        from latent_comm.mechanisms.h27_ontology.types import Predicate,ConceptDefinition,OntologySnapshot,OntologyDelta
        concept=ConceptDefinition('positive',Predicate('le','x',1.),(),('e',),('x',))
        delta=OntologyDelta(OntologySnapshot('o1',()),OntologySnapshot('o2',(concept,)),(),())
        self.assertEqual(concept_branch(self.root(),delta,node_id='concept',concept_id='positive').versions.ontology,'o2')
        with self.assertRaises(ContractError):concept_branch(self.root(),delta,node_id='bad',concept_id='missing')
        from latent_comm.mechanisms.h43_world_kernels.types import SharedNoiseJoint,ComposedWorldKernel
        from latent_comm.mechanisms.h44_dreaming.types import DreamWorld
        kernel=ComposedWorldKernel(('k',),(('s',),),(('a','do'),),(('a',((1.,),)),),(('o',),),((1.,),),SharedNoiseJoint((),(((),1.),)),(),'dream-v')
        dream=DreamWorld('dream',kernel,('k',),(),('finite model',))
        self.assertTrue(world_branch(self.root(),dream,node_id='world',world_version='dream-v').synthetic)
        with self.assertRaises(ContractError):world_branch(self.root(),dream,node_id='bad',world_version='invented')
    def test_root_anchor_must_match_same_structural_world(self):
        bad=replace(self.root(),anchor_state=(('x',0.),('y',99.)))
        with self.assertRaises(ContractError):search_counterfactuals(self.world(),{},bad,(),PublicGoal('y',0.),max_depth=0)

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
