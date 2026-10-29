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
    from .reference import validate_domain,dependency_order,verify_hard
    validate_domain(value['domain']);capsules=[]
    for c in value['capsules']:
        w=c['witness'];required=DomainPredicate(**w['required_predicate']) if w['required_predicate'] is not None else None
        witness=NegativeWitness(w['kind'],required,tuple(w['checked_domain']),w['grammar_scope'],w['status'])
        capsule=ExclusionCapsule(c['capsule_id'],DomainPredicate(**c['excluded']),tuple(c['assumptions']),witness,c['reliability'],c['mode'],tuple(c['dependencies']),tuple(c['retract_on']),c['domain_version'])
        if capsule.mode=='hard':verify_hard(capsule,value['domain'])
        capsules.append(capsule)
    dependency_order(capsules)
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
