"""X02: retain non-gluable local theories and compile explicit revision alternatives."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c10 import DisagreementInput,MultiDomainBelief
from latent_comm.mechanisms.h48_evidence_genealogy.types import ProvenanceGraph,DependenceModel,CalibratedSupport
from .contracts import bounded_horizon,assumptions,require_complete
ASSUMPTIONS=assumptions('Finite local sections, executable claims, observable records and a source genealogy are bound.','A gluing obstruction concerns the declared overlaps; it is not evidence that any local theory is globally true.','Distinction, domain separation and preserved-theory revision alternatives remain explicit branches.','Future models may learn from obstruction structure rather than force a consensus; NOT_RUN.')
@dataclass(frozen=True)
class PluralWorldRequest:
    disagreement: DisagreementInput
    genealogy: ProvenanceGraph
    dependence: DependenceModel
    versions: VersionSet
@dataclass(frozen=True)
class RevisionAlternative:
    action: str
    required_objects: tuple[str,...]
    postcondition: str
    status: str
@dataclass(frozen=True)
class PluralWorldRecord:
    theories: MultiDomainBelief
    source_support: CalibratedSupport
    alternatives: tuple[RevisionAlternative,...]
    global_truth_required: bool=False
@bounded_horizon('X02',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.compositions.c10 import run_reference
    from latent_comm.mechanisms.h48_evidence_genealogy.reference import calibrate_support
    q=request
    if q.disagreement.versions!=q.versions or q.genealogy.version!=q.versions.evidence:raise ContractError('VersionMismatch','local theories and genealogy must share semantic context')
    supports={s for r in q.disagreement.local_sections.restrictions for s in r.support};atoms={a.atom_id for a in q.genealogy.atoms}
    if not supports<=atoms:raise ContractError('MissingSource','each overlap claim retains its original evidence identity')
    theories=require_complete(run_reference(q.disagreement));support=calibrate_support(q.genealogy,q.dependence)
    alternatives=[]
    if theories.proposed_ontology is not None:
        additions=tuple(c.concept_id for c in theories.proposed_ontology.concepts if c.concept_id not in {x.concept_id for x in theories.prior_ontology.concepts})
        alternatives.append(RevisionAlternative('introduce_distinguishing_observable',additions,'Recompute overlap maps and versioned readers before using the new distinction.','proposal_not_truth'))
    if theories.residual_conflicts:
        alternatives.append(RevisionAlternative('split_context_domains',tuple(sorted(s.name for s in q.disagreement.local_sections.cover)),'No cross-domain inference until an explicit overlap contract is provided.','preserve_conflict'))
    alternatives.append(RevisionAlternative('retain_plural_theories',tuple(b.branch_id for b in theories.historical_belief.branches),'Keep original weights, unknown branch and source genealogy; do not average inconsistent theories.','available'))
    for _ in alternatives:meter.consume(steps=1)
    return PluralWorldRecord(theories,support,tuple(alternatives)),('A finite obstruction is scoped to this cover and restriction maps.','Revision alternatives are not automatically enacted or judged superior by absent experiments.')
