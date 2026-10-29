"""L04: executable concept search/relaxation and witnessed question relations."""
from dataclasses import dataclass
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import LossSpec,GradientEstimator,masked_tensor_mean
from latent_comm.safety.policy import require_research_action
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership

@dataclass(frozen=True)
class ConceptOutputs:
    values: object
    known: object
    action_logits: object
    old_reader: object
    old_reference: object
    description_bytes: int

class ConceptStage:
    def __init__(self,predicate,thresholds,weight,bias,versions,*,device='cpu',temperature=.2,description_weight=.001,drift_weight=.1):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h27_ontology.losses import LOSS_SPECS
        self.predicate=predicate;self.thresholds=thresholds;self.weight=weight;self.bias=bias;self.versions=versions;self.device=device;self.temperature=temperature;self.description_weight=description_weight;self.drift_weight=drift_weight
        self.loss_specs=LOSS_SPECS
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'concept_thresholds':dict(self.thresholds),'behavior_readout':{'weight':self.weight,'bias':self.bias}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h27_ontology.adapter import soft_predicate,concept_behavior
        from latent_comm.mechanisms.h27_ontology.types import Predicate
        observations=tensor_field(sender,'observations',device=self.device);queries=tensor_field(receiver,'query_indices',device=self.device,dtype='int64')
        if observations.ndim!=3 or observations.shape[-1]!=2 or queries.ndim!=2 or observations.shape[:2]!=queries.shape:raise ContractError(ErrorCode.INVALID_SHAPE,'concept world needs observations[B,N,2] and aligned query indices[B,N]')
        if bool((queries<0).any()) or bool((queries>=observations.shape[1]).any()):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'query outside observed public domain')
        if not torch.equal(queries,torch.arange(observations.shape[1],device=queries.device).expand_as(queries)):raise ContractError(ErrorCode.INVALID_SCHEMA,'W03 training contract preserves canonical query order; remap labels separately before another ordering')
        observations=observations.gather(1,queries.unsqueeze(-1).expand(-1,-1,2));b,n,_=observations.shape
        features={'authorized':observations[:,:,0].reshape(-1),'expired':observations[:,:,1].reshape(-1)};known={k:torch.isfinite(v) for k,v in features.items()}
        values,valid=soft_predicate(self.predicate,features,known,self.thresholds,temperature=self.temperature)
        logits,_=concept_behavior(values.unsqueeze(-1),valid.unsqueeze(-1),self.weight,self.bias)
        old,_=soft_predicate(Predicate('eq','authorized',True),features,known,self.thresholds,temperature=self.temperature)
        return ConceptOutputs(values.reshape(b,n),valid.reshape(b,n),logits.reshape(b,n,2),old.reshape(b,n),features['authorized'].reshape(b,n),self.predicate.description_length)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        target,valid=tensor_target(supervision,'predicate_outputs',device=self.device,dtype='int64');valid=valid&output.known
        pairs=[]
        for row,view in enumerate(supervision.views):
            for a,b in view.targets['distinction_pairs']:
                if not 0<=a<output.values.shape[1] or not 0<=b<output.values.shape[1]:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'distinction supervision index outside row')
                if bool(output.known[row,a]&output.known[row,b]):pairs.append(torch.relu(output.values.new_tensor(.5)-(output.values[row,a]-output.values[row,b]).abs()))
        from latent_comm.core.learning import LossValue
        distinction=torch.stack(pairs).mean() if pairs else LossValue(0.,0.,None,True,'no known required distinction pairs')
        behavior=torch.nn.functional.cross_entropy(output.action_logits.reshape(-1,2),target.reshape(-1),reduction='none').reshape(target.shape)
        return {'distinction':distinction,'behavior':masked_tensor_mean(behavior,valid),'drift':masked_tensor_mean((output.old_reader-output.old_reference.detach()).square(),output.known),'description':output.values.new_tensor(float(output.description_bytes))}


def select_concept_structure(old,records,required_pairs,atoms,*,concept_id,evidence,candidate_limit=64,description_weight=.001,drift_weight=.1):
    """Exact finite grammar search, not a fabricated gradient through an AST."""
    require_research_action('model_train')
    from latent_comm.mechanisms.h27_ontology.reference import search_concept
    return search_concept(old,records,required_pairs,atoms,concept_id=concept_id,evidence=evidence,candidate_limit=candidate_limit,description_weight=description_weight,drift_weight=drift_weight)

@dataclass(frozen=True)
class QuestionOutputs:
    relation_logits: object
    translated_domain: object
    original_domain: object
    candidate_mask: object
    path_log_probability: object
    selected: object

