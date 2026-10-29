"""X03: invent observable predicates that strictly refine a hypothesis partition."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.mechanisms.h27_ontology.types import Predicate
from latent_comm.mechanisms.h29_questions.types import QuestionIR,TransformLibrary,QuestionGraph
from latent_comm.mechanisms.h30_analogy.types import TypedOperationGraph,AnalogyMorphism,CompiledAnalogy
from latent_comm.mechanisms.h45_identifiability.types import IdentificationState,QuerySpec,QuerySelection
from .contracts import bounded_horizon,assumptions
ASSUMPTIONS=assumptions('Finite hypotheses have public observable records, a question IR, a typed analogy and a bounded predicate grammar.','A candidate question is new only if its response partition strictly separates a previously indistinguishable pair.','The finite procedure produces typed question edges, permitted measurements and retained rejected candidates.','A future model may learn to construct useful new observables beyond the declared grammar; NOT_RUN.')
@dataclass(frozen=True)
class InventionRequest:
    identification: IdentificationState
    records: tuple[tuple[str,dict],...]
    predicates: tuple[Predicate,...]
    question: QuestionIR
    rewrites: TransformLibrary
    source_graph: TypedOperationGraph
    target_graph: TypedOperationGraph
    morphism: AnalogyMorphism
    allowed_observable_fields: frozenset[str]
    versions: VersionSet
@dataclass(frozen=True)
class InventedMeasurement:
    query: QuerySpec
    predicate: Predicate
    newly_separated_pairs: tuple[tuple[str,str],...]
@dataclass(frozen=True)
class InventionRecord:
    question_graph: QuestionGraph
    analogy: CompiledAnalogy
    measurements: tuple[InventedMeasurement,...]
    selection: QuerySelection
    rejected: tuple[tuple[int,str],...]
    status: str
@bounded_horizon('X03',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.mechanisms.h27_ontology.reference import evaluate
    from latent_comm.mechanisms.h29_questions.reference import build_question_graph
    from latent_comm.mechanisms.h30_analogy.reference import check_morphism
    from latent_comm.mechanisms.h45_identifiability.reference import equivalence_partition,select_query
    q=request
    if q.identification.version!=q.versions.task or q.question.version!=q.versions.task:raise ContractError('VersionMismatch','questions and hypothesis state require current task semantics')
    records=dict(q.records)
    if len(records)!=len(q.records) or set(records)!=set(q.identification.hypotheses) or len(records)>8 or len(q.predicates)>8:raise ContractError('UnboundObservation','one public record per hypothesis, at most eight records and predicates')
    graph=build_question_graph(q.question,q.rewrites,max_transform_depth=1,candidate_questions=4,budget=StepBudget(max_steps=32,max_cases=32))
    analogy=check_morphism(q.source_graph,q.target_graph,q.morphism)
    if analogy.broken_squares:raise ContractError('NoncommutingAnalogy','similar language alone cannot transport a query operation')
    old=equivalence_partition(q.identification);pairs=tuple((a,b) for group in old for i,a in enumerate(group) for b in group[i+1:]);found=[];rejected=[]
    def fields(p):return {p.field} if p.field is not None else set().union(*(fields(c) for c in p.children))
    for index,predicate in enumerate(q.predicates):
        meter.consume(steps=1,cases=1)
        if not fields(predicate)<=q.allowed_observable_fields:raise ContractError('RoleLeakage','measurement grammar cannot inspect hidden or undeclared fields')
        values={h:evaluate(predicate,records[h]) for h in q.identification.hypotheses}
        if any(v is None for v in values.values()):rejected.append((index,'unknown observable; no fabricated response likelihood'));continue
        separated=tuple((a,b) for a,b in pairs if values[a]!=values[b])
        if not separated:rejected.append((index,'no new distinguishing power; paraphrase or redundant query'));continue
        query=QuerySpec('invented:'+str(index),('false','true'),tuple((0.,1.) if values[h] else (1.,0.) for h in q.identification.hypotheses),1.,True,True)
        found.append(InventedMeasurement(query,predicate,separated))
    revised=replace(q.identification,queries=q.identification.queries+tuple(m.query for m in found));selection=select_query(revised)
    return InventionRecord(graph,analogy,tuple(found),selection,tuple(rejected),'NewObservableDistinctions' if found else 'NoNewQuestionWithinGrammar'),('Declared finite likelihoods are program consequences, not real observations.','Question-edge soundness/completeness and analogy uncovered domains remain separate obligations.')
