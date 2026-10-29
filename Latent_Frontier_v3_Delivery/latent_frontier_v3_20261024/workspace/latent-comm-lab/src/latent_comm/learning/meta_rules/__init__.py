"""L08: bounded support/query meta-learning of a whitelisted update-rule AST."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,ErrorCode,StepBudget
from latent_comm.core.learning import LossSpec,GradientEstimator,LossValue,masked_tensor_mean
from latent_comm.learning.source import tensor_field
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action
from latent_comm.mechanisms.h38_plasticity.types import RuleNode,PlasticityProgram,SupportBatch,QueryBatch
from latent_comm.mechanisms.h38_plasticity.reference import validate_rule,validate_partitions

def rule_ast():
    return RuleNode('scale',(RuleNode('clip',(RuleNode('running_mean',(RuleNode('read',slot='gradient'),),scalar=.5,parameter='memory_decay'),),scalar=1.,parameter='clip'),),scalar=-.1,parameter='rate')

def validate_episode_ids(support_id,query_id):
    return validate_partitions(SupportBatch(None,None,support_id),QueryBatch(None,None,query_id))

@dataclass(frozen=True)
class Episode:
    initial: object
    support_inputs: object
    query_inputs: object
    support_id: str
    query_id: str
    source_rule: tuple | None

@dataclass(frozen=True)
class MetaOutput:
    episodes: tuple[Episode,...]
    maximum_unroll: int

class MetaRuleStage:
    """The engine owns outer optimization; this stage owns the finite inner graph.

    Only loss computation can read supervised labels. It creates separate typed
    support/query batches and the AST environment can read support-local
    statistics only. Fixed inner horizon is not determined from query outcomes.
    """
    def __init__(self,raw_rate,raw_memory,raw_clip,versions,*,variant='quadratic_full',inner_steps=3,max_update_norm=1.,device='cpu'):
        require_research_action('model_initialize')
        if variant not in {'quadratic_full','quadratic_first_order','episodic_full','episodic_first_order'}:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown meta-rule variant')
        self.raw_rate=raw_rate;self.raw_memory=raw_memory;self.raw_clip=raw_clip;self.versions=versions;self.variant=variant;self.device=device
        self.estimator='first_order' if variant.endswith('first_order') else 'exact_unroll'
        self.program=PlasticityProgram(rule_ast(),('adapter.theta',),max_update_norm,inner_steps,inner_steps,versions.isa,self.estimator)
        from latent_comm.mechanisms.h38_plasticity.losses import LOSS_SPECS
        objective=LOSS_SPECS[1] if self.estimator=='first_order' else LOSS_SPECS[0]
        self.loss_specs=(objective,LOSS_SPECS[2]);validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'plasticity_rule_parameters':{'raw_rate':self.raw_rate,'raw_memory':self.raw_memory,'raw_clip':self.raw_clip}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        if self.program.inner_steps>maximum_unroll:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'fixed support unroll exceeds phase budget')
        episodes=[]
        for i,(s,r) in enumerate(zip(sender.views,receiver.views)):
            if self.variant.startswith('quadratic'):
                rule=tuple(s.features['rule'])
                if len(rule)!=6 or rule[0]!='running_mean' or rule[2]!='clip' or rule[4]!='scale' or r.features['query_condition']!='separate finite quadratic readout':raise ContractError(ErrorCode.INVALID_SCHEMA,'W08 rule family mismatch')
                probes=torch.as_tensor(s.public_task['public_probes'],device=self.device,dtype=self.raw_rate.dtype)
                if probes.shape!=(2,2) or s.public_task['public_probes']!=r.public_task['public_probes']:raise ContractError(ErrorCode.INVALID_SHAPE,'W08 public quadratic probes must be the declared shared two-coordinate basis')
                initial=self.raw_rate.new_tensor([1.,2.]);support_inputs=probes;query_inputs=probes
                # These are analytic objective namespaces, not a claim that the
                # deterministic W08 fixture contains statistically held-out data.
                support_id='analytic_support:'+str(i);query_id='analytic_query:'+str(i)
            else:
                initial=torch.as_tensor(s.public_task['initial_adapter'],device=self.device,dtype=self.raw_rate.dtype);support_inputs=torch.as_tensor(s.features['support_inputs'],device=self.device,dtype=self.raw_rate.dtype);query_inputs=torch.as_tensor(r.features['query_inputs'],device=self.device,dtype=self.raw_rate.dtype);rule=None
                support_id=s.public_task['support_partition'];query_id=r.public_task['query_partition']
                validate_episode_ids(support_id,query_id)
            if initial.ndim!=1 or support_inputs.ndim!=2 or query_inputs.ndim!=2 or support_inputs.shape[1]!=initial.numel() or query_inputs.shape[1]!=initial.numel():raise ContractError(ErrorCode.INVALID_SHAPE,'linear scoped adapter inputs[N,D], theta[D] required')
            episodes.append(Episode(initial,support_inputs,query_inputs,support_id,query_id,rule))
        return MetaOutput(tuple(episodes),maximum_unroll)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h38_plasticity.adapter import tensor_interpret
        query_values=[];raw_norms=[]
        for episode,view in zip(output.episodes,supervision.views):
            if episode.source_rule is None:
                support_target=torch.as_tensor(view.targets['support_targets'],device=self.device,dtype=self.raw_rate.dtype);query_target=torch.as_tensor(view.targets['query_targets'],device=self.device,dtype=self.raw_rate.dtype)
                support_mask=torch.as_tensor(view.valid_masks.get('support_targets',[True]*support_target.numel()),device=self.device,dtype=torch.bool).reshape_as(support_target);query_mask=torch.as_tensor(view.valid_masks.get('query_targets',[True]*query_target.numel()),device=self.device,dtype=torch.bool).reshape_as(query_target)
                base_rate=-.1;base_memory=.5;base_clip=1.
            else:
                # W08 defines the analytic gradient theta and query sum(theta²).
                support_target=episode.support_inputs.new_zeros(episode.support_inputs.shape[0]);query_target=episode.query_inputs.new_zeros(episode.query_inputs.shape[0]);support_mask=torch.ones_like(support_target,dtype=torch.bool);query_mask=torch.ones_like(query_target,dtype=torch.bool)
                _,base_memory,_,base_clip,_,base_rate=episode.source_rule
            if support_target.shape!=(episode.support_inputs.shape[0],) or query_target.shape!=(episode.query_inputs.shape[0],):raise ContractError(ErrorCode.INVALID_SHAPE,'support/query targets must match their own partitions')
            if not bool(support_mask.any()) or not bool(query_mask.any()):continue
            support=SupportBatch(episode.support_inputs,support_target,episode.support_id);query=QueryBatch(episode.query_inputs,query_target,episode.query_id);validate_partitions(support,query)
            if not 0<base_memory<1 or base_clip<=0 or base_rate>=0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'rule scalar base domain invalid')
            # Reparameterizations preserve rule operator domains, not arbitrary AST execution.
            base_logit=self.raw_memory.new_tensor(base_memory/(1-base_memory)).log()
            psi={'rate':base_rate*self.raw_rate.exp(),'memory_decay':(self.raw_memory+base_logit).sigmoid(),'clip':base_clip*self.raw_clip.exp()}
            theta=episode.initial.detach().clone().requires_grad_(True);memory=torch.zeros_like(theta)
            for step in range(self.program.inner_steps):
                # Query inputs and labels do not occur in the support gradient.
                support_error=(support.inputs@theta-support.targets).square()
                support_loss=support_error.masked_select(support_mask).sum()/2
                gradient=torch.autograd.grad(support_loss,theta,create_graph=self.estimator=='exact_unroll',allow_unused=False)[0]
                if self.estimator=='first_order':gradient=gradient.detach()
                env={'gradient':gradient,'theta':theta,'memory':memory,'diagonal':gradient.square(),'mask':torch.ones_like(theta)};memory_out={}
                raw_update=tensor_interpret(self.program.ast,env,psi,memory_out)
                raw_norms.append(raw_update.norm());factor=(self.program.max_update_norm/raw_update.norm().clamp_min(1e-12)).clamp(max=1.)
                theta=theta+raw_update*factor;memory=memory_out.get('memory',memory)
            error=(query.inputs@theta-query.targets).square()
            query_values.append(error.masked_select(query_mask).sum()/query_mask.sum())
        name='outer_query_first_order' if self.estimator=='first_order' else 'outer_query_full'
        return {name:torch.stack(query_values).mean() if query_values else LossValue(0.,0.,None,True,'no episodes with valid support and held-out query'),'update_budget':torch.stack([(v-self.program.max_update_norm).clamp_min(0).square() for v in raw_norms]).mean() if raw_norms else LossValue(0.,0.,None,True,'no raw scoped updates')}

def choose_rule_structure(programs,validation_cost,*,candidate_limit=32):
    """Future finite enumeration; costs come from validation, never final test.

    The callback runs an authorized support/query adaptation using each complete
    candidate. The discrete selection is not an end-to-end gradient edge.
    """
    require_research_action('model_train')
    import math
    if not 1<=len(programs)<=candidate_limit<=64:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'finite rule candidate budget required')
    scored=[]
    for index,program in enumerate(programs):
        validate_rule(program.ast);cost=float(validation_cost(program))
        if not math.isfinite(cost):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'nonfinite validation cost')
        scored.append((cost,index,program))
    cost,index,program=min(scored,key=lambda row:(row[0],row[1]));return {'selected':program,'candidate_index':index,'validation_cost':cost,'estimator':'finite_enumeration','gradient_through_selection':False}

def build_stage(variant,versions,*,inner_steps=3,max_update_norm=1.,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    def p():return torch.nn.Parameter(torch.zeros((),device=device,dtype=getattr(torch,dtype)))
    return MetaRuleStage(p(),p(),p(),versions,variant=variant,inner_steps=inner_steps,max_update_norm=max_update_norm,device=device)
