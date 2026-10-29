from itertools import combinations
from random import Random
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import matvec,finite_scalar

def compose_hyperedge(edge,states):
    if any(m not in states for m in edge.members):raise ContractError('MissingMember','joint factor is unavailable, not a zero individual message')
    rank=len(edge.projections[0]);joint=[1.]*rank
    for member,projection in zip(edge.members,edge.projections):
        projected=matvec(projection,states[member]);joint=[a*b for a,b in zip(joint,projected)]
    return matvec(edge.readout,tuple(joint))
def subset_interaction(members,loss_table,*,budget=StepBudget()):
    if not 1<=len(members)<=6 or len(set(members))!=len(members):raise ContractError('BudgetExhausted','exact subset bound')
    meter=budget.meter();interaction=0.
    for size in range(len(members)+1):
        for subset in combinations(members,size):
            meter.consume(steps=1,cases=1);key=frozenset(subset)
            if key not in loss_table:raise ContractError('UndefinedValue','missing subset loss is not zero')
            interaction-=(-1)**(len(members)-size)*finite_scalar(loss_table[key])
    return interaction

def sampled_interaction(members,loss_table,*,samples,seed,budget=StepBudget()):
    if not 1<=samples<=64 or not 1<=len(members)<=6:raise ContractError('BudgetExhausted','finite sampling declaration')
    rng=Random(seed);meter=budget.meter();estimates=[]
    for _ in range(samples):
        meter.consume(steps=1,cases=1);mask=rng.randrange(1<<len(members));subset=frozenset(m for i,m in enumerate(members) if mask&(1<<i))
        if subset not in loss_table:raise ContractError('UndefinedValue','sampled subset unavailable')
        estimates.append(-(1<<len(members))*(-1)**(len(members)-len(subset))*loss_table[subset])
    mean=sum(estimates)/samples;variance=sum((x-mean)**2 for x in estimates)/(samples-1) if samples>1 else None
    return {'estimate':mean,'sample_variance':variance,'variance_of_mean':variance/samples if variance is not None else None,'samples':samples,'seed':seed,'exact':False}
def unique_support_count(edge):
    """Deduplicated atom count, never a statistical independence assertion."""
    return len(frozenset().union(*(s for _,s in edge.evidence_support)))

def independent_support_count(edge):
    """Legacy spelling; returns unique atom count, not independent evidence count."""
    return unique_support_count(edge)
