"""Predeclared stdlib proof witnesses; no neural module is imported or called.

Each invocation owns one aggregate budget. Unmetered elementary solvers receive
precharged bounds and a four-sweep Jacobi cap before execution. This instruments
helper cost without changing any repository source or claiming neural efficacy.
"""
from pathlib import Path
import sys, importlib, importlib.abc, json, math, hashlib
from dataclasses import asdict, replace
from fractions import Fraction as F
W=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(W/'src'))
FORBIDDEN={'torch','transformers','jax','tensorflow','numpy','scipy','requests','httpx','openai'}
class NoResearchImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in FORBIDDEN: raise RuntimeError('D02 blocked prohibited/nonstdlib import: '+fullname)
sys.meta_path.insert(0,NoResearchImports())
from latent_comm.core import StepBudget,ContractError
from latent_comm.core.budgets import aggregate_budget
from latent_comm.core import finite
ACTIVE=None
orig_eigh=finite.symmetric_eigh;orig_solve=finite.solve;orig_topo=finite.topological_order

def bounded_eigh(a,*,max_sweeps=128,tolerance=1e-12):
    ACTIVE.dimension(len(a));ACTIVE.consume(steps=4)
    return orig_eigh(a,max_sweeps=min(4,max_sweeps),tolerance=tolerance)
def bounded_solve(a,b,*,tolerance=1e-12):
    ACTIVE.dimension(len(a));ACTIVE.consume(steps=len(a))
    return orig_solve(a,b,tolerance=tolerance)
def bounded_topo(nodes,edges):
    ACTIVE.dimension(len(nodes));ACTIVE.consume(steps=len(nodes))
    return orig_topo(nodes,edges)
finite.symmetric_eigh=bounded_eigh;finite.solve=bounded_solve;finite.topological_order=bounded_topo

def module(slug):return importlib.import_module('latent_comm.mechanisms.'+slug+'.reference')
def close(a,b):assert abs(a-b)<=1e-9,(a,b)
def rejected(fn):
    try:fn()
    except ContractError as e:return str(e)
    raise AssertionError('expected typed rejection')
R=[]
def run(name,formal,dimension,fn,steps=128,cases=64):
    global ACTIVE
    limit=StepBudget(max_steps=steps,max_cases=cases,max_dimension=dimension,max_branches=16)
    try:
        with aggregate_budget(limit) as meter:
            ACTIVE=meter;meter.dimension(dimension);meter.consume(cases=1)
            values=fn(meter)
        result={'id':name,'formal_note':formal,'status':'PASS','declared_limits':asdict(limit),'consumed_steps_including_precharged_solver_bounds':meter.steps,'consumed_cases':meter.cases,'consumed_branches':meter.branches,'witness':values}
    except Exception as error:
        result={'id':name,'formal_note':formal,'status':'FAIL','error':type(error).__name__+': '+str(error),'declared_limits':asdict(limit)}
    finally:ACTIVE=None
    R.append(result)

def gauge(m):
    h=module('h25_gauge');g=((0.,1.),(1.,0.));frame=h.FrameSpec('old',2,'GL','1');target=h.FrameSpec('new',2,'GL','2')
    p=h.GaugePacket(frame,(1.,2.),((2.,0.),(0.,3.)),((1.,0.),));r=h.transport(p,g,target)
    assert r.effect_before==r.effect_after==(2.,)
    cross=h.transport_cross_map(((1.,2.),),g,((2.,),),frame,h.FrameSpec('out',1,'GL','1'));assert cross==((4.,2.),)
    m.consume(steps=4);bad_fixed_readout=(g[0][0]*1+g[0][1]*2);assert bad_fixed_readout==2
    return {'before':r.effect_before,'after':r.effect_after,'cross_map_shape':[1,2],'cross_map':cross,'fixed_readout_counterexample':[1,bad_fixed_readout]}
run('D02-F01-gauge','F01',2,gauge)

