"""X08: relay finite proof-search obligations without pretending a partial proof is complete."""
from dataclasses import dataclass
from latent_comm.core import ContractError,VersionSet
from latent_comm.mechanisms.h05_legacy.types import ContinuationPacket,ProgramOperation,ResumeContract
from latent_comm.mechanisms.h29_questions.types import QuestionIR
from latent_comm.mechanisms.h46_negative_knowledge.types import ExclusionCapsule,ConditionalFeasibleRegion
from .contracts import bounded_horizon,assumptions
ASSUMPTIONS=assumptions('A finite integer question domain, explicit exclusion premises and bounded proof/search continuation exist.','Each hard exclusion predicate is checked as necessary for the actual question on the exact finite domain.','A relay preserves the completed prefix, unresolved candidates, assumption provenance and remaining obligations.','Future research may relay discoveries that are not yet fully provable; finite proof checks are not an admission gate for all conjectures.')
@dataclass(frozen=True)
class DiscoveryRequest:
    question: QuestionIR
    domain: tuple[int,...]
    exclusions: tuple[ExclusionCapsule,...]
    active_assumptions: frozenset[str]
    retracted: frozenset[str]
    relay_steps: tuple[int,...]
    versions: VersionSet
@dataclass(frozen=True)
class DiscoveryRecord:
    region: ConditionalFeasibleRegion
    continuation: ContinuationPacket
    established_solutions: tuple[int,...]
    rejected_candidates: tuple[int,...]
    remaining_candidates: tuple[int,...]
    branch_lineage: tuple[tuple[str,str],...]
    status: str
@bounded_horizon('X08',ASSUMPTIONS)
def run(request,meter):
    from latent_comm.mechanisms.h46_negative_knowledge.reference import apply_exclusions,predicate_holds
    from latent_comm.mechanisms.h29_questions.reference import satisfies
    from latent_comm.mechanisms.h05_legacy.reference import capture,resume
    from latent_comm.mechanisms.h13_legacy.types import BranchState
    from latent_comm.mechanisms.h13_legacy.reference import fork,write_slot
    q=request
    if len(q.question.variables)!=1 or tuple(q.question.domains[0])!=tuple(q.domain) or q.question.version!=q.versions.task or not 1<=len(q.domain)<=4 or len(q.question.constraints)>2 or not 1<=len(q.relay_steps)<=3:raise ContractError('UnboundProofScope','one variable, at most four finite candidates and two constraints, three relays')
    for capsule in q.exclusions:
        if capsule.mode=='hard':
            for x in q.domain:
                meter.consume(steps=1,cases=1)
                if satisfies(q.question,(x,)) and not predicate_holds(capsule.witness.required_predicate,x):raise ContractError('UnsoundNecessaryCondition','exclusion witness predicate is not necessary for this actual question')
    region=apply_exclusions(q.domain,q.exclusions,q.active_assumptions,q.versions.ontology,retracted=q.retracted)
    # The finite checker is encoded as explicit arithmetic evidence per candidate.
    # Continuation entries record computed polynomial residuals; they do not encode
    # a preselected answer. Full relation checks still inspect every constraint.
    program=[]
    for x in region.feasible:
        for j,c in enumerate(q.question.constraints):
            expression=('const',-c.rhs)
            for coefficient,powers in c.terms:
                term=('const',coefficient)
                for _ in range(powers[0]):term=('mul',term,('const',x))
                expression=('add',expression,term)
            program.append(ProgramOperation('check:'+str(x)+':'+str(j),'residual:'+str(x)+':'+str(j),expression))
    contract=ResumeContract('finite-proof-program','none','float64','named-residuals','exact_program');packet=capture(tuple(program),{},contract=contract,versions=q.versions,transaction_version=q.versions.state,evidence=q.question.evidence)
    lineage=[];branch=BranchState('proof-root',(),(('program_counter',(0.,)),),(),frozenset(),(),'sequential',frozenset(q.question.evidence),q.versions.ontology,q.question.question_id,q.versions.state,q.versions)
    for i,count in enumerate(q.relay_steps):
        if not 1<=count<=8:raise ContractError('BudgetExhausted','each relay declares one to eight operations')
        meter.consume(steps=1);before=packet.program_counter;packet=resume(packet,max_operations=count);parent=branch.branch_id;branch=fork(branch,'relay:'+str(i));branch=write_slot(branch,'program_counter',(float(packet.program_counter),),reads=('program_counter',),operation='resume-proof',commutation_class='sequential');lineage.append((parent,branch.branch_id))
    completed=set(packet.completed_operations);proven=[];rejected=[];remaining=[]
    for x in region.feasible:
        needed={'check:'+str(x)+':'+str(j) for j in range(len(q.question.constraints))}
        if not needed<=completed:remaining.append(x)
        elif satisfies(q.question,(x,)):proven.append(x)
        else:rejected.append(x)
    return DiscoveryRecord(region,packet,tuple(proven),tuple(rejected),tuple(remaining),tuple(lineage),'FiniteProofComplete' if not remaining else 'UnfinishedProofRetained'),('Retraction rebuilds from the original domain; no permanently pruned candidates are silently reused.','A finite scoped proof or search failure says nothing about arbitrary domains or all scientific conjectures.')
