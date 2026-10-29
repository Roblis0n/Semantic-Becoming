"""C03: immutable shared computation branches and sequence-level belief mixtures."""
from dataclasses import dataclass,replace
import math
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h03_legacy.types import BeliefPacket
from latent_comm.mechanisms.h13_legacy.types import BranchState,MergeResult
from latent_comm.mechanisms.h21_legacy.types import PortfolioNode
from .contracts import linear_graph,infer_contracts,lower_plan,execute_reference,objective_phase
@dataclass(frozen=True)
class BeliefTreeInput:
    belief: BeliefPacket
    root: BranchState
    semantic_nodes: tuple[PortfolioNode,...]
    updates: tuple[tuple[str,tuple[tuple[str,tuple[float,...]],...]],...]
    likelihood: tuple[float,...]
    evidence_id: str
    sequence_log_likelihoods: tuple[tuple[float,...],...]
    versions: VersionSet
@dataclass(frozen=True)
class EncodedBeliefs:
    request: BeliefTreeInput
    prior: tuple[float,...]
    @property
    def versions(self):return self.request.versions
@dataclass(frozen=True)
class ForkedBeliefTree:
    encoded: EncodedBeliefs
    branches: tuple[BranchState,...]
    @property
    def versions(self):return self.encoded.versions
@dataclass(frozen=True)
class ConditionedBranches:
    tree: ForkedBeliefTree
    belief: BeliefPacket
    semantic_nodes: tuple[PortfolioNode,...]
    status: str
    @property
    def versions(self):return self.tree.versions
@dataclass(frozen=True)
class CompatibleMerge:
    conditioned: ConditionedBranches
    merge: MergeResult
    @property
    def versions(self):return self.conditioned.versions
@dataclass(frozen=True)
class BeliefTreeReadout:
    belief: BeliefPacket
    shared_state: tuple | None
    preserved_branches: tuple[BranchState,...]
    semantic_nodes: tuple[PortfolioNode,...]
    sequence_mixture_nll: float
    status: str
    versions: VersionSet
    unknown_alternatives_possible: bool=True

def belief_encode(value):
    from latent_comm.mechanisms.h03_legacy.reference import normalized_logs
    value.versions.require('state','frame','ontology','isa','world','task','evidence')
    ids=tuple(b.branch_id for b in value.belief.branches)
    if len(ids)!=2 or tuple(n.node_id for n in value.semantic_nodes)!=ids or set(dict(value.updates))!=set(ids):raise ContractError('BranchMismatch','C03 finite merge binds exactly two semantic branches and their own deltas')
    if value.belief.versions!=value.versions or value.root.versions!=value.versions or any(n.versions!=value.versions for n in value.semantic_nodes):raise ContractError('VersionMismatch','belief, computation and portfolio branches require one shared snapshot')
    if not value.evidence_id:raise ContractError('MissingSource','conditioning evidence identity required')
    return EncodedBeliefs(value,tuple(math.exp(x) for x in normalized_logs(value.belief)))

def fork(value):
    from latent_comm.mechanisms.h13_legacy.reference import fork as fork_branch,write_slot
    q=value.request;branches=[]
    for node in q.semantic_nodes:
        branch=fork_branch(q.root,node.node_id)
        for slot,state in dict(q.updates)[node.node_id]:branch=write_slot(branch,slot,state,reads=(slot,),operation='condition:'+node.node_id,commutation_class='independent_slots')
        branch=replace(branch,evidence=branch.evidence|node.evidence,question_transform=node.question_id,concept_structure=node.versions.ontology)
        branches.append(branch)
    return ForkedBeliefTree(value,tuple(branches))

