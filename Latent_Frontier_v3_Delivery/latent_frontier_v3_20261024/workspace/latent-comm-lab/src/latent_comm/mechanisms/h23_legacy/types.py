from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.core.finite import vector,finite_scalar
@dataclass(frozen=True)
class DiscrepancyReport:
    report_id: str
    kind: str
    message_digest: str
    probe_ids: tuple[str,...]
    residual: tuple[float,...]
    missing_variables: tuple[str,...]
    conflicting_domains: tuple[str,...]
    evidence_errors: frozenset[str]
    permitted_summary_fields: frozenset[str]
    versions: VersionSet
    conflict_edge_witness: tuple[str,...]=()
    def __post_init__(self):
        if self.kind not in ('none','numeric','semantic_domain','missing_variable','evidence_error'):raise ContractError('InvalidDiscrepancy','disagreement classes remain distinct')
        if not self.report_id or not self.message_digest:raise ContractError('InvalidDiscrepancy','report must bind original message')
        for x in self.residual:finite_scalar(x)
        expected={'probe_ids','residual','missing_variables','conflicting_domains','evidence_errors','conflict_edge_witness'}
        if not self.permitted_summary_fields<=expected:raise ContractError('RoleLeakage','receiver private text or arbitrary metadata not permitted')
        for name in expected:
            if getattr(self,name) and name not in self.permitted_summary_fields:raise ContractError('RoleLeakage','summary field not explicitly authorized')
        if self.kind=='numeric' and (not self.residual or len(self.probe_ids)!=len(self.residual)):raise ContractError('ShapeMismatch','numeric report has one residual per allowed probe')
        if self.kind=='semantic_domain' and len(self.conflicting_domains)<2:raise ContractError('InvalidDiscrepancy','domain conflict needs distinct domains')
        if self.kind=='missing_variable' and not self.missing_variables:raise ContractError('InvalidDiscrepancy','missing variable names required')
        if self.kind=='evidence_error' and not self.evidence_errors:raise ContractError('InvalidDiscrepancy','evidence handle to retract required')
        self.versions.require('state','frame','ontology','task','evidence')
@dataclass(frozen=True)
class RepairPacket:
    report_id: str
    original_digest: str
    kind: str
    delta: tuple[float,...]
    remaining_residual: tuple[float,...]
    source_frame: str
    evidence_retractions: frozenset[str]
    required_action: str | None
    versions: VersionSet
    conflict_edge_witness: tuple[str,...]=()
    def __post_init__(self):
        for x in self.delta+self.remaining_residual:finite_scalar(x)
        if self.kind not in ('numeric','none','semantic_domain','missing_variable','evidence_error'):raise ContractError('InvalidRepair','repair kind must retain diagnostic meaning')
        if self.kind!='numeric' and self.delta:raise ContractError('SemanticMismatch','semantic/evidence defects cannot be patched as numeric noise')
@dataclass(frozen=True)
class RepairSession:
    state: tuple[float,...]
    original_digest: str
    applied_reports: frozenset[str]
    rounds: int
    feedback_bytes: int
    repair_bytes: int
    evidence: frozenset[str]
    versions: VersionSet
    status: str='open'
    def __post_init__(self):
        vector(self.state)
        if min(self.rounds,self.feedback_bytes,self.repair_bytes)<0:raise ContractError('InvalidSession','nonnegative round and byte accounting')