def objectives(m):
    h=module('h32_perspective');f=h.ObjectiveFrame(h.freeze_goal('same goal'),(2.,3.),(.5,.5),((1.,0.),),(4.,),'1')
    r=h.change_view(f,((60.,0.),(0.,1.)),'2');close(r.original_value,r.transformed_value)
    error=rejected(lambda:h.change_view(f,((1.,0.),),'3'))
    return {'original':r.original_value,'transformed':r.transformed_value,'weights':r.dual_weights,'lost_direction_rejected':error}
run('D02-F01-objectives','F01',2,objectives)

def gluing(m):
    h=module('h26_sheaf');restr=tuple(h.AffineRestriction(k,a,b,((1.,),),((1.,),),(v,),('e:'+k,)) for k,a,b,v in [('xy','x','y',0.),('yz','y','z',0.),('zx','z','x',1.)]);p=h.SheafPacket(tuple(h.LocalDomain(k,1) for k in ('x','y','z')),restr,(h.Anchor('x',0,0.),),'1')
    r=h.glue(p);assert r.status=='NoGlobalSection';v=[x for _,row in r.residuals for x in row];close(sum(x*x for x in v),1/3)
    m.consume(steps=6);exact=(F(-1,3),)*3;assert sum(exact)==-1 and sum(x*x for x in exact)==F(1,3)
    return {'residuals':r.residuals,'least_square_loss':sum(x*x for x in v),'exact_fraction_lower_bound':'1/3','conflict':r.conflict_witness}
run('D02-F02-gluing','F02',3,gluing)

def concept(m):
    h=module('h27_ontology');old=h.ConceptDefinition('shape',h.Predicate('eq','shape','key'),(),('public:shape',),('shape',));snap=h.OntologySnapshot('1',(old,));records=({'shape':'key','expires':1},{'shape':'key','expires':3});atom=h.Predicate('le','expires',2)
    r=h.search_concept(snap,records,((0,1),),(atom,),concept_id='expiry',evidence=('public:expiry',),candidate_limit=4,depth=2)
    assert r.values==(True,False);assert h.evaluate(atom,{'shape':'key'}) is None
    return {'old_signature':[True,True],'new_signature':r.values,'missing_field':None,'examined':r.candidates_examined}
run('D02-F03-concept','F03',2,concept)

def disagreement(m):
    h=module('h36_disagreement');p=h.RuleProgram('implies',children=(h.RuleProgram('divisible',2),h.RuleProgram('divisible',4)));c=h.ScopedClaim('claim',p,(2,4),'1');r=h.find_counterexamples(c);assert r[0][0].value==2
    return {'counterexample':r[0][0].value,'scope':[2,4],'not_global':True}
run('D02-F03-disagreement','F03',2,disagreement)

def question(m):
    h=module('h29_questions');q=h.QuestionIR('square',('x',),((-2.,-1.,0.,1.,2.),),(h.PolynomialConstraint(((1.,(2,)),),'eq',4.),),'1');t=h.strengthen(q,h.PolynomialConstraint(((1.,(1,)),),'ge',0.),'positive');r=h.check_relation(t);assert r.sound and not r.complete and r.lost_solutions==((-2.,),)
    return {'relation':r.relation,'lost':r.lost_solutions,'original':r.source_solutions,'target':r.target_solutions}
run('D02-F04-question','F04',5,question)

def analogy(m):
    h=module('h30_analogy')
    def graph(prefix,step):return h.TypedOperationGraph(tuple(h.TypedObject(prefix+str(i),'n') for i in range(3)),(h.FiniteOperation('next','n','n',tuple((prefix+str(i),prefix+str(i+step)) for i in range(3-step))),),'1')
    a,b=graph('x',1),graph('y',1);mapping=h.AnalogyMorphism(tuple((f'x{i}',f'y{i}') for i in range(3)),(('next','next'),),(('n','n'),),('x0','x1','x2'));good=h.check_morphism(a,b,mapping);trace=h.compile_program(a,b,good,('next','next'),'x0');bad=h.check_morphism(a,graph('y',2),mapping);assert bad.broken_squares
    return {'good_trace':trace[1],'bad_squares':bad.broken_squares}
