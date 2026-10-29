from dataclasses import replace
from itertools import permutations
import math
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import norm,sub
from .types import BeliefPacket,BeliefBranch

def logsumexp(values):
    values=tuple(values)
    if not values or any(math.isnan(x) or x==math.inf for x in values):raise ContractError('InvalidLikelihood','finite or -inf log scores required')
    m=max(values)
    return -math.inf if m==-math.inf else m+math.log(math.fsum(math.exp(x-m) for x in values))
def normalized_logs(packet):
    norm=logsumexp(b.log_weight for b in packet.branches)
    return tuple(b.log_weight-norm for b in packet.branches)
def sequence_mixture_nll(packet,token_log_likelihoods):
    if len(token_log_likelihoods)!=len(packet.branches) or len({len(row) for row in token_log_likelihoods})!=1:raise ContractError('DimensionMismatch','branch x sequence likelihood table')
    if any(len(row)>128 for row in token_log_likelihoods):raise ContractError('BudgetExhausted','sequence fixture bound')
    for row in token_log_likelihoods:
        if any(math.isnan(x) or x>0 for x in row):raise ContractError('InvalidLikelihood','log probabilities must be <=0')
    # Sum the ENTIRE sequence per branch before mixing branches.
    return -logsumexp(w+sum(row) for w,row in zip(normalized_logs(packet),token_log_likelihoods,strict=True))
def prefix_posterior_update(packet,token_log_likelihoods):
    if len(token_log_likelihoods)!=len(packet.branches) or any(x>0 or math.isnan(x) for x in token_log_likelihoods):raise ContractError('InvalidLikelihood','one token log likelihood per branch')
    branches=tuple(replace(b,log_weight=w+l) for b,w,l in zip(packet.branches,normalized_logs(packet),token_log_likelihoods,strict=True))
    out=replace(packet,branches=branches)
    return replace(out,branches=tuple(replace(b,log_weight=w) for b,w in zip(out.branches,normalized_logs(out),strict=True)))
def update_evidence(packet,evidence_id,compatibility,*,generative_model_declared=False):
    if evidence_id in packet.consumed_evidence:return packet
    if len(compatibility)!=len(packet.branches) or any(not math.isfinite(x) for x in compatibility):raise ContractError('InvalidEvidence','one finite compatibility per branch')
    updated=tuple(replace(b,log_weight=b.log_weight+c,evidence_support=b.evidence_support|{evidence_id}) for b,c in zip(packet.branches,compatibility,strict=True))
    return replace(packet,branches=updated,consumed_evidence=packet.consumed_evidence|{evidence_id},probability_semantics='specified_generative_posterior' if generative_model_declared else 'candidate_weights')
def prune(packet,keep_ids):
    kept=[b for b in packet.branches if b.branch_id in keep_ids and not b.unknown]
    dropped=[b for b in packet.branches if b.branch_id not in keep_ids or b.unknown]
    if dropped:
        unknown=BeliefBranch('unknown:pruned',None,logsumexp(b.log_weight for b in dropped),'unresolved',frozenset().union(*(b.evidence_support for b in dropped)),'unbound',True)
        kept.append(unknown)
    return replace(packet,branches=tuple(kept))
def match_branches(left,right,*,budget=StepBudget()):
    if len(left)!=len(right):raise ContractError('DimensionMismatch','finite set matching cardinality')
    meter=budget.meter();best=math.inf;matches=[]
    for order in permutations(range(len(right))):
        meter.consume(steps=1,cases=1)
        if any(a.semantic_domain!=right[j].semantic_domain or a.ontology_version!=right[j].ontology_version or a.unknown!=right[j].unknown for a,j in zip(left,order)):continue
        cost=sum(norm(sub(a.state,right[j].state))**2 for a,j in zip(left,order) if not a.unknown)
        if cost<best-1e-12:best=cost;matches=[order]
        elif abs(cost-best)<=1e-12:matches.append(order)
    if not matches:raise ContractError('UnboundProjection','different ontologies/domains require an explicit comparable projection')
    return best,tuple(matches)
