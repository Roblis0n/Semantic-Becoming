"""C07: versioned persistent evidence, calibrated readout, typed repair and revocation.
Trusted local grants are a separate host bootstrap argument in the reference
request. A message can only name a capability id; it cannot install one.
"""
from dataclasses import dataclass
import json
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h12_legacy.types import PersistentCapsule,QueryResult
from latent_comm.mechanisms.h15_legacy.types import ProtocolMember
from latent_comm.mechanisms.h23_legacy.types import DiscrepancyReport,RepairPacket,RepairSession
from latent_comm.mechanisms.h24_legacy.types import CapabilityGrant,ScopedCell,EffectAudit
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase
@dataclass(frozen=True)
class ScopedMemoryInput:
    capsule: PersistentCapsule
    query: tuple[str,str]
    current_dependencies: tuple[tuple[str,str],...]
    sender: ProtocolMember
    receiver: ProtocolMember
    installed_grants: tuple[CapabilityGrant,...]
    capability_id: str
    principal: str
    session_id: str
    target_cell: ScopedCell
    target_state_version: str
    withdrawn_before: frozenset[str]
    withdraw_after: frozenset[str]
    step: int
    versions: VersionSet
    capsule_lineage: tuple[PersistentCapsule,...]=()
@dataclass(frozen=True)
class ScopedMemory:
    request: ScopedMemoryInput
    grant: CapabilityGrant
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class CalibratedMemory:
    scoped: ScopedMemory
    query_result: QueryResult
    transmitted: tuple[float,...] | None
    @property
    def versions(self):return self.scoped.versions
@dataclass(frozen=True)
class MemoryRepair:
    calibrated: CalibratedMemory
    report: DiscrepancyReport | None
    repair: RepairPacket | None
    corrected: tuple[float,...] | None
    @property
    def versions(self):return self.calibrated.versions
@dataclass(frozen=True)
class AppliedMemory:
    repaired: MemoryRepair
    cell: ScopedCell
    audit: EffectAudit | None
    @property
    def versions(self):return self.repaired.versions
@dataclass(frozen=True)
class ScopedMemoryReadout:
    cell: ScopedCell
    audit: EffectAudit | None
    repair_report: DiscrepancyReport | None
    invalidated_capsules: tuple
    revoked_capabilities: tuple[str,...]
    status: str
    versions: VersionSet
    revocation_semantics: str='future access and dependent evidence invalidation, not physical erasure or neural unlearning'

def _authority(q):
    from latent_comm.mechanisms.h24_legacy.reference import CapabilityAuthority
    return CapabilityAuthority(q.installed_grants,session_id=q.session_id)
def _capsule_store(q):
    from latent_comm.mechanisms.h12_legacy.reference import CapsuleStore
    if len(q.capsule_lineage)>16:raise ContractError('BudgetExhausted','finite explicit capsule ancestry bound')
    store=CapsuleStore();pending=list(q.capsule_lineage)+( [q.capsule] )
    if len({(c.document_id,c.version) for c in pending})!=len(pending):raise ContractError('VersionConflict','capsule lineage identities must be unique')
    while pending:
        ready=[c for c in pending if (c.parent_version is None or (c.document_id,c.parent_version) in store.entries) and all(d in store.entries for d in c.capsule_dependencies)]
        if not ready:raise ContractError('MissingAncestor','supply existing parent/dependency capsules before any query write')
        for c in ready:store.add(c);pending.remove(c)
    return store

def scope_check(value):
    value.versions.require('state','frame','ontology','isa','world','task','evidence')
    store=_capsule_store(value);store.withdraw(value.withdrawn_before);store.get(value.capsule.document_id,value.capsule.version)
    grant=_authority(value).resolve(value.capability_id,principal=value.principal,step=value.step,versions=value.versions,withdrawn=value.withdrawn_before)
    if not value.capsule.evidence_handles<=grant.evidence_handles:raise ContractError('CapabilityDenied','capsule sources must be authorized by installed grant')
    if value.target_cell.slot_id not in grant.writable_slots or value.target_cell.type_tag not in grant.allowed_types:raise ContractError('CapabilityDenied','message cannot choose an unauthorized target')
    return ScopedMemory(value,grant)
def version_calibrate(value):
    from latent_comm.mechanisms.h12_legacy.reference import read_query
    from latent_comm.mechanisms.h15_legacy.reference import transmit
    q=value.request
    if q.sender.versions!=q.versions or q.receiver.versions!=q.versions:raise ContractError('VersionMismatch','protocol calibration bound to exact input versions')
    result=read_query(q.capsule,q.query,step=q.step,versions=q.versions,current_dependencies=dict(q.current_dependencies),withdrawn=q.withdrawn_before)
    data=None if result.value is None else transmit(q.sender,q.receiver,(result.value,),required={'scalar_query'})
    return CalibratedMemory(value,result,data)
