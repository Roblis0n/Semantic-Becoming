"""C12: physically typed causal graft → shared-noise kernel → do/condition."""
from dataclasses import dataclass,replace
from itertools import product
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h09_legacy.types import CausalQuery
from latent_comm.mechanisms.h17_legacy.types import GroundedObject,FrameTransform
from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM,BoundaryBinding,GraftCertificate
from latent_comm.mechanisms.h43_world_kernels.types import SharedNoiseJoint,ConditionalRow,WorldKernel,ComposedWorldKernel
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference

@dataclass(frozen=True)
class ScientificWorldInput:
    source_module: CausalModule
    target: TargetSCM
    target_node: str
    boundary: tuple[BoundaryBinding,...]
    boundary_observation: GroundedObject
    physical_transform: FrameTransform
    output_scale: float
    output_offset: float
    new_world_version: str
    noise_distribution: tuple
    interventions: tuple[tuple[str,tuple[tuple[str,float],...]],...]
    query: CausalQuery
    versions: VersionSet

@dataclass(frozen=True)
class SourceEquations:
    request: ScientificWorldInput
    topological_order: tuple
    @property
    def versions(self):return self.request.versions

@dataclass(frozen=True)
class PhysicalBoundary:
    equations: SourceEquations
    converted_observation: GroundedObject
    @property
    def versions(self):return self.equations.versions

@dataclass(frozen=True)
class GraftedWorld:
    boundary: PhysicalBoundary
    certificate: GraftCertificate
    @property
    def versions(self):return replace(self.boundary.versions,world=self.certificate.after.version)

@dataclass(frozen=True)
class JointKernelPlan:
    graft: GraftedWorld
    kernel: ComposedWorldKernel
    variable_order: tuple[str,...]
    state_values: tuple[tuple[str,tuple[tuple[str,float],...]],...]
    action_assignments: tuple
    @property
    def versions(self):return self.graft.versions

@dataclass(frozen=True)
class HypotheticalConsequence:
    distribution: tuple
    kernel_distribution: tuple
    semantics: str
    version: str
    rollback_world: TargetSCM
    provenance: tuple[str,...]
    versions: VersionSet
    evidence_kind: str='synthetic_model_prediction_not_real_observation'


def source_equations(value):
    from latent_comm.mechanisms.h31_grafting.reference import validate_scm
    value.versions.require('frame','world','task','evidence')
    if value.target.version!=value.versions.world or value.boundary_observation.versions.world!=value.target.version:raise ContractError('VersionMismatch','source snapshot world is not the target observation world')
    if not 1<=len(value.target.modules)<=3 or not 1<=len(value.noise_distribution)<=4 or len(value.interventions)>2:raise ContractError('BudgetExhausted','C12 finite compilation declares at most three variables/four noise assignments/two interventions')
    return SourceEquations(value,validate_scm(value.target))


def convert_boundary(value):
    from latent_comm.mechanisms.h17_legacy.reference import transform_object
    q=value.request
    # The physical map converts target-boundary observations into source-module
    # units. Latent frame changes are a different operation and cannot substitute.
    if any(b.target_unit!=q.physical_transform.source.unit or b.source_unit!=q.physical_transform.target.unit for b in q.boundary):raise ContractError('UnitConflict','physical observation map and causal boundary units disagree')
    if q.physical_transform.linear!=((1.,0.),(0.,1.)) or q.physical_transform.translation!=(0.,0.):raise ContractError('BoundaryMismatch','this scalar causal binding requires an explicitly axis-aligned scale; compile a vector module for rotations/translations')
    if any(abs(b.scale-q.physical_transform.unit_scale)>1e-12 or b.offset!=0 for b in q.boundary):raise ContractError('UnitConflict','causal scale differs from physical boundary conversion')
    converted=transform_object(q.boundary_observation,q.physical_transform,target_versions=replace(q.boundary_observation.versions,frame=q.physical_transform.target.frame_id))
    if converted.position is None:raise ContractError('UnknownPosition','an occluded boundary is not an observed zero')
    return PhysicalBoundary(value,converted)


def graft_module(value):
    from latent_comm.mechanisms.h31_grafting.reference import graft
    q=value.equations.request
    unit=next(m.unit for m in q.target.modules if m.output==q.target_node)
    certificate=graft(q.source_module,q.target,q.target_node,q.boundary,q.new_world_version,output_scale=q.output_scale,output_offset=q.output_offset,target_unit=unit)
    return GraftedWorld(value,certificate)


