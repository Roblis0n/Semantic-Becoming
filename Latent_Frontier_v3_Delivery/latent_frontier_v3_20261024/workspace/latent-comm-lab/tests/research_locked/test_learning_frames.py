import ast
from pathlib import Path
import unittest
from latent_comm.core import ContractError,VersionSet,RoleView,Visibility
from latent_comm.core.learning import LossSpec,GradientEstimator,finite_masked_mean
from latent_comm.learning.contracts import Phase,TrainingPlan,validate_parameter_ownership,validate_phase,RoleTensors
from latent_comm.learning.engine import train
from latent_comm.learning.frames import build_stage
from latent_comm.learning.frames.train import describe
from latent_comm.data.collate import RoleBatch
class LearningFrames(unittest.TestCase):
    def test_analytic_covariance(self):
        from latent_comm.learning.frames.finite_objectives import gauge_objectives
        args=((1.,2.),((1.,1.),(0.,1.)),((1.,2.),),((1.,1.),(0.,1.)))
        good=gauge_objectives(*args,args[-1]);bad=gauge_objectives(*args,((1.,0.),(0.,1.)))
        self.assertAlmostEqual(good['effect'].value,0.);self.assertAlmostEqual(bad['effect'].value,4.);self.assertAlmostEqual(bad['covariance'].value,2.)
    def test_describe(self):self.assertEqual(describe()['research_state'],'NOT_RUN')
    def test_gate_before_model(self):
        with self.assertRaises(ContractError):build_stage('gauge',VersionSet())
    def test_gate_before_training(self):
        with self.assertRaises(ContractError):train(None,None,None,Path('.'))
    def test_owner_alias(self):
        p=object()
        with self.assertRaises(ContractError):validate_parameter_ownership({'a':{'x':p},'b':{'y':p}}, {})
    def test_base_alias(self):
        p=object()
        with self.assertRaises(ContractError):validate_parameter_ownership({'a':{'x':p}}, {'base':p})
    def test_owner_names(self):self.assertEqual(set(validate_parameter_ownership({'a':{'x':object()}},{})),{'a.x'})
    def test_nonfinite_weight_decay(self):
        for value in (float('inf'),float('nan')):
            with self.assertRaises(ContractError):Phase('x',('a',),(('loss',1.),),1,.1,value)
    def test_aggregate_finite_guard_before_backward(self):
        import math
        self.assertTrue(math.isfinite(1e308));self.assertFalse(math.isfinite(2.*1e308))
        text=(Path(__file__).resolve().parents[2]/'src/latent_comm/learning/engine.py').read_text()
        self.assertLess(text.index('torch.isfinite(objective)'),text.index('objective.backward()'))
    def test_covariance_has_no_readout_owner(self):
        from latent_comm.learning.frames import FRAME_LOSS_SPECS
        with self.assertRaises(ContractError):validate_phase(Phase('bad',('read_write_heads',),(('covariance',1.),),1,.1),{'read_write_heads':{'r':object()}},FRAME_LOSS_SPECS)
    def test_semantic_batch_identity(self):
        from latent_comm.learning.contracts import TrainingBatch,validate_batch_versions
        from latent_comm.data.collate import SupervisionBatch
        from latent_comm.data.records import SupervisionView
        current=VersionSet(frame='f2',task='t2')
        sender=RoleBatch(Visibility.SENDER,(RoleView(Visibility.SENDER,{}, {},current),))
        receiver=RoleBatch(Visibility.RECEIVER,(RoleView(Visibility.RECEIVER,{}, {},current),))
        batch=TrainingBatch(sender,receiver,SupervisionBatch((SupervisionView({}, {},'analytic'),)),{})
        with self.assertRaises(ContractError):validate_batch_versions(batch,VersionSet(frame='f1',task='t1'))
        validate_batch_versions(batch,current)
    def test_invalid_weights(self):
        with self.assertRaises(ContractError):Phase('x',('a',),(('loss',float('nan')),),1,.1)
    def test_unowned_loss(self):
        spec=LossSpec('loss','x','x','1','m','error',('b',),('x',),(),GradientEstimator.EXACT,'examples')
        with self.assertRaises(ContractError):validate_phase(Phase('x',('a',),(('loss',1.),),1,.1),{'a':{}},[spec])
    def test_fixture_cap_not_recipe_cap(self):
        plan=TrainingPlan('test',(Phase('x',('a',),(('l',1.),),1000,.1),),2,256,1.,10,'m','d','c');self.assertEqual(plan.maximum_unroll,256)
    def test_run_path(self):
        with self.assertRaises(ContractError):TrainingPlan('../escape',(Phase('x',('a',),(('l',1.),),1,.1),),1,1,1.,1,'m','d','c')
    def test_zero_valid(self):self.assertTrue(finite_masked_mean((1.,),(False,)).skipped)
    def test_role_origin(self):
        b=RoleBatch(Visibility.SENDER,(RoleView(Visibility.SENDER,{}, {'x':1},VersionSet()),))
        with self.assertRaises(ContractError):RoleTensors(b,{'embedding':object()},{'embedding':('hidden_solution',)})
    def test_ast_no_eager_neural(self):
        root=Path(__file__).resolve().parents[2]/'src/latent_comm/learning'
        for path in [root/'engine.py',root/'source.py',root/'frames/__init__.py',root/'frames/train.py']:
            tree=ast.parse(path.read_text())
            for node in tree.body:
                if isinstance(node,(ast.Import,ast.ImportFrom)):self.assertNotIn(getattr(node,'module',''),('torch','transformers'))
            for node in ast.walk(tree):
                if isinstance(node,ast.FunctionDef) and any(isinstance(n,ast.Import) and any(a.name=='torch' for a in n.names) for n in node.body):
                    self.assertTrue(any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id','')=='require_research_action' for n in node.body[:2]),node.name)
    def test_no_supervisor_forward(self):
        path=Path(__file__).resolve().parents[2]/'src/latent_comm/learning/engine.py';tree=ast.parse(path.read_text())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='forward_roles']
        self.assertEqual(len(calls),1);self.assertEqual([n.attr for n in calls[0].args],['sender','receiver'])
if __name__=='__main__':unittest.main()
