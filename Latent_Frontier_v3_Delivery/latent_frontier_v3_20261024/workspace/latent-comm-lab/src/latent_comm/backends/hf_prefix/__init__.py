"""Prefix injection with explicit padding, label alignment and incremental state."""
from dataclasses import dataclass
from latent_comm.core import ContractError,ErrorCode,TensorSpec
from latent_comm.safety.policy import require_research_action

@dataclass(frozen=True)
class PrefixLayout:
    prefix_length: int
    token_length: int
    attention_mask: tuple[tuple[bool,...],...]
    position_ids: tuple[tuple[int,...],...]
    loss_ignore_prefix: int
    padding_side: str

@dataclass(frozen=True)
class PrefixDecodeState:
    prefix_length: int
    cached_length: int
    attention_mask: object
    past_key_values: object
    model_revision: str
    prefix_inserted: bool=True

def plan_layout(token_mask: tuple[tuple[bool,...],...],prefix_length: int, *, padding_side: str) -> PrefixLayout:
    if not token_mask or (type(prefix_length) is not int or prefix_length<0) or padding_side not in {'left','right'}:raise ContractError(ErrorCode.INVALID_SHAPE,'invalid declared prefix layout')
    width=len(token_mask[0])
    if any(len(row)!=width or any(type(x) is not bool for x in row) for row in token_mask):raise ContractError(ErrorCode.INVALID_SHAPE,'rectangular Boolean token mask required')
    if width==0 and prefix_length==0:raise ContractError(ErrorCode.INVALID_SHAPE,'empty causal context')
    output=[];positions=[]
    for row in token_mask:
        if prefix_length==0 and not any(row):raise ContractError(ErrorCode.INVALID_SHAPE,'no visible causal context')
        expected=tuple(sorted(row,reverse=padding_side=='right'))
        if row!=expected:raise ContractError(ErrorCode.INVALID_SHAPE,'mask contradicts declared padding side')
        expanded=(True,)*prefix_length+row;count=0;pos=[]
        for valid in expanded:
            if valid:pos.append(count);count+=1
            else:pos.append(0)
        output.append(expanded);positions.append(tuple(pos))
    return PrefixLayout(prefix_length,width,tuple(output),tuple(positions),prefix_length,padding_side)

def visible_predecessors(layout: PrefixLayout) -> tuple[tuple[int,...],...]:
    """Logit position for each real target token, skipping masked padding gaps."""
    rows=[]
    for mask in layout.attention_mask:
        previous=layout.prefix_length-1
        row=[]
        for index in range(layout.token_length):
            position=layout.prefix_length+index
            if not mask[position]:row.append(-1);continue
            row.append(previous);previous=position
        rows.append(tuple(row))
    return tuple(rows)

@dataclass(frozen=True)
class PrefixForwardOutput:
    raw_output: object
    loss: object | None
    valid_loss_tokens: int
    @property
    def logits(self):return self.raw_output.logits
    @property
    def past_key_values(self):return self.raw_output.past_key_values
    def __getattr__(self,name):return getattr(self.raw_output,name)


def aligned_prefix_loss(logits,labels,layout: PrefixLayout):
    require_research_action('model_forward')
    import torch
    if labels.shape!=(len(layout.attention_mask),layout.token_length) or logits.ndim!=3 or logits.shape[:2]!=(labels.shape[0],layout.prefix_length+layout.token_length):raise ContractError(ErrorCode.INVALID_SHAPE,'causal logits/labels/layout axes differ')
    previous=torch.as_tensor(visible_predecessors(layout),device=logits.device,dtype=torch.long)
    targets=labels.to(device=logits.device);valid=(previous>=0)&(targets!=-100)
    count=int(valid.sum().detach().cpu())
    if count==0:return logits.sum()*0.,0
    rows=torch.arange(logits.shape[0],device=logits.device).unsqueeze(-1).expand_as(previous)
    selected=logits[rows[valid],previous[valid]]
    return torch.nn.functional.cross_entropy(selected,targets[valid],reduction='sum')/count,count

