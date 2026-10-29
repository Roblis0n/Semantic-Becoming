"""Small exact reference utilities. No neural models, data generation or training.

These establish finite examples only, not the scientific validity of a mechanism.
"""
from __future__ import annotations
from fractions import Fraction as F
from itertools import product, combinations
from math import factorial
from typing import Callable, Hashable, Sequence


def matmul(a: Sequence[Sequence[int | F]], b: Sequence[Sequence[int | F]]) -> list[list[F]]:
    if not a or not b or not a[0] or not b[0]:raise ValueError('nonempty matrices required')
    if len(a)>64 or len(b)>64 or len(a[0])>64 or len(b[0])>64:raise ValueError('fixture dimension limit')
    if any(len(row)!=len(a[0]) for row in a) or any(len(row)!=len(b[0]) for row in b):raise ValueError('ragged matrix')
    if len(a[0])!=len(b):raise ValueError('dimension mismatch')
    return [[sum((F(a[i][k])*F(b[k][j]) for k in range(len(b))),F(0)) for j in range(len(b[0]))] for i in range(len(a))]


def inverse2(a: Sequence[Sequence[int | F]]) -> list[list[F]]:
    if len(a)!=2 or any(len(row)!=2 for row in a):raise ValueError('requires 2x2')
    x,y,z,w=map(F,(a[0][0],a[0][1],a[1][0],a[1][1]))
    det=x*w-y*z
    if not det:raise ValueError('singular frame')
    return [[w/det,-y/det],[-z/det,x/det]]


def covariant_apply(g: Sequence[Sequence[int | F]], t: Sequence[Sequence[int | F]], z: Sequence[Sequence[int | F]]) -> dict:
    inv=inverse2(g)
    return {'left':matmul(g,matmul(t,z)),
            'right':matmul(matmul(matmul(g,t),inv),matmul(g,z))}


def scalar_transport(j: int | F, v: int | F, regularization: int | F=0) -> F:
    j,v,lam=F(j),F(v),F(regularization)
    if lam<0:raise ValueError('negative regularization')
    denominator=j*j+lam
    if denominator==0:raise ValueError('not uniquely identifiable')
    return j*v/denominator


def question_partition(domain: Sequence[Hashable], queries: Sequence[Callable]) -> list[tuple]:
    if len(domain)>64 or len(queries)>64:raise ValueError('fixture size limit')
    if len(set(domain))!=len(domain):raise ValueError('duplicate domain element')
    groups={}
    for x in domain:
        signature=tuple(q(x) for q in queries)
        groups.setdefault(signature,[]).append(x)
    return [tuple(group) for group in groups.values()]


def is_refinement(coarse: Sequence[Sequence[Hashable]], fine: Sequence[Sequence[Hashable]]) -> bool:
    c=[set(x) for x in coarse];f=[set(x) for x in fine]
    def valid(parts):
        flat=[x for part in parts for x in part]
        return all(parts) and len(flat)==len(set(flat))
    if not valid(c) or not valid(f):raise ValueError('not a partition')
    if set().union(*c)!=set().union(*f):return False
    return all(any(group<=parent for parent in c) for group in f)


def evaluate_boolean(expr: tuple | str, assignment: dict[str,bool], depth: int=0) -> bool:
    if depth>32:raise ValueError('expression depth limit')
    if isinstance(expr,str):
        if expr not in assignment:raise ValueError('missing evidence atom')
        return assignment[expr]
    if not isinstance(expr,tuple) or not expr:raise ValueError('bad expression')
    op,*args=expr
    if op=='not' and len(args)==1:return not evaluate_boolean(args[0],assignment,depth+1)
    if op not in ('and','or') or not args:raise ValueError('invalid Boolean operation')
    # Eager evaluation deliberately checks all referenced atoms, even if short-circuiting could skip them.
    values=[evaluate_boolean(a,assignment,depth+1) for a in args]
    return all(values) if op=='and' else any(values)


def independent_probability(expr: tuple | str, atom_probabilities: dict[str,F], *, independence_declared: bool=False) -> F:
    """Repeated atom IDs remain the same variable. Requires explicit independence."""
    if not independence_declared:raise ValueError('dependence unknown: do not factorize')
    if len(atom_probabilities)>12:raise ValueError('fixture atom limit')
    atoms=list(atom_probabilities)
    probs=[F(atom_probabilities[a]) for a in atoms]
    if any(p<0 or p>1 for p in probs):raise ValueError('invalid probability')
    total=F(0)
    for bits in product((False,True),repeat=len(atoms)):
        assignment=dict(zip(atoms,bits))
        weight=F(1)
        for p,b in zip(probs,bits):weight*=p if b else 1-p
        if evaluate_boolean(expr,assignment):total+=weight
    return total


def shapley(players: Sequence[str], value: Callable[[frozenset[str]],F]) -> dict[str,F]:
    if len(players)>8 or len(set(players))!=len(players):raise ValueError('player limit or duplicates')
    n=len(players)
    if n==0:return {}
    result={}
    for player in players:
        others=[x for x in players if x!=player];credit=F(0)
        for k in range(n):
            for subset in combinations(others,k):
                s=frozenset(subset)
                weight=F(factorial(k)*factorial(n-k-1),factorial(n))
                credit+=weight*(F(value(s|{player}))-F(value(s)))
        result[player]=credit
    return result


def fixture_report() -> dict:
    pair=covariant_apply([[0,1],[1,0]],[[2,0],[0,3]],[[1],[2]])
    c=question_partition([1,2,3,4],[lambda x:x%2])
    f=question_partition([1,2,3,4],[lambda x:x%2,lambda x:x>2])
    repeated=independent_probability(('or','e','e'),{'e':F(4,5)},independence_declared=True)
    distinct=independent_probability(('or','e','f'),{'e':F(4,5),'f':F(4,5)},independence_declared=True)
    x,y,z=F(0),F(1,3),F(2,3)
    residual=[x-y,y-z,z-x-1]
    return {'scope':'finite_exact_math_only','research_models_run':0,
            'gauge_equal':pair['left']==pair['right'],
            'inconsistent_cycle_residual_squared':str(sum(v*v for v in residual)),
            'transport_no_regularization':str(scalar_transport(4,1)),
            'transport_lambda_one':str(scalar_transport(4,1,1)),
            'task_partition_refines':is_refinement(c,f),
            'repeated_evidence':str(repeated),'independent_two_evidence':str(distinct),
            'coalition_credit':{k:str(v) for k,v in shapley(['a','b'],lambda s:F(len(s)==2)).items()},
            'scientific_effectiveness_tested':False}

if __name__=='__main__':
    import json
    print(json.dumps(fixture_report(),ensure_ascii=False,indent=2))
