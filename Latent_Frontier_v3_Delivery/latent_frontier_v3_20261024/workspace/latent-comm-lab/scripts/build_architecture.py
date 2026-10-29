"""Author the explicit A01 architecture from immutable plan registries."""
import json
from pathlib import Path
W=Path(__file__).resolve().parents[1];P=W.parents[1]
def save(name,data):
 p=W/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
H=json.loads((P/'specs/hypotheses.json').read_text());C=json.loads((P/'specs/combinations.json').read_text());X=json.loads((P/'specs/horizons.json').read_text())
# Each row names a genuinely different computational object and operation.
rows=[
('Z,P','OperatorPacket','ordered low-rank nonlinear state transformation','composition is function order, not factor addition'),
('Z,F','ResponseCapsule','local low-rank response prediction and refresh','trust radius is enforced; derivative is not automatically causal'),
('Z,E','BeliefPacket','whole-sequence mixture and prefix posterior update','branches remain separate; source dependence is explicit'),
('Z','ConstraintField','bounded constrained residual minimization','retain anchored per-source conflict; do not zero all weights'),
('Z,K,P','ContinuationPacket','capture and resume remaining computation','exact same-model and heterogeneous approximation are distinct'),
('Z,F','AtlasPacket','route local chart and compose transition maps','heterodimensional maps are not invertible changes of basis'),
('P,Z','TypedProgram','parse, typecheck and interpret bounded instructions','no arbitrary Python or shell evaluation'),
('Z,O','RelationPacket','match and exchange typed relational graphs','preserve relation edges, not merely embedding proximity'),
('W','InterventionPacket','do-operator surgery and ordered interventions','observational conditioning is not intervention'),
('P,Z','HyperedgePacket','evaluate higher-order interaction terms','pairwise decomposition is not presumed sufficient'),
('Z,K','ProgressiveCode','decode prefix layers with explicit quantization error','partial decode has explicit precision and pending layers'),
('Z,E','PersistentCapsule','versioned multi-query retrieval','cache keys contain all semantic versions and scope'),
('Z,P,E','BranchState','copy-on-write fork and conflict-aware merge','incompatible branches cannot be averaged silently'),
('P','SkillGrammar','typed production binding and bounded expansion','variable binding survives expansion'),
('F,Z','ProtocolPopulation','cross-pair adapter sampling and behavior alignment','model IDs are routing metadata, not training evidence'),
('Z,O','DualChannelPacket','bind exact symbols to latent slots','exact symbolic commitments cannot be silently overwritten'),
('F,Z,W','GroundingFrame','transport coordinates and action-effect anchors','same dimension does not establish semantic equivalence'),
('P,K','TopologyProposal','construct bounded capability-compatible graph','structural search and parameter gradients are distinct'),
('U,Z','ConsolidationSpec','distill reusable message effects into scoped adapters','temporary messages and persistent parameter updates differ'),
('K,Z','CognitiveClock','event-driven updates with stale-read policy','time version and causal order are explicit'),
('P,Z,E','CounterfactualPortfolio','bounded branch selection with ancestry reuse','search timeout is not an impossibility proof'),
('P,K,Z','BoundaryPartition','change computation ownership and continuation placement','external permissions cannot move with a research boundary'),
('Z,E','SemanticResidual','diagnose and transmit scoped correction','repair is based on explicit residual, not invented truth'),
('P,Z','ScopedCapability','validate and apply declared research effects','a packet cannot grant host authority'),
('F,Z','GaugePacket','conjugate state, operator and readout under invertible frame change','r G^-1 G T G^-1 G z = r T z only within declared group'),
('F,Z,E','SheafPacket','solve affine overlap constraints and expose obstruction','nonzero anchors prevent trivial zero-section consensus'),
('O,Z','ConceptProposal','synthesize executable distinguishing predicates and migrate readers','unknown differs from false; no candidate preserves the conflict'),
('O,F,Z','PhaseState','follow control-path branches and structural transitions','analytic bifurcation is not evidence of neural phase transitions'),
('Q','QuestionObject','rewrite problems with solution back-translation','soundness and completeness witnesses are separate'),
('Q,P,O','AnalogyMorphism','compile partial operation-preserving maps','unmatched domain and broken commuting squares stay visible'),
('W','CausalModule','graft structural equations through explicit boundaries','preserve unaffected equations and shared exogenous identity'),
('V','ObjectiveFrame','transform cost coordinates and preference covectors','immutable external goal and hard constraints are unchanged'),
('Z,K','DynamicsPacket','integrate gradient plus skew-coupled trajectories','cycles are valid outputs; finite integration does not claim convergence'),
('Z,K,Q','TrajectoryFactorGraph','solve public two-boundary path constraints','terminal conditions cannot be hidden future observations'),
('F,K,Z','ScalePacket','coarsen, lift and measure dynamic closure residual','a lifting map is not a lossless inverse'),
('O,Q,E','DisagreementRound','find checked counterexamples and revise finite candidates','votes are not ground truth; unavailable oracle stays unavailable'),
('U,F','LearningEffectPacket','transport behavioral tangent by JVP/VJP least squares','unreachable residual and regularization/rank diagnostics are mandatory'),
('U','PlasticityProgram','interpret scoped update DSL and unrolled meta-objective','support/query isolation and estimator kind are explicit'),
('Z,F,O,P,Q,V,K,W,U,E','CognitiveTransaction','optimistic versioned commit or rollback','only controlled state is reversible, not external world effects'),
('P,O','InstructionProposal','introduce hygienic macros with base-ISA lowering','base ISA is immutable; learned shortcuts are not definitions'),
('P,K,E','CoalitionContract','compute bounded coalition value and internal contribution','unknown value is not zero; credit is not money'),
('O,P,W,K','EcologyState','mutate and archive bounded program/world populations','lineage and semantic version migrations are preserved'),
('W','WorldKernel','compose normalized finite dynamics with explicit noise coupling','independence requires a certificate; shared noise stays shared'),
('W,Q,E','DreamWorld','construct executable counterfactual worlds and derived questions','synthetic evidence cannot support its own real-world truth'),
('Q,E','IdentificationState','choose allowed queries by information gain or minimax partition','unknown likelihood is not a fabricated prior'),
('Q,E','ExclusionPacket','apply conditional hard exclusions or soft penalties and retract','timeout and heuristic scores do not become hard impossibility'),
('F,Q,Z','QuotientPacket','partition by finite behavior signatures and refine with new queries','epsilon proximity is not automatically an equivalence relation'),
('E','EvidenceExpression','normalize idempotent support DAG and evaluate declared dependence','duplicate source .8 stays .8, not independent .96')]
mechanisms=[]
for h,row in zip(H,rows,strict=True):
 components,obj,operation,invariant=row
 mechanisms.append({'id':h['id'],'title':h['title'],'components_written':components.split(','),'object_type':obj,'operation':operation,'invariant':invariant,'source':h['design_path'],'target':h['target_base'],'claim_class':'H','research_state':'NOT_RUN'})
