import unittest,sys,json
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError,StepBudget
from latent_comm.horizon import identity_continuum as x01,plural_worlds as x02,problem_invention as x03,plasticity_network as x04,language_ecology as x05,multiscale_cognition as x06,trajectory_semantics as x07,discovery_continuations as x08,shared_dreams as x09,cognitive_commons as x10,concept_lifecycle as x11,semantic_compiler as x12
from latent_comm.mechanisms.h25_gauge.types import FrameSpec
from latent_comm.mechanisms.h27_ontology.types import Predicate,ConceptDefinition,OntologySnapshot
from latent_comm.mechanisms.h29_questions.types import QuestionIR,PolynomialConstraint,TransformLibrary
from latent_comm.mechanisms.h30_analogy.types import TypedOperationGraph,TypedObject,FiniteOperation,AnalogyMorphism
from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM
from latent_comm.mechanisms.h35_renormalization.types import ScalePacket
from latent_comm.mechanisms.h40_instruction_set.types import Expr,ISARevision
from latent_comm.mechanisms.h45_identifiability.types import IdentificationState
from latent_comm.mechanisms.h48_evidence_genealogy.types import EvidenceAtom,SupportNode,ProvenanceGraph,DependenceModel
V=VersionSet(state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
def fixture_x01():
 from latent_comm.mechanisms.h22_legacy.types import StateCell,PartitionState
 from latent_comm.mechanisms.h05_legacy.types import ProgramOperation
 actors=frozenset({'a','b','c'});cell=StateCell('cell','scalar',(3.,),'f1',actors,actors,'p',0);partition=PartitionState((('p',actors),),(cell,),frozenset(),'s1',V)
 return x01.IdentityRequest(partition,'cell','a',FrameSpec('a',1,'GL','f1'),1.,(x01.Participant('b',FrameSpec('b',1,'GL','f2'),((2.,),)),x01.Participant('c',FrameSpec('c',1,'GL','f3'),((.5,),))),(ProgramOperation('double','y',('mul',('var','x'),('const',2.))),ProgramOperation('inc','z',('add',('var','y'),('const',1.)),('double',))),('source',),frozenset(),V)
def fixture_x02():
 from test_c10 import fixture
 q=fixture();atoms=tuple(EvidenceAtom('e:'+str(i),'source:'+str(i),'observed',.8) for i in (1,2,3));nodes=tuple(SupportNode('n'+str(i),'atom',(),'e:'+str(i)) for i in (1,2,3))+(SupportNode('root','and',('n1','n2','n3')),)
 return x02.PluralWorldRequest(q,ProvenanceGraph(atoms,nodes,'root','e1'),DependenceModel('unknown',tuple(a.atom_id for a in atoms)),q.versions)
def fixture_x03():
 graph=TypedOperationGraph((TypedObject('a','S'),TypedObject('b','S')),(FiniteOperation('next','S','S',(('a','b'),)),),'g1');morphism=AnalogyMorphism((('a','a'),('b','b')),(('next','next'),),(('S','S'),),('a','b'))
 return x03.InventionRequest(IdentificationState(('h1','h2'),(),(.5,.5),'t1'),(('h1',{'x':0}),('h2',{'x':1})),(Predicate('le','x',0),Predicate('le','x',2)),QuestionIR('q',('x',),((0.,1.),),(PolynomialConstraint(((1.,(1,)),),'ge',0.),),'t1'),TransformLibrary((),'rules1'),graph,graph,morphism,frozenset({'x'}),V)
def fixture_x04():
 from test_c13 import fixture
 q=fixture();world=TargetSCM((CausalModule('prob','unit',(),(),(),0.,()),),(),'w1');module=CausalModule('source','unit',(),(),(),.5,())
 # Future training metadata may omit an unrelated world axis; bind it explicitly.
 v=replace(q.versions,world='w1');q=replace(q,versions=v,source_adapter=replace(q.source_adapter,versions=v),target_adapter=replace(q.target_adapter,versions=v),teacher_traces=tuple(replace(t,versions=v) for t in q.teacher_traces))
 return x04.PlasticityNetworkRequest(q,module,world,'prob',(),'w2',(),Expr('multiply',(Expr('var',name='delta0'),Expr('var',name='delta0'))),ISARevision('i1',()),2.,v)
def fixture_x05():
 from test_c16 import fixture
 q=fixture();v=replace(q.versions,ontology='o1');q=replace(q,versions=v)
 return x05.EcologyRequest((q,),OntologySnapshot('o1',()),ISARevision('i1',()),v)
def scale_fixture():return ScalePacket(((1.,0.),),((1.,),(0.,)),((2.,0.),(0.,1.)),(0.,0.),((2.,),),(0.,),('x','detail'),('coarse',),'s1','scale1')
def fixture_x06():
 from latent_comm.mechanisms.h47_quotient.types import FiniteQuery
 return x06.MultiscaleRequest(scale_fixture(),(1.,5.),2,True,FrameSpec('source',1,'GL','f1'),FrameSpec('target',1,'GL','f2'),((3.,),),(FiniteQuery('parity','parity',0,'q1'),),.5,V)
def fixture_x07():
 from test_c15 import fixture
 q=fixture();return x07.TrajectoryRequest(q,q.versions)
def fixture_x08():
 return x08.DiscoveryRequest(QuestionIR('roots',('x',),((-2.,0.,2.),),(PolynomialConstraint(((1.,(2,)),),'eq',4.),),'t1',('public-equation',)),(-2,0,2),(),frozenset(),frozenset(),(1,1),V)
def fixture_x09():
 from test_c16 import fixture
 from latent_comm.mechanisms.h43_world_kernels.types import WorldKernel,ConditionalRow
 q=fixture();k=q.kernels[0];other=WorldKernel('light','light',('on',),k.actions,(),(ConditionalRow('on','go',(),(1.,)),),('on',),((1.,),),'w1',k.scope);q=replace(q,kernels=(k,other),start_state=('closed','on'))
 world=TargetSCM((CausalModule('p','unit',(),(),(),0.,()),),(),'w1');module=CausalModule('source','unit',(),(),(),1.,())
 return x09.DreamRequest(q,module,world,'p',(),(),q.edits[0],'synthetic:shared',q.versions)
def fixture_x10():
 from test_c18 import fixture
 from latent_comm.mechanisms.h18_legacy.types import PrimitiveNode,GraphCandidate
 q=fixture();v=replace(q.versions,isa='i1');q=replace(q,versions=v,exact_values=replace(q.exact_values,versions=v),hyperedge=replace(q.hyperedge,versions=v));graph=GraphCandidate('joint',(PrimitiveNode('r','input'),PrimitiveNode('w','input'),PrimitiveNode('out','product')),(('r','out',0),('w','out',1)),'out',(),v)
 return x10.CommonsRequest(q,graph,(('r','reader'),('w','writer')),(('reader','writer'),('reader',),('reader','writer')),v)
def fixture_x11():
 from latent_comm.mechanisms.h28_bifurcation.types import PhaseState,StructureTransition
 old=ConceptDefinition('old',Predicate('le','x',0),(),('source',),('x',));new=ConceptDefinition('new',Predicate('le','x',1),('old',),('source',),('x',));ontology=OntologySnapshot('o1',(old,),(('reader','old'),));phase=PhaseState(-1.,(.1,),'o1','b','phase1');transition=StructureTransition('phase1','phase2',((1.,),),'o1','o2',('old-cache',))
 return x11.LifecycleRequest(ontology,(new,),('old',),(('reader','new'),),'o2',phase,transition,'old',{'x':0},ISARevision('i1',()),Expr('var',name='x'),(('x',0.),),V)
def fixture_x12():
 from test_c20 import fixture
 q=fixture();return x12.SemanticCompilationRequest(q,scale_fixture(),(q.backend,),q.versions)
MODULES=(x01,x02,x03,x04,x05,x06,x07,x08,x09,x10,x11,x12)
class HorizonTests(unittest.TestCase):
 def assert_finite(self,index):
  q=globals()['fixture_x'+str(index).zfill(2)]();r=MODULES[index-1].run(q);self.assertEqual(r.status,'FiniteComplete',r.obligations);self.assertEqual(r.research_state,'NOT_RUN');self.assertLessEqual(r.consumed_steps,128);self.assertLessEqual(r.consumed_cases,64);self.assertTrue(json.loads(r.export_json())['object_digest']);return r.value
 def test_x01_identity(self):self.assertEqual(dict(self.assert_finite(1).continuation.values)['z'],7.)
 def test_x02_plural(self):self.assertFalse(self.assert_finite(2).theories.consensus_claimed)
 def test_x03_invention(self):self.assertEqual(len(self.assert_finite(3).measurements),1)
 def test_x04_plasticity(self):self.assertEqual(self.assert_finite(4).transport_residual,(0.,-1.))
 def test_x05_ecology(self):self.assertEqual(len(self.assert_finite(5).generations),1)
 def test_x06_multiscale(self):self.assertEqual(self.assert_finite(6).final.coarse,(4.,))
 def test_x07_trajectory(self):self.assertEqual(self.assert_finite(7).execution.signed_area,1.)
 def test_x08_unfinished(self):self.assertEqual(self.assert_finite(8).remaining_candidates,(2,))
 def test_x09_dream(self):self.assertTrue(self.assert_finite(9).archive.evidence.synthetic)
 def test_x10_commons(self):self.assertFalse(self.assert_finite(10).plans[1].joint_factor_available)
 def test_x11_lifecycle(self):self.assertIsNone(self.assert_finite(11).current_value)
 def test_x12_unbound(self):self.assertEqual(self.assert_finite(12).status,'UnboundBackend')
 def test_each_budget_stops_before_excess(self):
  for i,module in enumerate(MODULES,1):
   r=module.run(globals()['fixture_x'+str(i).zfill(2)](),budget=StepBudget(max_steps=1));self.assertLessEqual(r.consumed_steps,1);self.assertIn(r.status,('PartialBudgetExhausted','FiniteComplete'))
 def test_ecology_partial_never_registers_final_digest(self):
  q=fixture_x05();r=x05.run(q,budget=StepBudget(max_steps=1));self.assertEqual(r.status,'PartialBudgetExhausted');self.assertIsNone(r.object_digest);self.assertEqual(r.value.pending_generation,0)
  r=x05.run(replace(q,generations=q.generations+q.generations));self.assertEqual(r.status,'PartialBudgetExhausted');self.assertIsNone(r.object_reference);self.assertEqual(len(r.value.generations),1);self.assertEqual(r.value.pending_generation,1);self.assertLessEqual(r.consumed_steps,128)
 def test_identity_no_new_permission(self):
  q=fixture_x01();q=replace(q,participants=(replace(q.participants[0],actor='intruder'),))
  with self.assertRaises(ContractError):x01.run(q)
 def test_identity_blocked_program_still_migrates_snapshot_frame(self):
  q=fixture_x01();q=replace(q,program=(replace(q.program[0],dependencies=('missing',)),)+q.program[1:]);r=x01.run(q).value
  self.assertEqual(r.status,'ContinuationRetained');self.assertEqual(r.partition.versions.frame,'f3');self.assertEqual(r.continuation.versions.frame,'f3');self.assertEqual(r.partition.cells[0].frame,'f3');self.assertEqual(r.continuation.program_counter,0)
 def test_identity_partition_version_is_not_invented(self):
  q=fixture_x01()
  with self.assertRaises(ContractError):x01.run(replace(q,partition=replace(q.partition,version='stale-state')))
 def test_invention_no_hidden_measurement(self):
  q=fixture_x03();q=replace(q,allowed_observable_fields=frozenset())
  with self.assertRaises(ContractError):x03.run(q)
 def test_plasticity_budget_must_be_finite(self):
  for maximum in (float('nan'),float('inf'),-1.):
   with self.assertRaises(ContractError):x04.run(replace(fixture_x04(),maximum_budget_cost=maximum))
 def test_scale_missing_detail_is_not_inverse(self):
  q=fixture_x06();bad=replace(q.scale,micro_dynamics=((2.,1.),(0.,1.)))
  with self.assertRaises(ContractError):x06.run(replace(q,scale=bad,retain_detail=False))
 def test_dream_never_real_namespace(self):
  with self.assertRaises(ContractError):x09.run(replace(fixture_x09(),namespace='observed:real'))
 def test_lifecycle_no_dangling_reader(self):
  with self.assertRaises(ContractError):x11.run(replace(fixture_x11(),reader_targets=()))
 def test_semantic_dead_code_pass_has_actual_transform(self):
  from latent_comm.mechanisms.h07_legacy.types import Instruction
  from latent_comm.mechanisms.h07_legacy.reference import compile_program
  result=x12.run(fixture_x12()).value;program=result.plan.plan.program;state_type=dict(program.packet.input_types)['initial'];unused=Instruction('unused','READ_SLOT',('initial',),state_type)
  expanded=compile_program(replace(program.packet,nodes=program.packet.nodes+(unused,)));optimized,removed=x12.eliminate_dead_pure_nodes(expanded)
  self.assertEqual(removed,('unused',));self.assertEqual(optimized.packet,program.packet)
 def test_no_neural_modules_loaded(self):self.assertFalse(set(sys.modules)&{'torch','transformers','jax','tensorflow','flax'})
if __name__=='__main__':unittest.main()
