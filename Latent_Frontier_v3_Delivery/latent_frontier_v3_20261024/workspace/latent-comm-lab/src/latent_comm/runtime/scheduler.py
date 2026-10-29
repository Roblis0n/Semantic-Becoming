"""Finite causal scheduling for explicit standard-library fixtures only.

Callbacks are trusted source, not an OS sandbox. Research dispatch always enters
the immutable policy gate. No models are imported or callbacks inferred from IR.
"""
from __future__ import annotations
from dataclasses import dataclass, field, replace, asdict
import heapq
import json
from typing import Callable
from latent_comm.core import ContractError, StepBudget, Scope, VersionSet
from .journal import canonical, sha256
from .transactions import Transaction, VersionedStore

@dataclass(frozen=True)
class Clock:
    scheduler_step: int = 0
    cognitive_phase: str = 'initial'
    path_index: int = 0
    causal_time: int = 0
    def advance(self, *, phase: str,received_time: int=0):
        return Clock(self.scheduler_step+1,phase,self.path_index+1,max(self.causal_time,received_time)+1)

@dataclass(frozen=True)
class Event:
    event_id: str
    handler: str
    payload_json: str = '{}'
    due_time: int = 0
    causal_time: int = 0
    expected_versions: tuple[tuple[str,int],...] = ()
    attempt: int = 0
    def __post_init__(self):
        if not self.event_id or not self.handler or any(type(v) is not int or v<0 for v in (self.due_time,self.causal_time,self.attempt)):raise ContractError('InvalidEvent','event identity and nonnegative clock/attempt required')
        VersionedStore._validate_value(json.loads(self.payload_json))
        if len({k for k,v in self.expected_versions})!=len(self.expected_versions) or any(not isinstance(k,str) or type(v) is not int or v<0 for k,v in self.expected_versions):raise ContractError('InvalidEvent','invalid expected versions')
    def payload(self):return json.loads(self.payload_json)

@dataclass(frozen=True)
class Write:
    key: str
    value: object
    type_name: str
    component: str
    versions: VersionSet
    migration: str | None = None

@dataclass(frozen=True)
class EventResult:
    writes: tuple[Write,...] = ()
    emitted: tuple[Event,...] = ()
    phase: str = 'computed'
    termination_reason: str = 'completed'

@dataclass(frozen=True)
class RegisteredHandler:
    function: Callable[['ReadContext',Event],EventResult]
    action: str = 'stdlib_math_fixture'

class ReadContext:
    def __init__(self,transaction):self._transaction=transaction
    def read(self,key):return self._transaction.read(key)
    def exists(self,key):return self._transaction.exists(key)

@dataclass(frozen=True)
class RunSummary:
    status: str
    processed: int
    queued: int
    completed: tuple[str,...]
    failed: tuple[str,...]
    clock: Clock

