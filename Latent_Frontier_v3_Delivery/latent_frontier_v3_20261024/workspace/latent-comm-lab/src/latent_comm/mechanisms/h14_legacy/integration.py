from latent_comm.core import ContractError

def concept_guard(grammar,ontology,concept_id,record):
    from latent_comm.mechanisms.h27_ontology.reference import evaluate
    if grammar.versions.ontology!=ontology.version:raise ContractError('VersionMismatch','H27 guard ontology differs from grammar')
    concepts={c.concept_id:c for c in ontology.concepts}
    if concept_id not in concepts:raise ContractError('UnboundReference','guard concept absent')
    return evaluate(concepts[concept_id].predicate,record) # None stays unknown, not false.

def transport_skill_operations(grammar,production_name,compiled_analogy):
    if grammar.versions.isa!=compiled_analogy.source_version or compiled_analogy.broken_squares or compiled_analogy.uncovered_edges:raise ContractError('RelationUnproven','H30 skill transport requires checked operation squares')
    productions={p.name:p for p in grammar.productions}
    if production_name not in productions:raise ContractError('UnboundReference','grammar production absent')
    mapping=dict(compiled_analogy.morphism.operation_map);body=productions[production_name].body
    if any(step.operation not in mapping for step in body):raise ContractError('UnmappedOperation','all primitive steps need explicit analogy correspondence')
    return tuple((step.local_name,mapping[step.operation],step.arguments) for step in body)

def scalar_macro_from_production(grammar,production_name,lowerings,*,target_isa):
    from latent_comm.mechanisms.h40_instruction_set.types import Expr,MacroDefinition
    production=next((p for p in grammar.productions if p.name==production_name),None)
    if production is None or target_isa!=grammar.versions.isa:raise ContractError('VersionMismatch','H40 explicit source grammar/ISA binding')
    if production.output_type.dimension!=1 or any(t.dimension!=1 for _,t in production.parameters):raise ContractError('LoweringFailure','scalar base ISA does not silently lower general vector skills')
    env={name:Expr('var',name=name) for name,_ in production.parameters}
    for step in production.body:
        if step.operation not in lowerings or any(arg not in env for arg in step.arguments):raise ContractError('LoweringFailure','explicit lexical primitive lowering required')
        macro=lowerings[step.operation]
        if len(macro.parameters)!=len(step.arguments):raise ContractError('TypeViolation','primitive macro arity differs')
        env[step.local_name]=Expr('call',tuple(env[arg] for arg in step.arguments),name=macro.name)
    if production.result_name not in env:raise ContractError('UnboundReference','production result absent')
    return MacroDefinition(production.name,tuple(name for name,_ in production.parameters),env[production.result_name],tuple('scalar' for _ in production.parameters),'scalar')
