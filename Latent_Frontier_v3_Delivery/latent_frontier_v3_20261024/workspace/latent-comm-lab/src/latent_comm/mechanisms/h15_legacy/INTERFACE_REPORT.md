# H15 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M15.

## Algorithm and limits

One sender message serves a heterogeneous population through dedicated readers. Tokenizer/model identity is not hidden answer input. Common behavior coordinates, not direct cross-tokenizer KL, provide alignment. Held-out pair sampling/dropout is structural source support, not measured generalization.

## Reference API

- `AdapterRegistry [typed store]`
- `eligible_pair(sender, receiver, required)`
- `sample_pairs(members, *, held_out_pairs, required, count, seed, receiver_dropout=(), budget=StepBudget())`
- `transmit(sender, receiver, state, *, required)`
- `coverage(members, observed_pairs)`

## Explicit consumer bindings

In `integration.py`: `gauge_protocol_member`, `learning_effect_boundary`, `quotient_protocol_boundary`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `population_forward(sender_state, sender_writer, receiver_readers, receiver_functions, receiver_inputs, *, capability_projection=None, capability_vector=None)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H15.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h15.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
