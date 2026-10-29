import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.joint.train import describe
from latent_comm.learning.joint import BoundaryContract,prefixed_specs,project_component_role,project_component_supervision,COUPLED_SPECS,COMPONENT_MODULES,component_order
from latent_comm.learning.contracts import Phase,validate_phase,validate_parameter_ownership
from latent_comm.core import ContractError,VersionSet,RoleView,Visibility
from latent_comm.data.collate import RoleBatch,SupervisionBatch
from latent_comm.data.records import SupervisionView
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/joint').glob('*.py'):
            tree=ast.parse(path.read_text())
            for node in tree.body:
                if isinstance(node,ast.Import):self.assertFalse(any(a.name.split('.')[0] in {'torch','transformers','numpy'} for a in node.names))
                if isinstance(node,ast.ImportFrom):self.assertNotIn((node.module or '').split('.')[0],{'torch','transformers','numpy'})
            for node in ast.walk(tree):
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    direct_neural=any(isinstance(n,ast.Import) and any(a.name=='torch' for a in n.names) for n in node.body)
                    if direct_neural or node.name in {'build_stage','forward_roles','losses','run'}:
                        body=node.body[1:] if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) else node.body
                        self.assertTrue(any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id','')=='require_research_action' for n in body[:2]),(path.name,node.name))
                    if node.name=='forward_roles':self.assertEqual([a.arg for a in node.args.args],['self','sender','receiver'])
    def test_recipe_is_unbound(self):
        cfg=json.loads((ROOT/'configs/learning/joint.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L13')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/joint/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def test_component_order_preserves_rng_assignment_on_reordered_config(self):
        import hashlib,random
        a={'left':{},'right':{}};b={'right':{},'left':{}}
        digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest(a),digest(b))
        def draw(bindings):
            rng=random.Random(17)
            return {alias:rng.random() for alias in component_order(bindings)}
        self.assertEqual(draw(a),draw(b))
        self.assertEqual(component_order(b),('left','right'))
    def test_all_learning_stages_registered(self):
        self.assertEqual(set(COMPONENT_MODULES),{'L'+str(i).zfill(2) for i in range(1,13)})
    def test_role_and_supervisor_projection_separated(self):
        versions=VersionSet(task='nested');outer=VersionSet(task='joint')
        role=RoleView(Visibility.SENDER,{}, {'components':{'a':{'public_task':{'purpose':'local'},'features':{'x':1},'versions':versions.as_dict()}}},outer)
        projected=project_component_role(RoleBatch(Visibility.SENDER,(role,)),'a',versions)
        self.assertEqual(projected.views[0].features['x'],1)
        with self.assertRaises(ContractError):project_component_role(RoleBatch(Visibility.SENDER,(role,)),'a',VersionSet(task='wrong'))
        supervisor=SupervisionBatch((SupervisionView({'components':{'a':{'targets':{'target':2},'valid_masks':{},'source_kind':'analytic'}}},{},'analytic'),))
        self.assertEqual(project_component_supervision(supervisor,'a').views[0].targets['target'],2)
    def test_namespaced_ledger_and_coupled_path_owners(self):
        specs=prefixed_specs('coupled',COUPLED_SPECS)
        self.assertEqual(specs[0].name,'coupled.coupled_query_full')
        for owner in ('transport.transport_operator','transport.behavior_encoder','plasticity_rule_parameters'):
            validate_phase(Phase('joint',(owner,),(('coupled_query_full',1.),),1,.01),{owner:{'p':object()}},COUPLED_SPECS)
    def test_owner_alias_cannot_hide_between_components(self):
        p=object()
        with self.assertRaises(ContractError):validate_parameter_ownership({'a.writer':{'p':p},'b.reader':{'p':p}}, {})
    def test_serialized_boundary_does_not_claim_live_graph(self):
        b=BoundaryContract('a','b','State',('task',),('Z',),'serialized_recompute','Recompute after reload.')
        self.assertEqual(b.mode,'serialized_recompute')
        with self.assertRaises(ContractError):BoundaryContract('a','b','State',('task',),('host',),'stop','invalid authority')
        with self.assertRaises(ContractError):BoundaryContract('a','b','State',('task',),('Z',),'automatic_gradient','invalid')
    def test_live_transport_uses_no_serialization(self):
        source=(ROOT/'src/latent_comm/learning/joint/__init__.py').read_text()
        self.assertIn('theta=output.initial[i]+delta[i]',source)
        self.assertIn('create_graph=self.estimator',source)
        self.assertIn('sum(self.unroll_allocations.values())>maximum_unroll',source)

if __name__=='__main__':unittest.main()
