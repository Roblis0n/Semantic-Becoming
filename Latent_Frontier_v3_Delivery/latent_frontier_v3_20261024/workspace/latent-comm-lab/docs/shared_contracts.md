# Shared contracts v1

All mechanism writers use stdlib-only imports from latent_comm.core. Research code may be written but never imported from torch/transformers or executed during this task. Neural/tensor entry functions must first call latent_comm.safety.policy.require_research_action('model_forward' or the correct action), then lazily import the tensor backend. No learned fixture or random neural initialization is allowed.

- ContractError(code, message, path='', recoverable=False, obligations=()) preserves structured Failure. Mechanism-specific code strings are allowed; do not swallow them into None or zero vectors.
- StepBudget (alias FixtureBudget) applies only to currently authorized finite checks. ResearchBudget retains larger future recipe bounds (e.g. H40 expansion 256) as metadata without executing them; its meter is separately policy-gated. StepBudget(max_steps=128, max_dimension=64, max_cases=64, max_branches=64) creates a fixture meter. charge finite searches and loops explicitly. Individual fixture dimensions/cases remain bounded.
- VersionSet separates schema/state/ontology/isa/frame/world/task/evidence. Required axes cannot be absent. ObjectRef is a namespaced identity, not a file. ObjectRegistry.resolve validates type, version, actor scope and recursive role visibility.
- TensorSpec(axes, shape, dtype, semantic_role, trainable_owner, device_policy='unallocated', mask_axes=(), status=ValueStatus.PRESENT) checks named axes and shape. No implicit padding/missing/zero conflation.
- RoleView/project_role performs physical whitelist projection and rejects nested label/hidden_solution/world_seed/oracle_trace/sample_id/split_id. Ref dependencies must also pass role access checks.
- LossSpec gives formula, numerator/denominator/mask/zero-valid behavior, parameter owners, required input gradients, stop edges, estimator and units. Frozen model weights do not imply no_grad on the receiver input path.
- core.finite provides immutable tuple vectors/matrices, dot/add/sub/scale/norm, transpose/matvec/matmul, eye/inverse/solve, bounded symmetric_eigh/least_squares, and finite topological_order. These are mathematical utilities, not research models. least_squares returns residual, rank, uniqueness, convergence and sweep count.
- packets distinguishes LiveTensor identity from StoredTensor with replay_requires_recompute. MigrationRegistry provides explicit axis transitions and DAG order. No automatic reinterpreting an old ontology or ISA.
- Legacy facades are A02-owned lazy named re-exports from dedicated mechanism types/reference/adapter/losses. Mechanism writers own their target_base only and must not edit these facades.

All own task cards, role prompts, dedicated mechanism cards, schema and recipes remain authoritative. These shared primitives do not replace dedicated algorithms. Current adapters are source/AST only; actual integration is NOT_RUN.

Registry validation recursively checks requested versions on every declared dependency, rejects embedded ObjectRefs omitted from dependencies, and recursively validates typed/dataclass/mapping role payloads. Opaque referenced payloads require an explicit typed role projection; live tensor identity is not copied.
