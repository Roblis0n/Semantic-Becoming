"""Immutable program-family partitions before sampling any instance or seed."""
from dataclasses import dataclass,asdict
import hashlib
import json
import re
from latent_comm.core import ContractError,ErrorCode
from .records import SplitProvenance

@dataclass(frozen=True)
class StructureSignature:
    family: str
    generator_version: str
    program_template: str
    causal_template: tuple[tuple[str,str],...] = ()
    concept_combination: tuple[str,...] = ()
    operation_family: tuple[str,...] = ()
    def __post_init__(self) -> None:
        if not self.family or not self.generator_version or not self.program_template:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'structure requires family, generator version and canonical template')
    def canonical(self) -> dict:
        return {'family':self.family,'generator_version':self.generator_version,'program_template':self.program_template,
                'causal_template':sorted(self.causal_template),'concept_combination':sorted(self.concept_combination),'operation_family':sorted(self.operation_family)}
    @property
    def digest(self) -> str:
        return hashlib.sha256(json.dumps(self.canonical(),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    @property
    def partition_digest(self) -> str:
        # Generator revision remains in provenance, but cannot independently
        # place the same structural template into different data partitions.
        structural=self.canonical()
        del structural['generator_version']
        return hashlib.sha256(json.dumps(structural,sort_keys=True,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class TemplateAssignment:
    signature: StructureSignature
    split: str

@dataclass(frozen=True)
class SplitManifest:
    assignments: tuple[TemplateAssignment,...]
    policy_version: str
    salt: str
    def __post_init__(self) -> None:
        ids=[a.signature.digest for a in self.assignments]
        if len(set(ids))!=len(ids):raise ContractError(ErrorCode.CONFLICT,'a structural template is assigned more than once')
        if any(a.split not in {'train','validation','test','novel_composition'} for a in self.assignments):
            raise ContractError(ErrorCode.INVALID_SCHEMA,'invalid dataset split')
        structural_splits={}
        for assignment in self.assignments:
            key=assignment.signature.partition_digest
            if key in structural_splits and structural_splits[key]!=assignment.split:
                raise ContractError(ErrorCode.CONFLICT,'generator revisions of the same structural template cannot cross splits')
            structural_splits[key]=assignment.split
    @property
    def digest(self) -> str:
        rows=[{'signature':a.signature.canonical(),'split':a.split} for a in sorted(self.assignments,key=lambda x:x.signature.digest)]
        return hashlib.sha256(json.dumps({'assignments':rows,'policy_version':self.policy_version,'salt':self.salt},sort_keys=True).encode()).hexdigest()
    def for_template(self,signature: StructureSignature) -> SplitProvenance:
        matches=[a for a in self.assignments if a.signature.digest==signature.digest]
        if not matches:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'template must be partitioned before instance generation')
        return SplitProvenance(matches[0].split,signature.digest,self.digest)
    def dataset_manifest(self,shards) -> dict:
        """Build metadata for already prepared shards; never generate data."""
        if not isinstance(shards,(list,tuple)) or not shards:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'dataset manifest requires shard declarations')
        assigned={a.signature.digest:a.split for a in self.assignments}
        result=[]
        for shard in shards:
            if not isinstance(shard,dict):raise ContractError(ErrorCode.INVALID_SCHEMA,'shard must be a mapping')
            path=shard.get('path');digest=shard.get('sha256');split=shard.get('split');structures=shard.get('structure_signatures')
            if (not isinstance(path,str) or not path or not isinstance(digest,str) or
                    re.fullmatch(r'[0-9a-f]{64}',digest) is None or
                    split not in {'train','validation','test','novel_composition'} or
                    not isinstance(structures,(list,tuple)) or not structures):
                raise ContractError(ErrorCode.INVALID_SCHEMA,'shard requires path, SHA-256, split and structural signatures')
            if any(not isinstance(signature,str) or assigned.get(signature)!=split for signature in structures):
                raise ContractError(ErrorCode.CONFLICT,'shard structure does not belong to its declared split')
            result.append(dict(shard))
        return {'split_manifest':asdict(self),'split_manifest_digest':self.digest,'shards':result}

def partition_templates(templates: tuple[StructureSignature,...], *, salt: str,novel_compositions: frozenset[tuple[str,...]]=frozenset(),thresholds: tuple[int,int]=(70,85)) -> SplitManifest:
    lo,hi=thresholds
    if not 0<lo<hi<100:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'split thresholds must be increasing percentages')
    reserved={tuple(sorted(combination)) for combination in novel_compositions}
    if any(len(combination)<2 for combination in reserved):
        raise ContractError(ErrorCode.INVALID_SCHEMA,'novel composition must involve at least two concepts')
    assignments=[]
    for template in templates:
        combination=tuple(sorted(template.concept_combination))
        if combination in reserved:
            split='novel_composition'
        else:
            bucket=int(hashlib.sha256((salt+':'+template.partition_digest).encode()).hexdigest(),16)%100
            split='train' if bucket<lo else 'validation' if bucket<hi else 'test'
        assignments.append(TemplateAssignment(template,split))
    return SplitManifest(tuple(assignments),'structural-v2',salt)

def derived_provenance(parents: tuple[SplitProvenance,...],parent_ids: tuple[str,...],signature: str) -> SplitProvenance:
    if not parents or len(parents)!=len(parent_ids):raise ContractError(ErrorCode.INVALID_SCHEMA,'derived record needs all parent identities')
    if len({(p.split,p.manifest_digest) for p in parents})!=1:
        raise ContractError(ErrorCode.CONFLICT,'derivation cannot cross split or manifest boundaries')
    if any(p.template_signature!=signature for p in parents):
        raise ContractError(ErrorCode.CONFLICT,'a new structure must be assigned before sampling, not relabeled after derivation')
    first=parents[0]
    return SplitProvenance(first.split,signature,first.manifest_digest,tuple(parent_ids))
