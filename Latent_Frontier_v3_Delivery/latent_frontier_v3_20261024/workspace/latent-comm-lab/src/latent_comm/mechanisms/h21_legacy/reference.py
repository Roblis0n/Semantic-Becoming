from dataclasses import replace
import hashlib,json,math
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import finite_scalar
from latent_comm.mechanisms.h31_grafting.reference import evaluate_scm,validate_scm
from .types import PortfolioNode,PortfolioResult

def semantic_key(node):
    payload={'state':node.anchor_state,'do':node.intervention,'kind':node.branch_kind,'question':node.question_id,'world':node.world_id,'versions':node.versions.as_dict(),'evidence':sorted(node.evidence),'synthetic':node.synthetic}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()
def public_score(node,goal):
    state=dict(node.anchor_state)
    if goal.variable not in state:raise ContractError('UnboundGoal','public goal variable absent in branch')
    return -(state[goal.variable]-goal.target)**2

def search_counterfactuals(world,noise,root,options,goal,*,max_depth,budget=StepBudget()):
    validate_scm(world)
    if world.version!=root.versions.world:raise ContractError('VersionMismatch','SCM and branch world version differ')
    if not 0<=max_depth<=128 or len(options)>64:raise ContractError('BudgetExhausted','finite explicit intervention search')
    if len(dict(options))!=len(options):raise ContractError('DuplicateVariable','one candidate domain per intervention variable')
    names={m.output for m in world.modules};allowed={m.output for m in world.modules if m.allowed_interventions}
    if any(name not in allowed or len(values)>64 for name,values in options):raise ContractError('InterventionForbidden','unknown or protected causal variable')
    meter=budget.meter();meter.consume(steps=len(world.modules),cases=1)
    expected=tuple(sorted(evaluate_scm(world,noise,interventions=root.intervention,budget=budget)))
    if tuple(sorted(root.anchor_state))!=expected:raise ContractError('AnchorMismatch','root must bind the same SCM, noise and do assignments')
    for name,values in options:
        for value in values:finite_scalar(value)
    nodes={root.node_id:root};keys={semantic_key(root):root.node_id};queue=[(root.node_id,0)];edges=[];evaluations=0;reused=0;best=root.node_id
    while queue:
        parent_id,depth=queue.pop(0);parent=nodes[parent_id]
        if depth>=max_depth:continue
        for name,values in options:
            for value in values:
                intervention=dict(parent.intervention);intervention[name]=value
                # The semantic operation key includes do assignments, not answer strings.
                shortcut=next((n for n in nodes.values() if n.intervention==tuple(sorted(intervention.items())) and n.question_id==parent.question_id and n.versions==parent.versions),None)
                if shortcut is not None:
                    if shortcut.node_id!=parent_id:edges.append((parent_id,shortcut.node_id))
                    reused+=1;continue
                try:meter.consume(steps=len(world.modules),branches=1,cases=1)
                except ContractError as e:
                    if e.failure.code!='BudgetExhausted':raise
                    return PortfolioResult(tuple(nodes.values()),tuple(edges),tuple([parent_id]+[k for k,_ in queue]),best,evaluations,reused,'search_exhausted_within_budget')
                state=evaluate_scm(world,noise,interventions=tuple(sorted(intervention.items())),budget=budget);evaluations+=1
                child=replace(parent,node_id=root.node_id+'/do:'+str(evaluations),anchor_state=tuple(sorted(state)),intervention=tuple(sorted(intervention.items())),lineage=parent.lineage+(parent_id,),selection_basis='public_goal_squared_error')
                key=semantic_key(child)
                if key in keys:edges.append((parent_id,keys[key]));reused+=1;continue
                keys[key]=child.node_id;nodes[child.node_id]=child;edges.append((parent_id,child.node_id));queue.append((child.node_id,depth+1))
                if public_score(child,goal)>public_score(nodes[best],goal):best=child.node_id
    return PortfolioResult(tuple(nodes.values()),tuple(edges),(),best,evaluations,reused,'enumerated_declared_depth_not_global_proof')

def update_evidence_weights(nodes,prior,likelihood,*,evidence_id,seen):
    if evidence_id in seen:return tuple(prior),frozenset(seen)
    if len(nodes)!=len(prior) or len(prior)!=len(likelihood) or any(not math.isfinite(p) or p<0 for p in tuple(prior)+tuple(likelihood)):raise ContractError('InvalidProbability','one nonnegative finite prior/likelihood per semantic branch')
    weights=[p*l for p,l in zip(prior,likelihood)];total=sum(weights)
    if total<=0:raise ContractError('EvidenceConflict','all represented branches contradicted; unknown alternatives remain possible')
    return tuple(w/total for w in weights),frozenset(seen)|{evidence_id}

def question_branch(node,transform,witness,*,node_id,budget=StepBudget()):
    from latent_comm.mechanisms.h29_questions.reference import check_relation
    checked=check_relation(transform,budget=budget)
    if checked!=witness:raise ContractError('RelationUnproven','supplied witness must match executable finite relation check')
    if transform.source.question_id!=node.question_id or transform.source.version!=node.versions.task or not witness.sound:raise ContractError('RelationUnproven','H29 branch requires checked answer backtranslation')
    return replace(node,node_id=node_id,branch_kind='question',question_id=transform.target.question_id,lineage=node.lineage+(node.node_id,),versions=replace(node.versions,task=transform.target.version),selection_basis='verified_question_relation')
def world_branch(node,dream,*,node_id,world_version):
    if world_version!=dream.kernel.version:raise ContractError('VersionMismatch','synthetic branch binds the actual constructed kernel version')
    if not dream.synthetic:raise ContractError('SyntheticAsReal','H44 constructed branch must remain synthetic')
    return replace(node,node_id=node_id,branch_kind='world',world_id=dream.world_id,versions=replace(node.versions,world=world_version),lineage=node.lineage+(node.node_id,),synthetic=True,selection_basis='constructed_world_coverage')
def counterexample_branch(node,counterexample,*,claim_id):
    if counterexample.claim_id!=claim_id or counterexample.status!='verified_counterexample' or counterexample.expected is None:raise ContractError('InvalidCounterexample','H36 requires executable checked counterexample, not disagreement alone')
    return replace(node,evidence=node.evidence|{claim_id+':'+str(counterexample.value)})
def identification_state(nodes,queries,prior,*,version):
    from latent_comm.mechanisms.h45_identifiability.types import IdentificationState
    if not nodes:raise ContractError('InvalidBranch','identification requires represented hypotheses')
    if any(n.versions.evidence!=nodes[0].versions.evidence for n in nodes):raise ContractError('VersionMismatch','H45 hypotheses need common evidence version')
    return IdentificationState(tuple(n.node_id for n in nodes),tuple(queries),tuple(prior),version,True)


def concept_branch(node,delta,*,node_id,concept_id):
    if delta.before.version!=node.versions.ontology or delta.after.version==delta.before.version:raise ContractError('VersionMismatch','concept branch requires an explicit ontology advance')
    if concept_id not in {c.concept_id for c in delta.after.concepts}:raise ContractError('DanglingConcept','new branch must bind an actual target concept')
    return replace(node,node_id=node_id,branch_kind='concept',versions=replace(node.versions,ontology=delta.after.version),lineage=node.lineage+(node.node_id,),selection_basis='ontology_definition:'+concept_id)
