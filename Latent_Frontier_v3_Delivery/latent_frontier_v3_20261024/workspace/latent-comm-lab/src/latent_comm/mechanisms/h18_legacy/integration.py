from dataclasses import replace
import hashlib,json
from latent_comm.core import ContractError

def propose_ontology_transition(graph,delta):
    if graph.versions.ontology!=delta.before.version or delta.before.version==delta.after.version:raise ContractError('VersionMismatch','H27 candidate transition must advance bound ontology')
    digest=hashlib.sha256(json.dumps({'before':delta.before.version,'after':delta.after.version,'concepts':[c.concept_id for c in delta.after.concepts],'migrations':delta.reader_migrations},sort_keys=True).encode()).hexdigest()
    return replace(graph,semantic_changes=graph.semantic_changes+(('O',delta.before.version,delta.after.version,digest),),versions=replace(graph.versions,ontology=delta.after.version))

def bind_plasticity_proposal(graph,rule,*,allowed_parameters):
    from latent_comm.mechanisms.h38_plasticity.reference import validate_rule
    if not set(rule.writable_groups)<=set(allowed_parameters):raise ContractError('WriteScopeViolation','H38 topology proposal cannot expand parameter rights')
    count=validate_rule(rule.ast)
    return rule,count,'proposal_not_parameter_update'

def lower_graph_macro(graph,expression,revision):
    from latent_comm.mechanisms.h40_instruction_set.reference import lower
    if graph.versions.isa!=revision.version:raise ContractError('VersionMismatch','H40 graph macro requires exact ISA revision')
    return lower(expression,revision)

def as_protocol_genome(graph,*,protocol_id,parent_ids=()):
    from latent_comm.mechanisms.h42_ecology.types import ProtocolGenome
    from .reference import validate_graph
    validate_graph(graph)
    operations={n.operation for n in graph.nodes};provided=[]
    if 'sum' in operations:provided.append('add')
    if 'negate' in operations and 'sum' in operations:provided.append('inverse')
    # No compare claim: the finite legacy graph has no conditional primitive.
    return ProtocolGenome(protocol_id,tuple(provided),(),tuple(parent_ids),graph.versions.isa)
