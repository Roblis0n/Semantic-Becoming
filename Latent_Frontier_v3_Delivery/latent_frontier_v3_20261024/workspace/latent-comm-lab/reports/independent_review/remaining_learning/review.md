# Remaining training-stage source review

Final snapshot: L01, L02 and L04–L13 are source-reviewed at current matching receipt bytes. All four concrete findings from this continuation review are repaired and independently verified. No unresolved defect remains from this scoped review. This is scoped source assurance, not whole-project acceptance or empirical training validation.

## Authority and methods

The current task cards, P00/P09 instructions, execution policy, role/data contracts and document 09 govern this review. No neural module was imported; no model, initialization, forward, train, generation, optimizer, gate-entry test, or bulk dataset generation was invoked. The review used source reading, AST parsing/signature binding, pure metadata/role validators and bounded stdlib fixtures only. Source and shared run-state were not edited. Only this review directory was written.

The independent passes ran 100 safe checks across L01, L02 and L04–L13 (89 stable-stage checks plus 11 final L13 checks). All passed; torch, transformers, tensorflow, jax and numpy were absent from sys.modules. The two L04 tests that invoke blocked research entry points were explicitly excluded. Checks retain the fixture caps of dimension 64, 128 steps and 64 cases per bounded fixture. AST binding found no mismatch in 353 resolvable direct imported project function calls; dynamic/member tensor APIs were separately inspected, not executed. No tensor-runtime compatibility claim is inferred from that static check.

The twelve current task receipts' output and check hashes match disk. The accepted L03 shared engine/contracts/source hashes are unchanged, so their accepted tests were not rerun. Stage entry points continue to delegate optimization, accumulation, clipping and tensor/RNG/source-cursor persistence to that engine. Stage-specific ephemeral solver/meta-learning state is freshly recomputed. Exact resume remains source-reviewed, not empirically established.

## Concrete findings and disposition

### L04: Default semantic versions incompatible with actual role records — repaired

The original single recipe version map required frame=f1 and isa=i1 for both variants. W03 concept records have no frame/isa; W04 question records have isa but no frame. The shared engine correctly rejects such mismatches before forward, so the default recipes could not bind their advertised actual records. The repair uses explicit versions_by_variant and a pure resolve_versions selection called from the gated runner. Independent AST comparison with the actual generators and seven safe L04 tests confirms the selected versions exactly match the advertised role records.

### L05: Missing operation-map owner on live behavior objective — repaired

AnalogyStage behavior uses the learned operation mixture in `(readout + delta) @ operation @ matching @ state`, but the inherited ledger omitted operation_map. This rejected a valid operation-map-only behavior phase and misstated the live gradient path. Stage-local ANALOGY_LOSS_SPECS now includes object_map, operation_map and target_readout on behavior, while matching remains object_map-only. The opaque-owner phase regression passes independently. No general mechanism ledger or unrelated stage was rewritten.

### L01: Missing upstream owners on dual-channel auxiliary objectives — repaired

The symbol/conflict heads consume a live pair derived from both the H01 writer and H16 reader. The inherited auxiliary ledger omitted upstream owners. DUAL_LOSS_SPECS now assigns writer+reader to conflict and writer+reader+symbol_predictor to symbol_structure. No detach was added to disguise a missing edge. Writer-only and reader-only phase checks for each auxiliary loss pass independently.

### L13: Component order not bound by recipe identity — repaired

The initial stable source hash was 308d6b4b9acc33965d8dccc39759a2d8d2a3798cfd3867859bc9c068807b6aef. JointStage stored dict(components) and iterated components.items(), while the run recipe digest used json.dumps(config, sort_keys=True). Reversing two stochastic component keys therefore preserves the accepted checkpoint recipe digest but reassigns successive restored RNG draws to different components. A two-component stdlib witness, accompanied by AST checks of the actual source, reproduced the collision without neural execution. The writer repaired both construction and storage using one validated component_order helper. All forward/loss/parameter traversals now follow the canonical stored alias order. The exact seeded RNG regression and all 11 final L13 checks pass independently. L13 receipt output/check hashes match, including final source e5f0f4b37603e67f4c809fe7fc4b1faf053b91986273881301e65e0c4accb13b.

