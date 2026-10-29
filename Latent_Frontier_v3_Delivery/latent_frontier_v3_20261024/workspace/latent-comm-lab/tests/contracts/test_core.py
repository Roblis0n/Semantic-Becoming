"""A02 stdlib contract and finite arithmetic checks; no neural fixtures."""
import ast
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from latent_comm.core import *
from latent_comm.core.finite import *
from latent_comm.core.learning import finite_masked_mean
from latent_comm.packets import *
from latent_comm.packets.storage import save_finite_json,load_finite_json,resolve_workspace_path

ROOT=Path(__file__).resolve().parents[2]
def versions(**kw):return VersionSet(state='s1',ontology='o1',isa='i1',frame='f1',world='w1',task='t1',evidence='e1',**kw)
def scope():return Scope('scope:research',frozenset({'alice'}),frozenset({'Z','O','P'}))

class CoreContractTests(unittest.TestCase):
    def test_import_has_no_neural_library(self):
        self.assertNotIn('torch',sys.modules);self.assertNotIn('transformers',sys.modules)
    def test_reference_is_not_path_or_url(self):
        for x in ['https://host/object','../secret','/tmp/foo','frame:../secret']:
            with self.assertRaises(ContractError):ObjectRef(x)
        self.assertEqual(ObjectRef('frame:v1:source').namespace,'frame')
    def test_required_versions_and_cache(self):
        with self.assertRaises(ContractError):VersionSet().require('ontology')
        v=versions();changed=replace(v,ontology='o2')
        self.assertNotEqual(v.cache_key('x',{},('ontology','task')),changed.cache_key('x',{},('ontology','task')))
    def test_type_and_stale_version_rejection(self):
        r=ObjectRegistry();ref=ObjectRef('frame:v1:a');r.register(RegisteredObject(ref,'Frame',(1,2),versions(),('frame',),scope(),Visibility.PUBLIC))
        self.assertEqual(r.resolve(ref,expected_type='Frame',versions=versions(),actor='alice',role=Visibility.SENDER),(1,2))
        for ty,v in [('Wrong',versions()),('Frame',replace(versions(),frame='f2'))]:
            with self.assertRaises(ContractError):r.resolve(ref,expected_type=ty,versions=v,actor='alice',role=Visibility.SENDER)
    def test_registry_nested_supervision_is_rejected(self):
        r=ObjectRegistry();secret=ObjectRef('evidence:v1:answer');public=ObjectRef('evidence:v1:wrapper')
        r.register(RegisteredObject(secret,'Answer',42,versions(),('evidence',),scope(),Visibility.SUPERVISION))
        r.register(RegisteredObject(public,'Wrapper',secret,versions(),('evidence',),scope(),Visibility.PUBLIC,(secret,)))
        with self.assertRaises(ContractError):r.resolve(public,expected_type='Wrapper',versions=versions(),actor='alice',role=Visibility.RECEIVER)
    def test_registry_retraction_invalidates_descendants(self):
        r=ObjectRegistry();a=ObjectRef('evidence:v1:a');b=ObjectRef('evidence:v1:b')
        r.register(RegisteredObject(a,'A',1,versions(),('evidence',),scope(),Visibility.PUBLIC))
        r.register(RegisteredObject(b,'B',2,versions(),('evidence',),scope(),Visibility.PUBLIC,(a,)))
        self.assertEqual(r.invalidate(frozenset({a.value})),(a.value,b.value))
    def test_immutable_registry_identity(self):
        r=ObjectRegistry();o=RegisteredObject(ObjectRef('z:v1:a'),'X',1,versions(),('state',),scope(),Visibility.PUBLIC);r.register(o)
        with self.assertRaises(ContractError):r.register(o)
    def test_scope_cannot_grant_host_authority(self):
        with self.assertRaises(ContractError):Scope('bad',frozenset({'alice'}),frozenset({'execution_policy'}))
        with self.assertRaises(ContractError):scope().check('mallory')
        with self.assertRaises(ContractError):scope().check('alice',writes=frozenset({'U'}))
    def test_scope_restriction_and_expiry(self):
        b=Scope('narrow',frozenset({'alice'}),frozenset({'Z'}),expires_step=2)
        s=scope().restrict(b);self.assertEqual(s.writable_components,frozenset({'Z'}))
        with self.assertRaises(ContractError):s.check('alice',step=3)
    def test_budget_atomic_charge(self):
        m=StepBudget(max_steps=2).meter();m.consume(steps=1)
        with self.assertRaises(ContractError):m.consume(steps=2,cases=1)
        self.assertEqual((m.steps,m.cases),(1,0))
        with self.assertRaises(ContractError):StepBudget(max_dimension=65)
    def test_future_budget_not_clipped_to_fixture_limit(self):
        future=ResearchBudget(256,128,512,128)
        self.assertEqual(future.max_steps,256)
        with self.assertRaises(ContractError):FixtureBudget(max_steps=256)
    def test_shape_named_axes(self):
        s=TensorSpec(('batch','slot','channel'),(2,3,4),'float32','message','adapter',mask_axes=('batch','slot'))
        self.assertEqual(s.axis('slot'),3)
        with self.assertRaises(ContractError):s.require_axes(('batch','token','channel'))
        with self.assertRaises(ContractError):TensorSpec(('x','x'),(2,2),'float32','state',None)
    def test_unknown_is_not_zero(self):
        self.assertNotEqual(ValueStatus.UNKNOWN,ValueStatus.PRESENT)
        self.assertNotEqual(ValueStatus.MISSING,ValueStatus.CONTRADICTION)
    def test_role_projection_drops_unselected_supervision(self):
        world={'task':'public question','clue':[1,2],'hidden_solution':4,'sample_id':'secret'}
        view=project_role(world,role=Visibility.SENDER,feature_fields=('clue',),public_fields=('task',),versions=versions())
        self.assertEqual(tuple(view.features),('clue',));self.assertNotIn('hidden_solution',view.features)
        with self.assertRaises(TypeError):view.features['clue']=9
    def test_nested_leakage_and_opaque_objects(self):
        for value in [{'nested':{'label':2}},object()]:
            with self.assertRaises(ContractError):RoleView(Visibility.RECEIVER,{}, {'x':value},versions())
    def test_nested_reference_leakage(self):
        r=ObjectRegistry();ref=ObjectRef('evidence:v1:s');r.register(RegisteredObject(ref,'Secret',1,versions(),('evidence',),scope(),Visibility.SUPERVISION))
        view=RoleView(Visibility.SENDER,{}, {'nested':[ref]},versions())
        with self.assertRaises(ContractError):view.resolve_refs(r,{ref.value:'Secret'},'alice')
    def test_live_tensor_retains_identity(self):
        class Descriptor:
            shape=(2,)
        x=Descriptor();live=LiveTensor(x,TensorSpec(('feature',),(2,),'float32','state','adapter'))
        self.assertIs(live.value,x)
        with self.assertRaises(ContractError):StoredTensor(ObjectRef('tensor:v1:a'),live.spec,'hash','finite_json',False)
    def test_loss_ledger_and_zero_valid(self):
        result=finite_masked_mean((2.,100.,4.),(True,False,True));self.assertEqual(result.value,3.)
        self.assertTrue(finite_masked_mean((2.,),(False,)).skipped)
        with self.assertRaises(ContractError):LossSpec('x','x','x','n','m','skip_with_reason',('adapter',),('x',),(('x','y'),),GradientEstimator.EXACT,'elements')
    def test_gauge_arithmetic_and_singular_rejection(self):
        g=((2.,0.),(0.,3.));t=((1.,1.),(0.,1.));z=(1.,2.);r=((1.,2.),)
        gi=inverse(g);tp=matmul(matmul(g,t),gi);rp=matmul(r,gi)
        actual=matvec(rp,matvec(tp,matvec(g,z)));expected=matvec(r,matvec(t,z))
        self.assertAlmostEqual(actual[0],expected[0])
        with self.assertRaises(ContractError):inverse(((1.,2.),(2.,4.)))
    def test_minimum_norm_and_unreachable_residual(self):
        fit=least_squares(((1.,0.),(0.,0.)),(2.,3.))
        self.assertEqual(fit.rank,1);self.assertFalse(fit.unique);self.assertTrue(fit.converged)
        self.assertAlmostEqual(fit.solution[0],2.);self.assertAlmostEqual(fit.solution[1],0.);self.assertAlmostEqual(norm(fit.residual),3.)
        rotated=least_squares(((1.,1.),),(2.,));self.assertAlmostEqual(rotated.solution[0],1.);self.assertAlmostEqual(rotated.solution[1],1.)
    def test_ridge_and_finite_rejection(self):
        fit=least_squares(((1.,0.),(0.,1.)),(2.,4.),regularization=1.)
        self.assertTrue(fit.unique);self.assertEqual(fit.solution,(1.,2.))
        with self.assertRaises(ContractError):vector((float('nan'),))
        with self.assertRaises(ContractError):vector(tuple(range(65)))
    def test_graph_order_and_cycle(self):
        self.assertEqual(topological_order(('c','a','b'),(('a','b'),('b','c'))),('a','b','c'))
        with self.assertRaises(ContractError):topological_order(('a','b'),(('a','b'),('b','a')))
    def test_migration_success_and_version_failure(self):
        r=MigrationRegistry();r.register(MigrationStep('o1-o2','ontology','o1','o2',(),lambda x:dict(x,new='unknown'),lambda x:x['new']=='unknown',('new field unknown for old readers',)))
        before={'x':1};out=r.apply(before,versions(),('o1-o2',),replace(versions(),ontology='o2'))
        self.assertNotIn('new',before);self.assertEqual(out.value['new'],'unknown');self.assertTrue(out.replay_requires_recompute)
        with self.assertRaises(ContractError):r.apply(before,replace(versions(),ontology='o3'),('o1-o2',),replace(versions(),ontology='o2'))
    def test_migration_cycle_rejected(self):
        r=MigrationRegistry()
        r.register(MigrationStep('a','ontology','o1','o2',('b',),lambda x:x,lambda x:True))
        r.register(MigrationStep('b','isa','i1','i2',('a',),lambda x:x,lambda x:True))
        with self.assertRaises(ContractError):r.apply({},versions(),('a','b'),replace(versions(),ontology='o2',isa='i2'))
    def test_schema_required_const_and_unknown(self):
        v=SchemaValidator({'type':'object','required':['synthetic'],'properties':{'synthetic':{'const':True}},'additionalProperties':False})
        v.validate({'synthetic':True})
        for x in [{},{'synthetic':False},{'synthetic':1},{'synthetic':True,'x':2}]:
            with self.assertRaises(ContractError):v.validate(x)
    def test_schema_duplicate_nonfinite_json(self):
        for x in ['{"x":1,"x":2}','{"x":NaN}']:
            with self.assertRaises(ContractError):load_json(x)
    def test_schema_mechanism_specific_restrictions(self):
        s=json.loads((ROOT/'specs/runtime_schemas/frontier_packet.schema.json').read_text());v=SchemaValidator(s)
        for key,field,value in [('H44Payload','synthetic',False),('H41Payload','credit_is_money',True),('H34Payload','terminal_source','future_observation')]:
            sub=s['$defs'][key]['properties'][field]
            with self.assertRaises(ContractError):v.validate(value,sub)
    def test_workspace_storage_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);digest=save_finite_json(root,'objects/a.json',{'purpose':'math_fixture','not_research_data':True,'value':2})
            self.assertEqual(load_finite_json(root,'objects/a.json',digest)['value'],2)
            (root/'objects/a.json').write_text('{}')
            with self.assertRaises(ContractError):load_finite_json(root,'objects/a.json',digest)
            with self.assertRaises(ContractError):resolve_workspace_path(root,'../x')

    def test_recursive_dependency_versions_rejected(self):
        r=ObjectRegistry();child=ObjectRef('concept:o1:a');wrapper=ObjectRef('wrapper:o2:a')
        r.register(RegisteredObject(child,'Concept',1,versions(),('ontology',),scope(),Visibility.PUBLIC))
        current=replace(versions(),ontology='o2')
        r.register(RegisteredObject(wrapper,'Wrapper',child,current,('ontology','evidence'),scope(),Visibility.PUBLIC,(child,)))
        with self.assertRaises(ContractError):r.resolve(wrapper,expected_type='Wrapper',versions=current,actor='alice',role=Visibility.SENDER)
    def test_referenced_public_payload_cannot_hide_labels(self):
        r=ObjectRegistry();ref=ObjectRef('record:v1:a')
        r.register(RegisteredObject(ref,'Record',{'nested':{'label':42}},versions(),('evidence',),scope(),Visibility.PUBLIC))
        view=RoleView(Visibility.RECEIVER,{}, {'record':ref},versions())
        with self.assertRaises(ContractError):view.resolve_refs(r,{ref.value:'Record'},'alice')
    def test_embedded_reference_must_be_declared_dependency(self):
        r=ObjectRegistry();secret=ObjectRef('answer:v1:a');wrapper=ObjectRef('wrapper:v1:a')
        r.register(RegisteredObject(secret,'Answer',42,versions(),('evidence',),scope(),Visibility.SUPERVISION))
        with self.assertRaises(ContractError):r.register(RegisteredObject(wrapper,'Wrapper',{'secret':secret},versions(),('evidence',),scope(),Visibility.PUBLIC))
    def test_post_registration_mutation_cannot_hide_reference(self):
        r=ObjectRegistry();secret=ObjectRef('answer:v1:mutable');wrapper=ObjectRef('wrapper:v1:mutable');payload={'data':1}
        r.register(RegisteredObject(secret,'Answer',42,versions(),('evidence',),scope(),Visibility.SUPERVISION))
        r.register(RegisteredObject(wrapper,'Wrapper',payload,versions(),('evidence',),scope(),Visibility.PUBLIC))
        payload['secret']=secret
        view=RoleView(Visibility.SENDER,{}, {'wrapper':wrapper},versions())
        with self.assertRaises(ContractError):view.resolve_refs(r,{wrapper.value:'Wrapper'},'alice')
        with self.assertRaises(ContractError):r.resolve(wrapper,expected_type='Wrapper',versions=versions(),actor='alice',role=Visibility.SENDER)
    def test_nested_typed_public_payload_preserves_identity(self):
        from dataclasses import dataclass
        @dataclass(frozen=True)
        class Record:
            coordinates: tuple[float,...]
        r=ObjectRegistry();ref=ObjectRef('record:v1:typed');value=Record((1.,2.))
        r.register(RegisteredObject(ref,'Record',value,versions(),('evidence',),scope(),Visibility.PUBLIC))
        self.assertIs(r.resolve(ref,expected_type='Record',versions=versions(),actor='alice',role=Visibility.SENDER),value)

    def test_metadata_classification_cross_boundary(self):
        from latent_comm.core.views import FORBIDDEN_FIELDS,FIELD_CLASSIFICATION
        contract=json.loads((ROOT/'specs/data_contracts.json').read_text())
        self.assertTrue(set(contract['never_model_inputs'])<=FORBIDDEN_FIELDS)
        for field in ('record_id','manifest_digest'):
            self.assertEqual(FIELD_CLASSIFICATION[field],'record_metadata_only')
            with self.assertRaises(ContractError):RoleView(Visibility.SENDER,{}, {'nested':{field:'id'}},versions())
            r=ObjectRegistry();ref=ObjectRef('record:v1:metadata')
            r.register(RegisteredObject(ref,'Record',{'nested':{field:'id'}},versions(),('evidence',),scope(),Visibility.PUBLIC))
            with self.assertRaises(ContractError):r.resolve(ref,expected_type='Record',versions=versions(),actor='alice',role=Visibility.RECEIVER)
        view=RoleView(Visibility.SENDER,{'task':'public goal','domain':(-2,2),'terminal_condition':0},{},versions())
        self.assertEqual(view.public_task['terminal_condition'],0)
    def test_nested_finite_wire_tree(self):
        for text in ('{"answer":{"value":1e1000}}','{"x":[-1e1000]}'):
            with self.assertRaises(ContractError):load_json(text)
        with self.assertRaises(ContractError):SchemaValidator({'type':'object'}).validate({'x':[float('inf')]})
        self.assertEqual(load_json('{"x":[1.5,null]}')['x'][0],1.5)

    def test_aliases_have_no_algorithm_copies(self):
        entries=json.loads((ROOT/'specs/legacy_alias_ownership.json').read_text())['entries']
        self.assertEqual(len({e['path'] for e in entries}),len(entries))
        for e in entries:
            tree=ast.parse((ROOT/e['path']).read_text())
            funcs=[n.name for n in tree.body if isinstance(n,ast.FunctionDef)]
            self.assertEqual(funcs,['__getattr__'])

