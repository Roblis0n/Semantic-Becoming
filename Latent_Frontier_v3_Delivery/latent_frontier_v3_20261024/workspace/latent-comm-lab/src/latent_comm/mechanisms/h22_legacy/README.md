# H22: Elastic authorized computation partitions and transactional ownership migration

Original algorithm preserved in `types.py` and `reference.py`; the future tensor implementation is `adapter.py`. The exact current recipe and original source are `inherited_v2/hypotheses/H22_动态模型边界.md` and `integration/I22_动态模型边界.md` relative to PLAN_ROOT. The task is M22.

V2 payload fields retained: partitions, cells, capability_graph, action, source_version, target_version, migrations, closed_cache_refs. Missing V3 semantic bindings are rejected by `migrate_legacy`; it never infers a frame, type, evidence source or causal interpretation. Version axes required here: state, frame, ontology, isa, task. Live graphs are not serialized. Stored records require recomputation. `resolve_payload` uses the shared registry's recursive role/version checks.

Connections: H28 explicit structure migration, H39 atomic version read/write set, H41 preauthorized coalition members. These are explicit data contracts and not claims of empirical compatibility. An absent version, map or provenance remains unbound. No cross-tokenizer logit KL is used. Research model and optimizer paths are source only, guarded before backend imports, and NOT_RUN. No research efficacy conclusion follows from the finite examples.

Training: hard partition policy and public handoff behavior; soft all-candidate and hard executed cost kept distinct. Gradients are owned by the mechanism writer/reader unless a LossSpec states otherwise. Base weights may be frozen with `requires_grad_(False)` but receiver input gradients remain connected. The shared learning trainer controls optimizer, clipping, accumulation and checkpointing; this module supplies the concrete tensor computation and loss graph. Discrete structures are selected outside gradients. Zero valid terms produce a differentiable zero and an explicit mask, not a fake supervised observation.

The contract test file checks dedicated positive/negative algorithms, version migration and AST gates without importing or executing tensor source. Dimensions <=64, cases <=64, steps <=128. Fixed mathematical objects are not neural fixtures or generated research data.

## Exact handoff

See `INTERFACE_REPORT.md` for callable signatures, concrete consumer bindings and remaining limits, and `training_api.json` for exact named loss/parameter wiring. All research execution remains NOT_RUN.
