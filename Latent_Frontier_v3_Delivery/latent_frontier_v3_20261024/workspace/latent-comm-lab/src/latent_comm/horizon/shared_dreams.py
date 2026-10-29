"""X09: grafted local mechanisms generate a synthetic world and task lineage."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet
from latent_comm.compositions.c16 import CounterfactualEcologyInput,SyntheticLineageArchive
from latent_comm.mechanisms.h31_grafting.types import CausalModule,TargetSCM,BoundaryBinding,GraftCertificate
from latent_comm.mechanisms.h44_dreaming.types import CounterfactualEdit
from .contracts import bounded_horizon,assumptions,require_complete
ASSUMPTIONS=assumptions('At least two local kernel sources, shared noise and an explicit causal graft boundary exist.','The grafted scalar is interpreted as a declared binary transition probability, not a factual observation.','Synthetic namespaces preserve world, task and ancestral mechanism lineage during finite construction.','Future models may learn new abstractions from constructed experiences; these are never automatic evidence about reality.')
@dataclass(frozen=True)
class DreamRequest:
    ecology: CounterfactualEcologyInput
    local_module: CausalModule
    target_scm: TargetSCM
    target_node: str
    bindings: tuple[BoundaryBinding,...]
    noise_assignment: tuple[tuple[str,float],...]
    edit_template: CounterfactualEdit
    namespace: str
    versions: VersionSet
@dataclass(frozen=True)
class SharedDreamRecord:
    graft: GraftCertificate
    probability: float
    archive: SyntheticLineageArchive
    namespace_records: tuple[tuple[str,str,tuple[str,...]],...]
    status: str='SyntheticWorldAndTasksConstructed'
@bounded_horizon('X09',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.mechanisms.h31_grafting.reference import graft,evaluate_scm
    from latent_comm.compositions.c16 import run_reference
    q=request
    if not q.namespace.startswith('synthetic:') or q.ecology.claim_kind!='synthetic_consequence' or len(q.ecology.kernels)!=2:raise ContractError('SyntheticAsReal','two-source dream must remain in a synthetic namespace and synthetic claim channel')
    if q.ecology.versions!=q.versions or q.target_scm.version!=q.versions.world:raise ContractError('VersionMismatch','world construction source contexts differ')
    cert=graft(q.local_module,q.target_scm,q.target_node,q.bindings,q.target_scm.version+':dream-graft');values=dict(evaluate_scm(cert.after,dict(q.noise_assignment)));p=values[q.target_node]
    if not 0<=p<=1 or len(q.edit_template.probabilities)!=2:raise ContractError('ProbabilityMismatch','declared causal-to-kernel interface requires a binary probability')
    edit=replace(q.edit_template,probabilities=(1-p,p));archive=require_complete(run_reference(replace(q.ecology,edits=(edit,))))
    meter.consume(steps=1)
    parents=archive.world.parent_kernel_ids+(q.target_scm.version,cert.after.version)
    records=((q.namespace+':world',archive.world.world_id,parents),(q.namespace+':evidence',archive.evidence.evidence_id,(archive.world.world_id,)+archive.evidence.parents))
    return SharedDreamRecord(cert,p,archive,records),('Synthetic transition consequences are not real observations.','A constructed world expands an executable experience space but proves no model has learned it.')
