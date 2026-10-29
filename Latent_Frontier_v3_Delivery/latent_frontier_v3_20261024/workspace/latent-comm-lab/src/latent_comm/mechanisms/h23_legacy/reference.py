from dataclasses import asdict,replace
import hashlib,json
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import matrix,vector,matvec,sub,add,norm,least_squares,scale
from .types import DiscrepancyReport,RepairPacket

def integrity_digest(payload):return hashlib.sha256(payload).hexdigest()
def verify_integrity(payload,expected):
    if integrity_digest(payload)!=expected:raise ContractError('ByteIntegrityFailure','transport retransmission required; semantic repair cannot edit checksum')
    return True

def diagnose(*,report_id,payload,expected_digest,probe_ids,observed,expected,allowed_fields,versions,domains=(),missing=(),evidence_errors=frozenset(),tolerance=1e-9):
    verify_integrity(payload,expected_digest)
    residual=sub(vector(observed),vector(expected)) if observed or expected else ()
    if evidence_errors:kind='evidence_error'
    elif len(set(domains))>1:kind='semantic_domain'
    elif missing:kind='missing_variable'
    elif norm(residual)>tolerance:kind='numeric'
    else:kind='none'
    return DiscrepancyReport(report_id,kind,expected_digest,tuple(probe_ids),residual,tuple(missing),tuple(domains),frozenset(evidence_errors),frozenset(allowed_fields),versions)

def build_repair(report,response_jacobian=None,*,budget=StepBudget()):
    if report.kind=='numeric':
        if response_jacobian is None:raise ContractError('UnboundResponse','numeric correction needs a declared local behavior response')
        a=matrix(response_jacobian)
        if len(a)!=len(report.residual):raise ContractError('ShapeMismatch','response rows must match permitted probes')
        meter=budget.meter();meter.consume(steps=len(a));meter.dimension(len(a[0]))
        solved=least_squares(a,scale(report.residual,-1.));delta=solved.solution;remaining=add(report.residual,matvec(a,delta))
        action=None if norm(remaining)<1e-9 else 'unreachable_residual_preserved'
    else:
        delta=();remaining=report.residual
        action={'none':None,'semantic_domain':'explicit_domain_map_or_ontology_revision','missing_variable':'explicit_variable_and_ontology_binding','evidence_error':'retract_source_and_recompute_dependents'}[report.kind]
    return RepairPacket(report.report_id,report.message_digest,report.kind,delta,remaining,report.versions.frame,report.evidence_errors if report.kind=='evidence_error' else frozenset(),action,report.versions,report.conflict_edge_witness)

def wire_bytes(obj):
    def normalize(x):
        if isinstance(x,(set,frozenset)):return sorted(x)
        raise TypeError(type(x).__name__)
    return json.dumps(asdict(obj),sort_keys=True,separators=(',',':'),default=normalize,allow_nan=False).encode()
def apply_repair(session,report,repair,*,max_rounds):
    if not 1<=max_rounds<=128:raise ContractError('BudgetExhausted','finite repair round limit')
    if session.status=='closed' or session.rounds>=max_rounds:raise ContractError('RepairRoundLimit','repair conversation ended')
    if repair.report_id!=report.report_id or report.message_digest!=session.original_digest or repair.original_digest!=session.original_digest:raise ContractError('StaleRepair','reply must bind exact original payload/report')
    if not repair.versions.matches(session.versions,('state','frame','ontology','task','evidence')):raise ContractError('VersionMismatch','stale response needs recomputation, not raw residual addition')
    if repair.conflict_edge_witness!=report.conflict_edge_witness or repair.kind!=report.kind or not report.versions.matches(session.versions,('state','frame','ontology','task','evidence')) or repair.source_frame!=report.versions.frame or repair.evidence_retractions!=(report.evidence_errors if report.kind=='evidence_error' else frozenset()):raise ContractError('SemanticMismatch','report/reply kind, versions, frame and exact retractions must agree before any effect')
    feedback=session.feedback_bytes+len(wire_bytes(report));reply=session.repair_bytes+len(wire_bytes(repair))
    if report.report_id in session.applied_reports:return replace(session,feedback_bytes=feedback,repair_bytes=reply,status='duplicate_ignored')
    state=session.state;evidence=session.evidence
    if repair.kind=='numeric':
        if repair.source_frame!=session.versions.frame:raise ContractError('FrameMismatch','numeric residual in different coordinates')
        state=add(state,repair.delta)
    elif repair.kind=='evidence_error':evidence=evidence-repair.evidence_retractions
    status='repair_applied' if repair.kind=='numeric' else ('no_repair_needed' if repair.kind=='none' else repair.required_action)
    return replace(session,state=state,evidence=evidence,applied_reports=session.applied_reports|{report.report_id},rounds=session.rounds+1,feedback_bytes=feedback,repair_bytes=reply,status=status)

def sheaf_conflict_report(gluing,sheaf,*,report_id,digest,versions):
    edges={edge.edge_id:edge for edge in sheaf.restrictions}
    if not gluing.conflict_witness or not set(gluing.conflict_witness)<=edges.keys():raise ContractError('NoConflictWitness','H26 obstruction edges must bind to the source sheaf')
    if sheaf.version!=versions.state:raise ContractError('VersionMismatch','H26 source sheaf version differs')
    domains=tuple(sorted({domain for edge_id in gluing.conflict_witness for domain in (edges[edge_id].left,edges[edge_id].right)}))
    return DiscrepancyReport(report_id,'semantic_domain',digest,(),(),(),domains,frozenset(),frozenset({'conflicting_domains','conflict_edge_witness'}),versions,tuple(gluing.conflict_witness))
def bind_ontology_repair(report,*,source_ontology,target_ontology,variable_bindings):
    if report.kind not in ('semantic_domain','missing_variable') or source_ontology!=report.versions.ontology or target_ontology==source_ontology:raise ContractError('MigrationRequired','H27 must explicitly advance ontology from current report')
    if not set(report.missing_variables)<=set(variable_bindings):raise ContractError('UnboundVariable','missing-variable repair needs explicit bindings')
    return {'source_ontology':source_ontology,'target_ontology':target_ontology,'bindings':tuple(sorted(variable_bindings.items()))}
def exclusion_for_repair(report,capsule):
    if capsule.domain_version!=report.versions.ontology:raise ContractError('VersionMismatch','H46 exclusion scope differs from discrepancy domain')
    if report.kind=='numeric' and capsule.mode=='hard':raise ContractError('HardSoftConfusion','numeric approximation residual cannot justify hard exclusion')
    return capsule
def provenance_retraction(report,invalidation):
    if report.kind!='evidence_error' or not set(invalidation.retracted_atoms)<=report.evidence_errors:raise ContractError('MissingSource','H48 retraction requires exact reported evidence atoms')
    return invalidation.invalidated_nodes
