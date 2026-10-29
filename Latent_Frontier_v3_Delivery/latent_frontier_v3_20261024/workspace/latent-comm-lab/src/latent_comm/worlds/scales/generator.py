"""W07: coarse closure witnesses and task-relative partition refinement."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode
from latent_comm.core.finite import matvec,sub,norm
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    closed: bool=True
    microstate: tuple[float,...]=(2.,0.,0.,0.)
    refined_query: bool=True

def signature(p: Parameters) -> StructureSignature:
    return StructureSignature('scales','v1','two_block_average:'+('closed' if p.closed else 'nonclosed'),operation_family=('coarsen','refine'))

def sample_parameters(signature_value,rng) -> Parameters:
    return Parameters(not signature_value.program_template.endswith('nonclosed'),(float(rng.randint(1,3)),0.,0.,0.),bool(rng.randint(0,1)))

def build_fixture(p: Parameters=Parameters()):
    if len(p.microstate)!=4:raise ContractError(ErrorCode.INVALID_SHAPE,'four-state micro template required')
    c=((.5,.5,0.,0.),(0.,0.,.5,.5));lift=((1.,0.),(1.,0.),(0.,1.),(0.,1.))
    f=((0.,1.,0.,0.),(1.,0.,0.,0.),(0.,0.,0.,1.),(0.,0.,1.,0.)) if p.closed else ((1.,0.,0.,0.),(0.,0.,1.,0.),(0.,1.,0.,0.),(0.,0.,0.,1.))
    coarse=matvec(c,p.microstate);next_coarse=matvec(c,matvec(f,p.microstate));residual=sub(next_coarse,coarse)
    a=(2.,0.,0.,0.);b=(0.,2.,0.,0.);closure_witness=(matvec(c,a),matvec(c,b),matvec(c,matvec(f,a)),matvec(c,matvec(f,b)))
    domain=(1,2,3,4);signatures=tuple((x%2,x>2) if p.refined_query else (x%2,) for x in domain);groups={}
    for x,s in zip(domain,signatures,strict=True):groups.setdefault(s,[]).append(x)
    fields={'task':'coarsen dynamics and refine only distinctions required by tasks','coarse_map':c,'micro_dynamics':f,'microstate':p.microstate,'query_family':('parity','greater_than_two') if p.refined_query else ('parity',)}
    targets={'coarse_state':coarse,'closure_residual':residual,'closure_counterexample':closure_witness,'lifting_residual':sub(matvec(lift,coarse),p.microstate),'task_partition':tuple(tuple(g) for g in groups.values())}
    contract=ProjectionContract(('task','query_family'),('coarse_map','micro_dynamics'),('microstate',),(('task','public coarse-graining objective'),('query_family','public task-relative observable definitions')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',frame='f1',world='w1',task='t1',evidence='e1'),fixture_name=str(p.closed))
