# H21 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M21.

## Algorithm and limits

Search evaluates the same declared SCM/noise/do root anchor, preserves branch state and lineage, and deduplicates semantic interventions. Public goal features select online branches; future outcome labels enter losses only. H29 relation witnesses are recomputed, H36 requires verified counterexamples, and H44 world branches stay synthetic with actual kernel versions. Timeout never proves impossibility.

## Reference API

- `semantic_key(node)`
- `public_score(node, goal)`
- `search_counterfactuals(world, noise, root, options, goal, *, max_depth, budget=StepBudget())`
- `update_evidence_weights(nodes, prior, likelihood, *, evidence_id, seen)`
- `question_branch(node, transform, witness, *, node_id, budget=StepBudget())`
- `world_branch(node, dream, *, node_id, world_version)`
- `counterexample_branch(node, counterexample, *, claim_id)`
- `identification_state(nodes, queries, prior, *, version)`
- `concept_branch(node, delta, *, node_id, concept_id)`

## Explicit consumer bindings

In `reference.py`: `question_branch`, `concept_branch`, `world_branch`, `counterexample_branch`, `identification_state`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `portfolio_scores(branch_states, goal_features, score_projection, coverage, valid)`
- `select_branch(scores, valid, *, sample)`
- `fork_prefix(prefix, branch_count)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H21.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h21.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.
