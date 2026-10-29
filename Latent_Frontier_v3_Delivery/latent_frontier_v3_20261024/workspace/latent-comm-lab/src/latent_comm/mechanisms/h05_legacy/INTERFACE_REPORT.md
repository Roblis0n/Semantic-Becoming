# H05 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M05.

## Algorithm and limits

Finite program continuation is the executed reference. Exact model capture/resume is unexecuted, live-only, same declared backend/tokenizer/layout/dtype, eval-mode and one-pending-token only; tensor shape/device/mask/position and B04 identity-transfer checks are present. CPU/CUDA RNG is restored only within a fork. Serialized metadata cannot preserve autograd or arbitrary model-internal state. Heterogeneous cache/progress transport is explicitly approximate and needs common-action supervision.

## Reference API

- `capture(program, values, *, contract, versions, transaction_version, evidence=(), boundaries=())`
- `validate(packet, *, contract, versions, transaction_version, available_evidence)`
- `resume(packet, *, available_dependencies=(), max_operations=1, budget=StepBudget())`
- `close(packet)`
- `serialize(packet)`
- `cut_points(program_length, count)`
- `validate_model_snapshot(snapshot, *, contract, versions, transaction_version, available_dependencies)`

## Explicit consumer bindings

In `integration.py`: `bind_public_terminal`, `after_transaction_commit`, `retract_continuation_evidence`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `translate_cache(cache, transfer, *, key_projections, value_projections, source_rope=None, target_rope=None)`
- `translate_progress(state, projection, public_boundary, dependency_mask)`
- `resume_model(model, new_token_ids, cache, attention_mask, cache_position, *, layout, contract, expected_contract, role_origins)`
- `capture_model_snapshot(cache, attention_mask, pending_token_ids, position_ids, *, contract, layout, position_spec, random_state_scope, cuda_devices, completed_operations, pending_dependencies, branch_lineage, transaction_version, role_origins, versions)`
- `resume_model_snapshot(model, snapshot, *, layout, contract, versions, transaction_version, available_dependencies)`
- `close_model_snapshot(snapshot)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H05.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h05.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
