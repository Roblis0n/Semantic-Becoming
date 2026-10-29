"""L10: executable shared-noise kernels, niche ecology and synthetic curriculum."""
from dataclasses import dataclass
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import LossSpec,GradientEstimator,LossValue,masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action

def loss_spec(name,formula,owners,units,*,estimator=GradientEstimator.EXACT,stops=()):
    return LossSpec(name,formula,'sum of valid per-'+units+' errors','valid '+units,'explicit per-objective valid mask','skip_with_reason',tuple(owners),('conditional_kernels','joint_distribution') if name in {'transition','shared_noise','multistep'} else ('observation_logits',),tuple(stops),estimator,units)

def binary_component(raw,noise_value):
    if len(raw)!=2 or raw[0] not in {'copy_noise','invert_noise'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'W11 component must expose its operation and noise identity')
    return int(noise_value) if raw[0]=='copy_noise' else 1-int(noise_value)

def lineage_contract(public):
    from latent_comm.mechanisms.h44_dreaming.reference import independent_holdout
    if public['synthetic'] is not True:raise ContractError(ErrorCode.ROLE_LEAKAGE,'dream training requires synthetic lineage')
    return independent_holdout(tuple(public['parent_sources']),tuple(public['holdout_sources']),independence_assumed=public.get('holdout_independence_assumed',False))

@dataclass(frozen=True)
class KernelOutput:
    transition: object
    observations: object
    joint: object
    behavior: object
    initial: object

