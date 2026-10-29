# H19 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M19.

## Algorithm and limits

Finite affine compilation is algebra, not a trained model. Persistent consolidation records immutable adapter versions, source traces, training-instance exclusions and retraction/rollback lineage. H38 rule AST and parameter scope are both validated. The teacher is detached; the no-message student remains differentiable. Parameter artifact loading, training and generalization are NOT_RUN.

## Reference API

- `compile_affine_operations(operations, *, budget=StepBudget())`
- `apply_skill(skill, state)`
- `validate_training_partition(traces, unseen_instance_ids, *, step, versions)`
- `AdapterHistory [typed store]`
- `bind_learning_effect(adapter, linearization)`
- `bind_update_rule(adapter, rule)`
- `macro_provenance(adapter, macro, *, source_trace_ids, isa_version)`

## Explicit consumer bindings

In `reference.py`: `bind_learning_effect`, `bind_update_rule`, `macro_provenance`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `teacher_student_outputs(teacher, student, public_inputs, message, adapter_parameters, *, allowed_names)`
- `operator_hypernetwork(operators, probe_states, projection_u, projection_v, projection_bias, *, rank)`
- `functional_distillation_step(parameters, loss, *, allowed_names, learning_rate, create_graph=False)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H19.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h19.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
