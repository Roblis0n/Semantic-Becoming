from dataclasses import replace
import json
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import matvec
from .types import StateReference,TransitionRecord

def resolve_reference(state,reference,*,actor,write=False):
    cells={c.cell_id:c for c in state.cells}
    if reference.cell_id not in cells:raise ContractError('UnboundReference','state cell not found')
    c=cells[reference.cell_id]
    if reference.partition_version!=state.version or reference.revision!=c.revision or reference.frame!=c.frame:raise ContractError('StaleReference','old ownership or coordinate reference invalid')
    if actor not in (c.writers if write else c.readers) or actor not in dict(state.partitions)[c.partition]:raise ContractError('CapabilityDenied','actor outside current authorized partition')
    return c.value

def transition(state,action,*,migrations=(),budget=StepBudget()):
    if action.expected_version!=state.version:raise ContractError('VersionConflict','atomic partition transition checks snapshot')
    groups=dict(state.partitions);sources=set(action.sources)
    if not sources<=groups.keys():raise ContractError('UnknownPartition','source partition absent')
    if action.target in groups and action.target not in sources:raise ContractError('PartitionCollision','cannot overwrite unrelated partition')
    eligible={c.cell_id for c in state.cells if c.partition in sources}
    selected=set(action.selected_cells)
    if not selected or not selected<=eligible:raise ContractError('OwnershipViolation','selected cells must belong to source partitions')
    if action.kind=='join' and (len(sources)<2 or selected!=eligible):raise ContractError('InvalidTransition','join combines all source cells')
    if action.kind in ('split','isolate') and (len(sources)!=1 or action.target in sources):raise ContractError('InvalidTransition','split/isolate creates a new partition')
    if action.kind=='isolate' and len(action.members)!=1:raise ContractError('InvalidTransition','isolate has one existing authorized actor')
    if action.kind=='handoff' and (len(sources)!=1 or selected!=eligible):raise ContractError('InvalidTransition','handoff transfers complete source ownership')
    maps={m.cell_id:m for m in migrations}
    if len(maps)!=len(migrations) or not maps.keys()<=selected:raise ContractError('UnboundMap','migration applies only to selected cells once')
    # Validate all writes before constructing a replacement. No external capability changes.
    meter=budget.meter();cells=[];invalid=[]
    for c in state.cells:
        meter.consume(steps=1)
        if c.cell_id not in selected:cells.append(c);continue
        if not action.members<=c.readers or not action.members&c.writers:raise ContractError('CapabilityExpansion','partition edits cannot grant new access')
        value=c.value;frame=c.frame
        if c.cell_id in maps:
            m=maps[c.cell_id]
            if m.source_frame!=frame:raise ContractError('FrameMismatch','explicit coordinate migration source')
            value=matvec(m.mapping,value);frame=m.target_frame
        invalid.append(StateReference(c.cell_id,c.revision,state.version,c.frame));cells.append(replace(c,value=value,frame=frame,partition=action.target,revision=c.revision+1))
    groups[action.target]=action.members
    for name in sources:
        if name!=action.target and not any(c.partition==name for c in cells):groups.pop(name)
    # All cache references close because each encodes the old partition layout/version.
    after=replace(state,partitions=tuple(sorted(groups.items())),cells=tuple(cells),open_cache_refs=frozenset(),version=action.new_version,versions=replace(state.versions,state=action.new_version))
    return TransitionRecord(state,after,action,tuple(invalid),state.open_cache_refs)

def rollback(record,current,*,new_version):
    if current!=record.after or new_version in (record.before.version,record.after.version):raise ContractError('VersionConflict','rollback must not overwrite newer state or resurrect stale references')
    cells=tuple(replace(c,revision=max(c.revision,next(a.revision for a in current.cells if a.cell_id==c.cell_id))+1) for c in record.before.cells)
    return replace(record.before,cells=cells,version=new_version,versions=replace(record.before.versions,state=new_version),open_cache_refs=frozenset())

def structure_migration(cell,structure_transition):
    from .types import CoordinateMigration
    if structure_transition.source_version!=str(cell.revision):raise ContractError('VersionMismatch','H28 structure transition source revision differs')
    return CoordinateMigration(cell.cell_id,cell.frame,structure_transition.new_structure,structure_transition.mapping,'H28:'+structure_transition.target_version)
def transaction_for_transition(record,*,cell_version):
    from latent_comm.mechanisms.h39_transactions.types import CognitiveTransaction,VersionedCell
    body=json.dumps({'partition_version':record.after.version,'partitions':[(n,sorted(a)) for n,a in record.after.partitions],'closed_cache_refs':sorted(record.closed_cache_refs),'cells':[{'cell_id':c.cell_id,'type_tag':c.type_tag,'value':c.value,'frame':c.frame,'readers':sorted(c.readers),'writers':sorted(c.writers),'partition':c.partition,'revision':c.revision} for c in record.after.cells],'versions':record.after.versions.as_dict()},sort_keys=True)
    return CognitiveTransaction('partition:'+record.after.version,(('state:partition',cell_version),),(VersionedCell('state:partition','partition',cell_version+1,body),))
def require_coalition_members(state,coalition):
    members=set().union(*(a for _,a in state.partitions))
    if not {a.name for a in coalition.agents}<=members:raise ContractError('CapabilityExpansion','H41 coalition cannot invent actors outside partition authorization')
    return coalition
