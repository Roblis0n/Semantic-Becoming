from latent_comm.core import ContractError
from .types import RelationNode,RelationEdge,RelationPacket

def as_typed_operation_graph(packet):
    from latent_comm.mechanisms.h30_analogy.types import TypedObject,FiniteOperation,TypedOperationGraph
    nodes={n.node_id:n for n in packet.nodes};groups={}
    for edge in packet.edges:
        if edge.semantics!='operation':continue
        groups.setdefault(edge.relation,[]).append(edge)
    operations=[]
    for name,edges in groups.items():
        inputs={nodes[e.source].role for e in edges};outputs={nodes[e.target].role for e in edges}
        if len(inputs)!=1 or len(outputs)!=1 or len({e.source for e in edges})!=len(edges):raise ContractError('TypeViolation','H30 relation must be a typed partial function, not arbitrary graph adjacency')
        operations.append(FiniteOperation(name,next(iter(inputs)),next(iter(outputs)),tuple((e.source,e.target) for e in edges)))
    if not operations:raise ContractError('UnboundOperation','no executable operation-labelled relation')
    return TypedOperationGraph(tuple(TypedObject(n.node_id,n.role) for n in packet.nodes),tuple(operations),packet.versions.ontology)

def bind_structural_edges(packet,world):
    if packet.versions.world!=world.version:raise ContractError('VersionMismatch','H31 relation and structural world versions differ')
    modules={m.output:m for m in world.modules};result=[]
    for edge in packet.edges:
        if edge.semantics=='causal':
            if edge.target not in modules or edge.source not in modules[edge.target].parents:raise ContractError('CausalIdentificationRequired','causal edge lacks an actual structural equation parent')
            result.append((edge,modules[edge.target]))
    return tuple(result)

def shared_noise_relation_graph(kernel,versions):
    if kernel.version!=versions.world:raise ContractError('VersionMismatch','H43 joint kernel version binding')
    dependencies=dict(kernel.dependency_map)
    if set(dependencies)!=set(kernel.component_ids):raise ContractError('UnboundNoise','explicit per-component noise identities required')
    nodes=tuple(RelationNode(k,'kernel',(float(len(dependencies[k])),),k) for k in kernel.component_ids);edges=[]
    for i,left in enumerate(kernel.component_ids):
        for right in kernel.component_ids[i+1:]:
            if set(dependencies[left])&set(dependencies[right]):edges.append(RelationEdge(left,right,'shared_noise','correlation'))
    return RelationPacket(nodes,tuple(edges),versions)
