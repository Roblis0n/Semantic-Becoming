# Focused review: Latent Frontier v3, M25–M38

Status: no unresolved blocker among the findings raised in this focused review, after writer repairs and independent recheck. This is not a whole-project acceptance, full mathematical proof, neural integration test or empirical readiness decision.

## Scope and method

- Read P00, execution policy, P03, all 14 task cards and relevant mechanism definitions; checked L04 ownership before raising the H29 graph gap.
- Inspected dedicated types, finite algorithms, tensor adapter source, loss/gradient ledgers, payload schemas/migrations, recipes, tests and receipts. Deeper review: H27, H29, H37 and H38.
- All 140 declared task outputs currently match their 14 receipt hashes; all receipts retain NOT_RUN. Exact file/receipt hashes are in reviewed_file_hashes.json.
- AST/source checks found no empty concrete core functions or top-level neural-library imports in this scope. Common codecs are shared patterns, but their objects and finite algorithms are mechanism-specific, not generic MLP/chat wrappers.
- Executed only small standard-library symbolic/matrix cases. Largest explicit reviewed reproduction had three parameter coordinates and a four-case answer domain; no model initialization, neural import, adapter call, forward, training, benchmark or external research API occurred.
- Existing contract definitions were read for meaningful positive, boundary and counterexample behavior. This review did not rerun the entire test suite. Tensor behavior was inspected as source only; scalar/source-expression checks below must not be described as executed tensor tests.

## Findings and verified repairs

1. H38 outer optimizer could own arbitrary base/inner parameters. Fixed with exact parameter-identity ownership and alias exclusion before zero_grad/backward/step. Recheck used plain object identities: intended ψ accepted; extra/missing/duplicate parameters and aliases to initial θ rejected. Locations: h38_plasticity/reference.py::validate_optimizer_ownership and adapter.py::meta_train_step.

2. H27 schema validator inspected only the root predicate field. A nested not(le(undeclared,5)) passed with domain=[expires] and accessed undeclared evidence. Fixed by recursive atom-domain validation in ConceptDefinition and codec. Original payload and direct invalid construction now reject; valid nested declaration passes. Locations: h27_ontology/types.py::ConceptDefinition and serialization.py::validate_payload.

3. H38 learned scalar bindings on running_mean/clip/precondition_diagonal were accepted but ignored. Both interpreters now consistently consume the bound scalar with operator-domain checks. The original one-scalar reproduction now produces 1.8 for beta=.1 and .2 for beta=.9 instead of 1.0 for both; beta=2 rejects. Unsupported parameter bindings reject. Locations: h38_plasticity/reference.py::validate_rule/interpret and adapter.py::tensor_interpret.

4. H26 tensor homogeneous-zero check was batch-global. Without anchors, bias [[1],[0]] previously allowed the second row to manufacture zero consensus. Fixed source checks all-zero evidence per batch row. The replacement expression and standard-library truth table were rechecked; tensor path remains unrun. Location: h26_sheaf/adapter.py::tensor_glue.

5. H29 initially lacked the task-card's bounded question-graph construction despite having sound individual rewrite and solution-relation primitives. Added RewriteRule, TransformLibrary, QuestionEdge, QuestionGraph, bounded graph builder and checked graph answer transport. Recheck retained a rejected auxiliary rewrite and its reason, a lost-root witness on a valid strengthening, a checked backtranslated answer, and a frontier at the candidate budget. No later L04 optimizer/training deliverables were demanded. Locations: h29_questions/types.py and reference.py::build_question_graph/transport_graph_answer.

## Coverage by mechanism

### H25

Gauge frame/state/operator/readout covariance; solve-based transport, cross-map and ordered path composition.

Meaningful distinction/counterexample inspected: singular/ill-conditioned frames; rotating only state changes behavior.

### H26

Affine cover constraints with hard-anchor elimination, overlap residuals and inclusion-minimal conflict witness.

Meaningful distinction/counterexample inspected: unanchored zero consensus; inconsistent cycle; missing overlap.

### H27