def query_residual(value):
    from latent_comm.mechanisms.h23_legacy.reference import diagnose,integrity_digest,build_repair,apply_repair
    if value.transmitted is None:return MemoryRepair(value,None,None,None)
    q=value.scoped.request;payload=json.dumps({'capsule_id':q.capsule.capsule_id,'version':q.capsule.version,'query':q.query,'transmitted':value.transmitted},sort_keys=True,allow_nan=False).encode();digest=integrity_digest(payload)
    # This diagnostic uses an explicitly permitted analytic source-query scalar,
    # not a private downstream label or oracle. It is part of the finite fixture.
    report=diagnose(report_id='query:'+q.capsule.version,payload=payload,expected_digest=digest,probe_ids=('retained_query',),observed=value.transmitted,expected=(value.query_result.value,),allowed_fields={'probe_ids','residual'},versions=q.versions)
    repair=build_repair(report,((1.,),));session=RepairSession(value.transmitted,digest,frozenset(),0,0,0,q.capsule.evidence_handles,q.versions)
    corrected=apply_repair(session,report,repair,max_rounds=1)
    return MemoryRepair(value,report,repair,corrected.state)
def apply(value):
    from latent_comm.mechanisms.h24_legacy.reference import ScopedStateStore
    from latent_comm.mechanisms.h24_legacy.types import ScopedEffect
    q=value.calibrated.scoped.request
    if value.corrected is None:return AppliedMemory(value,q.target_cell,None)
    if len(value.corrected)!=1 or len(q.target_cell.value)!=1:raise ContractError('ShapeMismatch','C07 scalar query must bind a scalar cell')
    store=ScopedStateStore((q.target_cell,));effect=ScopedEffect(q.capability_id,'replace_affine',(q.target_cell.slot_id,),(q.target_cell.slot_id,),((0.,),),value.corrected,q.target_cell.type_tag)
    audit=store.apply(effect,_authority(q),principal=q.principal,step=q.step,versions=q.versions,new_version=q.target_state_version,withdrawn=q.withdrawn_before)
    return AppliedMemory(value,store.cells[q.target_cell.slot_id],audit)
def revoke(value):
    from latent_comm.mechanisms.h12_legacy.reference import CapsuleStore
    q=value.repaired.calibrated.scoped.request;authority=_authority(q);store=_capsule_store(q)
    affected=store.withdraw(q.withdraw_after)
    for grant in q.installed_grants:
        if grant.evidence_handles&q.withdraw_after:authority.revoke(grant.capability_id)
    if affected:status='DependentEvidenceAndFutureAccessInvalidated'
    elif value.audit is None:status='SourceLookupRequiredNoWrite'
    else:status='ScopedQueryApplied'
    return ScopedMemoryReadout(value.cell,value.audit,value.repaired.report,affected,tuple(sorted(authority.revoked)),status,q.versions)
STAGES=(('scope_check',('H24',),'ScopedMemoryInput','ScopedMemory','stop'),('version_calibrate',('H12','H15'),'ScopedMemory','CalibratedMemory','differentiable'),('query_residual',('H23',),'CalibratedMemory','MemoryRepair','stop'),('apply',('H24',),'MemoryRepair','AppliedMemory','stop'),('revoke',('H12','H24'),'AppliedMemory','ScopedMemoryReadout','stop'))
def build_graph(versions):return linear_graph('C07',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','isa','world','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),obligations=('Host bootstrap grants are not created by message content.','Revocation invalidates future access and evidence but does not claim erasure of already derived knowledge.','New models need adaptation; unseen pair is a separate claim.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (ScopedMemoryInput,ScopedMemory,CalibratedMemory,MemoryRepair,AppliedMemory,ScopedMemoryReadout)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h12_legacy.losses import LEDGER as H12
    from latent_comm.mechanisms.h15_legacy.losses import LEDGER as H15
    from latent_comm.mechanisms.h23_legacy.losses import LEDGER as H23
    from latent_comm.mechanisms.h24_legacy.losses import LEDGER as H24
    return {'recipe':'C07','research_state':'NOT_RUN','phases':[objective_phase('persistent_queries',(('H12',H12,tuple(s.name for s in H12)),)),objective_phase('population_protocol',(('H15',H15,tuple(s.name for s in H15)),)),objective_phase('typed_repair',(('H23',H23,tuple(s.name for s in H23)),)),objective_phase('local_scope',(('H24',H24,tuple(s.name for s in H24)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES}}
