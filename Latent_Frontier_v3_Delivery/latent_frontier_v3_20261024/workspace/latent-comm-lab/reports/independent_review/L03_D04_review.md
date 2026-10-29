# L03/D04 focused source review

Status at final snapshot: all six reported defects are repaired and independently rechecked. No unresolved defect remains from this focused review. This is not whole-project acceptance.

## Authority and methods
Read the current P00, L03/D04 task cards, P09/P23 role prompts, docs 08/09, current execution policy, L03/D04 receipts, and actual target source. No model, neural library, training, optimizer, forward, initialization, dataset generation, or external model API was run. No source or shared task-state files were edited. The only executed project paths were stdlib metadata/RoleView/template validators. All such processes confirmed that torch, transformers, tensorflow, and jax were absent from sys.modules. AST parsing passed for the snapshotted Python files. The final recheck ran 34 safe checks: all 17 D04 tests plus 17 L03 stdlib/AST/finite tests. The two L03 tests that call blocked research entry points were deliberately excluded, with the entry gate checked statically instead. All 34 passed. Fixture sizes stayed below the declared caps.

## Findings

### D04-1: Forbidden metadata leaked into template input — repaired and verified
Original compiler hash: 61ba96b4833920d55de4e3c8f79f4747bd7b9f91b09dcd73761abed52a89d400.
The data contract forbids record_id and manifest_digest as model inputs, but the original RoleView and D04 forbidden-field lists omitted them. A RoleView with either key in features was accepted and serialized by compile_template. The repair adds recursive D04-boundary checks and aligns the D04 contract. Compiler e2b2fbbd4282c2da6d787ff889bc565212100eac9ad9e35e2a970cdacd3ec43c passes the rejection tests. A subsequent coordinated repair moved the classification into core.views.FIELD_CLASSIFICATION; D04 uses that authoritative set and its new consistency test passes. record_id and manifest_digest are now also rejected by RoleView itself.

### D04-2: Nested JSON exponent overflow accepted — repaired and verified
Original validate_response parsed 1e1000 into infinity. parse_constant only covered NaN/Infinity tokens; the open-ended answer payload did not recurse into SchemaValidator. The concrete receiver response {"status":"present","answer":{"value":1e1000},"used_object_refs":[],"obligations":[]} was accepted. The first repair used finite parse_float; the final coordinated repair routes D04 through core load_json and recursive validate_finite_json_tree. The exact nested exponent-overflow response is rejected. D04 now has 17 independently passing stdlib tests.

### L03-1: Nonfinite weight decay accepted — repaired and verified
contracts.py Phase.__post_init__ checked weight_decay < 0 without isfinite. Both Phase('p', ('owner',), (('loss', 1.0),), 1, 1e-3, float('inf')) and the NaN variant were accepted by the actual pure metadata validator. Repair adds finite nonnegative weight decay validation; both original NaN and infinity witnesses are now rejected in the independent rerun.

### L03-2: Weighted/reduced objective not checked for finiteness — repaired and verified
engine.py validates each unweighted loss, then multiplies by weights, sums and averages before backward without checking the aggregate. Finite operands may overflow (stdlib example 2.0 * 1e308), and finite derivatives do not imply a finite objective. Gradient clipping therefore is not a replacement. Minimal repair: validate the final scalar objective before backward. This finding is based on actual source operations and a scalar arithmetic witness, not neural execution. The repair now checks objective.ndim, torch.isfinite(objective), and objective.requires_grad before backward. AST inspection confirmed the finite guard precedes backward in the live loss branch.

### L03-3: Covariance loss lists a disconnected owner — repaired and verified
frames/__init__.py reuses the H25 general LOSS_SPECS, which declare read_write_heads as a covariance owner. The actual L03 covariance residual depends only on the left/right cross_map calibration; readout_delta is used only in behavior. validate_phase therefore accepts a read_write_heads-only/covariance-only phase with no live owner path. The stdlib metadata validation accepted this configuration. Repair adds FRAME_LOSS_SPECS with covariance owned only by cross_map. The previously accepted disconnected phase is now rejected by the actual stdlib validator. The general H25 ledger was not rewritten for this stage-specific fix.

### L03-4: Batch semantic versions are not matched to stage versions — repaired and verified
TrainingBatch checks sender/receiver equality and RoleBatch checks internal consistency, but engine.py sends a batch to the configured stage without matching the stage's declared version axes. JsonlSource trusts per-record VersionSet values. A consistently paired f2/t2 batch is therefore not rejected for an f1/t1 stage and can be saved under the stage's metadata. Minimal repair: compare stage-required, non-null axes before forward. The repair calls validate_batch_versions before stage.forward_roles; its default axes are the non-null configured stage versions. The pure version-mismatch regression passes and source ordering is confirmed by AST. Unspecified axes remain unconstrained, so an extra evidence e1 axis is not mistakenly rejected.

## Areas reviewed without an asserted defect
- Current-task research gates unconditionally reject before neural imports, callbacks or model construction. Describe paths are metadata only.
- Owner validation rejects identical parameter objects across owners and frozen-base mappings. L03's built owners are separately constructed. No storage-alias claim for arbitrary user-supplied stages was empirically tested.
- Frozen base handling uses requires_grad_(False), not a blanket receiver no_grad. The only no_grad block is checkpoint data restoration, not a live bridge.
- Losses have explicit per-term ledger fields, weights and valid-mask skip reasons. Current accumulation intentionally averages valid microbatch totals. The source is cyclic and optimizer-step-budgeted, not an epoch-limited iterator, so there is no final partial batch in this particular contract. No artificial partial-epoch defect is asserted.
- AdamW owner state is carried between phases and saved with all learnable parameters, CPU/CUDA/Python RNG and cursor. Load verifies record/tensor hashes, model/data identity, config/run identity, parameter names and shapes. The current learning rate is fixed per phase; there is no stateful scheduler to persist.
- RoleBatch/SupervisionBatch are physically separate. engine.forward_roles receives only sender and receiver. Supervision only enters losses. Template auxiliary roles retain sender/receiver visibility instead of gaining full-world access.

## Limits
Exact resume is source-reviewed, not empirically established. No optimizer or neural path may be run under the current policy. This review does not certify arbitrary future stage state, changed tensor-library behavior, later L tasks, or the whole project. Later L tasks were not stable/assigned at review time and are not treated as L03 defects. hash_snapshot.json records the exact reviewed bytes.

## Final exact-byte verification

All recorded output/check hashes in the current L03 and D04 receipts match disk at this snapshot. This checks these two receipts only, not the lead-reported 62-task global revalidation. Initial and final source hashes are retained in initial_hash_snapshot.json and hash_snapshot.json. No claim of empirical optimizer/resume validation is made.

- src/latent_comm/learning/contracts.py: 984c9e2e33338e14d6ebd487f69381322029175d620db68c0e5902f7221f1707
- src/latent_comm/learning/engine.py: bc032b047613e49c67de4a8f911c0615cd7aae42d27a21e3b443580443fb9569
- src/latent_comm/learning/frames/__init__.py: 68f14ae03ed8a5cc810be96fd398ef406c14419a8a5b9d9cd54ee109d56b725b
- prompts/model_templates/compiler.py: 7418dc649b3e09de3535d61eae5fb95a04d40b325a701b4f1666ac357ef7835a
- src/latent_comm/core/views.py: 769bd5510b6cdf4fa2806b497b5068189fa29dfcf17de0035216b69282eca844
- src/latent_comm/packets/schema.py: 46b6abf6a61101cbc94ce45bcd9712757afe3a618e1b651ccdfaa8c7eb05e8eb
