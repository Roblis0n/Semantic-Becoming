"""Transparent stdlib finite mathematics, not a neural model or research dataset.

Dimensions are bounded by 64. Iterative solvers explicitly bound sweeps/steps by
128. Matrix elementary arithmetic does not create a learned module or model.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from .errors import ContractError, ErrorCode

Vector=tuple[float,...]
Matrix=tuple[Vector,...]
def finite_scalar(x: float) -> float:
    if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x):
        raise ContractError(ErrorCode.OUT_OF_DOMAIN,'expected finite real scalar')
    return float(x)
def vector(x: object, *, allow_empty: bool=False) -> Vector:
    values=tuple(finite_scalar(v) for v in x)
    if len(values)>64 or (not values and not allow_empty):
        raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'vector dimension must be 1..64')
    return values

def matrix(x: object) -> Matrix:
    values=tuple(vector(row) for row in x)
    if not values or len(values)>64 or len({len(r) for r in values})!=1:
        raise ContractError(ErrorCode.INVALID_SHAPE,'matrix must be rectangular with dimensions 1..64')
    return values

def dot(a: Vector,b: Vector) -> float:
    a=vector(a);b=vector(b)
    if len(a)!=len(b):raise ContractError(ErrorCode.INVALID_SHAPE,'dot dimensions differ')
    return math.fsum(x*y for x,y in zip(a,b,strict=True))
def add(a: Vector,b: Vector) -> Vector:
    a=vector(a);b=vector(b)
    if len(a)!=len(b):raise ContractError(ErrorCode.INVALID_SHAPE,'vector dimensions differ')
    return tuple(x+y for x,y in zip(a,b,strict=True))
def sub(a: Vector,b: Vector) -> Vector:
    return add(a,scale(b,-1.0))
def scale(a: Vector,s: float) -> Vector:
    return tuple(v*finite_scalar(s) for v in vector(a))
def norm(a: Vector) -> float:
    return math.sqrt(max(0.0,dot(a,a)))
def transpose(a: Matrix) -> Matrix:
    return tuple(tuple(r) for r in zip(*matrix(a),strict=True))
def matvec(a: Matrix,b: Vector) -> Vector:
    return tuple(dot(row,b) for row in matrix(a))
def matmul(a: Matrix,b: Matrix) -> Matrix:
    a=matrix(a);bt=transpose(b)
    if len(a[0])!=len(bt[0]):raise ContractError(ErrorCode.INVALID_SHAPE,'matrix inner dimensions differ')
    return tuple(tuple(dot(row,col) for col in bt) for row in a)
def eye(n: int) -> Matrix:
    if type(n) is not int or not 0<n<=64:raise ContractError(ErrorCode.INVALID_SHAPE,'identity dimension outside 1..64')
    return tuple(tuple(float(i==j) for j in range(n)) for i in range(n))
def matrix_add(a: Matrix,b: Matrix) -> Matrix:
    a=matrix(a);b=matrix(b)
    if len(a)!=len(b):raise ContractError(ErrorCode.INVALID_SHAPE,'matrix rows differ')
    return tuple(add(x,y) for x,y in zip(a,b,strict=True))
def matrix_scale(a: Matrix,s: float) -> Matrix:
    return tuple(scale(row,s) for row in matrix(a))
def outer(a: Vector,b: Vector) -> Matrix:
    return tuple(scale(b,x) for x in vector(a))
def solve(a: Matrix,b: Vector, *, tolerance: float=1e-12) -> Vector:
    a=matrix(a);b=vector(b);n=len(a)
    if len(a[0])!=n or len(b)!=n:raise ContractError(ErrorCode.INVALID_SHAPE,'linear solve requires square compatible system')
    aug=[list(row)+[rhs] for row,rhs in zip(a,b,strict=True)]
    scale_a=max(abs(x) for row in a for x in row)
    threshold=tolerance*max(1.0,scale_a)
    for k in range(n):
        pivot=max(range(k,n),key=lambda i:abs(aug[i][k]))
        if abs(aug[pivot][k])<=threshold:raise ContractError('SingularMatrix','linear system is rank deficient')
        aug[k],aug[pivot]=aug[pivot],aug[k]
        divisor=aug[k][k];aug[k]=[x/divisor for x in aug[k]]
        for i in range(n):
            if i==k:continue
            factor=aug[i][k];aug[i]=[x-factor*y for x,y in zip(aug[i],aug[k],strict=True)]
    return tuple(row[-1] for row in aug)
def inverse(a: Matrix) -> Matrix:
    a=matrix(a);n=len(a)
    if len(a[0])!=n:raise ContractError('NonInvertibleFrame','non-square map has no gauge inverse')
    return transpose(tuple(solve(a,col) for col in eye(n)))

@dataclass(frozen=True)
class LeastSquaresResult:
    solution: Vector
    residual: Vector
    rank: int
    unique: bool
    regularization: float
    converged: bool
    sweeps: int

def symmetric_eigh(a: Matrix, *, max_sweeps: int=128,tolerance: float=1e-12) -> tuple[Vector,Matrix,int,bool]:
    a=matrix(a);n=len(a)
    if len(a[0])!=n or any(abs(a[i][j]-a[j][i])>tolerance for i in range(n) for j in range(n)):
        raise ContractError(ErrorCode.OUT_OF_DOMAIN,'Jacobi eigensolver requires a symmetric matrix')
    if not 0<max_sweeps<=128:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'eigen sweep bound')
    work=[list(r) for r in a];basis=[list(r) for r in eye(n)]
    converged=False;step=0
    for step in range(max_sweeps):
        if n==1:converged=True;break
        p,q=max(((i,j) for i in range(n) for j in range(i+1,n)),key=lambda ij:abs(work[ij[0]][ij[1]]))
        if abs(work[p][q])<=tolerance*max(1.0,max(abs(work[i][i]) for i in range(n))):converged=True;break
        angle=.5*math.atan2(2*work[p][q],work[q][q]-work[p][p]);c=math.cos(angle);s=math.sin(angle)
        app,aqq,apq=work[p][p],work[q][q],work[p][q]
        work[p][p]=c*c*app-2*s*c*apq+s*s*aqq
        work[q][q]=s*s*app+2*s*c*apq+c*c*aqq
        work[p][q]=work[q][p]=0.0
        for k in range(n):
            if k not in {p,q}:
                akp,akq=work[k][p],work[k][q]
                work[k][p]=work[p][k]=c*akp-s*akq
                work[k][q]=work[q][k]=s*akp+c*akq
            vkp,vkq=basis[k][p],basis[k][q]
            basis[k][p]=c*vkp-s*vkq;basis[k][q]=s*vkp+c*vkq
    return tuple(work[i][i] for i in range(n)),tuple(tuple(r) for r in basis),step+1,converged

def least_squares(a: Matrix,b: Vector, *, regularization: float=0.0,tolerance: float=1e-10) -> LeastSquaresResult:
    a=matrix(a);b=vector(b);regularization=finite_scalar(regularization)
    if len(a)!=len(b) or regularization<0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'invalid least squares dimensions or regularization')
    at=transpose(a);gram=matmul(at,a);rhs=matvec(at,b)
    eigen,basis,sweeps,ok=symmetric_eigh(gram,tolerance=tolerance*.01)
    threshold=tolerance*max(1.0,max(abs(v) for v in eigen));rank=sum(v>threshold for v in eigen)
    coefficients=matvec(transpose(basis),rhs)
    projected=tuple(c/(max(0.0,e)+regularization) if e>threshold or regularization>0 else 0.0 for c,e in zip(coefficients,eigen,strict=True))
    answer=matvec(basis,projected)
    return LeastSquaresResult(answer,sub(matvec(a,answer),b),rank,rank==len(a[0]) or regularization>0,regularization,ok,sweeps)

def topological_order(nodes: tuple[str,...], edges: tuple[tuple[str,str],...]) -> tuple[str,...]:
    if len(nodes)>64 or len(set(nodes))!=len(nodes):raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'finite graph bound or duplicate nodes')
    incoming={x:0 for x in nodes};children={x:[] for x in nodes}
    if len(set(edges))!=len(edges):raise ContractError(ErrorCode.CONFLICT,'duplicate graph edge')
    for a,b in edges:
        if a not in incoming or b not in incoming:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'edge endpoint absent')
        incoming[b]+=1;children[a].append(b)
    ready=sorted(n for n,d in incoming.items() if d==0);out=[]
    while ready:
        n=ready.pop(0);out.append(n)
        for child in sorted(children[n]):
            incoming[child]-=1
            if incoming[child]==0:ready.append(child);ready.sort()
    if len(out)!=len(nodes):raise ContractError(ErrorCode.CONFLICT,'directed cycle')
    return tuple(out)