class FiniteScheduler:
    def __init__(self,store, *, scope: Scope,actor: str,input_digest: str,budget=StepBudget(),max_queue=64,max_retries=3,same_error_retries=2):
        if type(max_queue) is not int or not 1<=max_queue<=64 or not 0<=max_retries<=3 or not 0<=same_error_retries<=2:raise ContractError('BudgetExhausted','queue/retry limits exceed finite policy')
        if not isinstance(input_digest,str) or not input_digest:raise ContractError('InvalidSchema','explicit input digest required')
        self.store=store;self.scope=scope;self.actor=actor;self.input_digest=input_digest;self.meter=budget.meter();self.max_queue=max_queue;self.max_retries=max_retries;self.same_error_retries=same_error_retries
        self.queue=[];self.sequence=0;self.seen=set();self.completed=set();self.failed=set();self.error_counts={};self.audit=[];self.clock=Clock();self.running=False
    def _can_enqueue(self,events):
        ids=[e.event_id for e in events]
        if len(self.queue)+len(events)>self.max_queue:raise ContractError('QueueFull','finite event queue exhausted')
        if len(set(ids))!=len(ids) or set(ids)&self.seen:raise ContractError('DuplicateEvent','event IDs must be unique')
        if len(self.seen)+len(ids)>64:raise ContractError('BudgetExhausted','finite event identity ledger exhausted')
    def enqueue(self,event: Event):
        self._can_enqueue((event,));self._push(event);self.seen.add(event.event_id)
    def _push(self,event):
        heapq.heappush(self.queue,(event.due_time,self.sequence,event));self.sequence+=1
    def _record(self,event,status,code='',writes=()):
        self.audit.append({'sequence':len(self.audit),'event_id':event.event_id,'attempt':event.attempt,'step':self.clock.scheduler_step,'causal_time':self.clock.causal_time,'status':status,'code':code,'writes':list(writes),'input_digest':self.input_digest,'store_digest':self.store.snapshot().digest})
    def run(self,handlers: dict[str,RegisteredHandler], *, max_events: int | None=None) -> RunSummary:
        if self.running:raise ContractError('ReentrantScheduler','one scheduler coordinator at a time')
        limit=self.meter.limit.max_steps if max_events is None else max_events
        if type(limit) is not int or not 0<=limit<=128:raise ContractError('BudgetExhausted','run slice must be 0..128')
        processed=0;status='complete';self.running=True
        try:
            for _ in range(limit):
                if not self.queue:break
                if self.meter.steps>=self.meter.limit.max_steps:status='budget_exhausted';break
                _,_,event=heapq.heappop(self.queue);self.meter.consume(steps=1);processed+=1
                self.clock=self.clock.advance(phase='dispatch',received_time=max(event.due_time,event.causal_time))
                tx=None
                try:
                    tx=self.store.begin(scope=self.scope,actor=self.actor,transaction_id='event:'+event.event_id,step=self.clock.scheduler_step)
                    if event.handler not in handlers:raise ContractError('UnboundHandler',event.handler)
                    handler=handlers[event.handler]
                    if handler.action!='stdlib_math_fixture':
                        from latent_comm.safety.policy import require_research_action
                        require_research_action(handler.action)
                    for key,version in event.expected_versions:
                        tx._observe(key)
                        if tx.snapshot.versions.get(key,0)!=version:raise ContractError('VersionConflict','event read-version dependency is stale',key)
                    result=handler.function(ReadContext(tx),event)
                    if not isinstance(result,EventResult):raise ContractError('InvalidEventResult','handler must return EventResult')
                    self._can_enqueue(result.emitted)
                    for write in result.writes:tx.write(write.key,write.value,type_name=write.type_name,component=write.component,versions=write.versions,migration=write.migration)
                    tx.commit()
                    for emitted in result.emitted:self.enqueue(emitted)
                    self.completed.add(event.event_id);self.clock=replace(self.clock,cognitive_phase=result.phase)
                    self._record(event,'done',result.termination_reason,tuple(w.key for w in result.writes))
                except ContractError as error:
                    if tx is not None and tx.state in {'active','prepared'}:tx.abort('event_rejected')
                    code=error.failure.code;key=(event.event_id,code);count=self.error_counts.get(key,0)+1;self.error_counts[key]=count
                    retry=error.failure.recoverable and event.attempt<self.max_retries and count<=self.same_error_retries
                    if retry:self._push(replace(event,attempt=event.attempt+1,due_time=self.clock.causal_time+1))
                    else:self.failed.add(event.event_id)
                    self._record(event,'retry' if retry else 'failed',code)
                except Exception as error:
                    if tx is not None and tx.state in {'active','prepared'}:tx.abort('handler_exception')
                    self.failed.add(event.event_id);self._record(event,'failed','HandlerError:'+type(error).__name__)
            if self.queue:status='budget_exhausted' if self.meter.steps>=self.meter.limit.max_steps else 'paused'
            elif self.failed:status='complete_with_failures'
            return RunSummary(status,processed,len(self.queue),tuple(sorted(self.completed)),tuple(sorted(self.failed)),self.clock)
        finally:self.running=False
    def checkpoint(self,workspace):
        if self.running:raise ContractError('CheckpointBoundary','only event boundaries are checkpointable')
        state={'format':1,'input_digest':self.input_digest,'store_digest':self.store.snapshot().digest,'clock':asdict(self.clock),'budget':asdict(self.meter.limit),'steps':self.meter.steps,'max_queue':self.max_queue,'max_retries':self.max_retries,'same_error_retries':self.same_error_retries,'queue':[{'sequence':seq,'event':asdict(e)} for _,seq,e in sorted(self.queue)],'sequence':self.sequence,'seen':sorted(self.seen),'completed':sorted(self.completed),'failed':sorted(self.failed),'error_counts':[[e,c,v] for (e,c),v in self.error_counts.items()],'audit':self.audit}
        return workspace.commit({'scheduler.json':canonical(state)},expected_generation=workspace.generation)
    @classmethod
    def resume(cls,workspace,store, *, scope,actor,input_digest):
        state=json.loads(workspace.read('scheduler.json'))
        if state.get('format')!=1 or state['input_digest']!=input_digest:raise ContractError('InputInvalidated','continuation inputs changed')
        if state['store_digest']!=store.snapshot().digest:raise ContractError('ContinuationConflict','store changed since safe checkpoint; reconcile rather than replay')
        self=cls(store,scope=scope,actor=actor,input_digest=input_digest,budget=StepBudget(**state['budget']),max_queue=state['max_queue'],max_retries=state['max_retries'],same_error_retries=state['same_error_retries'])
        self.meter.consume(steps=state['steps']);self.clock=Clock(**state['clock'])
        for item in state['queue']:
            raw=item['event'];raw['expected_versions']=tuple(tuple(p) for p in raw['expected_versions']);event=Event(**raw)
            self.enqueue(event)
        if type(state['sequence']) is not int or state['sequence']<len(self.queue):raise ContractError('JournalCorrupt','invalid queue sequence')
        self.sequence=state['sequence'];self.seen=set(state['seen']);self.completed=set(state['completed']);self.failed=set(state['failed']);self.error_counts={(e,c):v for e,c,v in state['error_counts']};self.audit=state['audit']
        queued={e.event_id for _,_,e in self.queue}
        if len(self.seen)>64 or not (queued|self.completed|self.failed)<=self.seen or queued&(self.completed|self.failed) or self.completed&self.failed or len(self.audit)>128:raise ContractError('JournalCorrupt','inconsistent event identity ledger')
        return self