class KernelStage:
    def __init__(self,left_delta,right_delta,noise_delta,observation_logits,versions,*,rollout_steps=3,device='cpu'):
        require_research_action('model_initialize')
        self.left_delta=left_delta;self.right_delta=right_delta;self.noise_delta=noise_delta;self.observation_logits=observation_logits;self.versions=versions;self.rollout_steps=rollout_steps;self.device=device
        self.loss_specs=(loss_spec('transition','mean_rows sum_next -target_prob*log(predicted_prob)',('kernel_generator','noise_coupling'),'transition rows'),loss_spec('observation','mean_states -log P(public_identity_observation|state)',('observation_generator',),'public state observations'),loss_spec('shared_noise','mean((joint-target_joint)^2)',('kernel_generator','noise_coupling'),'joint cells'),loss_spec('multistep','mean((rollout_behavior-target_distribution_rollout)^2)',('kernel_generator','noise_coupling','observation_generator'),'horizon cells'))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'kernel_generator':{'left_conditional':self.left_delta,'right_conditional':self.right_delta},'noise_coupling':{'support_log_weights':self.noise_delta},'observation_generator':{'state_observation_logits':self.observation_logits}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h43_world_kernels.adapter import tensor_shared_noise_compose,tensor_rollout
        if not 1<=self.rollout_steps<=maximum_unroll:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'kernel rollout horizon exceeds plan')
        joint_rows=[];initial_rows=[]
        for s,r in zip(sender.views,receiver.views):
            if s.public_task['synthetic'] is not True or r.public_task['synthetic'] is not True:raise ContractError(ErrorCode.ROLE_LEAKAGE,'constructed W11 worlds retain synthetic label')
            support=s.public_task['noise_contract']
            if support!=r.public_task['noise_contract']:raise ContractError(ErrorCode.CONFLICT,'joint exogenous support differs across roles')
            if len(support) not in {2,4}:raise ContractError(ErrorCode.INVALID_SHAPE,'binary joint support must have two or four atoms')
            if s.features['component_x'][1]==r.features['component_y'][1] and any(u!=v for u,v,_ in support):raise ContractError(ErrorCode.CONFLICT,'one noise identity cannot carry different values in a joint atom')
            left=[];right=[];probabilities=[]
            for u,v,p in support:
                if u not in (0,1) or v not in (0,1) or p<=0:raise ContractError(ErrorCode.INVALID_SCHEMA,'explicit positive binary noise atoms required')
                x=binary_component(s.features['component_x'],u);y=binary_component(r.features['component_y'],v)
                left.append([4. if j==x else -4. for j in range(2)]);right.append([4. if j==y else -4. for j in range(2)]);probabilities.append(p)
            if abs(sum(probabilities)-1)>1e-8:raise ContractError(ErrorCode.INVALID_SCHEMA,'public noise probabilities not normalized')
            l=torch.as_tensor(left,device=self.device,dtype=self.left_delta.dtype)+self.left_delta[:len(support)];rr=torch.as_tensor(right,device=self.device,dtype=self.right_delta.dtype)+self.right_delta[:len(support)]
            probabilities=torch.as_tensor(probabilities,device=self.device,dtype=l.dtype);weights=(probabilities.log()+self.noise_delta[:len(support)]).softmax(-1)
            # Residual component draws are independent CONDITIONAL ON the same
            # explicitly indexed joint atom. The exogenous atom is never redrawn.
            joint=tensor_shared_noise_compose(l.unsqueeze(0),rr.unsqueeze(0),weights,conditional_independence=True).squeeze(0);joint_rows.append(joint)
            initial=r.public_task['public_initial_state']
            if len(initial)!=2 or any(v not in (0,1) for v in initial):raise ContractError(ErrorCode.INVALID_SCHEMA,'binary initial state required')
            index=2*int(initial[0])+int(initial[1]);initial_rows.append(torch.nn.functional.one_hot(torch.tensor(index,device=self.device),4).to(l.dtype))
        joint=torch.stack(joint_rows);initial=torch.stack(initial_rows);transition=joint[:,None,:].expand(-1,4,-1)
        observation=self.observation_logits.unsqueeze(0).expand(joint.shape[0],-1,-1)
        _,outputs=tensor_rollout(initial,transition.clamp_min(1e-12).log().unsqueeze(1),tuple(0 for _ in range(self.rollout_steps)),observation)
        return KernelOutput(transition,observation.softmax(-1),joint,torch.stack(outputs,1),initial)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        targets=[];valid_rows=[]
        for view in supervision.views:
            rows=view.targets['joint_transition_rows'];table=[]
            if len(rows)!=4:raise ContractError(ErrorCode.INVALID_SHAPE,'four W11 transition states required')
            for expected,(state,outcomes) in enumerate(rows):
                if tuple(state)!=(expected//2,expected%2):raise ContractError(ErrorCode.INVALID_SCHEMA,'transition state order differs')
                row=[0.]*4
                for (x,y),prob in outcomes:row[2*int(x)+int(y)]+=float(prob)
                if min(row)<0 or abs(sum(row)-1)>1e-8:raise ContractError(ErrorCode.INVALID_SCHEMA,'supervised transition not normalized')
                table.append(row)
            targets.append(table);declared=view.valid_masks.get('joint_transition_rows');valid_rows.append(declared is None or all(declared))
        target=torch.as_tensor(targets,device=self.device,dtype=output.transition.dtype);valid=torch.as_tensor(valid_rows,device=self.device,dtype=torch.bool)
        cross_entropy=-(target*output.transition.clamp_min(1e-12).log()).sum(-1)
        reference=output.initial;rollout=[]
        for _ in range(self.rollout_steps):reference=torch.einsum('bi,bij->bj',reference,target);rollout.append(reference)
        reference=torch.stack(rollout,1)
        diagonal=output.observations.diagonal(dim1=-2,dim2=-1)
        return {'transition':masked_tensor_mean(cross_entropy,valid[:,None].expand_as(cross_entropy)),'observation':masked_tensor_mean(-diagonal.clamp_min(1e-12).log(),torch.ones_like(diagonal,dtype=torch.bool)),'shared_noise':masked_tensor_mean((output.joint-target[:,0]).square(),valid[:,None].expand_as(output.joint)),'multistep':masked_tensor_mean((output.behavior-reference).square(),valid[:,None,None].expand_as(reference))}

@dataclass(frozen=True)
class DreamOutput:
    legality: object
    selected_world: object
    selected_edit: object
    log_probability: object
    synthetic_inputs: object
    holdout_inputs: object

class DreamStage:
    def __init__(self,world_weight,edit_weight,legal_weight,interface,versions,*,adaptation_rate=.1,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h44_dreaming.losses import LOSS_SPECS
        self.world_weight=world_weight;self.edit_weight=edit_weight;self.legal_weight=legal_weight;self.interface=interface;self.versions=versions;self.adaptation_rate=adaptation_rate;self.device=device;self.loss_specs=LOSS_SPECS
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'world_proposer':{'world_weight':self.world_weight,'edit_weight':self.edit_weight,'legality_weight':self.legal_weight},'protocol_interface':{'affine_coefficients':self.interface}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h44_dreaming.adapter import tensor_world_proposal
        if maximum_unroll<1:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'one synthetic adaptation step required')
        for s,r in zip(sender.views,receiver.views):
            lineage_contract(s.public_task);lineage_contract(r.public_task)
            if s.public_task!=r.public_task:raise ContractError(ErrorCode.CONFLICT,'dream lineage/public task differs across roles')
        features=tensor_field(sender,'kernel_features',device=self.device);compatible=tensor_field(sender,'compatibility',device=self.device,dtype='bool');candidate_inputs=tensor_field(receiver,'synthetic_inputs',device=self.device);holdout=tensor_field(receiver,'holdout_inputs',device=self.device)
        modules,edits=tensor_world_proposal(features@self.world_weight,compatible,features@self.edit_weight)
        world_distribution=torch.distributions.Categorical(probs=modules);world=world_distribution.sample();row=torch.arange(world.shape[0],device=self.device);edit_distribution=torch.distributions.Categorical(probs=edits[row,world]);edit=edit_distribution.sample()
        if candidate_inputs.ndim!=5 or candidate_inputs.shape[:3]!=edits.shape or candidate_inputs.shape[-1]!=self.interface.numel() or holdout.ndim!=3 or holdout.shape[-1]!=self.interface.numel():raise ContractError(ErrorCode.INVALID_SHAPE,'synthetic_inputs[B,K,E,N,D] and independent holdout_inputs[B,H,D] required')
        return DreamOutput(features@self.legal_weight,world,edit,world_distribution.log_prob(world)+edit_distribution.log_prob(edit),candidate_inputs[row,world,edit],holdout)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h44_dreaming.losses import tensor_losses
        legal,legal_mask=tensor_target(supervision,'structural_valid',device=self.device);synthetic,synthetic_mask=tensor_target(supervision,'synthetic_targets',device=self.device);heldout,heldout_mask=tensor_target(supervision,'holdout_targets',device=self.device)
        row=torch.arange(output.selected_world.shape[0],device=self.device);synthetic=synthetic[row,output.selected_world,output.selected_edit];synthetic_mask=synthetic_mask[row,output.selected_world,output.selected_edit]
        if synthetic.shape!=output.synthetic_inputs.shape[:-1] or heldout.shape!=output.holdout_inputs.shape[:-1]:raise ContractError(ErrorCode.INVALID_SHAPE,'selected synthetic and independent targets must match their own inputs')
        curriculum=(output.synthetic_inputs@self.interface-synthetic).square();costs=[];valid=[]
        for inputs,targets,mask,query,y,qmask in zip(output.synthetic_inputs,synthetic,synthetic_mask,output.holdout_inputs,heldout,heldout_mask):
            if not bool(mask.any()) or not bool(qmask.any()):costs.append(self.interface.new_zeros(()));valid.append(False);continue
            # A functional copy permits validation adaptation while the actual
            # protocol owner is frozen during a proposer phase.
            theta=self.interface.detach().clone().requires_grad_(True);loss=((inputs@theta-targets).square().masked_select(mask)).mean();gradient=torch.autograd.grad(loss,theta,create_graph=False)[0];adapted=theta-self.adaptation_rate*gradient
            costs.append((query@adapted-y).square().masked_select(qmask).mean());valid.append(True)
        return tensor_losses(output.legality,legal,curriculum,output.log_probability,torch.stack(costs),(legal_mask,synthetic_mask,torch.as_tensor(valid,device=self.device,dtype=torch.bool)))

@dataclass(frozen=True)
class EcologyOutput:
    prediction: object
    selected: object
    log_probability: object
    novelty: object
    solvability: object

class EcologyStage:
    def __init__(self,novelty_weight,solvability_weight,interface,versions,*,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h42_ecology.losses import LOSS_SPECS
        self.novelty_weight=novelty_weight;self.solvability_weight=solvability_weight;self.interface=interface;self.versions=versions;self.device=device;self.loss_specs=LOSS_SPECS
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'environment_proposer':{'raw_novelty_weight':self.novelty_weight,'raw_solvability_weight':self.solvability_weight},'protocol_interface':{'affine_coefficients':self.interface}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h42_ecology.adapter import tensor_niche_policy
        competence=tensor_field(sender,'competence',device=self.device);novelty=tensor_field(sender,'novelty',device=self.device);solvability=tensor_field(sender,'solvability',device=self.device);valid=tensor_field(sender,'legal_mutations',device=self.device,dtype='bool');niches=tensor_field(sender,'niche_ids',device=self.device,dtype='int64');inputs=tensor_field(receiver,'task_inputs',device=self.device)
        choices=[];logps=[]
        for c,n,s,m,ids in zip(competence,novelty,solvability,valid,niches):
            policy=tensor_niche_policy(c,n,s,m,ids,novelty_weight=torch.nn.functional.softplus(self.novelty_weight),solvability_weight=torch.nn.functional.softplus(self.solvability_weight))
            if not bool(policy.sum()>0):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'no legal mutation in any declared niche')
            # Each nonempty niche has equal total mass before global normalization.
            distribution=torch.distributions.Categorical(probs=policy/policy.sum());choice=distribution.sample();choices.append(choice);logps.append(distribution.log_prob(choice))
        selected=torch.stack(choices);row=torch.arange(len(choices),device=self.device)
        if inputs.ndim!=4 or inputs.shape[:2]!=competence.shape or inputs.shape[-1]!=self.interface.numel():raise ContractError(ErrorCode.INVALID_SHAPE,'ecology task inputs[B,K,N,D] required')
        return EcologyOutput(inputs[row,selected]@self.interface,selected,torch.stack(logps),novelty[row,selected],solvability[row,selected])
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h42_ecology.losses import tensor_losses
        target,mask=tensor_target(supervision,'task_targets',device=self.device);row=torch.arange(output.selected.numel(),device=self.device);target=target[row,output.selected];mask=mask[row,output.selected]
        error=(output.prediction-target).square();count=mask.sum(-1);mean=(error.masked_fill(~mask,0).sum(-1)/count.clamp_min(1));reward=output.novelty+output.solvability-mean
        return tensor_losses(error,output.log_probability,reward,(mask,count>0))

def build_stage(variant,versions,*,rollout_steps=3,feature_dim=3,protocol_dim=2,edits=2,adaptation_rate=.1,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    def p(shape):return torch.nn.Parameter(torch.zeros(shape,device=device,dtype=getattr(torch,dtype)))
    if variant=='kernels':return KernelStage(p((4,2)),p((4,2)),p((4,)),p((4,4)),versions,rollout_steps=rollout_steps,device=device)
    if variant=='dream':return DreamStage(p((feature_dim,)),p((feature_dim,edits)),p((feature_dim,)),p((protocol_dim,)),versions,adaptation_rate=adaptation_rate,device=device)
    if variant=='ecology':return EcologyStage(p(()),p(()),p((protocol_dim,)),versions,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown worlds learning variant')
