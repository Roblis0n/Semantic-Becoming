from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def validate_graph(graph):
    atoms={a.atom_id:a for a in graph.atoms};nodes={n.node_id:n for n in graph.nodes}
    if not graph.version or len(atoms)!=len(graph.atoms) or len(nodes)!=len(graph.nodes) or len(atoms)>64 or len(nodes)>64 or graph.root not in nodes:raise ContractError('MissingSource','bounded unique atom/node identities, root and version required')
    if len({a.source_handle for a in graph.atoms})!=len(graph.atoms):raise ContractError('MissingSource','the same original source must reuse one stable atom, not distinct independent copies')
    visiting=set();done=set();order=[]
    def visit(key):
        if key not in nodes:raise ContractError('MissingSource','missing support node '+key)
        if key in visiting:raise ContractError('EvidenceCycle','circular restatement has no independent evidence semantics')
        if key in done:return
        visiting.add(key);node=nodes[key]
        if node.op=='atom' and node.atom_id not in atoms:raise ContractError('MissingSource','unknown source atom')
        for child in node.inputs:visit(child)
        visiting.remove(key);done.add(key);order.append(key)
    for key in nodes:visit(key)
    return atoms,nodes,tuple(order)

def normalize_support(graph):
    atoms,nodes,order=validate_graph(graph);normal={}
    for key in order:
        node=nodes[key]
        if node.op=='atom':normal[key]=('atom',node.atom_id);continue
        children=[]
        for ref in node.inputs:
            child=normal[ref]
            children.extend(child[1:] if child[0]==node.op else (child,))
        children=sorted(set(children),key=repr)
        # Idempotence plus absorption x OR (x AND y)=x and its dual.
        childset=set(children);opposite='and' if node.op=='or' else 'or'
        children=[c for c in children if not (c[0]==opposite and any(term in childset for term in c[1:]))]
        normal[key]=children[0] if len(children)==1 else (node.op,*children)
    return normal[graph.root]

def expression_atoms(expr):
    return {expr[1]} if expr[0]=='atom' else set().union(*(expression_atoms(c) for c in expr[1:]))

def evaluate_boolean(expr,assignment):
    if expr[0]=='atom':return assignment[expr[1]]
    values=[evaluate_boolean(c,assignment) for c in expr[1:]]
    return all(values) if expr[0]=='and' else any(values)

def unknown_bounds(expr,atoms):
    if expr[0]=='atom':
        p=atoms[expr[1]].marginal;return (0.,1.) if p is None else (p,p)
    bounds=[unknown_bounds(c,atoms) for c in expr[1:]]
    if expr[0]=='and':return max(0.,sum(b[0] for b in bounds)-len(bounds)+1),min(b[1] for b in bounds)
    return max(b[0] for b in bounds),min(1.,sum(b[1] for b in bounds))

def reachable_ancestry(graph):
    atoms,nodes,order=validate_graph(graph);counts={};seen=set()
    def visit(key):
        counts[key]=counts.get(key,0)+1
        if key in seen:return
        seen.add(key)
        for child in nodes[key].inputs:visit(child)
    visit(graph.root)
    atom_occurrences={}
    for key in seen:
        if nodes[key].op=='atom':atom_occurrences[nodes[key].atom_id]=atom_occurrences.get(nodes[key].atom_id,0)+counts[key]
    shared=tuple(sorted({key for key,count in counts.items() if count>1}|{atom for atom,count in atom_occurrences.items() if count>1}))
    return shared

def calibrate_support(graph,dependence,*,budget=StepBudget()):
    import itertools
    atoms,nodes,order=validate_graph(graph);expr=normalize_support(graph);coverage=tuple(sorted(expression_atoms(expr)));meter=budget.meter();meter.dimension(len(atoms));shared=reachable_ancestry(graph)
    scope='synthetic_or_mixed_not_independent_real_observation' if any(atoms[a].source_kind=='synthetic' for a in coverage) else 'local_sources_truth_not_guaranteed'
    if dependence.mode=='unknown':
        lower,upper=unknown_bounds(expr,atoms);prob=lower if lower==upper else None
        return CalibratedSupport(expr,prob,lower,upper,coverage,shared,'marginal_identified' if prob is not None else 'UnknownDependence',scope,graph.version,0)
    if set(dependence.atom_ids)-atoms.keys() or not set(coverage)<=set(dependence.atom_ids):raise ContractError('MissingSource','dependence model does not cover precisely named graph atoms')
    if dependence.mode=='declared_independent':
        if any(atoms[a].marginal is None for a in dependence.atom_ids):raise ContractError('UnsupportedCalibration','independent calculation requires all declared marginals')
        n=len(dependence.atom_ids)
        if 2**n>budget.max_cases:raise ContractError('ResourceExhausted','exact joint assignment enumeration exceeds authorized finite cases')
        assignments=((values,math.prod(atoms[a].marginal if b else 1-atoms[a].marginal for a,b in zip(dependence.atom_ids,values,strict=True))) for values in itertools.product((False,True),repeat=n))
    else:
        for i,a in enumerate(dependence.atom_ids):
            marginal=sum(j.probability for j in dependence.joint if j.values[i])
            if atoms[a].marginal is not None and abs(marginal-atoms[a].marginal)>1e-9:raise ContractError('UnsupportedCalibration','joint contradicts declared source marginal')
        assignments=((j.values,j.probability) for j in dependence.joint)
    probability=0.
    for values,mass in assignments:
        meter.consume(steps=1,cases=1)
        if evaluate_boolean(expr,dict(zip(dependence.atom_ids,values,strict=True))):probability+=mass
    return CalibratedSupport(expr,probability,probability,probability,coverage,shared,'exact_under_'+dependence.mode,scope,graph.version,meter.cases)

def retract_sources(graph,retracted_atoms):
    atoms,nodes,order=validate_graph(graph)
    if set(retracted_atoms)-atoms.keys():raise ContractError('MissingSource','cannot retract unknown original source')
    invalid=set()
    for key in order:
        node=nodes[key]
        if node.op=='atom' and node.atom_id in retracted_atoms or set(node.inputs)&invalid:invalid.add(key)
    return InvalidationSet(tuple(sorted(retracted_atoms)),tuple(key for key in order if key in invalid),graph.root in invalid,graph.version)

def migrate_graph(graph,node_id_map,new_version):
    validate_graph(graph)
    if set(node_id_map)!={n.node_id for n in graph.nodes} or len(set(node_id_map.values()))!=len(node_id_map):raise ContractError('MissingSource','node migration must be explicit bijection; stable atom/source identity is retained')
    migrated=ProvenanceGraph(graph.atoms,tuple(SupportNode(node_id_map[n.node_id],n.op,tuple(node_id_map[i] for i in n.inputs),n.atom_id) for n in graph.nodes),node_id_map[graph.root],new_version);validate_graph(migrated);return migrated

def compile_truth_table(graph,atom_ids,*,budget=StepBudget()):
    import itertools
    expr=normalize_support(graph)
    if len(set(atom_ids))!=len(atom_ids) or not expression_atoms(expr)<=set(atom_ids):raise ContractError('MissingSource','truth table requires unique complete atom axes')
    if 2**len(atom_ids)>budget.max_cases:raise ContractError('ResourceExhausted','truth table case budget exceeded')
    meter=budget.meter();rows=[];truth=[]
    for values in itertools.product((False,True),repeat=len(atom_ids)):
        meter.consume(steps=1,cases=1);rows.append(values);truth.append(evaluate_boolean(expr,dict(zip(atom_ids,values,strict=True))))
    return tuple(rows),tuple(truth)
