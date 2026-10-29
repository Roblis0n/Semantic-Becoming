from dataclasses import asdict,replace
import json
from latent_comm.core import ContractError

def migrate_capsule_ontology(capsule,delta,*,new_version):
    if capsule.versions.ontology!=delta.before.version or new_version==capsule.version:raise ContractError('VersionMismatch','H27 source ontology and new capsule version required')
    migration={old:new for consumer,old,new in delta.reader_migrations if consumer==capsule.capsule_id}
    names={name for name,_ in capsule.observations}
    source_ids={c.concept_id for c in delta.before.concepts};target_ids={c.concept_id for c in delta.after.concepts}
    if not names<=migration.keys() or not names<=source_ids or not {migration[k] for k in names}<=target_ids:raise ContractError('UnboundVariable','every retained concept must bind an actual source and target ontology definition')
    if len({migration[k] for k in names})!=len(names):raise ContractError('MigrationConflict','merging concepts with distinct scalar observations needs an explicit conflict resolver')
    return replace(capsule,version=new_version,parent_version=capsule.version,observations=tuple((migration[k],v) for k,v in capsule.observations),versions=replace(capsule.versions,ontology=delta.after.version),capsule_dependencies=capsule.capsule_dependencies+((capsule.document_id,capsule.version),))

def capsule_transaction(capsule,*,previous_cell_version):
    from latent_comm.mechanisms.h39_transactions.types import VersionedCell,CognitiveTransaction
    row=asdict(capsule)
    for key in ('allowed_query_family','evidence_handles'):row[key]=sorted(row[key])
    key='state:capsule:'+capsule.document_id
    return CognitiveTransaction('capsule:'+capsule.capsule_id+':'+capsule.version,((key,previous_cell_version),),(VersionedCell(key,'persistent_capsule',previous_cell_version+1,json.dumps(row,sort_keys=True,allow_nan=False)),))

def retract_capsule_sources(store,invalidation,*,evidence_version):
    if invalidation.version!=evidence_version:raise ContractError('VersionMismatch','H48 retraction scope must match source evidence version')
    return store.withdraw(set(invalidation.retracted_atoms))
