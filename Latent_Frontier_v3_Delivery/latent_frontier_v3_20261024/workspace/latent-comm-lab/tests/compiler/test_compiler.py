"""Finite compiler fixtures only; no tensor backend imports or model calls."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from latent_comm.compiler import compile_recipe, CompilationError, mechanism_registry, builtin_registry, PASSES, ir_text, ir_dot, request_research_execution
from latent_comm.core import ContractError

PLAN = Path(__file__).resolve().parents[4]

def recipe(key='H01'):
    cap = mechanism_registry()[key]; objects = {}; inputs = {}; outputs = {}
    for direction, ports in [('inputs',cap.inputs),('outputs',cap.outputs)]:
        for port,name in ports:
            ref=direction+':'+port; objects[ref]={'type':name,'versions':{'schema':'3',cap.required_version_axes[-1]:'v1'}}
            (inputs if direction=='inputs' else outputs)[port]=ref
    return {'schema_version':3,'id':'fixture','nodes':[{'id':'node','mechanism':key,'inputs':inputs,'outputs':outputs,'role':'public'}], 'objects':objects,'runtime_budget':{'max_steps':8}}

class CompilerTests(unittest.TestCase):
    def reject(self, r, code):
        with self.assertRaises(CompilationError) as ctx: compile_recipe(r)
        self.assertIn(code,{d.code for d in ctx.exception.diagnostics})
        return ctx.exception
    def test_all_mechanism_registrations(self):
        reg=mechanism_registry(); self.assertEqual(len(reg),48)
        self.assertTrue(all(x.inputs and x.outputs and x.required_capabilities and x.source_spec for x in reg.values()))
        self.assertGreater(len({x.outputs for x in reg.values()}),40)
    def test_all_declared_operations(self): self.assertEqual(len(builtin_registry()),17)
    def test_seven_passes(self):
        ir=compile_recipe(recipe()); self.assertEqual(ir.pass_trace,PASSES); self.assertEqual(ir.worst_case_steps,1)
        self.assertFalse(ir.research_execution_authorized); self.assertEqual(ir.research_state,'NOT_RUN')
    def test_all_48_typed_contracts(self):
        for key in mechanism_registry():
            ir=compile_recipe(recipe(key)); self.assertEqual(ir.nodes[0].mechanism,key)
    def test_original_48_recipes(self):
        for i in range(1,49):
            ir=compile_recipe(PLAN/'recipes'/f'H{i:02d}.json'); self.assertTrue(any(d.code=='BindingsRequired' for d in ir.diagnostics))
    def test_original_20_combinations(self):
        for i in range(1,21): self.assertEqual(compile_recipe(PLAN/'recipes'/f'C{i:02d}.json').research_state,'NOT_RUN')
    def test_h40_future_budget_preserved(self):
        ir=compile_recipe(PLAN/'recipes/H40.json'); self.assertEqual(ir.declared_parameters['expansion_budget'],256)
        r=recipe();r['runtime_budget']['max_steps']=10000;r['bounded_loops']=[{'id':'loop','body':['node'],'max_iterations':1000}]
        self.assertEqual(compile_recipe(r).worst_case_steps,1000)
    def test_source_localization(self):
        r=recipe();r['nodes'][0]['inputs']['in0']='missing:object'
        error=self.reject(r,'UnboundReference'); d=next(d for d in error.diagnostics if d.code=='UnboundReference')
        self.assertEqual(d.location.path,'/nodes/0/inputs/in0');self.assertGreater(d.location.line,1)
    def test_bad_json(self):
        for value in ['{"id": 1,}', '{"id":1,"id":2}', '{"id":NaN}', '[]']:
            with self.assertRaises(CompilationError):compile_recipe(value)
    def test_nested_exponent_overflow_is_invalid_json(self):
        from latent_comm.compiler.source import SourceDocument
        for payload in ('{"parameters":{"coefficient":1e1000}}','{"parameters":[-1e1000]}'):
            with self.assertRaises(CompilationError) as ctx:SourceDocument(payload)
            self.assertEqual(ctx.exception.diagnostics[0].code,'InvalidJSON')
        self.assertEqual(SourceDocument('{"parameters":{"coefficient":1e300}}').value['parameters']['coefficient'],1e300)
    def test_plan_not_research(self):
        r=recipe();r['tasks']=[];self.reject(r,'PlanIsNotResearchIR')
    def test_no_authorization_from_config(self):
        r=recipe();r['research_execution_authorized']=True;self.reject(r,'ResearchForbidden')
    def test_write_set_cannot_omit_capability_effects(self):
        r=recipe();r['nodes'][0]['write_set']=[];self.reject(r,'ScopeViolation')
        r=recipe();r['scope']=[];r['nodes'][0]['write_set']=[];self.reject(r,'ScopeViolation')
    def test_types(self):
        r=recipe();r['objects']['inputs:in0']['type']='Wrong';self.reject(r,'TypeMismatch')
    def test_shape_named_axes(self):
        r=recipe();r['objects']['inputs:in0']['tensor']={'axes':['feature'],'shape':[2],'dtype':'float64','semantic_role':'state'}
        r['nodes'][0]['input_tensors']={'in0':{'axes':['token'],'shape':[2]}};self.reject(r,'ShapeMismatch')
    def test_no_control_plane_write(self):
        r=recipe();r['nodes'][0]['write_set']=['execution_policy'];self.reject(r,'ScopeViolation')
    def test_missing_version(self):
        r=recipe();r['objects']['inputs:in0']['versions']={'schema':'3'};self.reject(r,'MissingVersion')
    def test_migration_insertion(self):
        r=recipe();r['nodes'][0]['required_versions']={'frame':'v2'}
        r['migrations']=[{'id':'frame-v2','axis':'frame','from':'v1','to':'v2','implementation':'explicit.reference.transform'}]
        ir=compile_recipe(r);self.assertEqual(sum(n.operation=='MigrateObject' for n in ir.nodes),2)
        self.assertTrue(all(t.versions.frame=='v2' for _,t in ir.nodes[-1].input_types))
    def test_missing_migration(self):
        r=recipe();r['nodes'][0]['required_versions']={'frame':'v2'};self.reject(r,'MigrationRequired')
    def test_migration_cycles(self):
        r=recipe();r['migrations']=[{'id':'a','depends_on':['b']},{'id':'b','depends_on':['a']}];self.reject(r,'MigrationConflict')
    def test_ambiguous_migration(self):
        r=recipe();r['migrations']=[{'id':x,'axis':'frame','from':'v1','to':'v2','implementation':'explicit'} for x in ['a','b']];self.reject(r,'AmbiguousMigration')
    def test_dependency_version_rejected(self):
        r=recipe();r['objects']['dependency:x']={'type':'State','versions':{'frame':'v0'}};r['objects']['inputs:in0']['dependencies']=['dependency:x'];self.reject(r,'DependencyVersionMismatch')
    def test_embedded_reference_must_be_declared(self):
        r=recipe();r['objects']['inputs:in0']['value']={'nested':{'$ref':'secret:labels'}};self.reject(r,'UndeclaredReference')
    def test_nested_role_leak(self):
        r=recipe();r['objects']['inputs:in0']['value']={'nested':[{'hidden_solution':4}]};self.reject(r,'RoleLeakage')
    def test_transitive_role_leak(self):
        r=recipe();r['objects']['extra:supervision']={'type':'Labels','visibility':'supervision'}
        r['objects']['inputs:in0']['dependencies']=['extra:supervision'];self.reject(r,'RoleLeakage')
    def test_role_migration_preserves_visibility(self):
        r=recipe();r['nodes'][0]['role']='sender';r['nodes'][0]['required_versions']={'frame':'v2'}
        for x in r['objects'].values():x['visibility']='sender'
        r['migrations']=[{'id':'a','axis':'frame','from':'v1','to':'v2','implementation':'explicit'}]
        self.assertEqual(len(compile_recipe(r).nodes),3)
    def test_discrete_gradient_rejected(self):
        r=recipe('H27');r['nodes'][0]['gradient_edges']={'in0':'differentiable'};self.reject(r,'DiscreteGradient')
    def test_frozen_input_gradient_preserved(self):
        r=recipe();r['nodes'][0]['frozen_weights']=True;r['nodes'][0]['required_input_gradients']=['in0']
        self.assertEqual(dict(compile_recipe(r).nodes[0].gradient_edges)['in0'],'differentiable')
        r['nodes'][0]['gradient_edges']={'in0':'stop'};self.reject(r,'GradientDisconnected')
    def test_explicit_estimator(self):
        r=recipe('H27');r['nodes'][0]['gradient_edges']={'in0':'straight_through'}
        self.assertEqual(dict(compile_recipe(r).nodes[0].gradient_edges)['in0'],'straight_through')
    def test_unbounded_loop(self):
        r=recipe();r['bounded_loops']=[{'id':'loop','body':['node']}];self.reject(r,'UnboundedLoop')
    def test_loop_budget(self):
        r=recipe();r['bounded_loops']=[{'id':'loop','body':['node'],'max_iterations':3}];ir=compile_recipe(r)
        self.assertEqual(ir.schedule,('loop',));self.assertEqual(ir.worst_case_steps,3)
        r['runtime_budget']['max_steps']=2;self.reject(r,'BudgetExceeded')
    def test_cycle_without_loop(self):
        r=recipe();r['nodes'][0]['depends_on']=['node'];self.reject(r,'ScheduleCycle')
    def test_typed_loop_carry(self):
        from latent_comm.compiler import Compiler
        from latent_comm.compiler.types import NodeCapability
        cap=NodeCapability('FixtureIncrement','FixtureIncrement',(('in0','Scalar'),),(('out0','Scalar'),),frozenset('Z'),frozenset('Z'),'exact','deterministic_given_inputs',('fixture_math',),('schema',),'fixture:increment','test-only')
        r={'schema_version':3,'id':'bounded','objects':{'a':{'type':'Scalar'},'b':{'type':'Scalar'}},'nodes':[{'id':'step','operation':'FixtureIncrement','inputs':{'in0':'a'},'outputs':{'out0':'b'}}],'bounded_loops':[{'id':'loop','body':['step'],'max_iterations':3,'carried':[['b','a']]}]}
        ir=Compiler({'FixtureIncrement':cap}).compile(r);self.assertEqual(ir.loops[0].carried,(('b','a'),));self.assertEqual(ir.worst_case_steps,3)
    def test_exports(self):
        ir=compile_recipe(recipe());self.assertIn('NOT_RUN',ir_text(ir));self.assertIn('digraph',ir_dot(ir));json.dumps(ir.to_dict())
    def test_research_gate(self):
        with self.assertRaises(ContractError):request_research_execution(compile_recipe(recipe()))
    def test_no_model_imports_subprocess(self):
        code="import sys; import latent_comm.compiler; assert not any(x in sys.modules for x in ['torch','transformers'])"
        subprocess.run([sys.executable,'-c',code],check=True)

if __name__=='__main__':unittest.main()