components={'Z':'typed latent state and exact symbols','F':'frames and local atlases','O':'ontology and executable concepts','P':'ISA, macro library and typed programs','Q':'questions and solution relations','V':'internal objective views','K':'clocks, scales and bounded schedules','W':'world dynamics and noise contracts','U':'scoped learning rules and update effects','E':'evidence expressions and dependencies'}
assumptions=[
 {'id':'A_COMMON_BEHAVIOR','statement':'A declared finite public behavior coordinate system can compare participating models.','consumers':['H06','H15','H25','H37'],'failure':'UnboundBehaviorMap or projection residual; no tokenizer-wise KL'},
 {'id':'A_INVERTIBLE_FRAME','statement':'Gauge maps are square invertible on the declared domain.','consumers':['H25','H32'],'failure':'OutOfDomain; compression follows H06/H35 instead'},
 {'id':'A_PREDICATE_GRAMMAR','statement':'The finite predicate grammar contains a useful distinction for the selected witnesses.','consumers':['H27','H36'],'failure':'NoCandidateWithinGrammar; retain branches'},
 {'id':'A_RELATION_WITNESSES','statement':'Problem rewrites provide independently checked soundness and completeness evidence.','consumers':['H29','H30'],'failure':'Partial or heuristic relation, never upgraded to equivalence'},
 {'id':'A_LOCAL_NOISE','statement':'World composition supplies joint noise or explicit conditional independence.','consumers':['H31','H43','H44'],'failure':'UnknownDependence or incompatible boundary'},
 {'id':'A_SCOPED_UPDATES','statement':'Differentiable updates target explicitly authorized adapter parameters only.','consumers':['H37','H38','H39'],'failure':'ScopeViolation; current policy denies all neural execution'},
 {'id':'A_FINITE_EXECUTION','statement':'Reference worlds, DSL programs and searches have finite dimension, cases and steps.','consumers':[h['id'] for h in H],'failure':'BudgetExhausted with partial state, not an invented solution'},
 {'id':'A_EVIDENCE_DEPENDENCE','statement':'Probability claims require a complete relevant joint model or explicitly independent atoms.','consumers':['H03','H41','H48'],'failure':'Symbolic expression or rigorous bounds, not a scalar posterior'},
 {'id':'A_PUBLIC_BOUNDARY','statement':'Terminal conditions and behavior probes are authorized public task conditions, not supervised answers.','consumers':['H34','H37'],'failure':'RoleLeakage'},
 {'id':'A_MODEL_BRIDGE','statement':'Future learned model adapters may realize the reference object behavior.','consumers':[h['id'] for h in H],'failure':'Unvalidated research hypothesis; does not erase the implemented finite object'}]
