from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

import hashlib

def freeze_goal(text):return ImmutableGoal(text,hashlib.sha256(text.encode()).hexdigest())

def change_view(frame,view_map,new_version,*,allow_loss=False,budget=StepBudget()):
    meter=budget.meter();a=matrix(view_map);meter.dimension(len(a));meter.consume(steps=1)
    if len(a[0])!=len(frame.costs) or new_version==frame.version:raise ContractError('SingularView','view must match source coordinates and advance version')
    result=least_squares(transpose(a),frame.weights)
    if not result.converged:raise ContractError('SingularView','dual-weight solve did not converge')
    lost=norm(result.residual)>1e-9
    if lost and not allow_loss:raise ContractError('InformationLoss','view discards a required preference direction')
    c=matvec(a,frame.costs);w=result.solution
    feasible=all(x<=y+1e-9 for x,y in zip(matvec(frame.constraint_matrix,frame.costs),frame.constraint_bounds))
    return GoalPreservingView(frame.goal.digest,c,w,result.residual,dot(frame.weights,frame.costs),dot(w,c),'InformationLoss' if lost else 'GoalValuePreserved',feasible,frame.version,new_version)

def assert_commit(view,current_goal):
    if current_goal.digest!=view.goal_digest:raise ContractError('GoalMutation','internal reparameterization cannot change the external goal')
    if not view.original_constraints_satisfied:raise ContractError('ConstraintViolation','transformed value does not override original hard constraints')
    if view.status!='GoalValuePreserved':raise ContractError('InformationLoss','lossy view cannot be committed as an equivalent objective')
    return view

def pareto_front(costs,feasible=None,budget=StepBudget()):
    if not costs:return ()
    costs=tuple(vector(c) for c in costs)
    if len({len(c) for c in costs})!=1:raise ContractError('PreferenceUndefined','cost axes differ')
    feasible=(True,)*len(costs) if feasible is None else tuple(feasible)
    if len(feasible)!=len(costs) or any(type(x) is not bool for x in feasible):raise ContractError('PreferenceUndefined','feasibility mask differs')
    meter=budget.meter();meter.dimension(len(costs));out=[]
    for i,c in enumerate(costs):
        if not feasible[i]:continue
        dominated=False
        for j,d in enumerate(costs):
            if j==i or not feasible[j]:continue
            meter.consume(steps=1)
            if all(x<=y for x,y in zip(d,c)) and any(x<y for x,y in zip(d,c)):dominated=True;break
        if not dominated:out.append(i)
    return tuple(out)
