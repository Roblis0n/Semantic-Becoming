from latent_comm.core import ContractError,StepBudget

def execute_concept_binding(compiled,ontology,concept_id,observation):
    from latent_comm.mechanisms.h27_ontology.reference import evaluate
    if ontology.version!=compiled.packet.versions.ontology:raise ContractError('VersionMismatch','H27 ontology must match compiled program')
    concepts={c.concept_id:c for c in ontology.concepts}
    if concept_id not in concepts:raise ContractError('UnboundReference','concept not installed')
    return evaluate(concepts[concept_id].predicate,observation)

def verify_question_binding(compiled,transform,*,budget=StepBudget()):
    from latent_comm.mechanisms.h29_questions.reference import check_relation
    if transform.source.version!=compiled.packet.versions.task:raise ContractError('VersionMismatch','H29 source question version differs')
    return check_relation(transform,budget=budget)

def validate_plasticity_binding(compiled,rule,*,allowed_parameters):
    from latent_comm.mechanisms.h38_plasticity.reference import validate_rule
    if not set(rule.writable_groups)<=set(allowed_parameters):raise ContractError('WriteScopeViolation','H38 update whitelist exceeds compiled binding')
    compiled.packet.scope.check('receiver',writes=frozenset({'U'}));return validate_rule(rule.ast)

def lower_macro_binding(compiled,expression,revision,*,budget=StepBudget()):
    from latent_comm.mechanisms.h40_instruction_set.reference import lower
    if revision.version!=compiled.packet.versions.isa:raise ContractError('VersionMismatch','H40 macro ISA revision differs')
    return lower(expression,revision,budget=budget)
