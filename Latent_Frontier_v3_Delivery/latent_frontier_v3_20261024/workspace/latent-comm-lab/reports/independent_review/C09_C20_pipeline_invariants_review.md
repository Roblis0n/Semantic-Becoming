# Independent C09–C20 typed-pipeline invariant review

## Outcome
Three concrete invariant defects were reported early, repaired by the implementation owner, and independently rechecked. No unresolved blocker remains in this focused C09–C20 review at the attached source hashes. This is a source/finite-contract assessment, not empirical research validation or whole-project acceptance.

## Authority and scope
Read current P00, execution_policy.json, P11, composition cards C09–C20, task ownership, implementation modules and relevant mechanism/compiler/runtime interfaces. No design inputs, source files, shared task state or receipts were edited. Only this reviewer-owned report and hash manifest were written. No neural library import, model initialization/download/forward/train/eval/API, paid action, public deployment or unrelated private access occurred. Receipts pending solely because inherited inputs are moving were not treated as defects.

## Substantive object-flow coverage
- C09 binds charts/frames and scale closure, hygienically lowers ISA expressions, transports actual operators and reads behavior. Partial heterogeneous transport remains explicitly noninvertible.
- C10 executes overlap obstruction, a bounded counterexample critic, predicate search and an ontology proposal branch; historical disagreement survives.
- C11 checks answer relations and commuting finite graph edges, binds numeric operators, executes H07 instructions and backtranslates an actual answer.
- C12 converts physical units, performs a rollback-capable SCM graft, compiles shared-noise kernels, and distinguishes do from conditioning.
- C13 binds provenance-bearing adapters and public behavior tangents, transports a finite update and prepares support/query-separated future training.
- C14 checks all read versions including read-only evidence, publishes ontology/partition together, recovers prepare/publish failures, and rolls back using increasing cell versions. Its enclosing version context is explicitly the immutable source snapshot, not a claim that nested candidate versions remain unchanged.
- C15 uses public terminal constraints, finite midpoint dynamics, bidirectional path messages and version-checked asynchronous continuation; hidden terminals are rejected and continuous endpoint residual is checked.
- C16 constructs synthetic worlds and evidence, checks question relations, mutates typed protocols and records lineage without measured competence claims.
- C17 filters permission/locality before query scoring or response evaluation, preserves unknown likelihood, deduplicates evidence and now separates temporary exclusions from persistent evidence posterior.
- C18 deduplicates stable evidence atom/source identities, refuses latent overwrite of exact values, computes a declared finite coalition game and internal Shapley credit, not money or measured capability.
- C19 retains the immutable goal, checks closure and only recovers missing detail from version-bound authorized capsule sources, then rechecks original hard constraints.
- C20 binds concept preconditions, finite answer relations, typed operations, macro semantics, analogy/gauge effects, parameter owners and backend capabilities. Research execution remains locked even if capability metadata is complete.

## Confirmed defects and closure
### R1: receiving chart validity was unchecked
Original c09.register_frames validated the source chart but accepted target_chart.invalidated=True and a target task_family excluding the requested task. Both produced a successful gauge effect in the existing fixture. The repaired path now rejects both with NoMatchingChart. Rechecked independently.

### R2: conditional exclusions destroyed probability mass
With hypothesis 0 observationally equal to hypothesis 1, an exclusion removed 0 before an ordinary response update. Feeding the returned belief into a subsequent assumption-retracted run restored candidate IDs but left weights (0,1,0); a fresh retracted run gave (0.5,0.5,0). The repair persists the unconditional evidence posterior and returns the exclusion-conditioned posterior separately. The same sequential counterexample now equals fresh replay exactly and does not reapply duplicate evidence.

### R3: nested budgets could exceed the fixture limit
The original outer interpreter counted only five or six stages while each nested call created a new budget. C16's standard fixture consumed 68 already-metered steps with only five reported stage steps. The same two-state world with task mutations (inverse, shift) and protocol mutations (add_inverse, add_threshold_concept) attempted step 129. An independent guard stopped before that excess during discovery.

The repair adds context-local aggregate charging and explicit partial ReferenceResult output. The altered grammar now returns BudgetExhausted at 128 steps and 38 cases, with mutate_and_compile/archive_lineage pending. A max_steps=10 call stops at 10. A normal run immediately afterward completes at 68, proving context reset. An independent nested-scope rejection leaves local/inner/outer counters atomically unchanged at (3,3,3). Consumers must inspect ReferenceResult.status before assuming value has the final pipeline type; later horizon/other integration is outside this focused sign-off until stable.

## Actual checks
- Final hash-stable smoke pass: one full standard-library fixture for each C09–C20, all Complete with concrete typed output and stage audit. Exact counts/types are in the companion JSON. A second 12/12 pass also bound the static local-import closure (including compiler registry metadata) to 198 unchanged source hashes.
- Seventeen focused positive/negative regressions passed across stale ISA, numeric edge mismatch, shared noise and do/condition, unauthorized intervention, read-only transaction conflicts, rollback, scope expansion, hidden boundaries, stale continuation, synthetic claims, dedup/exact symbols, missing/retracted refinement sources and learning ownership.
- Independent post-repair counterexamples verified all three fixes, aggregate context reset and atomic nested-budget accounting.
- AST parsing succeeded for reviewed implementation/test files. The composition sources contain no direct research-framework import, dynamic eval/exec/import, subprocess, requests or httpx calls. The final process imported none of torch, transformers, JAX or TensorFlow.

## Limitations
Finite mathematical examples do not validate neural semantics, training quality, learned alignment or unbounded horizon claims. C01–C08 and X01–X12 are not signed off here. Individual mechanism source can continue to evolve; this review applies only to the recorded hashes and must be refreshed for material downstream changes. No external empirical gate or unrequested architectural expansion was imposed.
