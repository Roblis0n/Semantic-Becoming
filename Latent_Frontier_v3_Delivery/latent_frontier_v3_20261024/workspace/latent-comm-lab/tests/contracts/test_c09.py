import unittest
from dataclasses import replace
from latent_comm.core import VersionSet,Scope,ContractError
from latent_comm.core.finite import eye
from latent_comm.compositions.c09 import *
from latent_comm.compositions.contracts import infer_contracts,lower_plan

def fixture():
    v=VersionSet(state='s1',frame='f1',ontology='o1',isa='isa1',task='t1',evidence='e1')
    op=OperatorPacket(((1.,),(0.,)),((0.,),(1.,)),(0.,),1.,'identity','state','state',v,Scope('fixture',frozenset({'receiver'}),frozenset({'Z'})))
    a=Chart('a','m1',(0.,0.),10.,eye(2),eye(2),frozenset({'task'}),'public-behavior',v)
    b=replace(a,chart_id='b',model_revision='m2',versions=replace(v,frame='f2'))
    scale=ScalePacket(eye(2),eye(2),((1.,1.),(0.,1.)),(0.,0.),((1.,1.),(0.,1.)),(0.,0.),('x','y'),('x','y'),'scale1','scale1')
    return LanguageInput(op,(1.,2.),a,b,FrameSpec('a',2,'GL','f1'),FrameSpec('b',2,'GL','f2'),((1.,1.),(0.,1.)),None,scale,'scale1',Expr('var',name='gain'),ISARevision('isa1',()),(('gain',1.),),((1.,2.),),((1.,1.),),'task')

class C09Tests(unittest.TestCase):
    def test_actual_chain_and_compiler(self):
        q=fixture();result=run_reference(q)
        self.assertEqual(len(result.audit),6);self.assertEqual(result.value.source_behavior,(7.,));self.assertAlmostEqual(result.value.behavior_residual[0],0.)
        ir=lower_plan(build_graph(q.versions));self.assertEqual(len(ir.nodes),6);self.assertEqual(ir.pass_trace[-1],'bounded_schedule_gate');self.assertFalse(any(d.code=='BindingsRequired' for d in ir.diagnostics))
    def test_invalidated_receiving_chart(self):
        q=fixture()
        with self.assertRaises(ContractError):run_reference(replace(q,target_chart=replace(q.target_chart,invalidated=True)))
    def test_receiving_chart_task_scope(self):
        q=fixture()
        with self.assertRaises(ContractError):run_reference(replace(q,target_chart=replace(q.target_chart,task_family=frozenset({'other-task'}))))
    def test_stale_isa(self):
        q=fixture()
        with self.assertRaises(ContractError):run_reference(replace(q,isa=ISARevision('isa2',())))
    def test_singular_frame(self):
        with self.assertRaises(ContractError):run_reference(replace(fixture(),gauge=((1.,1.),(2.,2.))))
    def test_wrong_scale_operation(self):
        q=fixture()
        with self.assertRaises(ContractError):run_reference(replace(q,scalar_inputs=(('gain',2.),)))
    def test_nonclosed_without_memory(self):
        q=fixture();scale=ScalePacket(((.5,.5),),((1.,),(1.,)),((1.,1.),(0.,1.)),(0.,0.),((1.,),),(0.,),('x','y'),('mean',),'scale1','coarse1')
        with self.assertRaises(ContractError):run_reference(replace(q,scale=scale,retain_detail=False))
        result=run_reference(replace(q,scale=scale));self.assertGreater(result.value.closure_error,0.);self.assertEqual(result.value.behavior_residual,(0.,))
    def test_heterogeneous_partial_action(self):
        q=fixture();target=Chart('b','m2',(0.,),10.,((1.,),),((1.,),),frozenset({'task'}),'public-behavior',replace(q.versions,frame='f2'))
        edge=Transition('a','b',((1.,2.),),(0.,),'f1','f2',frozenset({'task'}),'loses unobserved source distinctions')
        r=run_reference(replace(q,gauge=None,chart_transition=edge,target_chart=target,target_frame=FrameSpec('b',1,'GL','f2'),target_readout=((1.,),)))
        self.assertEqual(r.value.route,'partial_pushforward');self.assertEqual(r.value.behavior_residual,(0.,));self.assertIn('no target-wide inverse',r.value.lost_information)
    def test_training_is_not_one_global_loss(self):self.assertEqual(len(describe_training()['phases']),3)
if __name__=='__main__':unittest.main()
