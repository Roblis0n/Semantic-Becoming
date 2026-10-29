"""W05: finite SCM grafts, shared noise and operation-preserving analogy."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    source_multiplier: float=2.
    target_multiplier: float=3.
    boundary_scale: float=2.
    shared_noise: bool=True

def signature(p: Parameters) -> StructureSignature:
    return StructureSignature('causal_analogy','v1','linear_scm_graft:'+('shared' if p.shared_noise else 'independent'),causal_template=(('x','y'),),operation_family=('intervene','graft','commute'))

def sample_parameters(signature_value,rng) -> Parameters:
    return Parameters(float(rng.randint(1,3)),float(rng.randint(1,3)),float(rng.randint(1,3)),signature_value.program_template.endswith('shared'))

def build_fixture(p: Parameters=Parameters()):
    if p.boundary_scale==0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'boundary map must be invertible in this template')
    noise=((0.,0.,.5),(1.,1.,.5)) if p.shared_noise else ((0.,0.,.25),(0.,1.,.25),(1.,0.,.25),(1.,1.,.25))
    outputs=tuple((p.source_multiplier*(p.boundary_scale*1.)+u,p.target_multiplier*1.+v,prob) for u,v,prob in noise)
    # f(x)=scale*x commutes with source multiply iff target uses the same multiplier.
    defect=abs(p.boundary_scale*p.source_multiplier-p.target_multiplier*p.boundary_scale)
    fields={'task':'graft one declared structural mechanism and inspect boundary assumptions','source_module':('mul_add_noise',p.source_multiplier),'target_module':('mul_add_noise',p.target_multiplier),'boundary_scale':p.boundary_scale,'noise_contract':'shared_bit' if p.shared_noise else 'independent_bits'}
    targets={'joint_outputs_after_graft':outputs,'analogy_commutation_error':defect,'unaffected_equations_preserved':True,'noise_identity_preserved':p.shared_noise}
    contract=ProjectionContract(('task','noise_contract'),('source_module',),('target_module','boundary_scale'),(('task','public graft and analogy objective'),('noise_contract','declared structural noise assumption')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',frame='f1',world='w1',task='t1',evidence='e1'),fixture_name=str(p))
