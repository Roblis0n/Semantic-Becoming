# Finite runtime and recovery (A04)

Requirements: docs/11, P10, A04, H05 continuation, H13 branches, H20 clocks, and H39 cognitive transactions. These are actual state/control algorithms, not model stubs. Research execution remains NOT_RUN.

## Objects and invariants

- VersionedStore stores immutable typed JSON cells, independent semantic VersionSet axes, monotonic per-key versions, and tombstones. A snapshot cannot be modified by mutating a returned value. Transactions record every read, existence test, and blind write. Prepare and commit both validate read versions; disjoint writes cannot hide a read conflict. Delete/recreate does not reset a key version. A single lock swaps the complete candidate state. Type/version changes require named migration provenance and scope checks. The compiler/mechanism validates the migration's semantic algorithm; a runtime provenance name alone is not a mathematical certificate.
- BranchManager provides private snapshots and explicit ancestry. Nested branch merges compare the exact parent draft seen at fork, then merge a validated write set. No averaging of incompatible tensors or structures occurs. Open children must be merged or discarded before their parent can close. The branch count is explicitly metered.
- FiniteScheduler has a capacity-limited priority queue, stable enqueue ordering, permanent event-ID deduplication within its finite ledger, explicit read-version dependencies, bounded retries, and terminal audit records. Clock separates scheduler step, cognitive phase, path index, and causal time. Wall-clock timestamps are not used as semantic ordering. Emission validation occurs before state commit. Registered callbacks are trusted stdlib fixture code, not inferred or imported implementations; this is not an OS sandbox.
- loops.py executes the compiler's bounded schedule with explicit fixture-operation bindings and carried state. It meters each step, validates finite values/dimensions, and rejects unbound source declarations. It never imports the IR's implementation string. All research dispatches and non-fixture handlers enter the central immutable denial gate before callback execution.

## Crash and file semantics

AtomicWorkspace is a Linux single-coordinator implementation using an advisory ownership lock, immutable content-addressed generations, fsynced journal records, and one same-directory atomic CURRENT replacement. Logical files are packaged together in a generation; readers must use the API or the CURRENT generation to obtain atomic visibility. This is not a claim that arbitrary independent filesystem paths, different filesystems, external services, emails, payments, or published files can be rolled back.

Prepare writes a candidate generation but is not a commit. An fsynced COMMIT is the recovery decision. Recovery discards unmatched prepares and rolls all logical files forward after a committed decision. It verifies every hash and lineage link, rejects complete corrupt records, and removes only an incomplete final journal line. An interrupted coordinator refuses reads until recovery. Historical generations are retained, not deleted. Journal capacity, file counts/bytes, task counts, state counts, and all fixture loops are finite; exhaustion is a real failure, never an infinite retry.

Persistent values are sanitized local research state, not raw supervision, secrets, or model tensors. Journals/audit events carry IDs, versions, digests, writes, and terminal reasons, not original training labels. Actual neural tensors and autograd graphs are outside this JSON reference runtime; they require recomputation and future authorized adapters.

## Continuation and invalidation

Scheduler checkpoints are allowed only between events and bind the exact input digest and store digest. Resume after a state change refuses replay and requires explicit reconciliation. The store commit and a later scheduler checkpoint are not advertised as one distributed atomic operation; a crash in that interval is detected, rather than silently replaying an event or claiming arbitrary exactly-once effects.

DependencyIndex stores authoring task states independently of the project's shared ledger. Done requires nonempty output files and actual check files, all hash-bound. Changed input or artifact hashes reset the task and every descendant to pending. Interrupted running tasks return to pending; blocked/failed/cancelled records require a specific reason. This index does not mutate the coordinator's current run_state files.

## Verification and limits

51 finite standard-library tests cover transaction conflicts (including ABA), private branch behavior, queue/dedup/retry bounds, clock separation, before/after-commit fault injection, two-file visibility, torn versus corrupt journals, safe continuation, dependency invalidation, three-step carried IR execution, and no torch/transformers imports. Fault injection raises a local exception; no real host crash or external action is performed. Actual tests use dimensions <=64, steps <=128, and <=64 cases per fixture. Source-design budget metadata can exceed these limits, but these executable fixture APIs cannot.

Not run: neural/model initialization, forward/generate/train/eval, model API calls, bulk datasets, actual model-side continuation, distributed transaction stress, or external effects. This module is not an operating-system security sandbox.
