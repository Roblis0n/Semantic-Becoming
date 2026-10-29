from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import *
from .types import FieldResult

def residuals(field,z):return tuple((s.source_id,sub(matvec(s.A,z),s.b)) for s in field.sources)
def energy(field,z):return sum(.5*s.temperature*dot(r,r) for s,(_,r) in zip(field.sources,residuals(field,z)))+field.anchor_strength*dot(sub(z,field.anchor),sub(z,field.anchor))
def solve_field(field,*,steps,step_size,tolerance=1e-8,budget=StepBudget()):
    if type(steps) is not int or not 1<=steps<=128 or step_size<=0:raise ContractError('BudgetExhausted','explicit finite steps and positive step size')
    # Frobenius bound upper-bounds the quadratic Hessian spectral radius.
    bound=sum(s.temperature*sum(x*x for row in s.A for x in row) for s in field.sources)+2*field.anchor_strength
    if step_size>=2/bound:raise ContractError('UnstableStep','step exceeds conservative quadratic stability region')
    meter=budget.meter();z=field.anchor;trajectory=[z];reason='fixed_steps_exhausted'
    for _ in range(steps):
        meter.consume(steps=1);gradient=scale(sub(z,field.anchor),2*field.anchor_strength)
        for s,(_,r) in zip(field.sources,residuals(field,z)):gradient=add(gradient,scale(matvec(transpose(s.A),r),s.temperature))
        if norm(gradient)<=tolerance:reason='stationary_not_truth';break
        z=sub(z,scale(gradient,step_size));trajectory.append(z)
    r=residuals(field,z)
    return FieldResult(z,tuple(trajectory),r,tuple(source for source,value in r if norm(value)>tolerance),reason,tuple((s.source_id,s.source_state_version) for s in field.sources))

def exact_compatibility(field,tolerance=1e-8):
    A=tuple(row for s in field.sources for row in s.A);b=tuple(v for s in field.sources for v in s.b)
    result=least_squares(A,b)
    return {'compatible':norm(result.residual)<=tolerance if result.converged else None,'residual':result.residual,'solver_converged':result.converged,'unique':result.unique}
