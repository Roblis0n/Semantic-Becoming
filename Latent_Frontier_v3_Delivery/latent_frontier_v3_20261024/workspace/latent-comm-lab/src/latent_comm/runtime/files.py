"""Single-coordinator generational file transactions, not cross-filesystem atomicity.

Readers use this API/CURRENT. Immutable generations plus one atomic pointer make
multi-file state visible as a unit. An fsynced COMMIT is the recovery decision.
"""
from __future__ import annotations
try:
    import fcntl
except ImportError:
    fcntl = None
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from threading import RLock
import uuid
from latent_comm.core import ContractError
from .journal import Journal, canonical, sha256

class SimulatedCrash(RuntimeError):
    """Finite fault-injection signal; no real process or OS crash is induced."""

def atomic_bytes(path: Path, data: bytes) -> None:
    if path.is_symlink(): raise ContractError('UnsafePath','refusing to replace symlink',str(path))
    fd, temp = tempfile.mkstemp(prefix='.'+path.name, dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp,path)
        directory = os.open(path.parent,os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(temp): os.unlink(temp)

class AtomicWorkspace:
    def __init__(self, root: Path | str, *, max_files: int = 64, max_bytes: int = 2_000_000):
        if fcntl is None:
            raise ContractError('UnsupportedPlatform','durable AtomicWorkspace requires POSIX advisory locking')
        self.root = Path(root)
        if self.root.is_symlink() or any(p.is_symlink() for p in self.root.parents): raise ContractError('UnsafePath','root/ancestors cannot be symlinks')
        if type(max_files) is not int or not 1 <= max_files <= 64 or type(max_bytes) is not int or max_bytes <= 0: raise ContractError('BudgetExhausted','invalid file transaction bounds')
        self.root.mkdir(parents=True, exist_ok=True); self.max_files=max_files; self.max_bytes=max_bytes; self.lock=RLock(); self.dirty=False; self.closed=False
        for name in ('generations','writer.lock','CURRENT','journal.jsonl'):
            if (self.root/name).is_symlink(): raise ContractError('UnsafePath','transaction paths cannot be symlinks',name)
        (self.root/'generations').mkdir(exist_ok=True)
        self.owner=(self.root/'writer.lock').open('a+b')
        try: fcntl.flock(self.owner,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self.owner.close(); raise ContractError('CoordinatorBusy','one coordinator may own a workspace') from error
        self.journal=Journal(self.root/'journal.jsonl')
        try: self.recover()
        except BaseException: self.close(); raise
    def close(self):
        if not self.closed:
            fcntl.flock(self.owner,fcntl.LOCK_UN); self.owner.close(); self.closed=True
    def __enter__(self): return self
    def __exit__(self,*args): self.close()
    def _ensure(self):
        if self.closed: raise ContractError('CoordinatorClosed','workspace coordinator is closed')
        if self.dirty: raise ContractError('RecoveryRequired','interrupted commit requires recovery')
    @staticmethod
    def _name(name: str) -> str:
        if not isinstance(name,str) or not name or '\\' in name or '\x00' in name: raise ContractError('UnsafePath','invalid logical path')
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '.' in path.parts or str(path)!=name: raise ContractError('UnsafePath','only normalized relative paths are permitted',name)
        return name
    def _load(self, generation: str) -> dict[str,bytes]:
        if not isinstance(generation,str) or len(generation)!=64 or any(c not in '0123456789abcdef' for c in generation): raise ContractError('JournalCorrupt','invalid generation identity')
        path=self.root/'generations'/generation
        if path.is_symlink(): raise ContractError('UnsafePath','generation is a symlink')
        try: encoded=path.read_bytes(); manifest=json.loads(encoded)
        except (OSError,ValueError) as error: raise ContractError('JournalCorrupt','missing/corrupt committed generation',generation) from error
        if sha256(encoded)!=generation: raise ContractError('JournalCorrupt','generation hash mismatch',generation)
        if manifest.get('format')!=1 or not isinstance(manifest.get('files'),dict): raise ContractError('JournalCorrupt','generation schema')
        result={}
        for name,item in manifest['files'].items():
            self._name(name)
            try: data=bytes.fromhex(item['hex'])
            except (ValueError,KeyError,TypeError) as error: raise ContractError('JournalCorrupt','invalid file encoding',name) from error
            if sha256(data)!=item['sha256']: raise ContractError('JournalCorrupt','file checksum mismatch',name)
            result[name]=data
        if len(result)>self.max_files or sum(map(len,result.values()))>self.max_bytes: raise ContractError('BudgetExhausted','generation exceeds declared bounds')
        return result
    def recover(self) -> dict:
        with self.lock:
            if self.closed: raise ContractError('CoordinatorClosed','closed')
            torn=self.journal.repair_torn_tail(); scan=self.journal.scan(); prepared={}; committed=set(); head=None
            for event in scan.records:
                tid=event['transaction_id']; payload=event['payload']
                if event['kind']=='PREPARE':
                    if tid in prepared: raise ContractError('JournalCorrupt','duplicate prepare')
                    prepared[tid]=payload
                elif event['kind']=='COMMIT':
                    if tid not in prepared or tid in committed or payload!=prepared[tid] or payload['parent']!=head: raise ContractError('JournalCorrupt','invalid commit lineage')
                    self._load(payload['generation']); head=payload['generation']; committed.add(tid)
                else: raise ContractError('JournalCorrupt','unexpected file journal event')
            self.generation=head; self.files={} if head is None else self._load(head)
            atomic_bytes(self.root/'CURRENT',canonical({'generation':head})); self.dirty=False
            return {'generation':head,'torn_tail_removed':torn,'aborted_prepares':sorted(set(prepared)-committed),'research_state':'NOT_RUN'}
    def read(self,name: str) -> bytes:
        with self.lock:
            self._ensure(); name=self._name(name)
            if name not in self.files: raise ContractError('UnboundReference','file not in committed generation',name)
            return bytes(self.files[name])
    def commit(self, changes: dict[str,bytes | str | None], *, expected_generation: str | None, transaction_id: str | None=None, crash_at: str | None=None) -> str:
        with self.lock:
            self._ensure()
            if expected_generation!=self.generation: raise ContractError('VersionConflict','file generation changed')
            if not changes or len(changes)>self.max_files: raise ContractError('BudgetExhausted','empty/oversized file write set')
            candidate=dict(self.files)
            for name,value in changes.items():
                name=self._name(name)
                if value is None:
                    if name not in candidate: raise ContractError('UnboundReference','delete target does not exist',name)
                    del candidate[name]
                elif isinstance(value,(str,bytes)): candidate[name]=value.encode() if isinstance(value,str) else value
                else: raise ContractError('InvalidSchema','file content must be bytes or text')
            if len(candidate)>self.max_files or sum(map(len,candidate.values()))>self.max_bytes: raise ContractError('BudgetExhausted','file transaction bounds exceeded')
            if len(self.journal.scan().records)+2>self.journal.max_records: raise ContractError('BudgetExhausted','insufficient journal capacity for prepare and commit')
            tid=transaction_id or uuid.uuid4().hex
            if any(x['transaction_id']==tid for x in self.journal.scan().records): raise ContractError('TransactionReused','transaction identity already present')
            data=canonical({'format':1,'files':{k:{'sha256':sha256(v),'hex':v.hex()} for k,v in sorted(candidate.items())}}); generation=sha256(data)
            path=self.root/'generations'/generation
            if not path.exists(): atomic_bytes(path,data)
            else: self._load(generation)
            payload={'generation':generation,'parent':self.generation}
            self.dirty=True
            self.journal.append('PREPARE',tid,payload)
            if crash_at=='after_prepare': raise SimulatedCrash(crash_at)
            self.journal.append('COMMIT',tid,payload)
            if crash_at=='after_commit': raise SimulatedCrash(crash_at)
            atomic_bytes(self.root/'CURRENT',canonical({'generation':generation}))
            if crash_at=='after_publish': raise SimulatedCrash(crash_at)
            self.files=candidate;self.generation=generation;self.dirty=False
            return generation