run('D02-F04-analogy','F04',3,analogy)

def transport(m):
    h=module('h37_gradient_transport');a=h.BehaviorAnchorSet(('public:response',),'1');src=h.Linearization(((2.,),),a,('adapter.a',),'1');dst=h.Linearization(((4.,),),a,('adapter.b',),'1');exact=h.transport_direction(src,dst,(.5,),ridge=0.);reg=h.transport_direction(src,dst,(.5,),ridge=1.)
    close(exact.delta[0],.25);close(reg.delta[0],4/17);close(reg.projection_residual[0],-1/17);close(reg.unreachable_residual[0],0)
    return {'unregularized':exact.delta,'ridge1':reg.delta,'total_residual':reg.projection_residual,'unreachable':reg.unreachable_residual}
run('D02-F05-ridge','F05',2,transport)

def plasticity(m):
    h=module('h38_plasticity');p=h.PlasticityProgram(h.RuleNode('scale',(h.RuleNode('clip',(h.RuleNode('read',slot='gradient'),),1.),),-.1),('adapter.weight',),1.,2,4,'1','exact_unroll');r=h.apply_rule(p,(('adapter.weight',(2.,)),),(('adapter.weight',(4.,)),));close(dict(r.parameters)['adapter.weight'][0],1.9)
    m.consume(steps=12);psi=F(1,10);theta=2*(1-psi)**2;exact=-8*(1-psi)**3;first=theta*(-4+2*psi);assert exact==F(-729,125) and first==F(-1539,250) and exact!=first
    return {'clipped_update':1.9,'exact_meta_gradient':float(exact),'first_order_proxy':float(first),'analytic_not_neural':True}
run('D02-F05-plasticity','F05',1,plasticity)

def dynamics(m):
    h=module('h33_reciprocal');p=h.DynamicsPacket(((0.,0.),(0.,0.)),((0.,-1.),(1.,0.)),(1.,0.),'1',.5,4,(0,5));r=h.integrate(p);assert all(abs(x-1)<1e-9 for x in r.squared_norms);growth=h.euler_artifact(p.skew_coupling,(1.,0.),1.);assert growth==1
    m.consume(steps=8);grad=(1.,4.);kz=(-6.,6.);edot=-sum(x*x for x in grad)+sum(x*y for x,y in zip(grad,kz));assert edot==1
    return {'midpoint_squared_norms':r.squared_norms,'euler_norm_squared_growth':growth,'general_quadratic_energy_derivative_counterexample':edot}
run('D02-F06-dynamics','F06',2,dynamics)

def bifurcation(m):
    h=module('h28_bifurcation');m.consume(steps=12);negative=h.stationary_points(-1);positive=h.stationary_points(1);zero=h.stationary_points(0);assert negative[0].continuous=='stable';assert zero[0].continuous=='nonhyperbolic_higher_order_attracting'
    z0=2.;t=3.;z=z0/math.sqrt(1+2*z0*z0*t);close(z,.4)
    return {'negative':[asdict(x) for x in negative],'positive':[asdict(x) for x in positive],'critical':[asdict(x) for x in zero],'alpha0_exact_state_at_t3':z}
run('D02-F06-bifurcation','F06',1,bifurcation)

