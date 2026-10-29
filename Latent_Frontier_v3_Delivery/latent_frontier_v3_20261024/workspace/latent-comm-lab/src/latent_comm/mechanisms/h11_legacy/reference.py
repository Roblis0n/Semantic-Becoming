from dataclasses import asdict,replace
import json, math
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import vector
from .types import CodeLayer,ProgressiveState

def layer_bytes(layer):return json.dumps(asdict(layer),sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def encode(value,scales,*,message_id,task_family,semantic_scale,versions,budget=StepBudget()):
    value=vector(value);residual=list(value);layers=[];meter=budget.meter()
    for k,scale in enumerate(scales):
        meter.consume(steps=1)
        if scale<=0:raise ContractError('InvalidScale','positive quantization step')
        q=tuple(round(v/scale) for v in residual);residual=[v-n*scale for v,n in zip(residual,q)]
        layers.append(CodeLayer(message_id,k,k-1,tuple(range(len(value))),q,scale,max(abs(v) for v in residual),task_family,semantic_scale,versions))
    return tuple(layers)
def empty_state(message_id,dimension,versions):
    if not 1<=dimension<=64:raise ContractError('DimensionMismatch','bounded code width')
    return ProgressiveState(message_id,tuple(0. for _ in range(dimension)),(),0,None,0,0,versions)
def ingest(state,layer):
    if state.message_id!=layer.message_id or not state.versions.matches(layer.versions,('frame','task','state')):raise ContractError('VersionMismatch','cannot mix code streams')
    if any(not 0<=s<len(state.value) for s in layer.slots):raise ContractError('DimensionMismatch','changed slot outside stream')
    known={x.sequence:x for x in state.layers};wire=state.wire_bytes+len(layer_bytes(layer))
    if layer.sequence in known:
        if known[layer.sequence]!=layer:raise ContractError('CorruptRetransmission','same sequence with different payload')
        return replace(state,wire_bytes=wire)
    known[layer.sequence]=layer;value=list(state.value);seq=state.next_sequence;bound=state.uncertainty_bound
    while seq in known:
        item=known[seq]
        for slot,q in zip(item.slots,item.integers):value[slot]+=q*item.scale
        bound=item.remaining_error_bound;seq+=1
    return replace(state,value=tuple(value),layers=tuple(known[k] for k in sorted(known)),next_sequence=seq,uncertainty_bound=bound,wire_bytes=wire)
def request_more(state,*,tolerance,max_layer,cost_limit):
    if tolerance<0 or cost_limit<0:raise ContractError('InvalidBudget','nonnegative tolerance/cost')
    needed=state.uncertainty_bound is None or state.uncertainty_bound>tolerance
    if not needed:return state,{'status':'numeric_tolerance_met_not_semantic_proof'}
    if state.next_sequence>max_layer:return state,{'status':'source_exhausted_uncertainty_remains'}
    request={'message_id':state.message_id,'sequence':state.next_sequence,'reason':'missing_prefix_or_numeric_residual'};size=len(json.dumps(request,sort_keys=True).encode())
    if size>cost_limit:return state,{'status':'request_budget_exhausted'}
    return replace(state,request_bytes=state.request_bytes+size),request
