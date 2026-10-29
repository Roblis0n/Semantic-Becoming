"""Content-addressed task receipts and transitive input-change invalidation.

This is a reusable runtime index, not the coordinator's shared authoring ledger.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from latent_comm.core import ContractError
from .journal import canonical, sha256
from .files import atomic_bytes

STATUSES=frozenset({'pending','running','done','blocked','failed','cancelled'})

@dataclass(frozen=True)
class ArtifactRecord:
    task_id: str
    dependencies: tuple[str,...]
    input_digest: str
    status: str = 'pending'
    outputs: tuple[tuple[str,str],...] = ()
    checks: tuple[str,...] = ()
    reason: str = ''

class DependencyIndex:
    def __init__(self,root: Path | str, *, max_tasks=64):
        if type(max_tasks) is not int or not 1<=max_tasks<=64:raise ContractError('BudgetExhausted','task graph limit must be 1..64')
        self.root=Path(root).resolve();self.max_tasks=max_tasks;self.records={};self.audit=[]
    def _path(self,name):
        path=self.root/name
        if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(self.root):raise ContractError('UnsafePath','artifact must remain in owned root',str(name))
        return path
    def add(self,task_id,dependencies,input_digest):
        dependencies=tuple(dependencies)
        if not isinstance(task_id,str) or not task_id or task_id in self.records:raise ContractError('DuplicateTask','task identities must be unique')
        if len(self.records)>=self.max_tasks:raise ContractError('BudgetExhausted','task graph capacity exceeded')
        if len(set(dependencies))!=len(dependencies) or any(d not in self.records for d in dependencies):raise ContractError('UnboundDependency','register predecessor tasks first')
        if not isinstance(input_digest,str) or not input_digest:raise ContractError('InvalidSchema','input digest required')
        self.records[task_id]=ArtifactRecord(task_id,dependencies,input_digest)
    def _replace(self,task_id,**changes):
        from dataclasses import replace
        if task_id not in self.records:raise ContractError('UnboundReference','task not registered',task_id)
        record=replace(self.records[task_id],**changes);self.records[task_id]=record
        self.audit.append({'task_id':task_id,'status':record.status,'reason':record.reason,'input_digest':record.input_digest,'outputs':[name for name,_ in record.outputs]})
        return record
    def ready(self):
        return tuple(k for k,r in self.records.items() if r.status=='pending' and all(self.records[d].status=='done' for d in r.dependencies))
    def start(self,task_id):
        self.verify_outputs()
        if task_id not in self.ready():raise ContractError('DependenciesNotReady','task is not ready',task_id)
        return self._replace(task_id,status='running',reason='')
    def finish(self,task_id,output_paths,checks, *, expected_input_digest):
        self.verify_outputs()
        record=self.records[task_id]
        if record.status!='running':raise ContractError('InvalidTransition','only running tasks may finish')
        if record.input_digest!=expected_input_digest:raise ContractError('InputInvalidated','task inputs changed during work')
        if not output_paths or not checks:raise ContractError('UnverifiedCompletion','done requires outputs and actual check evidence')
        for check in checks:
            path=self._path(check)
            if not path.is_file() or path.stat().st_size==0:raise ContractError('MissingCheck','actual check evidence absent',check)
        outputs=[]
        for name in tuple(output_paths)+tuple(checks):
            path=self._path(name)
            if not path.is_file() or path.stat().st_size==0:raise ContractError('MissingArtifact','missing/empty output',name)
            outputs.append((name,sha256(path.read_bytes())))
        return self._replace(task_id,status='done',outputs=tuple(sorted(set(outputs))),checks=tuple(checks),reason='verified_source_or_fixture_only')
    def terminal(self,task_id,status,reason):
        if status not in {'blocked','failed','cancelled'} or not isinstance(reason,str) or not reason:raise ContractError('InvalidTransition','terminal failure requires a specific reason')
        if self.records[task_id].status=='done':raise ContractError('InvalidTransition','invalidate completed tasks before changing state')
        return self._replace(task_id,status=status,reason=reason)
    def invalidate(self,changed: dict[str,str], *, reason='input_digest_changed'):
        unknown=set(changed)-self.records.keys()
        if unknown:raise ContractError('UnboundReference','unknown changed task: '+str(sorted(unknown)))
        invalid={k for k,v in changed.items() if self.records[k].input_digest!=v}
        for _ in range(len(self.records)):
            descendants={k for k,r in self.records.items() if set(r.dependencies)&invalid}
            expanded=invalid|descendants
            if expanded==invalid:break
            invalid=expanded
        for key in sorted(invalid):self._replace(key,status='pending',outputs=(),checks=(),input_digest=changed.get(key,self.records[key].input_digest),reason=reason)
        return tuple(sorted(invalid))
    def verify_outputs(self):
        broken=[]
        for key,record in self.records.items():
            if record.status!='done':continue
            if not record.outputs or not record.checks:broken.append(key);continue
            for name,digest in record.outputs:
                path=self._path(name)
                if not path.is_file() or sha256(path.read_bytes())!=digest:broken.append(key);break
        if broken:
            # Version the observation, rather than accepting an unchanged input digest.
            changed={k:sha256(canonical({'prior':self.records[k].input_digest,'changed_artifact':k,'observed':[sha256(self._path(p).read_bytes()) if self._path(p).is_file() else 'missing' for p,_ in self.records[k].outputs]})) for k in broken}
            return self.invalidate(changed,reason='artifact_hash_changed')
        return ()
    def save(self,path):
        path=self._path(path);path.parent.mkdir(parents=True,exist_ok=True)
        body={'format':1,'max_tasks':self.max_tasks,'records':[asdict(r) for r in self.records.values()],'audit':self.audit,'research_state':'NOT_RUN'}
        atomic_bytes(path,canonical({'body':body,'sha256':sha256(canonical(body))}))
    @classmethod
    def resume(cls,root,path, *, current_inputs=None):
        self=cls(root);state=json.loads(self._path(path).read_bytes());body=state['body']
        if sha256(canonical(body))!=state['sha256'] or body.get('format')!=1:raise ContractError('JournalCorrupt','dependency checkpoint checksum/schema')
        if type(body['max_tasks']) is not int or not 1<=body['max_tasks']<=64:raise ContractError('JournalCorrupt','invalid task graph bound')
        self.max_tasks=body['max_tasks']
        for raw in body['records']:
            self.add(raw['task_id'],raw['dependencies'],raw['input_digest'])
            if raw['status'] not in STATUSES:raise ContractError('JournalCorrupt','invalid task state')
            self.records[raw['task_id']]=ArtifactRecord(raw['task_id'],tuple(raw['dependencies']),raw['input_digest'],raw['status'],tuple(tuple(p) for p in raw['outputs']),tuple(raw['checks']),raw['reason'])
        self.audit=list(body['audit']);self.verify_outputs()
        if current_inputs:self.invalidate(current_inputs)
        for key,r in tuple(self.records.items()):
            if r.status=='running':self._replace(key,status='pending',reason='interrupted_before_verified_commit')
        return self
