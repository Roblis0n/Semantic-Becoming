# H24: Scoped latent effects with host-installed non-escalating capabilities

Original algorithm preserved in `types.py` and `reference.py`; the future tensor implementation is `adapter.py`. The exact current recipe and original source are `inherited_v2/hypotheses/H24_有作用域的潜计算能力.md` and `integration/I24_有作用域的潜计算能力.md` relative to PLAN_ROOT. The task is M24.

V2 payload fields retained: capability_id, principal, session_id, readable_slots, writable_slots, allowed_types, expires_step, evidence_handles, target_views, update_parameters, macro_capabilities, transaction_writes, immutable_goal_digest. Missing V3 semantic bindings are rejected by `migrate_legacy`; it never infers a frame, type, evidence source or causal interpretation. Version axes required here: state, frame, ontology, isa, task, evidence. Live graphs are not serialized. Stored records require recomputation. `resolve_payload` uses the shared registry's recursive role/version checks.

Connections: H32 immutable external goal and internal view, H38 named parameter whitelist, H39 local transaction write set, H40 expanded macro effect scope. These are explicit data contracts and not claims of empirical compatibility. An absent version, map or provenance remains unbound. No cross-tokenizer logit KL is used. Research model and optimizer paths are source only, guarded before backend imports, and NOT_RUN. No research efficacy conclusion follows from the finite examples.

Training: forbidden proposed-effect penalty and task objective; actual protected coordinates remain identical by construction; no statistical privacy claim. Gradients are owned by the mechanism writer/reader unless a LossSpec states otherwise. Base weights may be frozen with `requires_grad_(False)` but receiver input gradients remain connected. The shared learning trainer controls optimizer, clipping, accumulation and checkpointing; this module supplies the concrete tensor computation and loss graph. Discrete structures are selected outside gradients. Zero valid terms produce a differentiable zero and an explicit mask, not a fake supervised observation.

The contract test file checks dedicated positive/negative algorithms, version migration and AST gates without importing or executing tensor source. Dimensions <=64, cases <=64, steps <=128. Fixed mathematical objects are not neural fixtures or generated research data.

## Exact handoff

See `INTERFACE_REPORT.md` for callable signatures, concrete consumer bindings and remaining limits, and `training_api.json` for exact named loss/parameter wiring. All research execution remains NOT_RUN.