def forward_with_prefix(model,input_ids,token_mask,prefix, *, capabilities,prefix_spec: TensorSpec,padding_side: str,role_origins=(),labels=None,use_cache: bool=False):
    require_research_action('model_forward')
    import torch
    capabilities.require('prefix')
    from latent_comm.backends.capabilities import validate_role_origins
    validate_role_origins(tuple(role_origins),input_ids.shape[0])
    prefix_spec.require_axes(('batch','prefix','channel'));prefix_spec.check_shape(tuple(prefix.shape))
    if input_ids.ndim!=2 or token_mask.shape!=input_ids.shape or input_ids.shape[0]!=prefix.shape[0]:raise ContractError(ErrorCode.INVALID_SHAPE,'token/prefix batch mismatch')
    embeddings=model.get_input_embeddings()(input_ids)
    if embeddings.shape[-1]!=prefix.shape[-1] or embeddings.shape[-1]!=capabilities.hidden_size:raise ContractError(ErrorCode.INVALID_SHAPE,'declared prefix channel mismatch')
    # Conversion retains a differentiable edge; it is not a serialization boundary.
    prefix=prefix.to(device=embeddings.device,dtype=embeddings.dtype)
    layout=plan_layout(tuple(tuple(bool(x) for x in row) for row in token_mask.detach().cpu().tolist()),prefix.shape[1],padding_side=padding_side)
    attention=torch.tensor(layout.attention_mask,device=embeddings.device,dtype=token_mask.dtype)
    position=torch.tensor(layout.position_ids,device=embeddings.device,dtype=torch.long)
    combined=torch.cat((prefix,embeddings),dim=1)
    kwargs={'inputs_embeds':combined,'attention_mask':attention,'position_ids':position,'use_cache':use_cache,'return_dict':True}
    if labels is not None and labels.shape!=input_ids.shape:raise ContractError(ErrorCode.INVALID_SHAPE,'labels must align to original tokens')
    # Never use the backend's physical one-slot shift across a left-padding gap.
    # Labels stay loss-only and the preceding visible causal position is explicit.
    if capabilities.cache_position_supported:kwargs['cache_position']=torch.arange(combined.shape[1],device=embeddings.device)
    raw=model(**kwargs)
    loss,count=aligned_prefix_loss(raw.logits,labels,layout) if labels is not None else (None,0)
    outputs=PrefixForwardOutput(raw,loss,count)
    state=PrefixDecodeState(prefix.shape[1],combined.shape[1],attention,outputs.past_key_values,capabilities.identity.model_revision) if use_cache else None
    return outputs,state

def decode_step(model,new_token_ids,state: PrefixDecodeState, *, capabilities,reinsert_prefix=None):
    require_research_action('model_forward')
    import torch
    if reinsert_prefix is not None:raise ContractError(ErrorCode.CONFLICT,'prefix must not be inserted on incremental steps')
    if not state.prefix_inserted or capabilities.identity.model_revision!=state.model_revision:raise ContractError(ErrorCode.VERSION_MISMATCH,'decode state model or prefix mismatch')
    if new_token_ids.ndim!=2 or new_token_ids.shape[1]!=1:raise ContractError(ErrorCode.INVALID_SHAPE,'incremental decode consumes one token per batch')
    attention=torch.cat((state.attention_mask,torch.ones_like(new_token_ids,dtype=state.attention_mask.dtype)),dim=1)
    position=(attention.long().cumsum(-1)-1)[:,-1:].clamp_min(0)
    kwargs={'input_ids':new_token_ids,'attention_mask':attention,'position_ids':position,'past_key_values':state.past_key_values,'use_cache':True,'return_dict':True}
    if capabilities.cache_position_supported:kwargs['cache_position']=torch.tensor([state.cached_length],device=new_token_ids.device)
    outputs=model(**kwargs)
    return outputs,PrefixDecodeState(state.prefix_length,state.cached_length+1,attention,outputs.past_key_values,state.model_revision)

def generate_with_prefix(model,input_ids,token_mask,prefix, *, capabilities,prefix_spec,padding_side: str,max_new_tokens: int,eos_token_id: int,role_origins=()):
    require_research_action('model_generate')
    import torch
    if type(max_new_tokens) is not int or max_new_tokens<=0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'explicit generation horizon required')
    outputs,state=forward_with_prefix(model,input_ids,token_mask,prefix,capabilities=capabilities,prefix_spec=prefix_spec,padding_side=padding_side,role_origins=role_origins,use_cache=True)
    # Last visible token can differ under right padding; select by actual expanded mask.
    positions=torch.arange(state.attention_mask.shape[1],device=input_ids.device).expand_as(state.attention_mask)
    last=positions.masked_fill(~state.attention_mask.bool(),-1).max(-1).values
    logits=outputs.logits[torch.arange(input_ids.shape[0],device=input_ids.device),last]
    finished=torch.zeros(input_ids.shape[0],device=input_ids.device,dtype=torch.bool);tokens=[]
    for step in range(max_new_tokens):
        token=logits.argmax(-1);token=torch.where(finished,torch.full_like(token,eos_token_id),token);tokens.append(token)
        finished=finished | (token==eos_token_id)
        if bool(finished.all()) or step+1==max_new_tokens:break
        outputs,state=decode_step(model,token[:,None],state,capabilities=capabilities);logits=outputs.logits[:,-1]
    # State contains processed tokens only; the final selected token is pending.
    return torch.stack(tokens,dim=1),state
