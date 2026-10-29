# H23 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M23.

## Algorithm and limits

Transport byte integrity and semantic repair are separate. Numeric, domain, missing-variable and evidence conflicts have different repair kinds. Replies bind report identity, kind, versions, frame, retractions and edge witnesses before mutation. H26 obstruction edges are resolved to actual endpoint domains, not mislabeled as domains. Unreachable residuals and both-direction byte cost remain visible.

## Reference API

- `integrity_digest(payload)`
- `verify_integrity(payload, expected)`
- `diagnose(*, report_id, payload, expected_digest, probe_ids, observed, expected, allowed_fields, versions, domains=(), missing=(), evidence_errors=frozenset(), tolerance=1e-09)`
- `build_repair(report, response_jacobian=None, *, budget=StepBudget())`
- `wire_bytes(obj)`
- `apply_repair(session, report, repair, *, max_rounds)`
- `sheaf_conflict_report(gluing, sheaf, *, report_id, digest, versions)`
- `bind_ontology_repair(report, *, source_ontology, target_ontology, variable_bindings)`
- `exclusion_for_repair(report, capsule)`
- `provenance_retraction(report, invalidation)`

## Explicit consumer bindings

In `reference.py`: `sheaf_conflict_report`, `bind_ontology_repair`, `exclusion_for_repair`, `provenance_retraction`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `encode_repair(public_sender_features, permitted_summary, probe_response, *, ridge)`
- `no_repair_gate(residual_features, weights, bias, numeric_domain_valid)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H23.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h23.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
