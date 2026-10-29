# Independent inherited-mechanism contract review

Current V3 M01-M24; selected A02 and B01-B06 state/message/prefix/KV/gradient/tokenizer/coordinate contracts. No later combination completeness requirement.

Outcome: All 13 reported findings and one repair-introduced M07 regression are closed within the stated bounded review scope.
Research execution: NOT_RUN. No neural or array library was imported by review fixtures.

Initial receipt binding: 314 outputs matched current receipts. Final rechecked source binding: 39 files; all still current: True.

## Summary
- Fixed exact KV identity and visible-prefix loss alignment.
- Fixed directional-basis, operator-frame, branch-metadata, and typed-reference contracts.
- Fixed invalid loss enums, explicit empty-mask policy, covariance ownership, and sampled-policy log probabilities.
- Fixed semantic-repair binding, sheaf witness/domain conversion, and transitive grant revocation.
- Independently verified both valid and invalid finite cases where allowed; neural paths were examined as source/AST only.

## IR01 — M02: Nonorthonormal directions change the response operator
Status: closed_receipt_bound_recheck
A=J D and B=D are returned without D^T D=I; tensor prediction uses A B^T. Scalar J=1,D=2 predicts 4, not 1.
Repair: Mirror finite orthonormal basis validation or explicitly use the dual basis.
First-pass receipt source: src/latent_comm/mechanisms/h02_legacy/adapter.py — aa75649c63cc2e3284d5ed61e659ae24f1a4463e7a8d6f606bc6f313f3e159e4
Recheck evidence: M02_M13_M16_M17_recheck.json

## IR02 — B04: Exact KV mode applies learned projections
Status: closed_source_recheck
Identity backend metadata still allowed key/value projection 2I, changing values while claimed exact.
Repair: Exact mode rejects projection/phase parameters and passes through positioned tensor identities; approximate mode retains learned maps.
First-pass receipt source: src/latent_comm/backends/hf_kv/__init__.py — f7dfbb3cc36078f30ee14429821feedc3a79be51bb97ae282158a3dad81d8353
Recheck evidence: backend_recheck.json

## IR03 — M07: Operator frame mismatch passes typed compilation
Status: closed_receipt_bound_recheck
APPLY_OPERATOR checks only kinds and output state preservation, not operator coordinate frame/dimension or actual bound packet metadata.
Repair: Require operator/state boundary type equality and validate runtime bindings against declared types.
First-pass receipt source: src/latent_comm/mechanisms/h07_legacy/reference.py — cc5a59fa14ae74f1de21761c2b5edd881a05d50c23fc64d5f0b4b88d029ab0a9
Recheck evidence: M07_recheck.json

## IR04 — M13: Missing participant metadata is accepted
Status: closed_receipt_bound_recheck
Two branches with structure_ids=(s,) and empty commutation_classes pass initial validation.
Repair: Require one structure and commutation record per branch; preserve independent read/write checks.
First-pass receipt source: src/latent_comm/mechanisms/h13_legacy/adapter.py — eb360b30a3f32d2eae4a35b05c0e57265b8e81df787aa2c5301ee2559f229726
Recheck evidence: M02_M13_M16_M17_recheck.json

## IR05 — M19,M20: Undefined gradient estimator enum blocks import
Status: closed_receipt_bound_AST_recheck
PATHWISE and SCORE_FUNCTION are absent from core GradientEstimator; four top-level references would raise AttributeError.
Repair: Use existing EXACT/POLICY_GRADIENT members and add static enum consistency checks.
First-pass receipt source: src/latent_comm/mechanisms/h19_legacy/losses.py — 8cb19cd72c0c1674e4c520b283566947ffba2c4a0beec57f6d3c45e9cdf89c76
First-pass receipt source: src/latent_comm/mechanisms/h20_legacy/losses.py — b345b5c90e03fa188d1943a8db7ab5b898addc4838a0536516d39c204556255a
Recheck evidence: loss_enum_empty_recheck.json

## IR06 — M19,M20: Empty-mask output contradicts loss ledger
Status: closed_receipt_bound_AST_recheck
Default masked_tensor_mean policy returns LossValue skip objects despite ledger promising differentiable_zero.
Repair: Pass zero_valid_policy explicitly on every loss reduction.
First-pass receipt source: src/latent_comm/mechanisms/h19_legacy/losses.py — 8cb19cd72c0c1674e4c520b283566947ffba2c4a0beec57f6d3c45e9cdf89c76
First-pass receipt source: src/latent_comm/mechanisms/h20_legacy/losses.py — b345b5c90e03fa188d1943a8db7ab5b898addc4838a0536516d39c204556255a
Recheck evidence: loss_enum_empty_recheck.json

## IR07 — B02: Left-padding loss predicts from masked pad
Status: closed_bounded_stdlib_and_source_recheck
P=1, token mask=(False,True), label y: backend physical shift trains y from pad logit 1 instead of visible prefix logit 0.
Repair: Gather each label from previous visible causal position and count only valid predicted labels.
First-pass receipt source: src/latent_comm/backends/hf_prefix/__init__.py — be6f2a71c854eed0a2099e87f83cf320865063901761db715bc57bc1e028776f
Recheck evidence: backend_recheck.json

