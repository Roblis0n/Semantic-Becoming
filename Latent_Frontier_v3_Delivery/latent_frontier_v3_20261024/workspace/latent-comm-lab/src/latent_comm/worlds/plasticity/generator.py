"""W08: explicit finite linear behavior transport and arithmetic update rules."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode,FixtureBudget
from latent_comm.core.finite import matvec,least_squares,add,scale
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    rank_deficient: bool=True
    regularization: float=0.
    direction: tuple[float,float]=(1.,2.)
    inner_steps: int=3
    learning_rate: float=.1

def signature(p: Parameters) -> StructureSignature:
    return StructureSignature('plasticity','v1','linear_behavior:'+('rank_deficient' if p.rank_deficient else 'full_rank'),operation_family=('jvp','vjp','scoped_update'))

def sample_parameters(signature_value,rng) -> Parameters:
    return Parameters(signature_value.program_template.endswith('rank_deficient'),0.,(float(rng.randint(1,3)),float(rng.randint(1,3))),3,.1)

def build_fixture(p: Parameters=Parameters()):
    source=((1.,0.),(0.,1.));target=((1.,0.),(0.,0. if p.rank_deficient else 2.));v=matvec(source,p.direction);fit=least_squares(target,v,regularization=p.regularization)
    if not 0<p.learning_rate<=1:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'update step outside declared rule scope')
    meter=FixtureBudget(max_steps=p.inner_steps).meter();theta=(1.,2.);trajectory=[theta];memory=(0.,0.)
    for _ in range(p.inner_steps):
        meter.consume(steps=1);gradient=theta;memory=add(scale(memory,.5),scale(gradient,.5));clipped=tuple(max(-1.,min(1.,g)) for g in memory);theta=add(theta,scale(clipped,-p.learning_rate));trajectory.append(theta)
    fields={'task':'transport a public behavior direction and interpret a bounded arithmetic update rule','public_probes':((1.,0.),(0.,1.)),'source_jacobian':source,'source_direction':p.direction,'target_jacobian':target,'rule':('running_mean',.5,'clip',1.,'scale',-p.learning_rate),'query_condition':'separate finite quadratic readout'}
    targets={'behavior_direction':v,'transported_update':fit.solution,'unreachable_residual':fit.residual,'rank':fit.rank,'unique':fit.unique,'inner_trajectory':tuple(trajectory),'query_loss':sum(t*t for t in theta)}
    contract=ProjectionContract(('task','public_probes'),('source_jacobian','source_direction','rule'),('target_jacobian','query_condition'),(('task','public direction-transport problem'),('public_probes','shared observable coordinate basis without hidden answers')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',frame='f1',isa='i1',world='w1',task='t1',evidence='e1'),fixture_name=str(p.rank_deficient))
