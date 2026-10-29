# H02 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M02.

## Algorithm and limits

A response is local to its bound anchor and radius. Directional acquisition requires an orthonormal basis. A learned low-rank response is approximate; H31 structural intervention and H43 predictive-kernel response remain separately tagged. A finite response fit is not a globally valid derivative.

## Reference API

- `needs_refresh(capsule, delta)`
- `predict_delta(capsule, delta)`
- `build_capsule(program, anchor, *, directions, step, radius, variables, conditions, versions, budget=StepBudget())`
- `compose_response(first, second)`
- `predict(capsule, query)`

## Explicit consumer bindings

In `integration.py`: `response_from_scm`, `response_from_kernel`, `query_likelihood_from_responses`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `tensor_predict(anchor, base, A, B, query, radius)`
- `acquire_response(response_function, anchor, directions, *, method, step=0.001)`
- `predict_response_factors(features, weight, bias, *, condition_dim, output_dim, rank)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H02.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h02.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