def alternative_bifurcations(m):
    m.consume(steps=20)
    mu=1.;omega=2.;x=1.;y=0.;r=math.hypot(x,y)
    dx=(mu-r*r)*x-omega*y;dy=omega*x+(mu-r*r)*y
    close((x*dx+y*dy)/r,0.);close((x*dy-y*dx)/(r*r),omega)
    close(mu-3*r*r,-2.)
    fold_x=1/math.sqrt(3);fold_mu=fold_x**3-fold_x
    close(fold_mu+fold_x-fold_x**3,0.);close(1-3*fold_x**2,0.)
    assert [(1-3*x*x)<0 for x in (-1,0,1)]==[True,False,True]
    return {'hopf_nonzero_orbit_radial_derivative':-2.,'angular_rate':omega,'fold':{'x':fold_x,'mu':fold_mu},'mu0_cubic_roots':[-1,0,1],'stable_outer_roots':[-1,1],'scope':'Scalar algebra of proposed normal forms; no new branch algorithm or neural execution.'}
run('D02-F06-distinct-bifurcations','F06',2,alternative_bifurcations)

def boundary(m):
    h=module('h34_boundary_value');edges=tuple((str(i),str(j)) for i in range(4) for j in (i,i+1) if j<4);g=h.TrajectoryFactorGraph(('0','1','2','3'),(edges,)*3,('0',),h.PublicTerminalConstraint(('3',),'public_goal','1'),'1');r=h.solve_boundary(g);assert r.paths==(('0','1','2','3'),)
    bad=h.solve_boundary(replace(g,transitions=(edges,)));assert bad.status=='BoundaryInfeasible'
    return {'path':r.paths,'one_step_status':bad.status}
run('D02-F06-boundary','F06',4,boundary)

def scales(m):
    h=module('h35_renormalization');m.consume(steps=10);p=h.ScalePacket(((1.,1.),),((.5,),(.5,)),((1.,0.),(0.,1.)),(1.,1.),((1.,),),(2.,),('a','b'),('sum',),'1','2');assert h.closure_report(p).closed;assert h.step_scale(p,h.coarsen(p,(1.,2.),False)).coarse==(5.,)
    bad=replace(p,micro_dynamics=((1.,1.),(0.,1.)),micro_bias=(0.,0.),macro_bias=(0.,));w=h.closure_counterexamples(bad,((1.,0.),(0.,1.)));assert w
    error=rejected(lambda:h.refine(p,h.coarsen(p,(1.,3.),False)))
    return {'closed_next_sum':5,'nonclosure':w,'lost_detail_rejected':error}
run('D02-F07-scales','F07',2,scales)

def quotients(m):
    h=module('h47_quotient');d=h.StateDomain(('one','two','three','four'),(1,2,3,4),'d1');old=h.form_quotient(d,(h.FiniteQuery('p','parity',0,'1'),),'1');new=h.refine_quotient(old,(h.FiniteQuery('gt','greater_than',2,'1'),),'2');near=h.approximate_clusters(((0.,),(.75,),(1.5,)),1.);assert len(old.classes)==2 and len(new.quotient.classes)==4 and not near.threshold_relation_transitive
    return {'old_classes':[c.members for c in old.classes],'new_classes':[c.members for c in new.quotient.classes],'nontransitive_witness':near.nontransitive_witness}
run('D02-F07-quotients','F07',4,quotients)

def causal(m):
    h=module('h31_grafting');w=h.TargetSCM((h.CausalModule('x','u',(),(),(),3.,()),h.CausalModule('y','u',('x',),('u',),(1.,),0.,()),h.CausalModule('z','u',('y',),('u',),(1.,),1.,())),('u',),'1');s=h.CausalModule('sy','u',('sx',),('u',),(2.,),0.,());c=h.graft(s,w,'y',(h.BoundaryBinding('sx','x','u','u'),),'2');r=dict(h.evaluate_scm(c.after,{'u':0.}));assert r=={'x':3.,'y':6.,'z':7.}
    return {'grafted_values':r,'affected':c.affected_descendants}
run('D02-F08-causal','F08',3,causal)

