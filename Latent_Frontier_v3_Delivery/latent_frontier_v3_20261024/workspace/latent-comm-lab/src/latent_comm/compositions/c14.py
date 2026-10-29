"""C14: private bifurcation branch, typed migration, atomic research-state publish."""
from dataclasses import dataclass,replace,asdict
import json
from tempfile import TemporaryDirectory
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h13_legacy.types import BranchState
from latent_comm.mechanisms.h22_legacy.types import PartitionState,PartitionAction,TransitionRecord
from latent_comm.mechanisms.h27_ontology.types import OntologySnapshot,ConceptDefinition,OntologyDelta
from latent_comm.mechanisms.h28_bifurcation.types import PhaseState,BranchTrajectory
from latent_comm.mechanisms.h39_transactions.types import VersionedCell,CognitiveTransaction,CommitRecord
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,_plain,objective_phase

@dataclass(frozen=True)
class StructureTransitionInput:
    branch: BranchState
    partition: PartitionState
    ontology: OntologySnapshot
    control_path: tuple[float,...]
    partition_action: PartitionAction
    concept_additions: tuple[ConceptDefinition,...]
    retire_concepts: tuple[str,...]
    reader_targets: tuple[tuple[str,str],...]
    new_ontology_version: str
    read_only_evidence: str
    concurrent_key: str | None
    crash_at: str | None
    rollback_after_commit: bool
    versions: VersionSet
@dataclass(frozen=True)
class MetaStateSnapshot:
    request: StructureTransitionInput
    cells: tuple[VersionedCell,...]
    read_versions: tuple[tuple[str,int],...]
    private_branch: BranchState
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class BifurcationCandidate:
    snapshot: MetaStateSnapshot
    trajectory: BranchTrajectory
    branch: BranchState
    @property
    def versions(self):return self.snapshot.versions
@dataclass(frozen=True)
class RewrittenStructure:
    candidate: BifurcationCandidate
    partition: TransitionRecord
    ontology: OntologyDelta
    @property
    def versions(self):return self.candidate.versions
@dataclass(frozen=True)
class PreparedMigration:
    rewritten: RewrittenStructure
    transaction: CognitiveTransaction
    invalidated_cache_refs: frozenset[str]
    reader_migrations: tuple
    @property
    def versions(self):return self.rewritten.versions
@dataclass(frozen=True)
class CheckedReadSet:
    migration: PreparedMigration
    visible_cells: tuple[VersionedCell,...]
    conflict_keys: tuple[str,...]
    @property
    def versions(self):return self.migration.versions
@dataclass(frozen=True)
class AtomicTransitionResult:
    status: str
    visible_cells: tuple[VersionedCell,...]
    proposed: PreparedMigration
    conflicts: tuple[str,...]
    recovery: tuple
    journal_phases: tuple[str,...]
    versions: VersionSet
    visibility_guarantee: str='single-coordinator local JSON atomic publish only'


def take_snapshot(value):
    from latent_comm.mechanisms.h13_legacy.reference import fork
    value.versions.require('state','ontology','isa','frame','task','evidence')
    if value.partition.versions!=value.versions or value.branch.versions!=value.versions or value.ontology.version!=value.versions.ontology:raise ContractError('VersionMismatch','all snapshot participants bind the same semantic context')
    if not 1<=len(value.control_path)<=8:raise ContractError('BudgetExhausted','C14 control fixture has one to eight control points')
    if value.concurrent_key not in (None,'state:partition','ontology:active','evidence:read_only') or value.crash_at not in (None,'after_prepare','after_publish'):raise ContractError('InvalidFixture','only declared finite conflict/crash points are supported')
    encode=lambda x:json.dumps(_plain(x),sort_keys=True,allow_nan=False)
    cells=(VersionedCell('state:partition','partition',0,encode(value.partition)),VersionedCell('ontology:active','ontology',0,encode(value.ontology)),VersionedCell('evidence:read_only','evidence',0,encode({'source':value.read_only_evidence})))
    return MetaStateSnapshot(value,cells,tuple((c.key,c.version) for c in cells),fork(value.branch,value.branch.branch_id+':candidate'))


def form_bifurcation(value):
    from latent_comm.mechanisms.h13_legacy.reference import write_slot
    from latent_comm.mechanisms.h28_bifurcation.reference import trace_control
    slots=dict(value.private_branch.base)
    if 'phase' not in slots or len(slots['phase'])!=1:raise ContractError('UnspecifiedDynamics','C14 binds an explicit scalar quartic phase slot')
    initial=PhaseState(value.request.control_path[0],slots['phase'],'quartic_phase',value.private_branch.branch_id,value.versions.state)
    trajectory=trace_control(initial,value.request.control_path,dt=.1,steps_per_control=2,budget=StepBudget(max_steps=16))
    branch=write_slot(value.private_branch,'phase',trajectory.states[-1].z,reads=('phase',),operation='bounded_quartic_flow',commutation_class='ordered_phase_flow')
    return BifurcationCandidate(value,trajectory,branch)