Executable three-valued predicate AST; finite concept search, extensional provenance and versioned ontology/consumer migration.

Meaningful distinction/counterexample inspected: unexpressible pair; missing/unknown evidence; retirement without replacement; nested-domain mismatch.

### H28

Pitchfork potential, continuous versus Euler stability, branch trajectory and explicit structural migration/cache invalidation.

Meaningful distinction/counterexample inspected: Euler instability is not a semantic phase transition.

### H29

Finite polynomial question IR, affine answer programs, verified solution relations, auxiliary elimination, bounded typed rewrite graph and checked solution transport.

Meaningful distinction/counterexample inspected: lost negative root; noninvertible relation; invalid auxiliary domain; rejected graph edges and bounded frontier.

### H30

Typed operation-graph morphisms, finite symmetric matches, commuting squares and verified target program composition.

Meaningful distinction/counterexample inspected: unmapped operation and type mismatch; failed commuting square.

### H31

Affine SCM module graft, explicit unit/noise interface, acyclic descendant recomputation and version-safe rollback.

Meaningful distinction/counterexample inspected: unit conflict; introduced cycle; copied noise identity.

### H32

Immutable goal digest, dual weight solve, retained lossy preference directions, original constraints and Pareto set.

Meaningful distinction/counterexample inspected: invariant objective value does not override original hard constraint.

### H33

Separated dissipative/skew dynamics with midpoint integration, readout windows and versioned coupling changes.

Meaningful distinction/counterexample inspected: Euler spurious norm gain; stale coupling; nonorthogonal migration.

### H34

Forward/backward reachable sets, bounded complete path candidates and retained pending work from public terminal constraints.

Meaningful distinction/counterexample inspected: infeasible boundary; multiple paths; hidden future label as terminal.

### H35

Coarsen/lift/detail objects, affine dynamic closure, explicit memory repair and refinement restrictions.

Meaningful distinction/counterexample inspected: same macro state with different next macro state; missing detail cannot be inverted.

### H36

Executable scoped claims, finite challenges, verified counterexamples, revision history and unresolved disputes.

Meaningful distinction/counterexample inspected: textual assertion is not executable evidence; agreement is not truth.

### H37

Public-behavior anchors and scoped linearization; CGLS plus finite rank/projection diagnostics; source-only functional JVP/VJP adapter.

Meaningful distinction/counterexample inspected: heterogeneous parameter dimensions; rank-deficient unreachable direction; ridge residual differs from unreachable residual; stale anchor.

### H38

Whitelisted stateful plasticity AST, typed support/query split, bounded update scope/lifetime, exact-unroll and named first-order source, constrained learned scalar bindings.

Meaningful distinction/counterexample inspected: forbidden read/write scope; held-out query leakage; expired rule; ignored scalar and optimizer ownership mutations.

## Important boundary conclusions

- H27 changes a computational concept through executable predicates and versioned consumers, not only labels or embeddings. Its tensor losses distinguish pair separation, behavior and drift; structure enumeration is not falsely called differentiable.
- H29 keeps soundness and completeness separate and records invalid answers/lost solutions. An independent two-step auxiliary-then-strengthening case remained sufficient, not equivalent, and preserved the lost negative root.
- H37 transports behavior effects rather than raw parameter coordinates. An independent 2-to-3 parameter-coordinate, rank-deficient ridge case returned delta=(.8,0,0), unreachable residual=(0,-3), and a separate regularization effect residual. Matrix-free rank remains explicitly unidentified rather than fabricated.
- H38 implements multiple whitelisted update operations and state memory, not merely a renamed SGD step. Source explicitly separates exact second-order unroll from first-order approximation, and query data enters only the outer loss call. Empirical usefulness and neural correctness remain untested.
- Schemas, migrations, specific losses, owners, valid masks and gradient-stop declarations are present throughout the reviewed mechanisms. Broader training organization and integration belong to downstream tasks; this report does not accept those tasks or claim they are complete.

No source, tests, configs, receipts or shared project state was edited by the reviewer. Only this review report and its hash snapshot were created.