## Stage-specific review coverage without an additional asserted defect

- L01: W01 operator composition uses actual H01 factors, nonzero factor seeds, explicit sender provenance and receiver maps. Exact symbolic sources, target references, versions, scopes and latent handles are checked before H16 fusion; symbolic authority is not generated by a classifier. Backend injection retains input gradients and does not silently initialize a base model.
- L02: Ordered operator programs are applied sequentially, not added. Response applicability masks both response and downstream task loss, with separate refresh training. Belief objectives sum complete per-branch sequence log likelihood before logsumexp; shifted teacher forcing enters only losses. Compatible one-to-one coverage matching excludes explicit unknown branches without discarding their probability mass. Generation paths have explicit horizons and prefix-dependent branch posteriors.
- L04: Predicate execution and distinction/drift objectives remain separate from discrete description selection. Question relation, answer mapping and stopped-reward selector paths are distinct. Targets are not available to forward_roles.
- L05: Causal grafting preserves the declared shared versus independent noise atoms and leaves the unaffected target module unchanged. Analogy shape/order paths and finite hardening revalidation were traced.
- L06: Reciprocal midpoint trajectories, constrained-boundary solve, scale closure/detail memory and bifurcation objectives use their dedicated algorithms. Version maps distinguish frame-aware scale records. Horizon and endpoint behavior were inspected statically.
- L07: Explicit common behavior coordinates drive the actual H37 matrix-free solver; nonconvergence rejects rather than silently accepting an unknown solve. Named scope and anchor calibration are retained; no token-space equivalence is invented.
- L08: Support and query partitions are distinct. Only support labels enter inner updates. The H38 restricted AST has bounded inner steps and fresh episode memory; full versus first-order gradients are explicitly distinguished. Raw pre-clipping update norms remain available to the budget objective.
- L09: Typed macro lowering and exact executable targets remain distinct from the trained fast implementation. Structural choice uses finite selection, not fabricated differentiability.
- L10: World kernels sum each shared noise atom once and use probability-weighted transition targets plus finite distribution rollouts. Dream/protocol and ecology/proposer phases have separate owners. Independent holdout error is stopped in proposer credit, while functional adaptation uses a detached copy rather than mutating protocol state.
- L11: Active identification uses independently checked finite response tables and no fabricated prior. Hard exclusion is proof/certificate based, not a learned-logit threshold. Quotient behavior is task-relative; exact partition operations remain distinct from soft clusters.
- L12: Coalition known-value/feasibility masks are explicit; policy utility and baseline value score are stopped. Evidence identity is checked as an equivalence relation; duplicate sources are collapsed once. Independence/joint calibration requires a named declaration and is not inferred from source-link similarity.
- L13: Source-stable graph inspection confirms fresh physical component projections, semantic version checks, namespaced parameter ownership and bounded total unroll allocation. The concrete transport-to-plasticity path preserves the live transported initialization; only support gradients are stopped in first-order mode. Query labels enter after support-only adaptation. First-order update-budget ownership is narrowed to rule parameters. Serialized boundaries do not claim a live autograd edge.

## Boundaries of this result

Recipes intentionally remain UNBOUND to external research manifests and all model execution remains NOT_RUN. Custom record extensions are identified as extensions, not silently treated as preexisting world records. No claim is made about empirical performance, convergence, full optimizer determinism, arbitrary invalid custom stages, changed library versions, or unreviewed project tasks. Exact reviewed output/check hashes and receipt states are in hash_snapshot.json and verification.json. safe_checks.txt records the independent safe test results.

## Final hash-bound checks

L13 is receipt-current at 2026-10-24T18:03:04Z. All twelve reviewed continuation-stage receipts have matching output/check hashes; no source mutation was made by this reviewer. Shared L03 source hashes remain equal to the prior accepted snapshot. These facts are rechecked at the final review timestamp in verification.json.