def rewrite_structure(value):
    from latent_comm.mechanisms.h22_legacy.reference import transition
    from latent_comm.mechanisms.h27_ontology.reference import revise_ontology
    q=value.snapshot.request
    partition=transition(q.partition,q.partition_action)
    ontology=revise_ontology(q.ontology,q.new_ontology_version,q.concept_additions,retire=q.retire_concepts,consumer_targets=q.reader_targets)
    # Both changes remain immutable private candidate objects. No shared cell
    # references the mutable builder or the candidate's Python object identity.
    partition=replace(partition,after=replace(partition.after,versions=replace(partition.after.versions,ontology=ontology.after.version)))
    return RewrittenStructure(value,partition,ontology)


def prepare_migration(value):
    from latent_comm.mechanisms.h22_legacy.reference import resolve_reference
    from latent_comm.mechanisms.h27_ontology.reference import read_concept
    q=value.candidate.snapshot.request
    for old in value.partition.invalidated_refs:
        try:resolve_reference(value.partition.after,old,actor=next(iter(q.partition_action.members)))
        except ContractError:pass
        else:raise ContractError('StaleReference','partition rewrite failed to invalidate an old reference')
    for reader,old,new in value.ontology.reader_migrations:
        # Resolve both historical and new typed definitions. Unknown values are
        # preserved; a reader migration is not silently reinterpreted as true.
        read_concept((value.ontology.before,),value.ontology.before.version,old,{})
        read_concept((value.ontology.after,),value.ontology.after.version,new,{})
    encode=lambda x:json.dumps(_plain(x),sort_keys=True,allow_nan=False)
    writes=(VersionedCell('ontology:active','ontology',1,encode(value.ontology.after)),VersionedCell('state:partition','partition',1,encode(value.partition.after)))
    tx=CognitiveTransaction('c14:publish',value.candidate.snapshot.read_versions,writes,(('ontology:active','state:partition'),))
    return PreparedMigration(value,tx,value.partition.closed_cache_refs,value.ontology.reader_migrations)


def check_read_versions(value):
    q=value.rewritten.candidate.snapshot.request;cells=value.rewritten.candidate.snapshot.cells
    if q.concurrent_key is not None:cells=tuple(replace(c,version=c.version+1) if c.key==q.concurrent_key else c for c in cells)
    actual={c.key:c.version for c in cells};conflicts=tuple(key for key,version in value.transaction.read_versions if actual.get(key,-1)!=version)
    return CheckedReadSet(value,cells,conflicts)


def commit_or_restore(value):
    from latent_comm.mechanisms.h39_transactions.reference import VersionedStore
    q=value.migration.rewritten.candidate.snapshot.request
    if value.conflict_keys:return AtomicTransitionResult('ConflictPreserved',value.visible_cells,value.migration,value.conflict_keys,(),(),q.versions)
    # Temporary local finite fixture exercises the actual H39 journal code, not
    # external accounts/files. Every read, including read-only evidence, is in tx.
    with TemporaryDirectory(prefix='c14-finite-') as directory:
        store=VersionedStore(directory)
        store.commit(CognitiveTransaction('c14:seed',tuple((c.key,-1) for c in value.visible_cells),value.visible_cells))
        recovery=();status='Committed'
        try:store.commit(value.migration.transaction,crash_at=q.crash_at)
        except ContractError as error:
            if q.crash_at is None or error.failure.code!='PartialCommit':raise
            recovery=store.recover();status='RecoveredCommitted' if recovery[-1][1]=='commit' else 'RecoveredAborted'
        if q.rollback_after_commit and status!='RecoveredAborted':
            store.rollback('c14:publish','c14:rollback');status='RolledBackWithNewCellVersions'
        cells=store.snapshot();phases=tuple(r['phase'] for r in store.records())
    return AtomicTransitionResult(status,cells,value.migration,(),recovery,phases,q.versions)

STAGES=(('take_snapshot',('H13','H39'),'StructureTransitionInput','MetaStateSnapshot','stop'),('form_bifurcation',('H13','H28'),'MetaStateSnapshot','BifurcationCandidate','stop'),('rewrite_structure',('H22','H27'),'BifurcationCandidate','RewrittenStructure','enumeration'),('prepare_migration',('H22','H27'),'RewrittenStructure','PreparedMigration','stop'),('check_read_versions',('H39',),'PreparedMigration','CheckedReadSet','stop'),('commit_or_restore',('H39',),'CheckedReadSet','AtomicTransitionResult','stop'))
def build_graph(versions):return linear_graph('C14',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','ontology','isa','frame','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),maximum_steps=64,obligations=('The graph version context is the immutable source snapshot; candidate versions are explicit nested objects.','Read-only dependencies participate in optimistic conflict validation.','No account, permission, filesystem authority or external action is rolled back.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (StructureTransitionInput,MetaStateSnapshot,BifurcationCandidate,RewrittenStructure,PreparedMigration,CheckedReadSet,AtomicTransitionResult)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h27_ontology.losses import LOSS_SPECS
    return {'recipe':'C14','research_state':'NOT_RUN','phases':[objective_phase('concept_proposal',(('H27',LOSS_SPECS,('distinction','behavior','description','drift')),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'nonlearnable_invariants':['version equality','capability bounds','atomic publication','historical reader resolution'],'branch_selection':'explicit finite control path, not claimed neural phase transition'}