if __name__=='__main__':unittest.main()


class AggregateBudgetTests(unittest.TestCase):
    def test_nested_local_budgets_do_not_mint_steps(self):
        from latent_comm.core.budgets import aggregate_budget,StepBudget
        with aggregate_budget(StepBudget(max_steps=3,max_cases=2)) as outer:
            a=StepBudget().meter();b=StepBudget().meter();a.consume(steps=2,cases=1)
            with self.assertRaises(ContractError):b.consume(steps=2,cases=1)
            self.assertEqual((outer.steps,outer.cases,a.steps,b.steps),(2,1,2,0));self.assertTrue(outer.exhausted)
        StepBudget().meter().consume(steps=128)
    def test_nested_context_charges_once_and_resets(self):
        from latent_comm.core.budgets import aggregate_budget,StepBudget
        with aggregate_budget(StepBudget(max_steps=4)) as outer:
            with aggregate_budget(StepBudget(max_steps=3)) as inner:
                inner.consume(steps=1);StepBudget().meter().consume(steps=2)
                self.assertEqual((inner.steps,outer.steps),(3,3))
            StepBudget().meter().consume(steps=1);self.assertEqual(outer.steps,4)
    def test_aggregate_dimension_and_case_limits(self):
        from latent_comm.core.budgets import aggregate_budget,StepBudget
        with aggregate_budget(StepBudget(max_dimension=2,max_cases=1)) as outer:
            child=StepBudget().meter();child.dimension(2);child.consume(cases=1)
            with self.assertRaises(ContractError):child.consume(cases=1)
            with self.assertRaises(ContractError):child.dimension(3)
            self.assertEqual(outer.cases,1)
