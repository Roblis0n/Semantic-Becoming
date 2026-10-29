"""L11: legal identification, certificate-separated exclusions and task quotients."""
from dataclasses import dataclass
from latent_comm.core import ContractError,ErrorCode,StepBudget
from latent_comm.core.budgets import aggregate_budget
from latent_comm.core.learning import LossSpec,GradientEstimator,LossValue,masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action

def signed_responses(programs,query):
    if tuple(programs)!=('y=x','y=-x'):raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'W12 stage binds declared signed-linear hypotheses, not arbitrary program strings')
    return (query,-query)

def certified_domain(constraint,active,version,budget=StepBudget()):
    from latent_comm.mechanisms.h46_negative_knowledge.types import DomainPredicate,NegativeWitness,ExclusionCapsule
    from latent_comm.mechanisms.h46_negative_knowledge.reference import apply_exclusions
    domain=(1,2,3,4)
    if constraint not in {'even','soft_even_preference'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'unknown W12 exclusion scope')
    witness=NegativeWitness('program_exhaustive',DomainPredicate('divisible',2),domain,None,'complete')
    capsule=ExclusionCapsule('even_scope',DomainPredicate('not_divisible',2),('even_required',),witness,1.,'hard' if constraint=='even' else 'soft',(),('even_required',),version)
    with aggregate_budget(budget):return apply_exclusions(domain,(capsule,),('even_required',) if active else (),version,budget=budget)

@dataclass(frozen=True)
class QueryOutput:
    probabilities: tuple
    alphabets: tuple
    queries: tuple
    selected: object
    log_probability: object