class QuestionStage:
    """Learn proposal ranking, not the logical relation itself.

    Relation labels are independently witnessed by H29. A learned classifier may
    prioritize verification but never substitutes for soundness/completeness.
    """
    def __init__(self,selector_weight,relation_weight,relation_bias,answer_scale,answer_offset,versions,*,device='cpu'):
        require_research_action('model_initialize')
        from latent_comm.mechanisms.h29_questions.losses import LOSS_SPECS
        self.selector_weight=selector_weight;self.relation_weight=relation_weight;self.relation_bias=relation_bias;self.answer_scale=answer_scale;self.answer_offset=answer_offset;self.versions=versions;self.device=device;self.loss_specs=LOSS_SPECS
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'transform_selector':{'selector':self.selector_weight,'relation_weight':self.relation_weight,'relation_bias':self.relation_bias},'answer_map':{'scale':self.answer_scale,'offset':self.answer_offset}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h29_questions.adapter import tensor_answer_transport
        # Encode only the visible equation and proposed transform, never solutions.
        squares=[];kinds=[];domain=tensor_field(sender,'domain',device=self.device,public=True)
        names={'positive_root_only':0,'both_roots':1,'relax_nonnegative':2}
        for s,r in zip(sender.views,receiver.views):
            equation=s.features['equation']
            if equation[0]!='square_equals' or r.features['transform'] not in names:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'question stage needs declared square rewrite family')
            squares.append(equation[1]);kinds.append(names[r.features['transform']])
        square=torch.as_tensor(squares,device=self.device,dtype=domain.dtype);kind=torch.as_tensor(kinds,device=self.device)
        features=torch.cat((square.unsqueeze(-1),torch.nn.functional.one_hot(kind,3).to(domain.dtype)),dim=-1)
        logits=torch.nn.functional.linear(features,self.relation_weight,self.relation_bias)
        # Public-domain candidate distribution. It does not encode a solved answer.
        candidate_features=torch.stack((domain,domain.square(),square.unsqueeze(-1).expand_as(domain)),dim=-1)
        scores=candidate_features@self.selector_weight
        candidate_mask=(kind.unsqueeze(-1)==1)|(domain>=0)
        if not bool(candidate_mask.any(-1).all()):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'no candidates in declared transform domain')
        distribution=torch.distributions.Categorical(logits=scores.masked_fill(~candidate_mask,-torch.inf))
        selected=distribution.sample();logp=distribution.log_prob(selected)
        mapped=tensor_answer_transport(domain.unsqueeze(-1),self.answer_scale.reshape(1,1,1).expand(domain.shape[0],1,1),self.answer_offset.reshape(1,1).expand(domain.shape[0],1)).squeeze(-1)
        return QuestionOutputs(logits,mapped,domain,candidate_mask,logp,selected)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h29_questions.losses import tensor_losses
        # Four classes encode independent soundness/completeness bits: no conflation.
        relations=[];answer_mask=torch.zeros_like(output.original_domain,dtype=torch.bool);advantages=[]
        for row,view in enumerate(supervision.views):
            t=view.targets;relations.append(2*int(t['sound'])+int(t['complete']))
            original=set(t['original_solutions']);transformed=set(t['transformed_solutions'])
            answer_mask[row]=torch.as_tensor([float(v) in transformed for v in output.original_domain[row].detach().cpu()],device=self.device)&output.candidate_mask[row]
            selected=float(output.original_domain[row,output.selected[row]].detach().cpu())
            # Score-function signal only, with an explicit stopped reward baseline.
            reward=float(selected in original and selected in transformed)
            baseline=len(original&transformed)/max(1,len(transformed));advantages.append(reward-baseline)
        labels=torch.as_tensor(relations,device=self.device);advantage=torch.as_tensor(advantages,device=self.device,dtype=output.path_log_probability.dtype)
        masks=(torch.ones_like(labels,dtype=torch.bool),answer_mask,torch.ones_like(labels,dtype=torch.bool))
        return tensor_losses(output.relation_logits,labels,output.translated_domain,output.original_domain,output.path_log_probability,advantage,masks)


def build_stage(variant,versions,*,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    def p(value):return torch.nn.Parameter(torch.as_tensor(value,device=device,dtype=getattr(torch,dtype)))
    if variant=='concept':
        from latent_comm.mechanisms.h27_ontology.types import Predicate
        ast=Predicate('and',children=(Predicate('eq','authorized',True),Predicate('not',children=(Predicate('eq','expired',True),))))
        return ConceptStage(ast,{'authorized':p(1.),'expired':p(1.)},p([[-1.],[1.]]),p([0.,0.]),versions,device=device)
    if variant=='questions':return QuestionStage(p([0.,0.,0.]),p([[0.]*4 for _ in range(4)]),p([0.]*4),p(1.),p(0.),versions,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown concept/question stage')


def search_question_structure(question,library,*,maximum_depth=5,candidate_questions=32):
    require_research_action('model_train')
    from latent_comm.mechanisms.h29_questions.reference import build_question_graph
    return build_question_graph(question,library,max_transform_depth=maximum_depth,candidate_questions=candidate_questions)
