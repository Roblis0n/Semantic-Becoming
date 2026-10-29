from __future__ import annotations
import math
from dataclasses import replace
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import *

import json,hashlib,os,tempfile,threading
from pathlib import Path
from dataclasses import asdict

def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def _digest(value):return hashlib.sha256(_canonical(value).encode()).hexdigest()

class VersionedStore:
    """Single in-process coordinator; atomic JSON visibility, append-only journal."""
    def __init__(self,directory):
        self.root=Path(directory).resolve();self.root.mkdir(parents=True,exist_ok=True);self.path=self.root/'state.json';self.journal=self.root/'journal.jsonl';self.lock=threading.RLock()
        if not self.path.exists():self._publish({})
    def _publish(self,state):
        fd,name=tempfile.mkstemp(dir=self.root,prefix='.candidate-')
        try:
            with os.fdopen(fd,'w') as f:f.write(_canonical(state));f.flush();os.fsync(f.fileno())
            os.replace(name,self.path)
            descriptor=os.open(self.root,os.O_RDONLY)
            try:os.fsync(descriptor)
            finally:os.close(descriptor)
        finally:
            if os.path.exists(name):os.unlink(name)
    def _append(self,record):
        with self.journal.open('a') as f:f.write(_canonical(record)+'\n');f.flush();os.fsync(f.fileno())
    def snapshot(self):
        with self.lock:
            value=json.loads(self.path.read_text())
            return tuple(VersionedCell(**v) for _,v in sorted(value.items()))
    def commit(self,transaction,budget=StepBudget(),crash_at=None):
        with self.lock:
            state={c.key:asdict(c) for c in self.snapshot()};reads=dict(transaction.read_versions);meter=budget.meter()
            for key,expected in reads.items():
                meter.consume(steps=1)
                if state.get(key,{}).get('version',-1)!=expected:raise ContractError('VersionConflict',f'read dependency changed: {key}')
            topological_order(tuple(w.key for w in transaction.writes),transaction.migration_dependencies)
            candidate=dict(state)
            for cell in transaction.writes:
                if cell.version!=reads[cell.key]+1:raise ContractError('VersionConflict','write must advance exactly one version')
                if cell.key in state and state[cell.key]['type_tag']!=cell.type_tag:raise ContractError('PartialCommit','type change needs an explicitly new typed key')
                candidate[cell.key]=asdict(cell)
            before=_digest(state);after=_digest(candidate)
            records=self.records()
            if any(r['transaction_id']==transaction.transaction_id for r in records):raise ContractError('VersionConflict','transaction identity already journaled')
            prepare={'phase':'prepare','transaction_id':transaction.transaction_id,'before_digest':before,'after_digest':after,'before':state,'after':candidate}
            self._append(prepare)
            if crash_at=='after_prepare':raise ContractError('PartialCommit','injected interruption after durable prepare')
            self._publish(candidate)
            if crash_at=='after_publish':raise ContractError('PartialCommit','injected interruption after atomic publish')
            self._append({'phase':'commit','transaction_id':transaction.transaction_id,'after_digest':after})
            return CommitRecord(transaction.transaction_id,before,after,tuple(w.key for w in transaction.writes),'committed')
    def records(self):
        if not self.journal.exists():return []
        try:return [json.loads(line) for line in self.journal.read_text().splitlines() if line]
        except (ValueError,TypeError) as e:raise ContractError('JournalCorrupt','journal contains malformed record') from e
    def recover(self):
        with self.lock:
            records=self.records();completed={r['transaction_id'] for r in records if r['phase'] in ('commit','abort')};out=[]
            for r in records:
                if r['phase']!='prepare' or r['transaction_id'] in completed:continue
                if _digest(r['before'])!=r['before_digest'] or _digest(r['after'])!=r['after_digest']:raise ContractError('JournalCorrupt','journal content hash differs')
                current=_digest(json.loads(self.path.read_text()))
                if current==r['after_digest']:phase='commit'
                elif current==r['before_digest']:phase='abort'
                else:raise ContractError('JournalCorrupt','visible state matches neither atomic side')
                self._append({'phase':phase,'transaction_id':r['transaction_id'],'recovered':True});out.append((r['transaction_id'],phase))
            return tuple(out)
    def rollback(self,transaction_id,new_transaction_id):
        with self.lock:
            record=next((r for r in self.records() if r['transaction_id']==transaction_id and r['phase']=='prepare'),None)
            if record is None:raise ContractError('JournalCorrupt','rollback preparation not found')
            current={c.key:asdict(c) for c in self.snapshot()}
            if _digest(current)!=record['after_digest']:raise ContractError('VersionConflict','cannot rollback over later state')
            if set(record['before'])!=set(current):raise ContractError('NonReversibleEffect','key creation rollback requires explicit tombstone migration')
            writes=tuple(VersionedCell(k,v['type_tag'],current[k]['version']+1,v['payload_json']) for k,v in record['before'].items())
            return self.commit(CognitiveTransaction(new_transaction_id,tuple((k,v['version']) for k,v in current.items()),writes))
