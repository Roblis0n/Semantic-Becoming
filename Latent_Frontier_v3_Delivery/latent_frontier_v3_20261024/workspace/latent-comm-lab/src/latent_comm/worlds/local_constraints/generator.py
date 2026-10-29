"""W02: anchored affine cycle worlds with honest non-gluing residuals."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode
from latent_comm.core.finite import least_squares,matvec,sub,norm
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    biases: tuple[float,float,float]=(1.,1.,-2.)
    anchor: float=1.
    inconsistent: bool=False

def signature(p: Parameters) -> StructureSignature:
    return StructureSignature('local_constraints','v1','anchored_affine_triangle:'+('inconsistent' if p.inconsistent else 'consistent'),causal_template=(('a','b'),('b','c'),('c','a')))

def sample_parameters(signature_value,rng) -> Parameters:
    a=float(rng.randint(1,3));b=float(rng.randint(1,3));bad=signature_value.program_template.endswith('inconsistent')
    return Parameters((a,b,-a-b+(1. if bad else 0.)),float(rng.randint(1,3)),bad)

def build_fixture(p: Parameters=Parameters()):
    if len(p.biases)!=3:raise ContractError(ErrorCode.INVALID_SHAPE,'three cycle biases required')
    # Eliminate the hard anchored variable a, rather than approximate its constraint.
    a=p.anchor;b0,b1,b2=p.biases
    system=((1.,0.),(-1.,1.),(0.,-1.));rhs=(b0+a,b1,b2-a)
    fit=least_squares(system,rhs)
    fields={'task':'retain local constraints and report overlap obstruction','anchor':a,'edge_ab':(1.,-1.,b0),'edge_bc':(1.,-1.,b1),'edge_ca':(1.,-1.,b2)}
    targets={'global_section':(a,*fit.solution),'overlap_residual':fit.residual,'obstruction_norm':norm(fit.residual),'exactly_gluable':abs(sum(p.biases))<1e-10}
    contract=ProjectionContract(('task','anchor'),('edge_ab','edge_bc'),('edge_ca',),(('task','public consistency question'),('anchor','public observed hard anchor, not hidden optimum')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',frame='f1',world='w1',task='t1',evidence='e1'),fixture_name=str(p.biases))
