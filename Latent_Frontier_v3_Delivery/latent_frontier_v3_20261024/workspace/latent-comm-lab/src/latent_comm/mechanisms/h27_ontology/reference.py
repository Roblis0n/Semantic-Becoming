from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

def evaluate(predicate,record):
    if predicate.op in ('eq','le'):
        value=record.get(predicate.field)
        if value is None:return None
        if predicate.op=='eq':return value==predicate.constant
        if type(value) not in (float,int):raise ContractError('UndefinedPredicate','ordered atom needs numeric evidence')
        return finite_scalar(value)<=predicate.constant
    values=tuple(evaluate(c,record) for c in predicate.children)
    if predicate.op=='not':return None if values[0] is None else not values[0]
    if predicate.op=='and':return False if False in values else None if None in values else True
    return True if True in values else None if None in values else False

def search_concept(old,records,required_pairs,atoms,*,concept_id,evidence,depth=4,candidate_limit=64,description_weight=.001,drift_weight=0.,budget=StepBudget()):
    from latent_comm.core.views import freeze_public
    if not records or not required_pairs or not atoms or not 1<=depth<=8 or not 1<=candidate_limit<=64:raise ContractError('GrammarExhausted','finite nonempty grammar, records and pairs required')
    meter=budget.meter();meter.dimension(len(records)); records=tuple(freeze_public(r) for r in records)
    for a,b in required_pairs:
        if not 0<=a<len(records) or not 0<=b<len(records):raise ContractError('OutOfDomain','pair index outside witness domain')
        if any(evaluate(c.predicate,records[a])!=evaluate(c.predicate,records[b]) for c in old.concepts):raise ContractError('NotAnExpressionGap','old language already distinguishes requested pair')
    candidates=list(atoms);seen=set();extensions={}; examined=0;best=None
    while candidates and examined<candidate_limit:
        p=candidates.pop(0)
        if p in seen or p.depth>depth:continue
        seen.add(p);meter.consume(steps=1,cases=1);examined+=1
        signature=tuple(evaluate(p,r) for r in records)
        group=extensions.setdefault(signature,[]);group.append(p)
        if all(signature[a] is not None and signature[b] is not None and signature[a]!=signature[b] for a,b in required_pairs):
            drift=sum(value is None for value in signature)/len(signature)
            score=description_weight*p.description_length+drift_weight*drift
            if best is None or score<best[0]:best=(score,p,signature)
        if p.depth<depth:
            candidates.append(Predicate('not',children=(p,)))
            for q in atoms:
                candidates.extend((Predicate('and',children=(p,q)),Predicate('or',children=(p,q))))
    if best is None:raise ContractError('GrammarExhausted',f'no separating concept in {examined} examined candidates; not a global impossibility proof',recoverable=True)
    score,p,signature=best
    definition=ConceptDefinition(concept_id,p,tuple(c.concept_id for c in old.concepts),tuple(evidence),tuple(sorted({k for r in records for k in r})))
    return DistinctionWitness(definition,signature,tuple(required_pairs),tuple(extensions[signature]),score,examined)

def revise_ontology(old,new_version,additions,retire=(),consumer_targets=()):
    if new_version==old.version:raise ContractError('AmbiguousMigration','new ontology version required')
    prior={c.concept_id:c for c in old.concepts};retire=set(retire)
    if not retire<=prior.keys():raise ContractError('DanglingConcept','retirement target absent')
    definitions={k:v for k,v in prior.items() if k not in retire}
    for c in additions:
        if c.concept_id in definitions:raise ContractError('AmbiguousMigration','new concept must not redefine an existing versioned ID')
        if not set(c.parents)<=prior.keys():raise ContractError('DanglingConcept','parent absent in prior ontology')
        definitions[c.concept_id]=c
    targets=dict(consumer_targets);migrations=[];consumers=[]
    for reader,concept in old.consumers:
        target=targets.get(reader,concept)
        if target not in definitions:raise ContractError('AmbiguousMigration','retired concept consumer requires explicit replacement')
        consumers.append((reader,target));migrations.append((reader,concept,target))
    after=OntologySnapshot(new_version,tuple(definitions.values()),tuple(consumers))
    return OntologyDelta(old,after,tuple(migrations),tuple(sorted(retire)))

def read_concept(snapshots,version,concept_id,record):
    for snapshot in snapshots:
        if snapshot.version==version:
            for c in snapshot.concepts:
                if c.concept_id==concept_id:return evaluate(c.predicate,record)
            raise ContractError('DanglingConcept','concept absent in requested historical ontology')
    raise ContractError('VersionMismatch','reader snapshot unavailable')

def predicate_from_dict(data,depth=0):
    if depth>8:raise ContractError('BudgetExhausted','predicate depth exceeds finite codec limit')
    if set(data)!={'op','field','constant','children'}:raise ContractError('InvalidSchema','predicate fields must be explicit')
    return Predicate(data['op'],data['field'],data['constant'],tuple(predicate_from_dict(c,depth+1) for c in data['children']))
