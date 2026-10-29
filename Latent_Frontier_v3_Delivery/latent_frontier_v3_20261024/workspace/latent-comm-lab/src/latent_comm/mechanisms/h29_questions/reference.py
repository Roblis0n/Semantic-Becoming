from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from latent_comm.core.budgets import aggregate_budget
from .types import *

from itertools import product

def satisfies(question,answer,tolerance=1e-9):
    if len(answer)!=len(question.variables):raise ContractError('OutOfDomain','answer coordinate arity differs')
    if any(x not in d for x,d in zip(answer,question.domains)):return False
    for c in question.constraints:
        v=sum(coef*math.prod(x**p for x,p in zip(answer,powers)) for coef,powers in c.terms)
        if c.relation=='eq' and abs(v-c.rhs)>tolerance:return False
        if c.relation=='le' and v>c.rhs+tolerance:return False
        if c.relation=='ge' and v<c.rhs-tolerance:return False
    return True

def solutions(question,budget=StepBudget()):
    meter=budget.meter();out=[]
    for answer in product(*question.domains):
        meter.consume(steps=1,cases=1)
        if satisfies(question,answer):out.append(tuple(answer))
    return tuple(out)

def translate(mapping,answer):return add(matvec(mapping.matrix,answer),mapping.offset)

def check_relation(transform,budget=StepBudget(),enforce_claim=True):
    with aggregate_budget(budget):
        return _check_relation(transform,budget,enforce_claim)

def _check_relation(transform,budget,enforce_claim):
    q,t,m=transform.source,transform.target,transform.backtranslation
    if m.source_question!=t.question_id or m.target_question!=q.question_id or len(m.matrix)!=len(q.variables) or len(m.matrix[0])!=len(t.variables):raise ContractError('RelationUnproven','answer map must point target answers back to original coordinates')
    original=solutions(q,budget);target=solutions(t,budget)
    mapped=tuple(dict.fromkeys(translate(m,a) for a in target));s=set(original);u=set(mapped)
    invalid=tuple(sorted(u-s));lost=tuple(sorted(s-u));sound=not invalid;complete=not lost
    relation='equivalent' if sound and complete else 'sufficient' if sound else 'necessary' if complete else 'heuristic'
    claim=transform.claimed_relation
    if claim not in ('equivalent','sufficient','necessary','partial','heuristic'):raise ContractError('RelationUnproven','unsupported answer relation')
    valid={'equivalent':sound and complete,'sufficient':sound,'partial':sound and not complete,'necessary':complete,'heuristic':True}[claim]
    if enforce_claim and not valid:raise ContractError('LostSolutions' if lost else 'RelationUnproven',f'claimed {claim} but verified {relation}')
    return RelationWitness(relation,sound,complete,original,target,mapped,invalid,lost)

def strengthen(question,constraint,new_id):
    target=replace(question,question_id=new_id,constraints=question.constraints+(constraint,))
    return QuestionTransform(question,target,AnswerMap(eye(len(question.variables)),(0.,)*len(question.variables),new_id,question.question_id),'sufficient',('same finite domain',))

def introduce_auxiliary(question,name,domain,coefficient,offset,new_id):
    if name in question.variables:raise ContractError('OutOfDomain','auxiliary name already bound')
    n=len(question.variables)
    if len(coefficient)!=n:raise ContractError('OutOfDomain','auxiliary affine binding arity differs')
    old=tuple(PolynomialConstraint(tuple((c,p+(0,)) for c,p in x.terms),x.relation,x.rhs) for x in question.constraints)
    terms=[(1.,(0,)*n+(1,))]
    for i,c in enumerate(coefficient):terms.append((-c,tuple(int(k==i) for k in range(n))+(0,)))
    target=QuestionIR(new_id,question.variables+(name,),question.domains+(tuple(domain),),old+(PolynomialConstraint(tuple(terms),'eq',offset),),question.version,question.evidence)
    projection=tuple(tuple(float(i==j) for j in range(n+1)) for i in range(n))
    transform=QuestionTransform(question,target,AnswerMap(projection,(0.,)*n,new_id,question.question_id),'equivalent',('auxiliary domain covers every source solution',))
    check_relation(transform)
    return transform

def compose(first,second,budget=StepBudget()):
    with aggregate_budget(budget):
        return _compose(first,second,budget)

def _compose(first,second,budget):
    if first.target!=second.source:raise ContractError('RelationUnproven','question path endpoints differ')
    check_relation(first,budget);check_relation(second,budget)
    a,b=first.backtranslation,second.backtranslation
    m=AnswerMap(matmul(a.matrix,b.matrix),add(matvec(a.matrix,b.offset),a.offset),second.target.question_id,first.source.question_id)
    combined=QuestionTransform(first.source,second.target,m,'heuristic',first.preconditions+second.preconditions)
    witness=check_relation(combined,budget)
    return replace(combined,claimed_relation=witness.relation)

