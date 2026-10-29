"""X11: versioned concept birth/retirement with historical readers and atomic migration."""
from dataclasses import dataclass
from tempfile import TemporaryDirectory
import json
from latent_comm.core import ContractError,VersionSet
from latent_comm.mechanisms.h27_ontology.types import OntologySnapshot,ConceptDefinition,OntologyDelta
from latent_comm.mechanisms.h28_bifurcation.types import PhaseState,StructureTransition,BranchTrajectory
from latent_comm.mechanisms.h40_instruction_set.types import ISARevision,Expr
from .contracts import bounded_horizon,assumptions
ASSUMPTIONS=assumptions('An immutable historical ontology, explicit reader migration and structure-transition certificate exist.','Retired concepts retain their historical meaning; current readers cannot silently use removed identifiers.','A finite lifecycle graph commits ontology, reader and structure changes atomically and exports a base-ISA lowering.','Future model parameters may adapt to new concepts; deleting a registry entry is not proof of neural forgetting.')
@dataclass(frozen=True)
class LifecycleRequest:
    ontology: OntologySnapshot
    additions: tuple[ConceptDefinition,...]
    retired: tuple[str,...]
    reader_targets: tuple[tuple[str,str],...]
    next_ontology_version: str
    phase: PhaseState
    structure_transition: StructureTransition
    historical_concept: str
    record: dict
    isa: ISARevision
    reader_expression: Expr
    reader_inputs: tuple[tuple[str,float],...]
    versions: VersionSet
@dataclass(frozen=True)
class LifecycleRecord:
    delta: OntologyDelta
    structure: BranchTrajectory
    historical_value: bool | None
    current_value: bool | None
    lowered_reader: Expr
    reader_value: float
    lifecycle_edges: tuple[tuple[str,str,str],...]
    transaction_id: str
    status: str='VersionedLifecycleCommitted'
@bounded_horizon('X11',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.mechanisms.h27_ontology.reference import revise_ontology,read_concept
    from latent_comm.mechanisms.h28_bifurcation.reference import trace_control
    from latent_comm.mechanisms.h40_instruction_set.reference import lower,execute_base
    from latent_comm.mechanisms.h39_transactions.reference import VersionedStore
    from latent_comm.mechanisms.h39_transactions.types import CognitiveTransaction,VersionedCell
    q=request
    if q.ontology.version!=q.versions.ontology or q.isa.version!=q.versions.isa or len(q.additions)>4:raise ContractError('VersionMismatch','explicit current ontology/ISA and bounded additions required')
    delta=revise_ontology(q.ontology,q.next_ontology_version,q.additions,retire=q.retired,consumer_targets=q.reader_targets)
    historical=read_concept((q.ontology,),q.ontology.version,q.historical_concept,q.record)
    current=None if q.historical_concept in q.retired else read_concept((delta.after,),delta.after.version,q.historical_concept,q.record)
    if q.structure_transition.old_structure!=q.ontology.version or q.structure_transition.new_structure!=delta.after.version:raise ContractError('UnboundMigration','phase structure transition must name this exact ontology lifecycle')
    trajectory=trace_control(q.phase,(q.phase.alpha,),steps_per_control=1,transitions=((0,q.structure_transition),))
    lowered=lower(q.reader_expression,q.isa);value=execute_base(lowered,dict(q.reader_inputs));edges=[]
    for c in q.additions:
        meter.consume(steps=1);edges.extend((p,c.concept_id,'split_or_recombine') for p in c.parents);edges.append((delta.after.version,c.concept_id,'born'))
    for c in q.retired:edges.append((c,delta.after.version,'retired_historical_reader_retained'))
    payload=json.dumps({'before':delta.before.version,'after':delta.after.version,'readers':delta.reader_migrations,'retired':delta.retired,'structure_version':trajectory.states[-1].version},sort_keys=True)
    with TemporaryDirectory(prefix='latent-x11-') as directory:
        store=VersionedStore(directory);tx=CognitiveTransaction('concept-lifecycle',(('ontology:lifecycle',-1),('state:structure',-1)),(VersionedCell('ontology:lifecycle','ontology-migration',0,payload),VersionedCell('state:structure','structure-migration',0,payload)));store.commit(tx)
        if len(store.snapshot())!=2:raise ContractError('PartialCommit','ontology and structure must be visible together')
    return LifecycleRecord(delta,trajectory,historical,current,lowered,value,tuple(edges),'concept-lifecycle'),('Current absence is distinguished from a historical predicate value of false.','Lifecycle transaction is local one-process atomicity, not a claim of distributed consistency or parameter unlearning.')