def compile_joint_kernel(value):
    from latent_comm.mechanisms.h31_grafting.reference import evaluate_scm,validate_scm
    from latent_comm.mechanisms.h43_world_kernels.reference import compose_kernels
    q=value.boundary.equations.request;world=value.certificate.after;order=validate_scm(world)
    actions=(('observe',()),)+q.interventions
    if len(dict(actions))!=len(actions):raise ContractError('ActionMismatch','action IDs are unique; observe cannot be overwritten')
    if any(set(dict(noise))!=set(world.noise_ids) for noise,_ in q.noise_distribution):raise ContractError('NoiseIdentityConflict','one joint noise assignment must bind every shared identity')
    encoded_noise=tuple((tuple(str(dict(noise)[identity]) for identity in world.noise_ids),p) for noise,p in q.noise_distribution)
    noise_joint=SharedNoiseJoint(world.noise_ids,encoded_noise)
    outputs={}
    for name,assignment in actions:
        for noise,_ in q.noise_distribution:
            key=tuple(str(dict(noise)[identity]) for identity in world.noise_ids)
            outputs[(name,key)]=dict(evaluate_scm(world,dict(noise),assignment,budget=StepBudget(max_steps=3)))
    states={variable:tuple(sorted({record[variable] for record in outputs.values()})) for variable in order}
    encoded={variable:tuple((f'{variable}:{i}',number) for i,number in enumerate(numbers)) for variable,numbers in states.items()}
    joint_count=1
    for variable in order:joint_count*=len(states[variable])
    if joint_count*len(actions)*len(encoded_noise)>64:raise ContractError('BudgetExhausted','expanded joint kernel exceeds declared C12 fixture construction budget')
    semantics=tuple((name,'observational resampling' if name=='observe' else 'do:'+repr(assignment)) for name,assignment in actions);kernels=[]
    for variable in order:
        labels=tuple(label for label,_ in encoded[variable]);numbers=states[variable];rows=[]
        for state in labels:
            for action,_ in actions:
                for noise,_ in encoded_noise:
                    number=outputs[(action,noise)][variable]
                    rows.append(ConditionalRow(state,action,noise,tuple(float(x==number) for x in numbers)))
        observation=tuple(tuple(float(i==j) for j in range(len(labels))) for i in range(len(labels)))
        # All causal parent effects were compiled by the SCM. Each component is
        # deterministic conditional on the SAME joint noise, never independently redrawn.
        kernels.append(WorldKernel('scm:'+variable,variable,labels,semantics,world.noise_ids,tuple(rows),labels,observation,world.version,'synthetic-scientific-world'))
    kernel=compose_kernels(tuple(kernels),noise_joint,new_version=world.version,budget=StepBudget(max_steps=64))
    return JointKernelPlan(value,kernel,order,tuple(encoded.items()),actions)


def plan_intervention(value):
    from latent_comm.mechanisms.h09_legacy.reference import query_distribution
    from latent_comm.mechanisms.h31_grafting.reference import rollback
    q=value.graft.boundary.equations.request;world=value.graft.certificate.after;query=q.query
    distribution=query_distribution(world,q.noise_distribution,query,budget=StepBudget(max_steps=32,max_cases=4))
    if query.semantics=='do':
        action=next((name for name,assignments in value.action_assignments if assignments==query.assignments and name!='observe'),None)
        if action is None:raise ContractError('ActionMismatch','requested intervention was not compiled/authorized')
    else:action='observe'
    probabilities=dict(value.kernel.transitions)[action][0];decoded={k:dict(v) for k,v in value.state_values};counts={};mass=0.
    for state,p in zip(value.kernel.states,probabilities):
        values={name:decoded[name][label] for name,label in zip(value.variable_order,state)}
        if query.semantics=='condition' and any(values[k]!=x for k,x in query.assignments):continue
        counts[values[query.outcome]]=counts.get(values[query.outcome],0.)+p;mass+=p
    if mass==0:raise ContractError('ImpossibleObservation','kernel conditioning event has zero probability')
    marginal=tuple(sorted((x,p/mass) for x,p in counts.items() if p>0))
    # The two paths aggregate normalized floating-point masses in different
    # orders. Compare each outcome numerically; absent zero-mass keys are equal.
    source=dict(distribution);composed=dict(marginal)
    if any(abs(source.get(outcome,0.)-composed.get(outcome,0.))>1e-9 for outcome in source.keys()|composed.keys()):
        raise ContractError('CompositionMismatch','SCM and shared-noise kernel consequence differ')
    before=rollback(value.graft.certificate,world)
    return HypotheticalConsequence(distribution,marginal,query.semantics,world.version,before,value.kernel.component_ids,value.versions)


STAGES=(('source_equations',('H09','H31'),'ScientificWorldInput','SourceEquations','stop'),('convert_boundary',('H17',),'SourceEquations','PhysicalBoundary','stop'),('graft_module',('H31',),'PhysicalBoundary','GraftedWorld','stop'),('compile_joint_kernel',('H43',),'GraftedWorld','JointKernelPlan','enumeration'),('plan_intervention',('H09','H43'),'JointKernelPlan','HypotheticalConsequence','stop'))
def build_graph(versions,new_world_version=None):
    graph=linear_graph('C12',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','frame','world','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('Kernel compilation is finite affine-SCM resampling, not an unbounded causal world model.','All consequences are synthetic; unit conversion is not causal identification.'))
    new=replace(versions,world=new_world_version) if new_world_version is not None else versions
    return replace(graph,objects=tuple(replace(o,versions=new) if o.object_id in {'graft_module:out','compile_joint_kernel:out','plan_intervention:out'} else o for o in graph.objects))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions,request.new_world_version),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (ScientificWorldInput,SourceEquations,PhysicalBoundary,GraftedWorld,JointKernelPlan,HypotheticalConsequence)},budget=budget)
def describe_training():
    from .contracts import objective_phase
    from latent_comm.mechanisms.h31_grafting.losses import LOSS_SPECS as H31
    from latent_comm.mechanisms.h43_world_kernels.losses import LOSS_SPECS as H43
    return {'recipe':'C12','research_state':'NOT_RUN','phases':[
        objective_phase('structural_boundary',(('H31',H31,('graft', 'boundary')),)),
        objective_phase('world_kernel',(('H43',H43,('transition', 'observation', 'shared_noise', 'multistep')),)),
    ],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'frozen':['base_models','immutable_source_definitions'],'structure_search':'enumeration is distinct from differentiable phases','execution':'unified gated runner only; no joint global loss by default'}
