"""Structural partition before sampling, role projection and resumable future generation."""
from dataclasses import replace
import hashlib
import random
from latent_comm.core import ContractError,ErrorCode,Visibility
from latent_comm.safety.policy import require_research_action
from latent_comm.data import RoleBatch,SplitManifest,partition_templates,generate_dataset,save_cursor,load_cursor
from .generator import signature,sample_parameters,build_fixture

def manifest_for(parameters: tuple, *, salt: str,novel_compositions: frozenset=frozenset()) -> SplitManifest:
    return partition_templates(tuple(signature(p) for p in parameters),salt=salt,novel_compositions=novel_compositions)

def build_instance(structure,seed: int,provenance):
    require_research_action('research_execution')
    parameters=sample_parameters(structure,random.Random(seed))
    if signature(parameters).digest!=structure.digest:
        raise ContractError(ErrorCode.CONFLICT,'sampler changed the assigned structural template')
    finite_record=build_fixture(parameters)
    record_id='record:'+hashlib.sha256(f'{structure.digest}:{seed}'.encode()).hexdigest()
    return replace(finite_record,record_id=record_id,split_provenance=provenance,purpose='research_data',not_research_data=False)

def iter_records(manifest: SplitManifest, *, instances_per_template: int,seed: int,cursor=None):
    yield from generate_dataset(manifest,build_instance,instances_per_template=instances_per_template,seed=seed,cursor=cursor)

def collate_role(records: tuple,role: Visibility) -> RoleBatch:
    if role not in {Visibility.SENDER,Visibility.RECEIVER}:
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'supervision is never a model role batch')
    views=tuple(record.sender_view if role==Visibility.SENDER else record.receiver_view for record in records)
    return RoleBatch(role,views)
