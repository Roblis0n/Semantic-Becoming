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
    from .reference import validate_graph,normalize_support,expression_atoms
    atoms=tuple(EvidenceAtom(a['atom_id'],a['source_handle'],a['source_kind'],a['marginal'],tuple(a['world_lineage'])) for a in value['atoms'])
    nodes=tuple(SupportNode(n['node_id'],n['op'],tuple(n['inputs']),n['atom_id']) for n in value['nodes'])
    graph=ProvenanceGraph(atoms,nodes,value['root'],value['version']);known,_,_=validate_graph(graph)
    d=value['dependence'];dependence=DependenceModel(d['mode'],tuple(d['atom_ids']),tuple(JointAssignment(tuple(j['values']),j['probability']) for j in d['joint']),d['declaration_id'])
    if set(dependence.atom_ids)-known.keys():raise ContractError('MissingSource','dependence references unknown atom')
    if dependence.mode!='unknown' and not expression_atoms(normalize_support(graph))<=set(dependence.atom_ids):raise ContractError('MissingSource','dependence does not cover expression atoms')
    if dependence.mode=='declared_independent' and any(known[a].marginal is None for a in dependence.atom_ids):raise ContractError('UnsupportedCalibration','independence requires declared marginals')
    if dependence.mode=='explicit_joint':
        for i,a in enumerate(dependence.atom_ids):
            if known[a].marginal is not None and abs(sum(j.probability for j in dependence.joint if j.values[i])-known[a].marginal)>1e-9:raise ContractError('UnsupportedCalibration','joint contradicts declared marginal')
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