class IdentificationStage:
    """W12 has no prior: minimax partition reward, never invented entropy gain."""
    def __init__(self,response_slopes,query_weight,versions,*,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h45_identifiability.losses import LOSS_SPECS
        self.response_slopes=response_slopes;self.query_weight=query_weight;self.versions=versions;self.device=device
        self.loss_specs=(LOSS_SPECS[0],LossSpec('query_policy','-mean(log_pi(allowed_query)*stop(2-max_response_partition_size)))','sum of legal query policy score times independently checked minimax reduction','valid allowed local queries','query response table available','skip_with_reason',('query_proposer',),('query_log_probability',),(('verified_partition_reduction','query_policy'),),GradientEstimator.POLICY_GRADIENT,'queries'))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'response_encoder':{'hypothesis_slopes':self.response_slopes},'query_proposer':{'public_query_feature_weight':self.query_weight}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        probabilities=[];alphabets=[];query_sets=[];selected=[];logps=[]
        for s,r in zip(sender.views,receiver.views):
            queries=tuple(s.public_task['allowed_queries'])
            if not queries or queries!=tuple(r.public_task['allowed_queries']) or len(queries)>64:raise ContractError(ErrorCode.INVALID_SCHEMA,'identical finite host-allowed local queries required')
            for q in queries:signed_responses(s.features['hypothesis_programs'],q)
            alphabet=tuple(sorted(set(v for q in queries for v in signed_responses(s.features['hypothesis_programs'],q))))
            q=torch.as_tensor(queries,device=self.device,dtype=self.query_weight.dtype);answers=q[:,None]*self.response_slopes[None,:];values=torch.as_tensor(alphabet,device=self.device,dtype=q.dtype)
            likelihood=(-(answers[:,:,None]-values[None,None,:]).square()).softmax(-1)
            features=torch.stack((q.abs(),q.square(),torch.ones_like(q)),-1);distribution=torch.distributions.Categorical(logits=features@self.query_weight);choice=distribution.sample()
            probabilities.append(likelihood);alphabets.append(alphabet);query_sets.append(queries);selected.append(choice);logps.append(distribution.log_prob(choice))
        return QueryOutput(tuple(probabilities),tuple(alphabets),tuple(query_sets),torch.stack(selected),torch.stack(logps))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        response=[];gains=[];valid=[]
        for i,(probability,alphabet,queries,view) in enumerate(zip(output.probabilities,output.alphabets,output.queries,supervision.views)):
            table=dict(view.targets['query_response_table']);selected=int(output.selected[i].detach())
            if set(table)!=set(queries):raise ContractError(ErrorCode.INVALID_SCHEMA,'supervised response table differs from authorized query domain')
            labels=torch.tensor([[alphabet.index(v) for v in table[q]] for q in queries],device=self.device,dtype=torch.int64);picked=probability.gather(-1,labels.unsqueeze(-1)).squeeze(-1)
            declared=view.valid_masks.get('query_response_table');okay=declared is None or all(declared)
            if okay:response.append(-picked.clamp_min(1e-12).log().mean())
            answers=table[queries[selected]];worst=max(answers.count(x) for x in set(answers));gains.append(2-worst);valid.append(okay)
        reward=output.log_probability.new_tensor(gains);mask=torch.as_tensor(valid,device=self.device,dtype=torch.bool)
        return {'response':torch.stack(response).mean() if response else LossValue(0.,0.,None,True,'no complete response tables'),'query_policy':masked_tensor_mean(-output.log_probability*reward.detach(),mask)}

@dataclass(frozen=True)
class ExclusionOutput:
    predicates: object
    scope: object
    scope_labels: object
    hard_keep: object

class ExclusionStage:
    def __init__(self,predicate_weights,scope_weights,versions,*,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h46_negative_knowledge.losses import LOSS_SPECS
        self.predicate_weights=predicate_weights;self.scope_weights=scope_weights;self.versions=versions;self.device=device;self.loss_specs=LOSS_SPECS;validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'exclusion_generator':{'predicate_weights':self.predicate_weights},'scope_predictor':{'scope_weights':self.scope_weights}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h46_negative_knowledge.adapter import propose_exclusions
        features=[];scopes=[];keep=[];labels=[]
        for r in receiver.views:
            constraint=r.features['constraint'];active=r.features['assumption_active'];hard=constraint=='even'
            if type(active) is not bool:raise ContractError(ErrorCode.INVALID_SCHEMA,'scope activity must be explicit boolean')
            region=certified_domain(constraint,active,self.versions.world,StepBudget(max_steps=min(128,maximum_unroll)))
            features.append([[float(x),float(x%2),1.] for x in (1,2,3,4)]);scopes.append([float(hard),float(active),1.]);keep.append([x in region.feasible for x in (1,2,3,4)]);labels.append([float(hard and active)])
        f=torch.as_tensor(features,device=self.device,dtype=self.predicate_weights.dtype);scope=torch.as_tensor(scopes,device=self.device,dtype=f.dtype);result=propose_exclusions(f,scope,self.predicate_weights,self.scope_weights)
        return ExclusionOutput(result['predicate_logits'],result['scope_logits'],f.new_tensor(labels),torch.as_tensor(keep,device=self.device,dtype=torch.bool))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h46_negative_knowledge.losses import tensor_losses
        labels=[];mask=[]
        for view in supervision.views:
            excluded=set(view.targets['excluded_domain'])
            if not excluded<={1,2,3,4}:raise ContractError(ErrorCode.INVALID_SCHEMA,'exclusion target escaped declared finite domain')
            labels.append([[float(x in excluded)] for x in (1,2,3,4)]);declared=view.valid_masks.get('excluded_domain');mask.append([[declared is None or all(declared)]]*4)
        return tensor_losses(output.predicates,output.scope,(output.predicates.new_tensor(labels),output.scope_labels),(torch.as_tensor(mask,device=self.device,dtype=torch.bool)&output.scope_labels.bool().unsqueeze(1),torch.ones_like(output.scope,dtype=torch.bool)))

@dataclass(frozen=True)
class QuotientOutput:
    reconstructed: object
    assignment: object
    public_query_targets: object

class QuotientStage:
    def __init__(self,state_projection,query_projection,prototypes,versions,*,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h47_quotient.losses import LOSS_SPECS
        self.state_projection=state_projection;self.query_projection=query_projection;self.prototypes=prototypes;self.versions=versions;self.device=device;self.loss_specs=LOSS_SPECS;validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'state_encoder':{'projection':self.state_projection},'task_conditioner':{'projection':self.query_projection},'prototypes':{'coordinates':self.prototypes}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h47_quotient.adapter import encode_task_relative
        families=[tuple(v.public_task['query_family']) for v in sender.views]
        if any(f!=families[0] for f in families) or any(tuple(v.public_task['query_family'])!=families[0] for v in receiver.views):raise ContractError(ErrorCode.INVALID_SCHEMA,'homogeneous identical public query family required')
        if not set(families[0])<={'parity','greater_than_two'} or not families[0]:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'W07 finite quotient query family required')
        b=len(families);states=torch.as_tensor([[float(x),float(x*x),1.] for x in (1,2,3,4)],device=self.device,dtype=self.state_projection.dtype).expand(b,-1,-1)
        queries=states.new_tensor([[1.,0.] if q=='parity' else [0.,1.] for q in families[0]]).expand(b,-1,-1)
        targets=states.new_tensor([[float(x%2) if q=='parity' else float(x>2) for q in families[0]] for x in (1,2,3,4)]).expand(b,-1,-1)
        result=encode_task_relative(states,queries,self.state_projection,self.query_projection,self.prototypes.unsqueeze(0).expand(b,-1,-1))
        return QuotientOutput(result['reconstructed_behavior'],result['assignments'],targets)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h47_quotient.losses import tensor_losses
        return tensor_losses(output.reconstructed,output.public_query_targets,output.assignment,(torch.ones_like(output.reconstructed,dtype=torch.bool),torch.ones_like(output.assignment[:,:,0],dtype=torch.bool)))

def exact_partition(queries,*,version='quotient:1',budget=StepBudget()):
    """Hard task-relative classes use exact executable responses, not soft clusters."""
    from latent_comm.mechanisms.h47_quotient.types import StateDomain,FiniteQuery
    from latent_comm.mechanisms.h47_quotient.reference import form_quotient
    domain=StateDomain(('1','2','3','4'),(1,2,3,4),'domain:1');definitions=[]
    for q in queries:
        if q not in {'parity','greater_than_two'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'unknown finite query')
        definitions.append(FiniteQuery(q,'parity' if q=='parity' else 'greater_than',0 if q=='parity' else 2,'q1'))
    with aggregate_budget(budget):return form_quotient(domain,tuple(definitions),version,budget=budget)

def build_stage(variant,versions,*,embedding_dim=2,prototype_count=4,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    def p(value):return torch.nn.Parameter(torch.as_tensor(value,device=device,dtype=getattr(torch,dtype)))
    if variant=='identification':return IdentificationStage(p([1.,-1.]),p([0.,0.,0.]),versions,device=device)
    if variant=='exclusions':return ExclusionStage(p([[0.,0.,0.]]),p([[0.,0.,0.]]),versions,device=device)
    if variant=='quotient':return QuotientStage(p(torch.eye(3,embedding_dim)),p(torch.eye(2,embedding_dim)),p(torch.arange(prototype_count*embedding_dim).reshape(prototype_count,embedding_dim)/max(1,prototype_count*embedding_dim)),versions,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown uncertainty stage')
