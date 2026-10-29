# H03 interface and source handoff

Status: dedicated source and bounded stdlib contracts; all research paths NOT_RUN. Task M03.

## Algorithm and limits

The sequence mixture is computed before marginalizing branches. Unknown support is retained explicitly, and absence of an unknown branch is not an exhaustiveness certificate. Finite assignment is discrete; matched squared distances alone have pathwise gradients. JSON null represents minus-infinity log mass only in the typed belief codec.

## Reference API

- `logsumexp(values)`
- `normalized_logs(packet)`
- `sequence_mixture_nll(packet, token_log_likelihoods)`
- `prefix_posterior_update(packet, token_log_likelihoods)`
- `update_evidence(packet, evidence_id, compatibility, *, generative_model_declared=False)`
- `prune(packet, keep_ids)`
- `match_branches(left, right, *, budget=StepBudget())`

## Explicit consumer bindings

In `integration.py`: `branch_overlap_residuals`, `update_from_counterexample`, `as_identification_state`, `branch_provenance`.
These use canonical H25–H48 objects and preserve their declared version, semantic and authority boundaries. The tests cover the current materialized source; downstream changes require revalidation.

## Future tensor API

- `mixture_sequence_logprob(branch_logits, token_ids, token_mask, branch_log_weights, *, tokenizer_contracts)`
- `tensor_prefix_update(log_weights, token_logps)`
- `generate_branches(log_weights, branch_step, branch_generate, *, mode, max_steps, eos_id, tokenizer_contracts=())`
- `matched_branch_cost(branch_states, target_states, assignment, matched_valid)`

## Loss and training handoff

`training_api.json` and `configs/mechanisms/H03.json` contain exact forward entry points, named loss inputs, live/stop-gradient edges, masks, numerators/denominators and parameter-owner bindings. Every manifest loss term names an actual loss return key. Select individual terms; never sum `total` and the same components. Diagnostic return fields are not optimization terms. Stage-prefixed bindings are explicit L-stage construction responsibilities, not a claim that a model has been initialized.

Use `latent_comm.learning.engine.train` with the documented stage interface. The engine owns optimizer, freezing, clipping, accumulation and checkpointing. This mechanism does not introduce another trainer. Frozen base parameters must not suppress gradients through the receiver. Common behavior alignment replaces invalid direct comparisons across tokenizers. The current gate remains closed.

## Wire and migration boundary

`schema.json`, `migration.py` and `wire_example.json` provide strict finite JSON structural validation, exact version axes, duplicate-key rejection and explicit legacy field bindings. `wire_example.json` is a structural codec example, not a neural fixture or a claim that every example is a semantically valid executable object. Construct the corresponding typed objects and use the reference binding checks before execution; registry resolution is separate and recursive. There is no generic opaque-object deserializer or implicit inference of missing frame, scope, source or causal meaning. Live tensors/autograd graphs are never round-tripped by this JSON schema.

## Verification

`tests/contracts/test_h03.py` contains mechanism-specific finite positive/negative tests, consumer checks, codec/migration checks, loss/API consistency and AST checks. The authoring checks block neural and network imports and do not import adapter modules. Individual finite fixtures remain within dimension 64, 64 cases and 128 steps. Passing these checks establishes only the tested source contracts, not numerical tensor correctness, model compatibility, learning effectiveness or benchmark performance.

Typed `encode_belief` / `decode_belief` additionally preserve zero-mass branches by mapping negative infinity to JSON null, then reconstructing validated BeliefBranch/BeliefPacket objects.
