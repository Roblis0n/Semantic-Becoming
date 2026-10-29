# H01 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M01.

## Algorithm and limits

Composition is ordered function execution, not factor addition. H40 macro lowering is exact only for the explicitly accepted scalar affine subcase; nonlinear operators are rejected by that lowerer. H35 compatibility is a finite-probe check, not a global closure proof.

## Reference API

- `identity(dimension, domain, versions)`
- `compose(first, second)`
- `chain(packet)`
- `apply(state, packet, *, actor='receiver', step=0, budget=StepBudget())`
- `restrict_scope(packet, scope)`
- `change_frame(packet, gauge, target_versions)`
- `serialize(packet)`

## Explicit consumer bindings

In `integration.py`: `gauge_operator`, `finite_operation_graph`, `coarse_effect_check`, `scalar_affine_macro`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `tensor_operator(state, U, V, bias, alpha, *, nonlinearity='tanh')`
- `generate_operator(sender_features, weight, bias, *, dimension, rank)`
- `apply_to_receiver(receiver_state, read_matrix, write_matrix, factors, model, *, capabilities, inputs, injection='prefix', layer=None, slot_mask=None, padding_side='right')`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H01.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h01.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
