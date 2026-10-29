# Independent C01–C08 typed-pipeline invariant review

## Outcome
Three concrete object-flow defects were reported early, repaired by the source owner, and independently rechecked. No unresolved blocker remains in this focused scope at the companion hashes. C01–C08 all produced concrete typed outputs under the aggregate finite limits. Earlier accepted C09–C20 results were not rerun; X01–X12 remain outside this review until their sources are stable.

## Scope and method
Read the current task cards, ownership/design registry, inherited eight-route design (read-only reference), C01–C08 source/config/tests, and actual mechanism interfaces. Current P00 and execution policy remained authoritative. No source, design input or shared task state was edited. Only these reviewer-owned report files were written. Checks used standard-library finite examples; no model frameworks imported, no weights/model initialization/forward/training/evaluation/API, and no external action.

## Confirmed findings and repair verification
1. C01 allowed target chart and operator ontology to change together while source chart, partition and reported result stayed in ontology o1. This silently crossed a semantic boundary merely because frame/shape checks passed. The repair binds the source chart to the exact snapshot, permits only explicit target-frame change, and binds the operator to the complete target context. The exact synchronized target-chart/operator counterexample now raises MigrationRequired; valid heterogeneous projection still completes.
2. C05 accepted source and target physical observations both marked old-world while their relation graphs/charts/request remained w1, returning an action labeled w1 with a changed object still in old-world. The repair binds each side’s objects, relation packet and chart on world/task/ontology/evidence while preserving explicit physical and latent frame conversion. The exact stale-world counterexample now raises VersionMismatch.
3. C07 unconditionally rebuilt an empty CapsuleStore in its final revoke stage. An otherwise readable existing capsule with parent_version failed there, even with no requested revocation, and the input had no way to supply its ancestry. The repair adds explicit existing capsule lineage and validates it topologically before any write. Supplied parented capsules now work; missing ancestry fails in scope_check; explicit dependency withdrawal rejects before query/write; source withdrawal invalidates both supplied parent and child and revokes the grant. No ancestor records are invented.

## Mechanism-semantic coverage
- C01 performs actual local chart projection, capability-preserving partition handoff and typed operator execution. It does not claim an inverse for information-losing projections.
- C02 forms actual response-derived linear constraints, checks validity before and after field motion, diagnoses source residuals and leaves a re-solve obligation after refreshing. Unauthorized sources are not silently dropped.
- C03 keeps computation branches and probability identities separate, preserves conflicts, supports safe disjoint-slot reuse, and uses sequence-level rather than tokenwise mixing. Repeated evidence does not multiply belief again.
- C04 captures/resumes exact finite DSL suffixes at multiple cutpoints, respects dependencies and stale receiver versions, and distinguishes this from heterogeneous model-cache equivalence.
- C05 matches anchored relation graphs, validates physical observations, separately transports physical units and latent coordinates, and performs only a labeled synthetic action. Ambiguous matching performs no action.
- C06 expands typed skills, executes local operators and a genuine multilinear joint effect, preserves evidence provenance, and only compiles the affine local component rather than mislabeling the joint interaction as one affine skill.
- C07 resolves installed capabilities before reads/writes, checks source dependency versions and calibrated protocol compatibility, performs a typed residual repair and scoped local effect, then represents revocation as future access/evidence invalidation rather than unlearning.
- C08 expands safe macros, proves agreement of its declared affine sublanguage via coefficient propagation, checks exact owned-state references and executes both graph and program. Nonlinear/unequal graphs are not accepted through probe fitting. Budget exhaustion returns explicit pending stages.

## Actual checks and boundaries
Final hash-stable pass: 8/8 full fixtures Complete, with aggregate steps 7, 12, 5, 14, 6, 11, 8, 15. Nineteen focused regressions passed across ownership, chart coverage, refresh, conflicting beliefs, repeated evidence, continuation cuts/dependencies/staleness, ambiguous grounding, trace separation, capability/retraction boundaries, affine equivalence and partial budgets. Additional independent repair counterexamples and lineage cases passed. The JSON binds the static local-import closure plus compiler registry, tests and configs and records exact output types/counts.

This verifies finite source contracts, not neural usefulness, learned alignment, arbitrary program equivalence, empirical distillation or unlimited future horizons. No empirical admission gate or unrequested architecture was imposed. Material source changes invalidate only the affected hash-bound conclusions.
