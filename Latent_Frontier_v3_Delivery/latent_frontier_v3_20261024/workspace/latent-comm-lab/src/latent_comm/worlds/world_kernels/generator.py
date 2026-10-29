"""W11: executable shared-noise transition worlds and counterfactual edits."""
from dataclasses import dataclass
from latent_comm.core import VersionSet,ContractError,ErrorCode,FixtureBudget
from latent_comm.data import StructureSignature,ProjectionContract,WorldFactory

@dataclass(frozen=True)
class Parameters:
    shared_noise: bool=True
    invert_second: bool=False
    steps: int=3

def signature(p: Parameters) -> StructureSignature:
    return StructureSignature('world_kernels','v1','binary_kernel:'+('shared' if p.shared_noise else 'independent')+(':counterfactual' if p.invert_second else ':base'),causal_template=(('noise','x'),('noise','y')) if p.shared_noise else (('noise_x','x'),('noise_y','y')),operation_family=('transition','observe','counterfactual_edit'))

def sample_parameters(signature_value,rng) -> Parameters:
    return Parameters(':shared:' in signature_value.program_template,signature_value.program_template.endswith('counterfactual'),3)

def build_fixture(p: Parameters=Parameters()):
    meter=FixtureBudget(max_steps=p.steps).meter()
    noise=((0,0,.5),(1,1,.5)) if p.shared_noise else ((0,0,.25),(0,1,.25),(1,0,.25),(1,1,.25))
    outcomes=tuple((x,1-y if p.invert_second else y,prob) for x,y,prob in noise)
    rows=tuple((state,tuple(((x,y),prob) for x,y,prob in outcomes)) for state in ((0,0),(0,1),(1,0),(1,1)))
    if any(abs(sum(prob for _,prob in row)-1)>1e-12 for _,row in rows):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'transition row normalization')
    path=[(0,0)]
    for i in range(p.steps):meter.consume(steps=1);chosen=outcomes[i%len(outcomes)];path.append(chosen[:2])
    fields={'task':'compose finite dynamics while retaining noise identity','component_x':('copy_noise','shared' if p.shared_noise else 'noise_x'),'component_y':('invert_noise' if p.invert_second else 'copy_noise','shared' if p.shared_noise else 'noise_y'),'noise_contract':noise,'synthetic':True,'public_initial_state':(0,0)}
    targets={'joint_transition_rows':rows,'probability_equal':sum(prob for x,y,prob in outcomes if x==y),'illustrative_path':tuple(path),'path_kind':'declared deterministic noise schedule, not random empirical rollout','synthetic_evidence':True,'parent_worlds':('kernel:x','kernel:y'),'counterfactual_edit':p.invert_second}
    contract=ProjectionContract(('task','noise_contract','synthetic','public_initial_state'),('component_x',),('component_y',),(('task','public compositional dynamics objective'),('noise_contract','declared joint exogenous distribution'),('synthetic','mandatory hypothetical-world label'),('public_initial_state','authorized initial condition')))
    return WorldFactory(signature(p),contract).fixture(fields,targets,versions=VersionSet(state='s1',world='w1',task='t1',evidence='e1'),fixture_name=str(p))