## IR08 — M17: Covariance head is disconnected from promised objective
Status: closed_receipt_bound_recheck
Dedicated covariance_weight head produces uncertainty, but loss accepts no covariance and ledger claims position/covariance error.
Repair: Add a masked uncertainty loss with exact denominator and parameter owner.
First-pass receipt source: src/latent_comm/mechanisms/h17_legacy/losses.py — 8de3f5b183b96fa23d0786edd2798a22af517e48b5d1d92f8e7652489e562589
Recheck evidence: M02_M13_M16_M17_recheck.json

## IR09 — M16: Entity/reference pointer is not registered as dependency
Status: closed_receipt_bound_recheck
ObjectRef(value) is constructed and discarded; value remains str, invisible to recursive ObjectRegistry dependency validation.
Repair: Retain typed target reference or explicitly validate/declare targets before symbol authority.
First-pass receipt source: src/latent_comm/mechanisms/h16_legacy/types.py — cc2f80c86ccfdd4a38635d6705bf109af51ee7a099a040c7268fd0a18d441305
Recheck evidence: M02_M13_M16_M17_recheck.json

## IR10 — M23: Semantic discrepancy can be treated as numeric repair
Status: closed_receipt_bound_recheck
IDs/digests match but kind and report/session versions are not checked; a semantic_domain report can drive numeric state addition.
Repair: Bind report/repair kind, all semantic versions, source frame and evidence retractions before application.
First-pass receipt source: src/latent_comm/mechanisms/h23_legacy/reference.py — 838ad7010db4d9638de023ac251045c07a5a1981a30005e12dcace0eab8f27df
Recheck evidence: M22_M24_recheck.json

## IR11 — M22: Hard policy has no selected live log probability
Status: closed_receipt_bound_recheck
Hard mode returns deterministic argmax one-hot while dedicated loss/config require POLICY_GRADIENT logprob; controller discards probability graph.
Repair: Separate stochastic policy from deterministic hard evaluation and return selected action plus live log probability.
First-pass receipt source: src/latent_comm/mechanisms/h22_legacy/adapter.py — 5b9dc5ac6fed7b8c1c179755ecd88c56b1f0e9ed56adae9e0f0ff5d99e69835d
Recheck evidence: M22_M24_recheck.json

## IR12 — M24: Derived grant survives parent revocation
Status: closed_receipt_bound_recheck
Confirmed finite source execution: narrow p to c, revoke p, resolve c succeeds. Parent lineage is not retained.
Repair: Track parent grants and enforce revocation transitively.
First-pass receipt source: src/latent_comm/mechanisms/h24_legacy/reference.py — 6eead1facf6a0ba220ba4ae5771a30be9c13ee447e45b59f39f5f7db25ae3c0d
Recheck evidence: M22_M24_recheck.json

## IR13 — M23: Edge obstruction IDs are misused as domain IDs
Status: closed_receipt_bound_recheck
H26 GluingCandidate.conflict_witness lists edge IDs; H23 copies that tuple to conflicting_domains. A legitimate single-edge obstruction yields one string and is rejected as fewer than two domains.
Repair: Bind the source SheafPacket and resolve witness edges to endpoint domain IDs; retain edge witness meaning.
First-pass receipt source: src/latent_comm/mechanisms/h23_legacy/reference.py — 838ad7010db4d9638de023ac251045c07a5a1981a30005e12dcace0eab8f27df
Recheck evidence: M22_M24_recheck.json

## Repair regression
M07 likelihood-vector binding regression was independently caught and corrected. Positive typed belief refinement returns posterior (1/3,2/3); dict binding rejects cleanly. See M07_recheck.json.

## Observed dedicated contracts, not blanket correctness guarantees
- M01 nonlinear gauge transport uses U=G U and V=G^-T V, preserving residual-operator conjugacy.
- M03 whole-sequence branch likelihood is summed before logsumexp; per-token history updates branch weights.
- M04 reference field has an explicit anchor and conservative quadratic step bound.
- M06 distinguishes heterogeneous chart maps from invertible coordinate change.
- M09 separates observation, conditioning and structural intervention.
- M10 exact subset interaction and sampled variance are separately represented.
- M11 byte accounting includes headers, retransmission and request messages; numeric uncertainty is not semantic proof.
- M12 evidence encoder has no future-query argument.
- M14 grammar expansion uses fresh lexical SSA bindings and bounded compilation.
- M15 uses common behavior coordinates rather than cross-tokenizer logits.
- M17 physical unit scaling is propagated to covariance as A Sigma A^T.
- M18 soft routing counts every executed candidate, distinct from sampled routing cost.
- M19 detaches teacher outputs without wrapping student computation in no_grad.
- M20 vector-clock causality is distinct from scheduling step, phase and path index.
- M21 online selection uses public goals and does not mark bounded exhaustion as impossibility.
- M22 transitions advance ownership versions and close old cache references.
- M23 byte integrity and semantic repair are separate operations.
- M24 finite runtime canonicalizes aliases before checking installed scopes.

## Boundaries
- Source correctness is not empirical efficacy.
- No model integration or tensor computation was executed.
- Moving files were skipped; a M23 counterexample attempt aborted on receipt mismatch before project import.
- Parent/owner is responsible for implementation changes; this reviewer writes only review artifacts.
- New consumer integration.py files or config/test additions made after the bounded review are not implicitly certified by this report.
- All closures apply to named findings and the recorded source hashes, not to empirical efficacy or a whole-project completion gate.