def world(m):
    h=module('h43_world_kernels')
    def sensor(name):
        rows=tuple(h.ConditionalRow(s,'observe',(u,),(1.,0.) if u=='dry' else (0.,1.)) for s in ('0','1') for u in ('dry','wet'))
        return h.WorldKernel(name,name,('0','1'),(('observe','read-weather'),),('weather',),rows,('0','1'),((1.,0.),(0.,1.)),'1','public:world')
    kernels=(sensor('left'),sensor('right'));noise=h.SharedNoiseJoint(('weather',),((('dry',),.5),(('wet',),.5)));k=h.compose_kernels(kernels,noise);row=dict(k.transitions)['observe'][0];assert row==(.5,0.,0.,.5)
    m.consume(steps=4);independent_equal=F(1,4)+F(1,4);assert independent_equal==F(1,2)
    dream=module('h44_dreaming');dw=dream.construct_dream(kernels,noise,());obs=dream.observe_dream(dw,(1.,0.,0.,0.),('observe',));error=rejected(lambda:dream.assert_evidence_use(obs,'real','real_world_fact'))
    return {'shared_joint':row,'shared_equal_probability':1,'independent_equal_probability':float(independent_equal),'synthetic_real_claim_rejected':error}
run('D02-F08-world','F08',4,world)

def evidence(m):
    h=module('h48_evidence_genealogy');atoms=(h.EvidenceAtom('e','original:e','observed',.8),h.EvidenceAtom('f','original:f','observed',.8));nodes=(h.SupportNode('A','atom',(),'e'),h.SupportNode('B','atom',(),'f'),h.SupportNode('root','or',('A','B')));g=h.ProvenanceGraph(atoms,nodes,'root','1');ind=h.calibrate_support(g,h.DependenceModel('declared_independent',('e','f'),declaration_id='explicit'));unknown=h.calibrate_support(g,h.DependenceModel('unknown',('e','f')))
    dup=h.ProvenanceGraph((atoms[0],),(nodes[0],h.SupportNode('B','atom',(),'e'),nodes[2]),'root','1');same=h.calibrate_support(dup,h.DependenceModel('unknown',('e',)));close(ind.probability,.96);close(same.probability,.8);assert (unknown.lower_bound,unknown.upper_bound)==(.8,1.);assert h.retract_sources(g,('e',)).root_invalidated
    return {'duplicate':same.probability,'independent':ind.probability,'unknown_bounds':[unknown.lower_bound,unknown.upper_bound],'retraction_means':'dependency invalidation, not proof of falsehood'}
run('D02-F08-evidence','F08',2,evidence)

def macros(m):
    h=module('h40_instruction_set');body=h.Expr('multiply',(h.Expr('add',(h.Expr('var',name='x'),h.Expr('const',value=1))),h.Expr('const',value=2)));isa=h.ISARevision('1',(h.MacroDefinition('mu',('x',),body,('scalar',)),));x=h.execute_base(h.lower(h.Expr('call',(h.Expr('const',value=0),),name='mu'),isa),{});assert x==2
    capture=h.Expr('let',(h.Expr('const',value=1),h.Expr('add',(h.Expr('var',name='x'),h.Expr('var',name='y')))),name='y');rev=h.ISARevision('2',(h.MacroDefinition('m',('x',),capture,('scalar',)),));y=h.execute_base(h.lower(h.Expr('call',(h.Expr('var',name='y'),),name='m'),rev),{'y':2});assert y==3
    return {'ordered_macro_at0':x,'wrong_order_at0':1,'capture_avoidance':y}
run('D02-F09-macros','F09',4,macros)

def coalition(m):
    h=module('h41_coalitions');g=h.CoalitionGame(('A','B'),(((),0.),(('A',),0.),(('B',),0.),(('A','B'),1.)),'1');r=h.exact_shapley(g);assert dict(r.contributions)=={'A':.5,'B':.5};close(r.efficiency_residual,0)
    return {'contributions':r.contributions,'efficiency_residual':r.efficiency_residual}
run('D02-F09-coalition','F09',2,coalition)

