import unittest
from dataclasses import replace
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c12 import *
from latent_comm.mechanisms.h17_legacy.types import PhysicalFrame

def fixture(semantics='do'):
 v=VersionSet(frame='f1',world='w1',task='t1',evidence='e1')
 x=CausalModule('X','m',(),(),(),0.,(('u',1.),));y=CausalModule('Y','m',('X',),('m',),(0.,),0.,())
 world=TargetSCM((x,y),('u',),'w1');source=CausalModule('source_y','m',('source_x',),('cm',),(.01,),0.,(('u',1.),))
 targetframe=PhysicalFrame('physical-m','m','right','visible_position','latent-target');sourceframe=PhysicalFrame('physical-cm','cm','right','visible_position','latent-source')
 observation=GroundedObject('boundary',(.5,0.),((.01,0.),(0.,.01)),targetframe,0.,'observed',v)
 transform=FrameTransform(targetframe,sourceframe,((1.,0.),(0.,1.)),(0.,0.),100.)
 query=CausalQuery(semantics,(('X',1.),) if semantics!='observe' else (),'Y',replace(v,world='w2'))
 return ScientificWorldInput(source,world,'Y',(BoundaryBinding('source_x','X','cm','m',100.,0.),),observation,transform,1.,0.,'w2',(((('u',0.),),.5),((('u',1.),),.5)),(('force_x_one',(('X',1.),)),),query,v)
class C12Tests(unittest.TestCase):
 def test_shared_noise_do_not_condition(self):
  do=run_reference(fixture()).value;condition=run_reference(fixture('condition')).value
  self.assertEqual(do.distribution,((1.,.5),(2.,.5)));self.assertEqual(condition.distribution,((2.,1.),));self.assertEqual(do.distribution,do.kernel_distribution)
  self.assertEqual(do.rollback_world.version,'w1');self.assertIn('synthetic',do.evidence_kind)
 def test_observational_dependence(self):
  r=run_reference(fixture('observe'));self.assertEqual(r.value.distribution,((0.,.5),(2.,.5)));self.assertEqual(len(r.audit),5)
 def test_probability_mass_is_invariant_to_noise_row_order(self):
  q=fixture('observe')
  x=replace(q.target.modules[0],noise_terms=(('u',1.),));y=replace(q.target.modules[1],coefficients=(0.,))
  target=replace(q.target,modules=(x,y),noise_ids=('u','v'))
  source=replace(q.source_module,coefficients=(0.,),noise_terms=(('v',1.),))
  atoms=(((('u',1.),('v',0.)),.2),((('u',0.),('v',1.)),.4),((('u',1.),('v',1.)),.3),((('u',0.),('v',0.)),.1))
  q=replace(q,target=target,source_module=source,noise_distribution=atoms,interventions=())
  for rows in (atoms,tuple(reversed(atoms))):
   result=run_reference(replace(q,noise_distribution=rows)).value
   self.assertAlmostEqual(dict(result.distribution)[0.],.3)
   self.assertAlmostEqual(dict(result.distribution)[1.],.7)
   self.assertAlmostEqual(dict(result.kernel_distribution)[0.],.3)
   self.assertAlmostEqual(dict(result.kernel_distribution)[1.],.7)
 def test_unit_mismatch(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,boundary=(replace(q.boundary[0],scale=1.),)))
 def test_unknown_noise(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,source_module=replace(q.source_module,noise_terms=(('new-independent',1.),))))
 def test_uncompiled_intervention(self):
  q=fixture();q=replace(q,query=replace(q.query,assignments=(('X',0.),)))
  with self.assertRaises(ContractError):run_reference(q)
 def test_bound_versions(self):
  q=fixture();ir=lower_plan(build_graph(q.versions,'w2'));self.assertEqual(dict(ir.objects)['graft_module:out'].versions.world,'w2')
if __name__=='__main__':unittest.main()
