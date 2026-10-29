from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def validate_scm(world):
    if not world.version:raise ContractError('VersionMismatch','world version required')
    nodes=tuple(m.output for m in world.modules);units={m.output:m.unit for m in world.modules}
    if len(set(world.noise_ids))!=len(world.noise_ids):raise ContractError('NoiseIdentityConflict','duplicate noise identity')
    for module in world.modules:
        for p,u in zip(module.parents,module.parent_units):
            if units.get(p)!=u:raise ContractError('UnitConflict','parent variable missing or unit mismatch')
        if any(n not in world.noise_ids for n,_ in module.noise_terms):raise ContractError('NoiseIdentityConflict','unbound external noise identity')
    try:return topological_order(nodes,tuple((p,m.output) for m in world.modules for p in m.parents))
    except ContractError as e:raise ContractError('CycleIntroduced','only acyclic SCM modules are supported') from e

# A snapshot is local to this process and can only be obtained from snapshot_scm.
# Its metadata lets incremental evaluation identify every changed input/equation.
from dataclasses import dataclass, field
_SNAPSHOT_SEAL = object()

@dataclass(frozen=True)
class _SCMSnapshot:
    world: TargetSCM
    noise: tuple
    interventions: tuple
    values: tuple
    _seal: object = field(repr=False, compare=False)

def snapshot_scm(world,noise,interventions=(),budget=StepBudget()):
    """Evaluate and retain the world, exogenous assignment and intervention context."""
    noise_copy=tuple(sorted((key,finite_scalar(value)) for key,value in noise.items()))
    interventions=tuple(interventions)
    values=evaluate_scm(world,dict(noise_copy),interventions,budget=budget)
    return _SCMSnapshot(world,noise_copy,interventions,values,_SNAPSHOT_SEAL)

def evaluate_scm(world,noise,interventions=(),budget=StepBudget(),prior_values=(),changed=()):
    """Evaluate an SCM; incremental reuse requires a snapshot from snapshot_scm.

    Bare value tuples have no noise, intervention or world provenance and are
    rejected. A valid snapshot is reused only where equations and inputs agree;
    descendants of every changed node are recomputed automatically.
    """
    order=validate_scm(world);modules={m.output:m for m in world.modules};interventions=tuple(interventions);do=dict(interventions);meter=budget.meter()
    if len(do)!=len(interventions):raise ContractError('BoundaryMismatch','duplicate intervention targets are ambiguous')
    if set(do)-modules.keys():raise ContractError('BoundaryMismatch','intervention target absent')
    if any(not modules[k].allowed_interventions for k in do):raise ContractError('BoundaryMismatch','intervention outside module scope')
    if set(noise)!=set(world.noise_ids):raise ContractError('NoiseIdentityConflict','one assignment per declared shared noise identity required')
    noise={key:finite_scalar(value) for key,value in noise.items()};do={key:finite_scalar(value) for key,value in do.items()}
    affected=set(changed);values={}
    if affected-modules.keys():raise ContractError('BoundaryMismatch','changed variable absent from the current world')
    if prior_values:
        if not isinstance(prior_values,_SCMSnapshot) or prior_values._seal is not _SNAPSHOT_SEAL:
            raise ContractError('BoundaryMismatch','incremental reuse requires a snapshot from snapshot_scm, not bare values')
        old_modules={m.output:m for m in prior_values.world.modules};old_noise=dict(prior_values.noise);old_do=dict(prior_values.interventions);values=dict(prior_values.values)
        missing=object()
        for k,m in modules.items():
            if old_modules.get(k)!=m or old_do.get(k,missing)!=do.get(k,missing) or any(old_noise.get(n,missing)!=noise[n] for n,_ in m.noise_terms):affected.add(k)
    for k in order:
        m=modules[k]
        if any(p in affected for p in m.parents):affected.add(k)
        if prior_values and k not in affected:
            if k not in values:raise ContractError('BoundaryMismatch','cached unchanged variable missing')
            continue
        meter.consume(steps=1)
        values[k]=do[k] if k in do else finite_scalar(m.bias+sum(c*values[p] for p,c in zip(m.parents,m.coefficients))+sum(c*noise[n] for n,c in m.noise_terms))
    return tuple((k,values[k]) for k in order)

def graft(source,target,target_node,bindings,new_version,*,output_scale=1.,output_offset=0.,target_unit=None):
    validate_scm(target);modules={m.output:m for m in target.modules}
    if target_node not in modules or new_version==target.version:raise ContractError('BoundaryMismatch','replace a named node and advance world version')
    mapping={b.source_parent:b for b in bindings}
    if set(mapping)!=set(source.parents):raise ContractError('BoundaryMismatch','source parents must all have explicit boundary bindings')
    old=modules[target_node];target_unit=target_unit or source.unit
    if target_unit!=old.unit:raise ContractError('UnitConflict','output conversion must name target unit')
    if source.unit!=old.unit and output_scale==1. and output_offset==0.:raise ContractError('UnitConflict','different output units require an explicit conversion')
    coeff=[];parents=[];units=[];bias=source.bias
    for p,u,c in zip(source.parents,source.parent_units,source.coefficients):
        b=mapping[p]
        if b.source_unit!=u or b.target_parent not in modules or modules[b.target_parent].unit!=b.target_unit:raise ContractError('UnitConflict','boundary conversion units do not match')
        if b.source_unit!=b.target_unit and b.scale==1. and b.offset==0.:raise ContractError('UnitConflict','unit mismatch needs nontrivial explicit conversion')
        finite_scalar(b.scale);finite_scalar(b.offset);parents.append(b.target_parent);units.append(b.target_unit);coeff.append(output_scale*c*b.scale);bias+=c*b.offset
    if any(n not in target.noise_ids for n,_ in source.noise_terms):raise ContractError('NoiseIdentityConflict','grafting cannot silently manufacture independent noise')
    replacement=CausalModule(target_node,old.unit,tuple(parents),tuple(units),tuple(coeff),output_scale*bias+output_offset,tuple((n,output_scale*c) for n,c in source.noise_terms),source.allowed_interventions)
    after=TargetSCM(tuple(replacement if m.output==target_node else m for m in target.modules),target.noise_ids,new_version);order=validate_scm(after)
    affected={target_node}
    for n in order:
        if any(p in affected for p in next(m for m in after.modules if m.output==n).parents):affected.add(n)
    return GraftCertificate(target,after,target_node,tuple(n for n in order if n in affected),tuple((b.source_parent,b.target_parent) for b in bindings)+((source.output,target_node),),target.noise_ids,('affine structural equations','explicit unit conversions','shared exogenous identities preserved'))

def rollback(certificate,current):
    if current!=certificate.after:raise ContractError('VersionMismatch','rollback cannot overwrite a newer world')
    return certificate.before
