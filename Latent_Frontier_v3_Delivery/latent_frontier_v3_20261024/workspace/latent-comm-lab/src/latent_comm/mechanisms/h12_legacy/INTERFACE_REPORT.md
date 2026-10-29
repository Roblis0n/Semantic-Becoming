# H12 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M12.

## Algorithm and limits

Capsules are query-independent at encoding and support only their declared family. Other queries require source lookup. Versions and source/capsule dependencies are explicit; withdrawal propagates transitively and invalidates cache identity. Ontology migration binds actual source/target definitions and rejects implicit concept merges. Storage restores detached finite artifacts, not live computation graphs.

## Reference API

- `build_capsule(observations, *, capsule_id, document_id, version, query_family, evidence, dependencies, expires_step, versions, parent_version=None, capsule_dependencies=())`
- `read_query(capsule, query, *, step, versions, current_dependencies, withdrawn=frozenset())`
- `cache_key(capsule, query)`
- `CapsuleStore [typed store]`

## Explicit consumer bindings

In `integration.py`: `migrate_capsule_ontology`, `capsule_transaction`, `retract_capsule_sources`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `encode_once(evidence_states, evidence_mask, slot_queries, key_projection, value_projection)`
- `read_many(capsule_slots, query_states, query_projection, *, capsule_valid)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H12.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h12.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
