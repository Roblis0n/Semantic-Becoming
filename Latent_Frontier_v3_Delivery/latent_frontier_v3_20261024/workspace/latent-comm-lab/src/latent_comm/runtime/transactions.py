"""Optimistic serializable read/write-set transactions over local research state."""
from __future__ import annotations
from dataclasses import dataclass
from threading import RLock
from types import MappingProxyType
import json
import uuid
from latent_comm.core import ContractError, Scope, VersionSet
from latent_comm.core.scopes import RESEARCH_COMPONENTS
from latent_comm.core.views import FORBIDDEN_FIELDS
from .files import AtomicWorkspace
from .journal import canonical, sha256

@dataclass(frozen=True)
class Cell:
    value_json: str
    type_name: str
    version: int
    component: str
    versions: VersionSet
    def value(self): return json.loads(self.value_json)
    def to_dict(self): return {'value':json.loads(self.value_json),'type_name':self.type_name,'version':self.version,'component':self.component,'versions':self.versions.as_dict()}

@dataclass(frozen=True)
class Snapshot:
    revision: int
    cells: MappingProxyType
    versions: MappingProxyType
    digest: str

@dataclass(frozen=True)
class CommitRecord:
    transaction_id: str
    revision: int
    input_digest: str
    output_digest: str
    read_versions: tuple[tuple[str,int],...]
    writes: tuple[str,...]
    termination_reason: str

class VersionedStore:
    def __init__(self, workspace: AtomicWorkspace | None=None, *, max_objects: int=64):
        if type(max_objects) is not int or not 1<=max_objects<=64: raise ContractError('BudgetExhausted','finite store needs 1..64 objects')
        self.lock=RLock();self.workspace=workspace;self.max_objects=max_objects;self._cells={};self._versions={};self.revision=0;self.history=[];self.terminal_ids=set()
        if workspace and 'store.json' in workspace.files: self._restore(json.loads(workspace.read('store.json')))
    def _restore(self,state):
        if state.get('format')!=1 or type(state.get('revision')) is not int or state['revision']<0: raise ContractError('JournalCorrupt','invalid store snapshot')
        cells={}
        for key,value in state['cells'].items():
            self._validate_key(key); self._validate_value(value['value'])
            if type(value['version']) is not int or value['version']<=0 or value['component'] not in RESEARCH_COMPONENTS or not value['type_name']: raise ContractError('JournalCorrupt','invalid cell version/type/component')
            cells[key]=Cell(canonical(value['value']).decode(),value['type_name'],value['version'],value['component'],VersionSet(**value['versions']))
        if len(cells)>self.max_objects: raise ContractError('BudgetExhausted','restored store exceeds bound')
        versions=state.get('key_versions',{})
        if any(not isinstance(k,str) or type(v) is not int or v<=0 for k,v in versions.items()) or any(versions.get(k)!=v.version for k,v in cells.items()):raise ContractError('JournalCorrupt','invalid monotonic key versions')
        self._cells=cells;self._versions=dict(versions);self.revision=state['revision'];self.terminal_ids=set(state.get('terminal_ids',[]))
        if len(self.terminal_ids)>64 or any(not isinstance(t,str) or not t for t in self.terminal_ids) or len(versions)>64:raise ContractError('JournalCorrupt','invalid finite version/transaction ledger')
    @staticmethod
    def _validate_key(key):
        if not isinstance(key,str) or ':' not in key or len(key)>256: raise ContractError('UnboundReference','store keys must be namespaced identities')
    @staticmethod
    def _validate_value(value):
        def walk(x, depth=0):
            if depth>32: raise ContractError('BudgetExhausted','value nesting exceeds 32')
            if isinstance(x,dict):
                if any(not isinstance(k,str) for k in x): raise ContractError('InvalidSchema','object keys must be strings')
                bad=set(x)&(FORBIDDEN_FIELDS|{'password','api_key','secret','access_token','refresh_token'})
                if bad: raise ContractError('RoleLeakage','runtime persistence accepts sanitized local state, not secret/supervision payloads')
                for v in x.values():walk(v,depth+1)
            elif isinstance(x,(tuple,list)):
                if len(x)>64: raise ContractError('BudgetExhausted','finite value array exceeds 64')
                for v in x:walk(v,depth+1)
            elif not (x is None or isinstance(x,(str,int,float,bool))): raise ContractError('InvalidSchema','only JSON values may be persisted')
        walk(value); encoded=canonical(value)
        if len(encoded)>65536: raise ContractError('BudgetExhausted','finite object exceeds 64 KiB')
    def export(self):
        return {'format':1,'revision':self.revision,'cells':{k:v.to_dict() for k,v in sorted(self._cells.items())},'terminal_ids':sorted(self.terminal_ids),'key_versions':dict(self._versions)}
    def snapshot(self) -> Snapshot:
        with self.lock:
            if self.workspace:self.workspace._ensure()
            state={'key_versions':dict(self._versions),'revision':self.revision,'cells':{k:v.to_dict() for k,v in sorted(self._cells.items())}}
            return Snapshot(self.revision,MappingProxyType(dict(self._cells)),MappingProxyType(dict(self._versions)),sha256(canonical(state)))
    def begin(self, *, scope: Scope, actor: str, transaction_id: str | None=None, step: int=0) -> 'Transaction':
        scope.check(actor,step=step)
        return Transaction(self,self.snapshot(),scope,actor,transaction_id or uuid.uuid4().hex,step=step)
    def recover(self):
        if not self.workspace: raise ContractError('RecoveryUnavailable','in-memory store has no durable journal')
        with self.lock:
            report=self.workspace.recover()
            if 'store.json' in self.workspace.files:self._restore(json.loads(self.workspace.read('store.json')))
            else:self._cells={};self._versions={};self.revision=0;self.terminal_ids=set()
            return report