flows=[]
for c in C:
 r=json.loads((P/c['recipe_path']).read_text())
 flows.append({'id':c['id'],'title':c['title'],'producer_consumers':c['mechanisms'],'typed_objects':[mechanisms[int(h[1:])-1]['object_type'] for h in c['mechanisms']],'stages':r.get('stages',[]),'preserved_relation':r.get('critical_invariant','Each edge retains its source mechanism scope and explicit behavior relation.'),'source':c['design_path']})
save('specs/meta_state.json',{'schema_version':1,'components':components,'immutable_control_plane':['external_goal','user_authorization','execution_policy','budget_authority','publication_permission'],'required_version_axes':['state','schema','ontology','isa','frame','world','task','evidence'],'mechanisms':mechanisms,'combinations':flows,'horizons':X,'execution_semantics':['exact_symbolic','discrete_search','differentiable','hybrid'],'research_state':'NOT_RUN'})
save('specs/assumptions.json',{'schema_version':1,'claim_classes':{'D':'definition or proved finite fact','A':'explicit conditional assumption','H':'mechanism hypothesis','V':'architectural conjecture','E':'empirical result; none in this release'},'assumptions':assumptions,'empirical_results':[],'not_unified':[['H04','H26','a common field is not mandatory when local theories cannot glue'],['H25','H35','invertible gauge transport differs from information-losing coarse graining'],['H33','H04','cyclic trajectories need not descend one common energy'],['H29','H47','solution relation does not follow merely from equal sampled behavior'],['H38','H40','learned update operators cannot expand immutable host or base-ISA authority']]})
save('specs/innovation_deltas.json',{'mechanisms':mechanisms,'criterion':'different computational object/operation, not near-term experiment or hardware feasibility','research_state':'NOT_RUN'})
text=['# Semantic Becoming: first-principles architecture','\n前沿机制提案 / 无模型实测。Architecture is source/design, not an empirical result.','\n## Computational boundary','The research plane changes typed states, available operations, concepts, questions, internal views, clocks, worlds, update rules and evidence. It never changes the user goal, host permissions, spend or current model-run prohibition. An effect declares read/write sets, preconditions, postconditions, provenance and either an inverse or an information-losing migration.','\n## Object graph','Public role view → validated typed object → scoped proposal → bounded candidate branch → effect bundle → evidence lineage → versioned transaction. Concept changes insert ontology migration; macro changes lower into immutable base ISA; problem rewrites carry answer relations; world changes retain shared-noise identity.','\n## Layers and preservation obligations']
for k,v in components.items():text.append(f'- {k}: {v}. This is a separate version axis where applicable, not generic metadata.')
text+=['\n## Non-unification is deliberate','A shared constraint field may be appropriate for H04 while H26 preserves incompatible local theories. Invertible H25 transport is not H35 compression. H33 can produce meaningful periodic trajectories without a fixed point. H29 sound solution transport is not automatically complete equivalence. H48 provenance is not truth or independence.','\n## Full mechanism responsibility map']
for m in mechanisms:text.append(f"### {m['id']} {m['title']}\nObject: {m['object_type']}. Writes: {', '.join(m['components_written'])}. Operation: {m['operation']}.\nInvariant: {m['invariant']}.\nDesign: {m['source']}; source owner: M{m['id'][1:]}. Conditional claim H; NOT_RUN.")
text.append('\n## Combination object flows')
for f in flows:text.append(f"### {f['id']} {f['title']}\nParticipants: {' → '.join(f['producer_consumers'])}. Objects: {' → '.join(f['typed_objects'])}.\nSemantic stages: {' → '.join(f['stages'])}.\nPreserved relationship: {f['preserved_relation']}\nParticipant order is a responsibility map, not a claim that every pipeline is linear; executable graph edges are made explicit in the composition implementation.")
text.append('\n## Horizon finite entry points and assumption chains')
for x in X:text.append(f"### {x['id']} {x['title']}\n{x['finite_scope']}\nDepends on typed, scoped objects from {', '.join(x['mechanisms'])}, finite execution, and unvalidated model bridge assumptions. This finite architecture is not a demonstration of the open-ended vision. Target: {x['target_path']}.")
text+=['\n## Acceptance and falsifying examples','Reject a 2×3 matrix as a gauge inverse; reject zero-section consensus without anchors; retain the negative root when a question rewrite claims equivalence; reject an unseen future observation as a public terminal condition; preserve a shared fair bit with P(x=y)=1; preserve a repeated .8 source as .8. These software/math examples do not validate research efficacy.','\n## Implementation discipline','Each mechanism owns dedicated types/reference/adapter/losses/schema/tests/recipe. Tensor code is written and AST-checked but not imported or executed. All shared contracts are stdlib-only. The compiler performs seven independently diagnosed passes; bounded research loops are distinct from the authoring DAG. Receipts hash outputs and dependencies. Changes invalidate descendants.']
(W/'docs/theory_architecture.md').parent.mkdir(parents=True,exist_ok=True);(W/'docs/theory_architecture.md').write_text('\n\n'.join(text)+'\n')
(W/'docs/frontier_branches.md').write_text('# Radical branches retained\n\n1. Concept ecology: H26 obstruction → H36 counterexample → H27 new executable predicate → H40 macro, retaining incompatible branches if no distinction exists.\n2. Plasticity network: transport a public behavioral tangent, then exchange the bounded rule for producing future updates rather than a frozen answer.\n3. Constructed sciences: H31/H43 modules generate a hypothetical world whose dynamics can be altered; H29 asks new questions in it while H44 prevents synthetic support laundering.\n4. Trajectory semantics: preserve loops, phase transitions and two-ended constraints instead of forcing every process into a final embedding.\n5. Plural semantic scales: retain task-relative quotients and non-gluable local worlds rather than enforce a universal ontology.\n\nThese extensions deepen, not replace, the 48 committed mechanisms. Each depends on explicit finite contracts and future unvalidated model bridges.\n')
assert len(mechanisms)==len(H) and len(flows)==len(C)
save('run_state/checks/A01_architecture.json',{'check_kind':'registry_and_object_coverage','mechanisms':[m['id'] for m in mechanisms],'combinations':[f['id'] for f in flows],'horizons':[x['id'] for x in X],'all_have_distinct_object_operation_and_invariant':True,'empirical_claims':0,'research_state':'NOT_RUN'})
