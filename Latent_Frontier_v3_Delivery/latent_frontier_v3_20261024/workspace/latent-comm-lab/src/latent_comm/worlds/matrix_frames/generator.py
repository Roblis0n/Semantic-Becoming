"""W01: invertible, singular and heterodimensional coordinate worlds."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode
from latent_comm.core.finite import matrix,vector,matvec,matmul,inverse,transpose
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    kind: str='invertible'
    shear: float=1.0
    state: tuple[float,...]=(1.0,2.0)

def signature(p: Parameters) -> StructureSignature:
    if p.kind not in {'invertible','singular','dimensional'}:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'unknown frame family')
    return StructureSignature('matrix_frames','v1','linear_operator_change_of_frame:'+p.kind,operation_family=('matvec','transport'))

def sample_parameters(signature_value: StructureSignature,rng) -> Parameters:
    return Parameters(signature_value.program_template.rsplit(':',1)[-1],float(rng.randint(-3,3)),(float(rng.randint(-3,3)),float(rng.randint(-3,3))))

def build_fixture(p: Parameters=Parameters()):
    sig=signature(p);z=vector(p.state)
    if len(z)!=2:raise ContractError(ErrorCode.INVALID_SHAPE,'this declared template is two dimensional')
    g=((1.,p.shear),(0.,1.)) if p.kind=='invertible' else ((1.,p.shear),(2.,2*p.shear)) if p.kind=='singular' else ((1.,p.shear),)
    t=((1.,1.),(0.,1.));r=((1.,2.),);fields={'task':'apply the same declared linear operation after coordinate transport','frame':g,'state':z,'operator':t,'readout':r}
    targets={'source_result':matvec(r,matvec(t,z)),'transported_state':matvec(g,z),'invertible':p.kind=='invertible'}
    if p.kind=='invertible':
        gi=inverse(g);targets.update({'transported_operator':matmul(matmul(g,t),gi),'transported_readout':matmul(r,gi)})
    else:targets['failure_kind']='NonInvertibleFrame'
    contract=ProjectionContract(('task',),('frame','operator'),('state','readout'),(('task','public operation goal without transformed answer'),))
    return WorldFactory(sig,contract).fixture(fields,targets,versions=VersionSet(state='s1',frame='f1',world='w1',task='t1',evidence='e1'),fixture_name=p.kind)
