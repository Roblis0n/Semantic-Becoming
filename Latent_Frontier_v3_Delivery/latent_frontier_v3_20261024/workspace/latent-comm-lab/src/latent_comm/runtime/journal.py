"""Bounded hash-chained write-ahead journal with torn-tail recovery."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from threading import RLock
from latent_comm.core import ContractError

def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',',':'), ensure_ascii=False, allow_nan=False).encode('utf-8')

def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

@dataclass(frozen=True)
class JournalScan:
    records: tuple[dict, ...]
    valid_bytes: int
    torn_tail: bool

class Journal:
    def __init__(self, path: Path | str, *, max_records: int = 128):
        if type(max_records) is not int or not 1 <= max_records <= 128: raise ContractError('BudgetExhausted','journal fixture limit must be 1..128')
        self.path = Path(path); self.max_records = max_records; self.lock = RLock()
        if self.path.is_symlink(): raise ContractError('UnsafePath','journal cannot be a symlink')
        self.path.parent.mkdir(parents=True, exist_ok=True)
    def scan(self) -> JournalScan:
        data = self.path.read_bytes() if self.path.exists() else b''
        records = []; previous = '0'*64; valid_bytes = 0
        for line in data.splitlines(keepends=True):
            if not line.endswith(b'\n'): return JournalScan(tuple(records), valid_bytes, True)
            if len(records) >= self.max_records: raise ContractError('BudgetExhausted','journal recovery limit exceeded')
            try:
                record = json.loads(line); digest = record.pop('sha256')
                if record['seq'] != len(records) or record['previous_hash'] != previous or sha256(canonical(record)) != digest: raise ValueError('broken hash chain')
                if not isinstance(record['kind'],str) or not isinstance(record['payload'],dict): raise ValueError('invalid event shape')
            except (ValueError,KeyError,TypeError) as error: raise ContractError('JournalCorrupt',str(error),str(self.path)) from error
            record['sha256'] = digest; records.append(record); previous = digest; valid_bytes += len(line)
        return JournalScan(tuple(records), valid_bytes, False)
    def repair_torn_tail(self) -> bool:
        with self.lock:
            scan = self.scan()
            if scan.torn_tail:
                with self.path.open('r+b') as stream: stream.truncate(scan.valid_bytes); stream.flush(); os.fsync(stream.fileno())
            return scan.torn_tail
    def append(self, kind: str, transaction_id: str, payload: dict) -> dict:
        with self.lock:
            scan = self.scan()
            if scan.torn_tail: raise ContractError('RecoveryRequired','repair incomplete tail before append')
            if len(scan.records) >= self.max_records: raise ContractError('BudgetExhausted','journal capacity exhausted')
            record = {'seq':len(scan.records),'kind':kind,'transaction_id':transaction_id,'payload':payload,'previous_hash':scan.records[-1]['sha256'] if scan.records else '0'*64}
            record['sha256'] = sha256(canonical(record))
            with self.path.open('ab') as stream: stream.write(canonical(record)+b'\n'); stream.flush(); os.fsync(stream.fileno())
            return record
