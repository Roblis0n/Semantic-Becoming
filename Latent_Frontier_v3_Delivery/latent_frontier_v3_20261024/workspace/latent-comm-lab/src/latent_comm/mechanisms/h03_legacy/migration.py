"""Explicit V2 binding: no guessed frame, ontology, scope or evidence."""
from copy import deepcopy
from latent_comm.core import ContractError, VersionSet, Visibility
REQUIRED_FIELDS=('branches', 'generation_mode', 'consumed_evidence', 'probability_semantics')
REQUIRED_AXES=('task', 'evidence')
def migrate_legacy(record, *, bindings, versions):
    if record.get('schema_version') not in (1,'1.0',2):
        raise ContractError('VersionMismatch','expected an explicit legacy schema')
    versions.require(*REQUIRED_AXES)
    unknown=set(record)-set(REQUIRED_FIELDS)-{'schema_version','versions'}
    if unknown: raise ContractError('InvalidSchema',f'unknown legacy fields: {sorted(unknown)}')
    out={k:deepcopy(v) for k,v in record.items() if k in REQUIRED_FIELDS}
    for key,value in bindings.items():
        if key not in REQUIRED_FIELDS or (key in out and out[key]!=value):
            raise ContractError('MigrationConflict','binding may only supply missing semantic fields')
        out[key]=deepcopy(value)
    missing=set(REQUIRED_FIELDS)-set(out)
    if missing: raise ContractError('UnboundReference',f'explicit bindings required: {sorted(missing)}')
    migrated=dict(out,schema_version=3,versions=versions.as_dict())
    validate_wire(migrated)
    return migrated
def validate_wire(record):
    from pathlib import Path
    from latent_comm.packets.schema import SchemaValidator,load_json
    schema=load_json(Path(__file__).with_name('schema.json').read_text())
    SchemaValidator(schema).validate(record)
    try:versions=VersionSet(**record['versions'])
    except (TypeError,KeyError) as error:raise ContractError('InvalidSchema','invalid explicit version axes') from error
    versions.require(*REQUIRED_AXES)
    return versions

def encode_wire(record):
    import json
    validate_wire(record)
    return json.dumps(record,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')

def decode_wire(payload):
    from latent_comm.packets.schema import load_json
    try:text=payload.decode('utf-8',errors='strict') if isinstance(payload,bytes) else payload
    except UnicodeError as error:raise ContractError('InvalidSchema','wire payload is strict UTF-8') from error
    record=load_json(text);validate_wire(record);return record

def resolve_payload(envelope, context, *, role=Visibility.RECEIVER, granted_capabilities=frozenset()):
    if envelope.kind!='H03' or envelope.schema_version!=3:
        raise ContractError('InvalidSchema','mechanism envelope mismatch')
    if envelope.capabilities_required-granted_capabilities:
        raise ContractError('UnsupportedCapability','envelope asks for ungranted capabilities')
    return context.registry.resolve(envelope.payload_ref, expected_type='H03',
        versions=context.versions,actor=context.actor,role=role)


def encode_belief(packet):
    import math
    branches=[{'branch_id':b.branch_id,'state':None if b.state is None else list(b.state),'log_weight':None if b.log_weight==-math.inf else b.log_weight,'semantic_domain':b.semantic_domain,'evidence_support':sorted(b.evidence_support),'ontology_version':b.ontology_version,'unknown':b.unknown} for b in packet.branches]
    return encode_wire({'schema_version':3,'versions':packet.versions.as_dict(),'branches':branches,'generation_mode':packet.generation_mode,'consumed_evidence':sorted(packet.consumed_evidence),'probability_semantics':packet.probability_semantics})

def decode_belief(payload):
    import math
    from .types import BeliefBranch,BeliefPacket
    row=decode_wire(payload)
    branches=tuple(BeliefBranch(b['branch_id'],None if b['state'] is None else tuple(b['state']),-math.inf if b['log_weight'] is None else b['log_weight'],b['semantic_domain'],frozenset(b['evidence_support']),b['ontology_version'],b['unknown']) for b in row['branches'])
    return BeliefPacket(branches,row['generation_mode'],VersionSet(**row['versions']),frozenset(row['consumed_evidence']),row['probability_semantics'])
