"""L09: immutable-base macro semantics, polynomial fast paths and typed bindings."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,ErrorCode,StepBudget
from latent_comm.core.budgets import aggregate_budget
from latent_comm.core.learning import LossSpec,GradientEstimator,masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action
from latent_comm.mechanisms.h40_instruction_set.types import Expr,MacroDefinition,ISARevision
from latent_comm.mechanisms.h40_instruction_set.reference import lower,encoding_bytes,free_variables

def parse_world_expression(raw,depth=0):
    if depth>12 or not isinstance(raw,(tuple,list)) or not raw:raise ContractError(ErrorCode.INVALID_SCHEMA,'bounded W09 expression required')
    op=raw[0]
    if op=='const' and len(raw)==2:return Expr('const',value=float(raw[1]))
    if op=='var' and len(raw)==2:return Expr('var',name=raw[1])
    if op in {'add','mul'} and len(raw)==3:return Expr('multiply' if op=='mul' else op,tuple(parse_world_expression(c,depth+1) for c in raw[1:]))
    if op=='let' and len(raw)==4:return Expr('let',(parse_world_expression(raw[2],depth+1),parse_world_expression(raw[3],depth+1)),name=raw[1])
    raise ContractError(ErrorCode.INVALID_SCHEMA,'expression is not in immutable typed base ISA')

def compiled_world_macro(raw,version,budget=StepBudget()):
    body=parse_world_expression(raw)
    if free_variables(body)!={'arg'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'W09 macro must bind exactly its scalar arg')
    revision=ISARevision(version,(MacroDefinition('world_macro',('arg',),body,('scalar',)),))
    expression=Expr('add',(Expr('call',(Expr('var',name='caller_argument'),),name='world_macro'),Expr('const',value=1.)))
    with aggregate_budget(budget):expanded=lower(expression,revision,budget)
    return revision,expanded

@dataclass(frozen=True)
class MacroOutput:
    fast: object
    exact: object
    binding_logits: object | None

class MacroStage:
    def __init__(self,coefficients,binding_weight,versions,*,device='cpu'):
        require_research_action('model_initialize')
        self.coefficients=coefficients;self.binding_weight=binding_weight;self.versions=versions;self.device=device
        from latent_comm.mechanisms.h40_instruction_set.losses import LOSS_SPECS
        self.loss_specs=tuple(s for s in LOSS_SPECS if s.name in ({'fast_behavior','binding'} if binding_weight is not None else {'fast_behavior'}))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):
        groups={'fast_macro_coefficients':{'monomial_coefficients':self.coefficients}}
        if self.binding_weight is not None:groups['binding_selector']={'lexical_feature_weight':self.binding_weight}
        return groups
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h40_instruction_set.adapter import tensor_base_execute,tensor_fast_polynomial
        arguments=[];exact=[]
        for s,r in zip(sender.views,receiver.views):
            raw=s.features['macro']
            # The fast representation is this explicit polynomial family only;
            # arbitrary macros still execute after exact base lowering.
            if raw[0]!='mul' or raw[1][0]!='var' or raw[1][1]!='arg' or raw[2][0]!='const':raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'fast family supports arg times one declared scalar coefficient')
            _,expanded=compiled_world_macro(raw,self.versions.isa,StepBudget(max_steps=min(128,maximum_unroll)))
            x=torch.as_tensor(r.features['caller_argument'],device=self.device,dtype=self.coefficients.dtype).reshape(1)
            exact.append(tensor_base_execute(expanded,{'caller_argument':x}).reshape(()));arguments.append(torch.stack((x.reshape(()),x.new_tensor(raw[2][1]))))
        arguments=torch.stack(arguments);powers=torch.tensor(((0,0),(1,0),(0,1),(1,1)),device=self.device,dtype=torch.int64)
        fast=tensor_fast_polynomial(arguments,powers,self.coefficients)
        logits=None
        if self.binding_weight is not None:
            features=tensor_field(receiver,'binding_features',device=self.device);valid=tensor_field(receiver,'binding_valid',device=self.device,dtype='bool')
            if features.ndim!=3 or features.shape[-1]!=self.binding_weight.numel() or valid.shape!=features.shape[:2] or not bool(valid.any(-1).all()):raise ContractError(ErrorCode.INVALID_SHAPE,'typed binding candidates[B,C,F] require a nonempty valid domain')
            logits=(features@self.binding_weight).masked_fill(~valid,-torch.inf)
        return MacroOutput(fast,torch.stack(exact),logits)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        _,valid=tensor_target(supervision,'program_output',device=self.device)
        terms={'fast_behavior':masked_tensor_mean((output.fast-output.exact.detach()).square(),valid)}
        if output.binding_logits is not None:
            labels,mask=tensor_target(supervision,'binding_index',device=self.device,dtype='int64')
            safe=labels.clamp(0,output.binding_logits.shape[-1]-1)
            if bool((((labels<0)|(labels>=output.binding_logits.shape[-1]))&mask).any()) or bool((~torch.isfinite(output.binding_logits.gather(-1,safe.unsqueeze(-1)).squeeze(-1))&mask).any()):raise ContractError(ErrorCode.INVALID_SCHEMA,'supervised binding must be one valid typed candidate')
            terms['binding']=masked_tensor_mean(torch.nn.functional.cross_entropy(output.binding_logits,safe,reduction='none'),mask)
        return terms

def select_macro_structure(corpus,name,*,maximum_steps=128):
    """Actual byte-saving search with hygienic lowering, no gradient on AST edits."""
    require_research_action('model_train')
    from latent_comm.mechanisms.h40_instruction_set.reference import propose_macro
    if not 1<=maximum_steps<=128:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'explicit finite structure-search budget required')
    budget=StepBudget(max_steps=maximum_steps)
    with aggregate_budget(budget):proposal=propose_macro(corpus,name,budget)
    return {'proposal':proposal,'saved_bytes':proposal.saved_bytes,'estimator':'finite_enumeration','gradient_through_lowering':False}

def build_stage(variant,versions,*,binding_features=3,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    if variant not in {'fast_macro','typed_binding'}:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown macro learning variant')
    coefficients=torch.nn.Parameter(torch.zeros(4,device=device,dtype=getattr(torch,dtype)))
    binding=None if variant=='fast_macro' else torch.nn.Parameter(torch.zeros(binding_features,device=device,dtype=getattr(torch,dtype)))
    return MacroStage(coefficients,binding,versions,device=device)
