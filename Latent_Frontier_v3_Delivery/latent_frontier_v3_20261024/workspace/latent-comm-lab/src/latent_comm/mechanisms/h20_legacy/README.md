# H20: Asynchronous versioned events with vector clocks and explicit staleness

Original algorithm preserved in `types.py` and `reference.py`; the future tensor implementation is `adapter.py`. The exact current recipe and original source are `inherited_v2/hypotheses/H20_异步认知时钟.md` and `integration/I20_异步认知时钟.md` relative to PLAN_ROOT. The task is M20.

V2 payload fields retained: event_id, kind, source, clock, dependencies, source_state_version, receiver_versions, earliest_step, expires_step, stale_policy, payload_ref. Missing V3 semantic bindings are rejected by `migrate_legacy`; it never infers a frame, type, evidence source or causal interpretation. Version axes required here: state, ontology, world, evidence. Live graphs are not serialized. Stored records require recomputation. `resolve_payload` uses the shared registry's recursive role/version checks.

Connections: H33 phase/readout, H34 path index, H39 transactional read set. These are explicit data contracts and not claims of empirical compatibility. An absent version, map or provenance remains unbound. No cross-tokenizer logit KL is used. Research model and optimizer paths are source only, guarded before backend imports, and NOT_RUN. No research efficacy conclusion follows from the finite examples.

Training: eligible-event CE or score-function timing with detached advantage, task objective; no correctness inferred from event maturity. Gradients are owned by the mechanism writer/reader unless a LossSpec states otherwise. Base weights may be frozen with `requires_grad_(False)` but receiver input gradients remain connected. The shared learning trainer controls optimizer, clipping, accumulation and checkpointing; this module supplies the concrete tensor computation and loss graph. Discrete structures are selected outside gradients. Zero valid terms produce a differentiable zero and an explicit mask, not a fake supervised observation.

The contract test file checks dedicated positive/negative algorithms, version migration and AST gates without importing or executing tensor source. Dimensions <=64, cases <=64, steps <=128. Fixed mathematical objects are not neural fixtures or generated research data.

## Exact handoff

See `INTERFACE_REPORT.md` for callable signatures, concrete consumer bindings and remaining limits, and `training_api.json` for exact named loss/parameter wiring. All research execution remains NOT_RUN.
