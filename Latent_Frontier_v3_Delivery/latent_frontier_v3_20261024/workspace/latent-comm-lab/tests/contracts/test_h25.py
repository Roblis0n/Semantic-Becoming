import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h25_gauge.types import *
from latent_comm.mechanisms.h25_gauge.reference import *
from latent_comm.mechanisms.h25_gauge.serialization import *
import latent_comm.mechanisms.h25_gauge.adapter as adapter

class H25Contracts(unittest.TestCase):
    def setUp(self):
        self.a=FrameSpec('f:a',2,'GL','1');self.b=FrameSpec('f:b',2,'GL','2')
        self.packet=GaugePacket(self.a,(1.,2.),((2.,0.),(0.,3.)),((1.,0.),))
        self.swap=((0.,1.),(1.,0.))
    def test_action_preservation_and_counterexample(self):
        r=transport(self.packet,self.swap,self.b)
        self.assertEqual(r.transported.state,(2.,1.));self.assertEqual(r.effect_after,(2.,));self.assertEqual(r.residual,(0.,))
        self.assertNotEqual(matvec(self.packet.readout,r.transported.state),matvec(self.packet.readout,self.packet.state))
    def test_singular_and_near_singular(self):
        for g in [((1.,0.),(0.,0.)),((1.,0.),(0.,1e-8))]:
            with self.assertRaises(ContractError):transport(self.packet,g,self.b)
    def test_dimension_rejection(self):
        with self.assertRaises(ContractError):transport(self.packet,((1.,0.,0.),(0.,1.,0.)),self.b)
    def test_three_stage_path(self):
        r=compose_path(self.packet,((self.swap,self.b),(self.swap,self.a),(self.swap,self.b)))
        self.assertEqual(r.path,('f:a','f:b','f:a','f:b'));self.assertEqual(r.residual,(0.,))
    def test_cross_map_can_be_rectangular(self):
        c=FrameSpec('f:c',1,'GL','1')
        self.assertEqual(transport_cross_map(((1.,2.),),self.swap,((2.,),),self.a,c),((4.,2.),))
    def test_budget_and_migration(self):
        with self.assertRaises(ContractError):compose_path(self.packet,((self.swap,self.b),(self.swap,self.a)),StepBudget(max_steps=1))
        self.assertEqual(migrate_frame(self.packet,self.swap,self.b).frame.version,'2')
    def test_serialization_and_unsupported_migration(self):
        p={'schema_version':3,'frame_id':'f:a','frame_version':'1','target_frame_id':'f:b','dimension':2,'group':'GL','domain':['finite_vectors'],'state':[1,2],'operator':[[2,0],[0,3]],'readout':[[1,0]],'gauge':[[0,1],[1,0]],'condition_limit':10000}
        self.assertEqual(decode_payload(encode_payload(p)),p)
        old=dict(p,schema_version=2);self.assertEqual(migrate_payload(old,2),p)
        with self.assertRaises(ContractError):migrate_payload(old,1)
    def test_gate_precedes_any_tensor_access(self):
        with self.assertRaises(Exception):adapter.tensor_transport(None,None,None,None)
    def test_neural_source_is_lazy_and_gated(self):
        tree=ast.parse(Path(adapter.__file__).read_text())
        self.assertFalse(any(isinstance(x,(ast.Import,ast.ImportFrom)) and any(a.name.startswith(('torch','transformers')) for a in x.names) for x in tree.body))
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                imports=[x for x in ast.walk(node) if isinstance(x,ast.Import) and any(a.name=='torch' for a in x.names)]
                if imports:
                    gates=[x for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require_research_action']
                    self.assertTrue(gates)
                    self.assertLess(min(x.lineno for x in gates),min(x.lineno for x in imports))

if __name__=='__main__':unittest.main()
