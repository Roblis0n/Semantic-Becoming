"""W06: exact planar rotation, dissipation and public two-boundary paths."""
from dataclasses import dataclass
import math
from latent_comm.core import VersionSet,ContractError,ErrorCode,FixtureBudget
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    mode: str='rotation'
    start: tuple[float,float]=(1.,0.)
    terminal: tuple[float,float]=(0.,1.)
    steps: int=4
    dt: float=.25
    damping: float=0.

def signature(p: Parameters) -> StructureSignature:
    if p.mode not in {'rotation','dissipation','boundary'}:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'unknown dynamical template')
    return StructureSignature('dynamics','v1',p.mode,operation_family=('integrate','read_trajectory'))

def sample_parameters(signature_value,rng) -> Parameters:
    mode=signature_value.program_template;return Parameters(mode,(float(rng.randint(1,3)),0.),(0.,1.),4,.25,.5 if mode=='dissipation' else 0.)

def build_fixture(p: Parameters=Parameters()):
    meter=FixtureBudget(max_steps=p.steps).meter()
    if p.dt<=0 or p.damping<0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'positive timestep and nonnegative damping required')
    path=[p.start]
    for t in range(p.steps):
        meter.consume(steps=1)
        if p.mode=='boundary':
            u=(t+1)/p.steps;z=tuple((1-u)*a+u*b for a,b in zip(p.start,p.terminal,strict=True))
        else:
            x,y=path[-1];c=math.cos(p.dt);s=math.sin(p.dt);decay=math.exp(-p.damping*p.dt);z=(decay*(c*x-s*y),decay*(s*x+c*y))
        path.append(z)
    fields={'task':'retain the entire declared trajectory, not only an endpoint','mode':p.mode,'start':p.start,'terminal':p.terminal,'terminal_source':'public_goal','steps':p.steps,'dt':p.dt,'damping':p.damping}
    targets={'trajectory':tuple(path),'norms':tuple(math.hypot(*z) for z in path),'terminal_residual':tuple(a-b for a,b in zip(path[-1],p.terminal,strict=True)),'analytic_transition':p.mode!='boundary'}
    contract=ProjectionContract(('task','terminal','terminal_source','steps','dt'),('mode','damping'),('start',),(('task','public trajectory objective'),('terminal','explicit task goal, not future observed state'),('terminal_source','public provenance of endpoint constraint'),('steps','finite task horizon'),('dt','public simulation timestep')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',world='w1',task='t1',evidence='e1'),fixture_name=p.mode)