class Transaction:
    def __init__(self, store, snapshot, scope, actor, transaction_id, step=0):
        self.step=step;self.store=store;self.snapshot=snapshot;self.scope=scope;self.actor=actor;self.transaction_id=transaction_id;self.read_versions={};self.pending={};self.state='active';self.migrations=[]
    def _active(self):
        if self.state not in {'active','prepared'}: raise ContractError('TransactionClosed',self.state)
    def _observe(self,key):
        self.store._validate_key(key);self.scope.check(self.actor,object_id=key,step=self.step)
        cell=self.snapshot.cells.get(key);self.read_versions.setdefault(key,self.snapshot.versions.get(key,0))
        return cell
    def read(self,key):
        self._active();cell=self._observe(key)
        if key in self.pending:cell=self.pending[key]
        if cell is None: raise ContractError('UnboundReference','missing state object',key)
        return cell.value()
    def exists(self,key):
        self._active();cell=self._observe(key);return self.pending.get(key,cell) is not None
    def write(self,key,value, *, type_name: str,component: str,versions: VersionSet,migration: str | None=None):
        self._active();self.store._validate_value(value)
        if not isinstance(type_name,str) or not type_name: raise ContractError('InvalidSchema','explicit cell type required')
        self.scope.check(self.actor,object_id=key,writes=frozenset({component}),step=self.step)
        old=self._observe(key)
        if old is not None and (old.type_name!=type_name or old.versions!=versions or old.component!=component):
            if not isinstance(migration,str) or not migration:raise ContractError('MigrationRequired','type/version/component changes require a named migration',key)
            self.scope.check(self.actor,object_id=key,writes=frozenset({old.component}),step=self.step)
            self.migrations.append((key,migration))
        version=self.snapshot.versions.get(key,0)+1
        self.pending[key]=Cell(canonical(value).decode(),type_name,version,component,versions);self.state='active'
    def delete(self,key):
        self._active();old=self._observe(key);current=self.pending.get(key,old)
        if current is None:raise ContractError('UnboundReference','delete missing object',key)
        self.scope.check(self.actor,object_id=key,writes=frozenset({current.component}),step=self.step)
        if old is None:self.pending.pop(key,None)
        else:self.pending[key]=None
        self.state='active'
    def external_effect(self,kind,*args,**kwargs):
        raise ContractError('NonReversibleEffect','external messages, payments, publication and host effects are outside cognitive/file transactions',str(kind))
    def _validate(self):
        self._active()
        if self.transaction_id in self.store.terminal_ids:raise ContractError('TransactionReused','transaction already committed')
        for key,version in self.read_versions.items():
            actual=self.store._versions.get(key,0)
            if actual!=version:raise ContractError('VersionConflict',f'expected {version}, found {actual}',key,recoverable=True,obligations=('explicitly rebase and recompute',))
    def prepare(self) -> str:
        with self.store.lock:
            self._validate();self.state='prepared'
            return sha256(canonical({'snapshot':self.snapshot.digest,'read_versions':self.read_versions,'writes':{k:v.to_dict() if v else None for k,v in self.pending.items()}}))
    def commit(self, *, crash_at: str | None=None) -> CommitRecord:
        with self.store.lock:
            try:self._validate()
            except ContractError as error:
                self.state='conflict'
                self.store.history.append(CommitRecord(self.transaction_id,self.store.revision,self.snapshot.digest,self.store.snapshot().digest,tuple(sorted(self.read_versions.items())),tuple(sorted(self.pending)),'conflict:'+error.failure.code))
                raise
            candidate=dict(self.store._cells)
            for key,cell in self.pending.items():
                if cell is None:candidate.pop(key,None)
                else:candidate[key]=cell
            if len(candidate)>self.store.max_objects:raise ContractError('BudgetExhausted','store object count exhausted')
            key_versions=dict(self.store._versions)
            for key in self.pending:key_versions[key]=key_versions.get(key,0)+1
            if len(key_versions)>64:raise ContractError('BudgetExhausted','finite tombstone index exhausted')
            revision=self.store.revision+1;ids=self.store.terminal_ids|{self.transaction_id}
            if len(ids)>64:raise ContractError('BudgetExhausted','finite commit identity ledger exhausted')
            state={'format':1,'revision':revision,'cells':{k:v.to_dict() for k,v in sorted(candidate.items())},'terminal_ids':sorted(ids),'key_versions':key_versions}
            if self.store.workspace:
                try:self.store.workspace.commit({'store.json':canonical(state)},expected_generation=self.store.workspace.generation,transaction_id=self.transaction_id,crash_at=crash_at)
                except BaseException:self.state='recovery_required';raise
            self.store._cells=candidate;self.store._versions=key_versions;self.store.revision=revision;self.store.terminal_ids=ids;self.state='committed'
            result=CommitRecord(self.transaction_id,revision,self.snapshot.digest,self.store.snapshot().digest,tuple(sorted(self.read_versions.items())),tuple(sorted(self.pending)),'committed')
            self.store.history.append(result);return result
    def abort(self,reason='aborted'):
        self._active();self.pending.clear();self.state='aborted'
        record=CommitRecord(self.transaction_id,self.store.revision,self.snapshot.digest,self.store.snapshot().digest,tuple(sorted(self.read_versions.items())),(),reason)
        self.store.history.append(record);return record
