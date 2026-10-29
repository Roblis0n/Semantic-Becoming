from dataclasses import replace
import math
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import matvec,sub,norm
from .reference import normalized_logs,prefix_posterior_update

def branch_overlap_residuals(packet,sheaf,*,budget=StepBudget()):
    if packet.versions.state!=sheaf.version:raise ContractError('VersionMismatch','H26 local sections bind to one state version')
    sizes=[d.dimension for d in sheaf.cover];out=[];meter=budget.meter()
    for branch in packet.branches:
        if branch.unknown:out.append((branch.branch_id,None));continue
        if len(branch.state)!=sum(sizes):raise ContractError('DimensionMismatch','branch state must explicitly concatenate local cover coordinates')
        sections={};offset=0
        for domain in sheaf.cover:sections[domain.name]=branch.state[offset:offset+domain.dimension];offset+=domain.dimension
        residuals=[]
        for edge in sheaf.restrictions:
            meter.consume(steps=1);residuals.append((edge.edge_id,sub(sub(matvec(edge.left_map,sections[edge.left]),matvec(edge.right_map,sections[edge.right])),edge.bias)))
        out.append((branch.branch_id,tuple(residuals)))
    return tuple(out) # Conflicting branches remain represented, not silently pruned.

def update_from_counterexample(packet,counterexample,branch_claims):
    if counterexample.status!='verified_counterexample' or counterexample.expected is None:raise ContractError('InvalidCounterexample','H36 disagreement alone is not a verified refutation')
    if not set(branch_claims)<=set(b.branch_id for b in packet.branches):raise ContractError('UnboundReference','claim binding names absent branch')
    likelihood=tuple(-math.inf if branch_claims.get(b.branch_id)==counterexample.claim_id and not b.unknown else 0. for b in packet.branches)
    return prefix_posterior_update(packet,likelihood)

def as_identification_state(packet,queries,*,version):
    from latent_comm.mechanisms.h45_identifiability.types import IdentificationState
    return IdentificationState(tuple(b.branch_id for b in packet.branches),tuple(queries),tuple(math.exp(x) for x in normalized_logs(packet)),version,True) # Candidate support is not an exhaustiveness certificate.

def branch_provenance(branch,atoms,*,version):
    from latent_comm.mechanisms.h48_evidence_genealogy.types import ProvenanceGraph,SupportNode
    selected=tuple(a for a in atoms if a.atom_id in branch.evidence_support)
    if {a.atom_id for a in selected}!=set(branch.evidence_support) or not selected:raise ContractError('MissingSource','H48 requires each branch support atom explicitly bound')
    nodes=tuple(SupportNode('atom:'+a.atom_id,'atom',(),a.atom_id) for a in selected)
    root='support:'+branch.branch_id;nodes+=(SupportNode(root,'and',tuple(n.node_id for n in nodes)),)
    return ProvenanceGraph(selected,nodes,root,version)