def answer_preimages(mapping,original_answer,target_question,budget=StepBudget()):
    return tuple(a for a in solutions(target_question,budget) if translate(mapping,a)==original_answer)

def migrate_question(question,new_version,renames):
    if set(renames)!=set(question.variables) or len(set(renames.values()))!=len(renames):raise ContractError('RelationUnproven','variable migration must preserve all coordinate bindings')
    return replace(question,variables=tuple(renames[v] for v in question.variables),version=new_version)

def apply_rewrite_rule(question,rule,new_id):
    if rule.kind=='strengthen':
        if rule.constraint is None:raise ContractError('RelationUnproven','strengthening requires an executable constraint')
        return strengthen(question,rule.constraint,new_id)
    if rule.kind=='introduce_auxiliary':
        return introduce_auxiliary(question,rule.auxiliary_name,rule.auxiliary_domain,rule.auxiliary_coefficients,rule.auxiliary_offset,new_id)
    if not 0<=rule.drop_constraint_index<len(question.constraints):
        raise ContractError('RelationUnproven','relaxation constraint index absent')
    constraints=tuple(c for i,c in enumerate(question.constraints) if i!=rule.drop_constraint_index)
    target=replace(question,question_id=new_id,constraints=constraints)
    return QuestionTransform(question,target,AnswerMap(eye(len(question.variables)),(0.,)*len(question.variables),new_id,question.question_id),'necessary',('same finite variable domain',))

def build_question_graph(initial,library,*,max_transform_depth=5,candidate_questions=32,budget=StepBudget()):
    with aggregate_budget(budget):
        return _build_question_graph(initial,library,max_transform_depth=max_transform_depth,candidate_questions=candidate_questions,budget=budget)

def _build_question_graph(initial,library,*,max_transform_depth,candidate_questions,budget):
    import json
    from dataclasses import asdict
    if not 0<=max_transform_depth<=128 or not 1<=candidate_questions<=64:
        raise ContractError('TransformBudget','explicit finite depth and question bounds required')
    def signature(q):
        return json.dumps({'variables':q.variables,'domains':q.domains,'constraints':[asdict(c) for c in q.constraints]},sort_keys=True)
    nodes={initial.question_id:initial};seen={signature(initial):initial.question_id};frontier=[(initial.question_id,0)];edges=[];meter=budget.meter();status='complete_within_declared_depth'
    while frontier:
        source_id,depth=frontier.pop(0)
        if depth>=max_transform_depth:continue
        question=nodes[source_id]
        for rule in library.rules:
            if len(nodes)>=candidate_questions or meter.steps>=budget.max_steps:
                frontier.insert(0,(source_id,depth));status='TransformBudget';break
            edge_id='edge:'+str(len(edges));new_id=source_id+'/'+rule.rule_id+':'+str(len(edges))
            try:
                meter.consume(steps=1)
                transform=apply_rewrite_rule(question,rule,new_id)
                witness=check_relation(transform,budget)
                key=signature(transform.target)
                if key in seen:
                    target=nodes[seen[key]]
                    transform=replace(transform,target=target,backtranslation=replace(transform.backtranslation,source_question=target.question_id))
                else:
                    target=transform.target;seen[key]=target.question_id;nodes[target.question_id]=target;frontier.append((target.question_id,depth+1))
                edges.append(QuestionEdge(edge_id,source_id,target.question_id,rule.rule_id,transform,witness,None))
            except ContractError as error:
                if error.failure.code=='BudgetExhausted':
                    frontier.insert(0,(source_id,depth));status='TransformBudget';break
                edges.append(QuestionEdge(edge_id,source_id,None,rule.rule_id,None,None,str(error)))
        if status=='TransformBudget':break
    return QuestionGraph(tuple(nodes.values()),tuple(edges),tuple(frontier),status,library.version)

def transport_graph_answer(graph,edge_ids,answer):
    edges={e.edge_id:e for e in graph.edges};path=[]
    for edge_id in edge_ids:
        if edge_id not in edges or edges[edge_id].transform is None:raise ContractError('RelationUnproven','path contains an absent or rejected rewrite')
        edge=edges[edge_id]
        if path and path[-1].target_id!=edge.source_id:raise ContractError('RelationUnproven','question graph path is disconnected')
        if not edge.witness.sound:raise ContractError('RelationUnproven','necessary/heuristic edge cannot reliably transport every target answer')
        path.append(edge)
    if not path:raise ContractError('RelationUnproven','explicit solution transport path required')
    if not satisfies(path[-1].transform.target,answer):raise ContractError('OutOfDomain','provided terminal answer is not a target solution')
    result=tuple(answer)
    for edge in reversed(path):result=translate(edge.transform.backtranslation,result)
    return result
