import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h43_world_kernels.types import *
from latent_comm.mechanisms.h43_world_kernels.reference import *
from latent_comm.mechanisms.h43_world_kernels.serialization import *
import latent_comm.mechanisms.h43_world_kernels.adapter as adapter

class H43Contracts(unittest.TestCase):
    def test_component_ids_are_unique(self):
        left=self.sensor('same');right=replace(left,state_port='other')
        with self.assertRaises(ContractError):compose_kernels((left,right),self.noise())
    def test_observation_identities_are_nonempty_unique(self):
        row=(ConditionalRow('s','a',(),(1.,)),)
        for observations in (('o','o'),('', 'o')):
            with self.assertRaises(ContractError):WorldKernel('k','port',('s',),(('a','read'),),(),row,observations,((.2,.8),),'v1','public')
    def sensor(self,name):
        rows=tuple(ConditionalRow(s,'observe',(u,),(1.,0.) if u=='dry' else (0.,1.)) for s in ('0','1') for u in ('dry','wet'))
        return WorldKernel(name,name,('0','1'),(('observe','read-weather'),),('weather',),rows,('0','1'),eye(2),'1','public:world')
    def noise(self):return SharedNoiseJoint(('weather',),((('dry',),.5),(('wet',),.5)))
    def test_shared_noise_not_independent(self):
        k=compose_kernels((self.sensor('left'),self.sensor('right')),self.noise());self.assertEqual(dict(k.transitions)['observe'][0],(.5,0.,0.,.5))
        self.assertEqual(sum(dict(k.transitions)['observe'][0][i] for i in (0,3)),1.)
    def test_normalization_and_prediction_lineage(self):
        k=compose_kernels((self.sensor('left'),self.sensor('right')),self.noise());r=rollout(k,(1.,0.,0.,0.),('observe','observe'));self.assertEqual(r['parents'],('left','right'));self.assertIn('not_real',r['evidence_kind'])
        with self.assertRaises(ContractError):SharedNoiseJoint(('weather',),((('dry',),.4),))
    def test_action_and_port_conflicts(self):
        with self.assertRaises(ContractError):compose_kernels((self.sensor('same'),self.sensor('same')),self.noise())
        with self.assertRaises(ContractError):compose_kernels((self.sensor('a'),replace(self.sensor('b'),actions=(('observe','different'),))),self.noise())
    def test_migration_and_gate(self):
        k=migrate_kernel(self.sensor('a'),'2',{'0':'off','1':'on'});self.assertEqual(k.states,('off','on'))
        with self.assertRaises(Exception):adapter.tensor_shared_noise_compose(None,None,None,conditional_independence=True)
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
