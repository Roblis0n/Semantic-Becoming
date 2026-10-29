from dataclasses import asdict,replace
import json,hashlib
from latent_comm.core import ContractError,VersionSet
from .types import PersistentCapsule,QueryResult

def build_capsule(observations,*,capsule_id,document_id,version,query_family,evidence,dependencies,expires_step,versions,parent_version=None,capsule_dependencies=()):
    # Encoder receives evidence only. No future query or answer argument exists.
    return PersistentCapsule(capsule_id,document_id,version,parent_version,tuple(sorted(observations.items())),frozenset(query_family),frozenset(evidence),tuple(sorted(dependencies.items())),expires_step,versions,tuple(capsule_dependencies))
def read_query(capsule,query,*,step,versions,current_dependencies,withdrawn=frozenset()):
    if step>capsule.expires_step or capsule.evidence_handles&withdrawn:raise ContractError('ExpiredCapsule','expired or retracted evidence')
    if not capsule.versions.matches(versions,('ontology','world','evidence','task')) or any(current_dependencies.get(k)!=v for k,v in capsule.dependency_versions):raise ContractError('MigrationRequired','old object remains readable but not valid for this world')
    kind,key=query;values=dict(capsule.observations)
    if kind not in capsule.allowed_query_family:return QueryResult(None,'outside_compression_task_family',True,capsule.version)
    if kind=='lookup':
        if key not in values:return QueryResult(None,'missing_retained_detail',True,capsule.version)
        value=values[key]
    elif kind=='sum':value=sum(values.values())
    elif kind=='mean':
        if not values:return QueryResult(None,'empty_observation_set',False,capsule.version)
        value=sum(values.values())/len(values)
    elif kind=='max':
        if not values:return QueryResult(None,'empty_observation_set',False,capsule.version)
        value=max(values.values())
    else:return QueryResult(None,'unsupported_query_operator',True,capsule.version)
    return QueryResult(value,'answered_from_capsule',False,capsule.version)
def cache_key(capsule,query):
    raw=json.dumps({'capsule':capsule.capsule_id,'version':capsule.version,'query':query,'dependencies':capsule.dependency_versions,'capsule_dependencies':capsule.capsule_dependencies},sort_keys=True).encode()
    return capsule.versions.cache_key(hashlib.sha256(raw).hexdigest(),{},('ontology','world','evidence','task'))
class CapsuleStore:
    def __init__(self):self.entries={};self.invalidated=set()
    def add(self,capsule):
        key=(capsule.document_id,capsule.version)
        if key in self.entries:raise ContractError('VersionConflict','never overwrite a capsule version')
        if capsule.parent_version is not None and (capsule.document_id,capsule.parent_version) not in self.entries:raise ContractError('MissingAncestor','parent capsule required')
        if any(dep not in self.entries or dep in self.invalidated for dep in capsule.capsule_dependencies):raise ContractError('MissingSource','capsule source dependency must exist and remain valid')
        self.entries[key]=capsule
    def withdraw(self,evidence):
        impacted={k for k,v in self.entries.items() if v.evidence_handles&set(evidence)};self.invalidated|=impacted
        changed=True
        while changed:
            descendants={k for k,v in self.entries.items() if set(v.capsule_dependencies)&self.invalidated}-self.invalidated
            changed=bool(descendants);self.invalidated|=descendants;impacted|=descendants
        return tuple(sorted(impacted))
    def get(self,document_id,version):
        key=(document_id,version)
        if key in self.invalidated:raise ContractError('RetractedCapsule','source withdrawn')
        if key not in self.entries:raise ContractError('UnknownCapsule','missing version')
        return self.entries[key]
    def persist(self,workspace):
        rows=[]
        for key,c in sorted(self.entries.items()):
            row=asdict(c);row['allowed_query_family']=sorted(c.allowed_query_family);row['evidence_handles']=sorted(c.evidence_handles);rows.append(row)
        payload=json.dumps({'entries':rows,'invalidated':sorted(self.invalidated)},sort_keys=True,allow_nan=False)
        return workspace.commit({'capsules.json':payload},expected_generation=workspace.generation)
    @classmethod
    def restore(cls,workspace):
        obj=json.loads(workspace.read('capsules.json'));store=cls()
        pending=list(obj['entries'])
        while pending:
            ready=[row for row in pending if (row['parent_version'] is None or (row['document_id'],row['parent_version']) in store.entries) and all(tuple(dep) in store.entries for dep in row.get('capsule_dependencies',()))]
            if not ready:raise ContractError('MissingAncestor','stored capsule ancestry/dependencies missing or cyclic')
            for original in ready:
                pending.remove(original);row=dict(original);row['versions']=VersionSet(**row['versions']);row['observations']=tuple(tuple(v) for v in row['observations']);row['dependency_versions']=tuple(tuple(v) for v in row['dependency_versions']);row['capsule_dependencies']=tuple(tuple(v) for v in row.get('capsule_dependencies',()));row['allowed_query_family']=frozenset(row['allowed_query_family']);row['evidence_handles']=frozenset(row['evidence_handles'])
                store.add(PersistentCapsule(**row))
        store.invalidated={tuple(v) for v in obj['invalidated']}
        if not store.invalidated<=store.entries.keys():raise ContractError('UnknownCapsule','stored invalidation references missing capsule')
        changed=True
        while changed:
            descendants={k for k,v in store.entries.items() if set(v.capsule_dependencies)&store.invalidated}-store.invalidated;changed=bool(descendants);store.invalidated|=descendants
        return store
