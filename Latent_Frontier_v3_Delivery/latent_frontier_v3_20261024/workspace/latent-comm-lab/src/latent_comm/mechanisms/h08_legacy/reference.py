from itertools import permutations
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import matvec,add,scale
from .types import MatchResult

def match_nodes(source,target,*,preserved_semantics,budget=StepBudget()):
    if not set(preserved_semantics)<={'operation','causal','correlation','spatial'}:raise ContractError('UnknownRelation','declared edge-kind preservation')
    if not source.versions.matches(target.versions,('ontology','task')):raise ContractError('UnboundProjection','cross-ontology mapping requires H30 explicit relation map')
    if len(source.nodes)>len(target.nodes):return MatchResult((),True,0,tuple(n.node_id for n in source.nodes),'no_injection')
    meter=budget.meter();matches=[];lookup={(e.source,e.target,e.relation,e.semantics) for e in target.edges}
    for order in permutations(target.nodes,len(source.nodes)):
        try:meter.consume(steps=1,cases=1)
        except ContractError:return MatchResult(tuple(matches),False,meter.cases,(),'budget_exhausted_not_no_match')
        if any(a.role!=b.role or (a.anchor is not None and a.anchor!=b.anchor) for a,b in zip(source.nodes,order)):continue
        mapping={a.node_id:b.node_id for a,b in zip(source.nodes,order)}
        if all((mapping[e.source],mapping[e.target],e.relation,e.semantics) in lookup for e in source.edges if e.semantics in preserved_semantics):matches.append(tuple(mapping.items()))
    return MatchResult(tuple(matches),True,meter.cases,(),'ambiguous' if len(matches)>1 else 'unique' if matches else 'no_match')

def exchange(packet,relation_maps,*,rounds=1,budget=StepBudget()):
    if not 1<=rounds<=128:raise ContractError('BudgetExhausted','bounded message passing')
    states={n.node_id:n.features for n in packet.nodes};meter=budget.meter()
    for _ in range(rounds):
        meter.consume(steps=1);messages={k:[] for k in states}
        for e in packet.edges:
            key=(e.relation,e.semantics)
            if key not in relation_maps:raise ContractError('UnboundRelationMap',str(key))
            messages[e.target].append(matvec(relation_maps[key],states[e.source]))
        updated={}
        for k,z in states.items():
            total=tuple(0. for _ in z)
            for msg in messages[k]:total=add(total,msg)
            updated[k]=add(z,scale(total,1/max(1,len(messages[k]))))
        states=updated
    return tuple(states.items())
def require_intervenable(edge,structural_module):
    if edge.semantics!='causal' or structural_module is None:raise ContractError('CausalIdentificationRequired','an adjacency edge does not authorize or define do')
    return structural_module