def ecology(m):
    h=module('h42_ecology');m.consume(steps=4);t=h.TaskGenome('t','add',1.,True,0.,False,(),'1');inv=h.mutate_task(t,'inverse','inv');p=h.ProtocolGenome('p',('add','compare','inverse'),(),(),'1');y=.5;x=h.execute_program(inv,p,y);roundtrip=h.execute_program(t,p,x);assert x==-.5 and roundtrip!=y
    return {'input_y':y,'sign_reversal_result':x,'forward_again':roundtrip,'not_general_inverse':True}
run('D02-F09-ecology','F09',1,ecology)

def identify(m):
    h=module('h45_identifiability');s=h.IdentificationState(('plus','minus'),(h.QuerySpec('x0',('0',),((1.,),(1.,)),0.,True,True),h.QuerySpec('x1',('1','-1'),((1.,0.),(0.,1.)),0.,True,True)),(.5,.5),'1');r=h.select_query(s);assert r.query_id=='x1';close(r.information_gain,math.log(2));z=h.select_query(replace(s,queries=(s.queries[0],)));assert z.status=='NonIdentifiable'
    m.consume(steps=4);noisy=h.QuerySpec('noisy',('0','1'),((.4,.6),(.6,.4)),0.,True,True);gain=h.information_gain((.5,.5),noisy);assert gain>0 and all(x>0 for row in noisy.likelihood for x in row)
    return {'selected':r.query_id,'information_gain_nats':r.information_gain,'x0_only':z.status,'noisy_information_positive_but_support_overlaps':gain}
run('D02-F10-identify','F10',2,identify)

def exclusions(m):
    h=module('h46_negative_knowledge');d=(1,2,3,4);c=h.ExclusionCapsule('even',h.DomainPredicate('not_divisible',2),('even_required',),h.NegativeWitness('program_exhaustive',h.DomainPredicate('divisible',2),d,None,'complete'),1.,'hard',(),(),'1');r=h.apply_exclusions(d,(c,),('even_required',),'1');assert r.feasible==(2,4);back=h.retract_exclusions(r,(c,),('even_required',),('even_required',));assert back.region.feasible==d
    bad=replace(c,capsule_id='bad',excluded=h.DomainPredicate('ge',3));error=rejected(lambda:h.apply_exclusions(d,(bad,),('even_required',),'1'))
    return {'remaining':r.feasible,'restored':back.restored_candidates,'overgeneralization_rejected':error,'required_condition':'even_required is a valid task necessary condition in this fixture'}
run('D02-F10-exclusions','F10',4,exclusions)

def budget_guard(m):
    child=StepBudget(max_steps=128).meter();child.consume(steps=3)
    error=rejected(lambda:StepBudget(max_steps=128).meter().consume(steps=2))
    assert m.steps==3
    return {'expected_nested_rejection':error,'aggregate_steps_after_rejected_work':m.steps}
run('D02-budget-nested','policy',1,budget_guard,steps=4,cases=2)
assert not any(n.split('.')[0] in FORBIDDEN for n in sys.modules)
log={'task_id':'D02','research_state':'NOT_RUN','neural_imports':[],'research_execution_count':0,'fixture_policy':{'max_dimension':64,'max_steps':128,'max_cases':64,'max_declared_fixture_dimension':max(r['declared_limits']['max_dimension'] for r in R),'case_semantics':'Each listed fixture is an independently predeclared mathematical witness, not a training/evaluation sample. Every nested meter shares its enclosing aggregate.','unmetered_helpers':'Before source calls, Gaussian elimination reserves n pivots; Jacobi reserves four sweeps and receives max_sweeps<=4; topology reserves node count. Primitive scalar arithmetic is not a neural forward.'},'checks':R,'passed':sum(r['status']=='PASS' for r in R),'failed':sum(r['status']=='FAIL' for r in R),'source_runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(W/'run_state/checks/D02_math_fixtures.json').write_text(json.dumps(log,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps(log,ensure_ascii=False,indent=2))
raise SystemExit(bool(log['failed']))
