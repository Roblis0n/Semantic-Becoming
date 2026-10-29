# H20 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M20.

## Algorithm and limits

Vector-clock causality is not wall-clock order; phase/path indices are explicit. Stale events reject, request recomputation or require an explicit remap certificate. Pending dependencies are not silently satisfied. Event supervised and sampled policy objectives have separate eligibility/valid masks; logits can be returned explicitly.

## Reference API

- `happens_before(left, right)`
- `tick(clock, actor, *, physical_step, phase=None, path_index=None, received=None)`
- `staleness(event, current_versions, step, remaps=())`
- `EventScheduler [typed store]`
- `bind_dynamics_event(event, dynamics, *, readout_index)`
- `bind_path_event(event, path, *, trajectory_version)`
- `bind_transaction(event, transaction)`

## Explicit consumer bindings

In `reference.py`: `bind_dynamics_event`, `bind_path_event`, `bind_transaction`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `event_policy(features, weights, bias, eligible, *, sampling, return_logits=False)`
- `version_gated_merge(current, delta, version_match, dependency_ready, *, gain)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H20.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h20.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
