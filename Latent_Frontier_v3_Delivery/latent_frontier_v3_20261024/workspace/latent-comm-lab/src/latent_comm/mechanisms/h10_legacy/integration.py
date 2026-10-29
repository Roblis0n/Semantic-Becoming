from latent_comm.core import ContractError

def coalition_from_subset_losses(edge,loss_table,*,value_version):
    from latent_comm.mechanisms.h41_coalitions.types import CoalitionGame
    if not value_version or any(not set(subset)<=set(edge.members) for subset in loss_table):raise ContractError('UndefinedValue','H41 finite subset losses must name declared members')
    return CoalitionGame(edge.members,tuple((tuple(sorted(subset)),-float(loss)) for subset,loss in loss_table.items()),value_version)

def population_expressibility(edge,protocols,task):
    from latent_comm.mechanisms.h42_ecology.reference import required_operators
    members={p.protocol_id:p for p in protocols}
    if not set(edge.members)<=members.keys() or task.version!=edge.versions.task:raise ContractError('VersionMismatch','H42 hyperedge members and task versions bind explicitly')
    provided=set().union(*(set(members[name].operators) for name in edge.members));missing=set(required_operators(task))-provided
    return tuple(sorted(missing)),'static_joint_expressibility_not_competence'

def hyperedge_provenance(edge,atoms):
    from latent_comm.mechanisms.h48_evidence_genealogy.types import SupportNode,ProvenanceGraph
    support=frozenset().union(*(handles for _,handles in edge.evidence_support));selected=tuple(a for a in atoms if a.atom_id in support)
    if {a.atom_id for a in selected}!=support or not support:raise ContractError('MissingSource','H48 requires every distinct support atom')
    nodes=tuple(SupportNode('atom:'+a.atom_id,'atom',(),a.atom_id) for a in selected);root='hyperedge:'+edge.edge_id
    return ProvenanceGraph(selected,nodes+(SupportNode(root,'and',tuple(n.node_id for n in nodes)),),root,edge.versions.evidence)
