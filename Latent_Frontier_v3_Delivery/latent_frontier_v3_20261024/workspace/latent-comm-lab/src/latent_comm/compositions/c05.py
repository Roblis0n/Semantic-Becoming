"""C05: relation matching, local latent charts and physically typed synthetic action."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.core.finite import matvec,norm,sub
from latent_comm.mechanisms.h06_legacy.types import Chart,Transition
from latent_comm.mechanisms.h08_legacy.types import RelationPacket,MatchResult
from latent_comm.mechanisms.h17_legacy.types import GroundedObject,FrameTransform
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase
@dataclass(frozen=True)
class RelationalGroundingInput:
    source_relations: RelationPacket
    target_relations: RelationPacket
    source_objects: tuple[GroundedObject,...]
    target_objects: tuple[GroundedObject,...]
    physical_transform: FrameTransform
    source_chart: Chart
    target_chart: Chart
    latent_transition: Transition
    source_action_state: tuple[float,...]
    source_action_readout: tuple
    target_action_readout: tuple
    action_object: str
    task_family: str
    next_timestamp: float
    versions: VersionSet
@dataclass(frozen=True)
class ExtractedRelations:
    request: RelationalGroundingInput
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class AnchoredMatch:
    relations: ExtractedRelations
    matches: MatchResult
    target_object_id: str | None
    @property
    def versions(self):return self.relations.versions
@dataclass(frozen=True)
class GroundedChartAction:
    match: AnchoredMatch
    source_displacement: tuple[float,...] | None
    target_displacement: tuple[float,...] | None
    @property
    def versions(self):return self.match.versions
@dataclass(frozen=True)
class ModalActionReadout:
    mapping_candidates: tuple
    changed_object: GroundedObject | None
    after_relations: tuple
    status: str
    versions: VersionSet
    action_kind: str='finite_synthetic_translation_not_robot_or_model_execution'

def relation_extract(value):
    from latent_comm.mechanisms.h17_legacy.reference import spatial_relation
    if len(value.source_objects)>4 or len(value.target_objects)>4:raise ContractError('BudgetExhausted','C05 finite matching has at most four physical objects per side')
    axes=('world','task','ontology','evidence')
    value.versions.require(*axes)
    for packet,objects,chart,physical in ((value.source_relations,value.source_objects,value.source_chart,value.physical_transform.source),(value.target_relations,value.target_objects,value.target_chart,value.physical_transform.target)):
        if not packet.versions.matches(value.versions,axes) or not chart.versions.matches(value.versions,axes) or packet.versions.frame!=chart.versions.frame or physical.latent_frame_id!=chart.versions.frame:raise ContractError('VersionMismatch','physical, relation and chart contexts need a shared world/task/ontology/evidence binding with explicit side frame')
        if any(not o.versions.matches(value.versions,axes) or o.versions.frame!=chart.versions.frame or o.frame!=physical for o in objects):raise ContractError('VersionMismatch','stale or differently framed physical observations cannot be attached by numeric identity alone')
        if len({o.object_id for o in objects})!=len(objects):raise ContractError('DuplicateBinding','physical object identity must be unique on each side')
        lookup={o.object_id:o for o in objects}
        if set(lookup)!={n.node_id for n in packet.nodes}:raise ContractError('AnchorMismatch','relation graph must refer to these exact physical object identities')
        for edge in packet.edges:
            if edge.semantics=='spatial' and edge.relation in ('right','left','aligned'):
                relation=spatial_relation(lookup[edge.source],lookup[edge.target])
                if relation=='unknown' or relation[0]!=edge.relation:raise ContractError('UnverifiedRelation','asserted directional relation differs from current physical observations')
    if value.action_object not in {o.object_id for o in value.source_objects}:raise ContractError('UnknownObject','action source object absent')
    return ExtractedRelations(value)

def anchor_match(value):
    from latent_comm.mechanisms.h08_legacy.reference import match_nodes
    from latent_comm.mechanisms.h17_legacy.reference import transform_object
    q=value.request;matches=match_nodes(q.source_relations,q.target_relations,preserved_semantics=('spatial',),budget=StepBudget(max_steps=24,max_cases=24))
    if len(matches.mappings)!=1 or not matches.exhaustive:return AnchoredMatch(value,matches,None)
    mapping=dict(matches.mappings[0]);target={o.object_id:o for o in q.target_objects}
    for source in q.source_objects:
        observed=target[mapping[source.object_id]]
        converted=transform_object(source,q.physical_transform,target_versions=observed.versions)
        if converted.frame!=observed.frame or converted.timestamp!=observed.timestamp:raise ContractError('UnalignedObservation','matched physical anchors have different frames or times')
        if converted.position is not None and observed.position is not None and norm(sub(converted.position,observed.position))>1e-8:raise ContractError('AnchorMismatch','latent matching does not override inconsistent physical anchor coordinates')
    return AnchoredMatch(value,matches,mapping[q.action_object])

def chart_bind(value):
    from latent_comm.mechanisms.h06_legacy.reference import encode,transition,write_back
    from latent_comm.mechanisms.h17_legacy.reference import transform_displacement
    if value.target_object_id is None:return GroundedChartAction(value,None,None)
    q=value.relations.request
    source=encode(q.source_chart,q.source_action_state,task=q.task_family,model_revision=q.source_chart.model_revision)
    target=transition(source,q.latent_transition,q.source_chart,q.target_chart,task=q.task_family)
    target_check=encode(q.target_chart,write_back(q.target_chart,target),task=q.task_family,model_revision=q.target_chart.model_revision)
    if norm(sub(target_check,target))>1e-9:raise ContractError('IrrecoverableDetail','target chart cannot read its proposed action state')
    source_action=matvec(q.source_action_readout,source);target_action=matvec(q.target_action_readout,target)
    physical=transform_displacement(source_action,q.physical_transform)
    if norm(sub(physical,target_action))>1e-9:raise ContractError('UnitConflict','latent chart action readout and physical unit conversion do not commute')
    return GroundedChartAction(value,source_action,target_action)

def modal_action(value):
    from latent_comm.mechanisms.h17_legacy.reference import apply_synthetic_action,spatial_relation
    q=value.match.relations.request
    if value.target_displacement is None:return ModalActionReadout(value.match.matches.mappings,None,(),'AmbiguousOrUnmatchedNoAction',q.versions)
    obj=next(o for o in q.target_objects if o.object_id==value.match.target_object_id)
    changed=apply_synthetic_action(obj,value.target_displacement,unit=q.physical_transform.target.unit,next_timestamp=q.next_timestamp)
    # Compare at a common simulated timestamp without claiming a new observation.
    from dataclasses import replace
    relations=tuple((changed.object_id,o.object_id,spatial_relation(changed,replace(o,timestamp=q.next_timestamp))) for o in q.target_objects if o.object_id!=changed.object_id)
    return ModalActionReadout(value.match.matches.mappings,changed,relations,'SyntheticActionWithPhysicalContract',q.versions)

STAGES=(('relation_extract',('H08','H17'),'RelationalGroundingInput','ExtractedRelations','stop'),('anchor_match',('H08','H17'),'ExtractedRelations','AnchoredMatch','enumeration'),('chart_bind',('H06','H17'),'AnchoredMatch','GroundedChartAction','differentiable'),('modal_action',('H17',),'GroundedChartAction','ModalActionReadout','stop'))
def build_graph(versions):return linear_graph('C05',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','frame','ontology','world','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),obligations=('Latent coordinates and physical units are distinct contracts.','Ambiguous relation matches preserve alternatives and issue no action.','A spatial edge is not a structural causal intervention certificate.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (RelationalGroundingInput,ExtractedRelations,AnchoredMatch,GroundedChartAction,ModalActionReadout)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h06_legacy.losses import LEDGER as H06
    from latent_comm.mechanisms.h08_legacy.losses import LEDGER as H08
    from latent_comm.mechanisms.h17_legacy.losses import LEDGER as H17
    return {'recipe':'C05','research_state':'NOT_RUN','phases':[objective_phase('local_chart',(('H06',H06,tuple(s.name for s in H06)),)),objective_phase('relational_alignment',(('H08',H08,tuple(s.name for s in H08)),)),objective_phase('physical_grounding',(('H17',H17,tuple(s.name for s in H17)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'unsupported_claim':'no real vision, action model or robot execution'}
