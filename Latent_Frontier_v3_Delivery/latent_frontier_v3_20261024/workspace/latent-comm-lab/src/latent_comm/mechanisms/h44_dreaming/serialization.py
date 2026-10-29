"""Resolved payload codec; references must first be resolved through ObjectRegistry.

Schema migrations never silently change frame, ontology, ISA, world or evidence.
Serialized values require recomputation before differentiable replay.
"""
from pathlib import Path
import json
from latent_comm.packets.schema import SchemaValidator, load_json
from latent_comm.core import ContractError
from .types import *

def validate_payload(value):
    SchemaValidator(json.loads(Path(__file__).with_name('schema.json').read_text())).validate(value)
    if value['world_id'] in value['parent_kernel_ids']:raise ContractError('CircularSupport','world cannot generate its own parent kernel')
    for e in value['edits']:
        if e['kernel_id'] not in value['parent_kernel_ids'] or any(p<0 for p in e['probabilities']) or abs(sum(e['probabilities'])-1)>1e-9:raise ContractError('IncompatibleWorlds','edit target or normalized transition invalid')
    return value

def encode_payload(value):
    validate_payload(value)
    return json.dumps(value,sort_keys=True,allow_nan=False)

def decode_payload(text):
    return validate_payload(load_json(text))

def migrate_payload(old, source_version):
    if source_version != 2:
        raise ContractError('UnsupportedMigration', 'only explicit schema 2 to 3 migration is implemented')
    if 'schema_version' in old and old['schema_version'] != 2:
        raise ContractError('VersionMismatch', 'source declaration differs')
    result = dict(old)
    result['schema_version'] = 3
    validate_payload(result)
    return result
