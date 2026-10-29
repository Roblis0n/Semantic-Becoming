# H14: Hygienic typed skill grammar lowering

Original algorithm preserved in `types.py` and `reference.py`; the future tensor implementation is `adapter.py`. The exact current recipe and original source are `inherited_v2/hypotheses/H14_潜技能语法.md` and `integration/I14_潜技能语法.md` relative to PLAN_ROOT. The task is M14.

V2 payload fields retained: productions, grammar_version, base_isa, task_family. Missing V3 semantic bindings are rejected by `migrate_legacy`; it never infers a frame, type, evidence source or causal interpretation. Version axes required here: ontology, isa, frame. Live graphs are not serialized. Stored records require recomputation. `resolve_payload` uses the shared registry's recursive role/version checks.

Connections: H27: explicit ontology version in types, H30: operation mappings not name similarity, H40: every skill lowers to immutable base ISA. These are explicit data contracts and not claims of empirical compatibility. An absent version, map or provenance remains unbound. No cross-tokenizer logit KL is used. Research model and optimizer paths are source only, guarded before backend imports, and NOT_RUN. No research efficacy conclusion follows from the finite examples.

Training: production classification, expanded execution and condition-guarded rewrite losses. Lexical binding never reads caller locals implicitly; structures discrete, parameters differentiable.. Gradients are owned by the mechanism writer/reader unless a LossSpec states otherwise. Base weights may be frozen with `requires_grad_(False)` but receiver input gradients remain connected. The shared learning trainer controls optimizer, clipping, accumulation and checkpointing; this module supplies the concrete tensor computation and loss graph. Discrete structures are selected outside gradients. Zero valid terms produce a differentiable zero and an explicit mask, not a fake supervised observation.

The contract test file checks dedicated positive/negative algorithms, version migration and AST gates without importing or executing tensor source. Dimensions <=64, cases <=64, steps <=128. Fixed mathematical objects are not neural fixtures or generated research data.

## Exact handoff

See `INTERFACE_REPORT.md` for callable signatures, concrete consumer bindings and remaining limits, and `training_api.json` for exact named loss/parameter wiring. All research execution remains NOT_RUN.
