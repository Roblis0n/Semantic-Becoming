from dataclasses import replace
from latent_comm.core import ContractError,StepBudget
from .types import CognitiveClock,EventDecision

def happens_before(left,right):
    a=dict(left.causal);b=dict(right.causal);keys=set(a)|set(b)
    return all(a.get(k,0)<=b.get(k,0) for k in keys) and any(a.get(k,0)<b.get(k,0) for k in keys)
def tick(clock,actor,*,physical_step,phase=None,path_index=None,received=None):
    if physical_step<clock.physical_step:raise ContractError('InvalidClock','local physical scheduling step cannot go backwards')
    causal=dict(clock.causal)
    if received:
        for k,v in received.causal:causal[k]=max(causal.get(k,0),v)
    causal[actor]=causal.get(actor,0)+1
    return CognitiveClock(physical_step,phase or clock.phase,clock.phase_index+int(phase is not None and phase!=clock.phase),clock.path_id,clock.path_index if path_index is None else path_index,tuple(sorted(causal.items())))
def staleness(event,current_versions,step,remaps=()):
    if step>event.expires_step:return 'expired',None
    matches=all(current_versions.get(k)==v for k,v in event.receiver_versions)
    if matches:return 'ready',event.payload_ref
    if event.stale_policy=='reject':return 'stale_rejected',None
    if event.stale_policy=='recompute':return 'recompute_required',None
    valid=[m for m in remaps if m.source_requirements==event.receiver_versions and m.original_payload==event.payload_ref and all(current_versions.get(k)==v for k,v in m.target_requirements)]
    if len(valid)!=1:return 'remap_required',None
    return 'remapped',valid[0].remapped_payload
class EventScheduler:
    def __init__(self,*,max_steps=128):
        if not 1<=max_steps<=128:raise ContractError('BudgetExhausted','finite scheduler bound')
        self.max_steps=max_steps;self.step=0;self.events={};self.completed=set();self.terminal=set();self.log=[]
    def deliver(self,event):
        if event.event_id in self.events:
            if self.events[event.event_id]!=event:raise ContractError('EventCollision','same id with different content')
            return 'duplicate_ignored'
        if len(self.events)>=64:raise ContractError('BudgetExhausted','bounded event queue')
        self.events[event.event_id]=event;return 'queued'
    def advance(self,current_versions,*,remaps=()):
        if self.step>=self.max_steps:return (), 'schedule_budget_exhausted'
        self.step+=1;decisions=[]
        # Stable tie-break is only for deterministic replay, never causal proof.
        for key in sorted(self.events):
            e=self.events[key]
            if key in self.terminal or e.earliest_step>self.step:continue
            if self.step>e.expires_step:status,payload='expired',None
            elif not e.dependencies<=self.completed:continue
            else:
                for dep in e.dependencies:
                    if not happens_before(self.events[dep].clock,e.clock):raise ContractError('CausalClockMismatch','dependency must strictly precede event vector clock')
                status,payload=staleness(e,current_versions,self.step,remaps)
            d=EventDecision(key,self.step,status,payload,e.clock.phase,(e.clock.path_id,e.clock.path_index));decisions.append(d);self.log.append(d)
            if status in ('ready','remapped'):self.completed.add(key);self.terminal.add(key)
            elif status in ('expired','stale_rejected'):self.terminal.add(key)
            # recompute/remap requests remain pending, not silently accepted.
        status='complete' if len(self.terminal)==len(self.events) else ('schedule_budget_exhausted' if self.step>=self.max_steps else 'pending')
        return tuple(decisions),status

def bind_dynamics_event(event,dynamics,*,readout_index):
    if event.source_state_version!=dynamics.version or not dynamics.readout_window[0]<=readout_index<dynamics.readout_window[1]:raise ContractError('VersionMismatch','H33 readout index and dynamics version must bind')
    return (event.clock.phase,readout_index,dynamics.version)
def bind_path_event(event,path,*,trajectory_version):
    if event.source_state_version!=trajectory_version or not 0<=event.clock.path_index<len(path):raise ContractError('VersionMismatch','H34 path index is not physical scheduling time')
    return path[event.clock.path_index]
def bind_transaction(event,transaction):
    requirements=dict(event.receiver_versions)
    if any(requirements.get(k)!=str(v) for k,v in transaction.read_versions):raise ContractError('VersionConflict','H39 read set requires exact event applicability versions')
    return transaction
