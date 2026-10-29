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
    WorldKernel(value['kernel_id'],value['state_port'],tuple(value['states']),tuple(tuple(a) for a in value['actions']),tuple(value['noise_ids']),tuple(ConditionalRow(r['state'],r['action'],tuple(r['noise_values']),tuple(r['probabilities'])) for r in value['transition_rows']),tuple(value['observations']),tuple(tuple(r) for r in value['observation_rows']),value['version'],value['scope'])
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