def condition_update(value):
    from latent_comm.mechanisms.h21_legacy.reference import update_evidence_weights
    q=value.encoded.request
    try:weights,seen=update_evidence_weights(q.semantic_nodes,value.encoded.prior,q.likelihood,evidence_id=q.evidence_id,seen=q.belief.consumed_evidence)
    except ContractError as error:
        if error.failure.code!='EvidenceConflict':raise
        return ConditionedBranches(value,q.belief,q.semantic_nodes,'EvidenceConflictUnknownAlternativesRetained')
    branches=tuple(replace(b,log_weight=math.log(p) if p else -math.inf,evidence_support=b.evidence_support|{q.evidence_id}) for b,p in zip(q.belief.branches,weights))
    belief=replace(q.belief,branches=branches,consumed_evidence=seen,probability_semantics='specified_generative_posterior')
    nodes=tuple(replace(n,evidence=n.evidence|{q.evidence_id}) for n in q.semantic_nodes)
    return ConditionedBranches(value,belief,nodes,'ConditionedWithinRepresentedFamily')

def compatible_merge(value):
    from latent_comm.mechanisms.h13_legacy.reference import merge
    # Computational reuse and probabilistic identity are distinct. Even a safe
    # disjoint-slot merge does not average or coalesce hypothesis branch weights.
    left,right=value.tree.branches;nodes=value.semantic_nodes
    if nodes[0].world_id!=nodes[1].world_id or nodes[0].question_id!=nodes[1].question_id or nodes[0].synthetic!=nodes[1].synthetic:
        result=MergeResult(None,(left,right),'semantic_context_conflict_preserved',left.evidence|right.evidence)
    else:result=merge(left,right)
    return CompatibleMerge(value,result)

def decode(value):
    from latent_comm.mechanisms.h03_legacy.reference import sequence_mixture_nll
    q=value.conditioned.tree.encoded.request
    score=sequence_mixture_nll(value.conditioned.belief,q.sequence_log_likelihoods)
    return BeliefTreeReadout(value.conditioned.belief,value.merge.state,value.merge.preserved_branches,value.conditioned.semantic_nodes,score,value.conditioned.status+':'+value.merge.status,q.versions)

STAGES=(('belief_encode',('H03','H21'),'BeliefTreeInput','EncodedBeliefs','stop'),('fork',('H13',),'EncodedBeliefs','ForkedBeliefTree','stop'),('condition_update',('H03','H21'),'ForkedBeliefTree','ConditionedBranches','differentiable'),('compatible_merge',('H13','H21'),'ConditionedBranches','CompatibleMerge','stop'),('decode',('H03',),'CompatibleMerge','BeliefTreeReadout','differentiable'))
def build_graph(versions):return linear_graph('C03',tuple((n,m,a,b,__name__+'.'+n,g) for n,m,a,b,g in STAGES),versions,required_axes=('schema','state','frame','ontology','isa','world','task','evidence'),scope=('Z','F','O','P','Q','V','K','W','U','E'),obligations=('Safe computational merge does not establish probabilistic hypothesis equivalence.','All-zero likelihood remains evidence conflict, not false certainty.','Sequence mixture sums a whole sequence within each branch before mixing.'))
def run_reference(request,*,budget=StepBudget()):return execute_reference(build_graph(request.versions),{'input':request},{n:globals()[n] for n,*_ in STAGES},{c.__name__:c for c in (BeliefTreeInput,EncodedBeliefs,ForkedBeliefTree,ConditionedBranches,CompatibleMerge,BeliefTreeReadout)},budget=budget)
def describe_training():
    from latent_comm.mechanisms.h03_legacy.losses import LEDGER as H03
    from latent_comm.mechanisms.h13_legacy.losses import LEDGER as H13
    from latent_comm.mechanisms.h21_legacy.losses import LEDGER as H21
    return {'recipe':'C03','research_state':'NOT_RUN','phases':[objective_phase('belief',(('H03',H03,tuple(s.name for s in H03)),)),objective_phase('branch_state',(('H13',H13,tuple(s.name for s in H13)),)),objective_phase('semantic_portfolio',(('H21',H21,tuple(s.name for s in H21)),))],'gradient_boundaries':{n:g for n,_,_,_,g in STAGES},'joint_phase':'shared live graphs require explicit nonoverlapping owner/optimizer map; no duplicate backward'}
