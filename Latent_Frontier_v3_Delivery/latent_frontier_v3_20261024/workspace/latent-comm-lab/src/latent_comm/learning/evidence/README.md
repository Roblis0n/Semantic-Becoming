# L12: coalition learning and logically correct evidence genealogy

NOT_RUN. Coalition stage binds W10: the sender and receiver expose disjoint parts of the known value table, while public player identities and credit_is_money=false define the task. Their role views are joined only inside the dedicated stage. Known empty/singleton/pair anchors yield the actual pair-synergy value family, then learned residual coefficients calibrate it via H41's coalition evaluator. Unknown values remain masked and required missing anchors are errors, never zero observations. A separately owned membership policy samples only known feasible coalitions; its task utility is stopped, and the baseline value score is detached so policy gradient does not silently train the value estimator. This is internal task allocation, not money or a fairness claim.

Evidence variants separate identity, dependence and calibration:
- evidence_identical binds W10's shared source relation. It validates the relation as a true equivalence, collapses repeated occurrences into one atom, and calibrates the one support probability. p OR p remains p.
- evidence_independent needs a bound named declaration_id and a manifest whose finite source family actually asserts independence. Distinct source IDs alone are not permission to factorize. It computes a complete unique assignment truth table with H48 exact_support_tensor.
- evidence_joint likewise requires a named explicit-joint declaration and learns a normalized distribution over the complete assignment table; marginal atom probabilities are derived from that same joint. Its source schema must supply matching explicit_joint targets, not the W10 independence label.
- source_linking uses a separate projected source_features[B,A,F] / supervisor shared_source[B,A,A] dataset. Its learned scores only rank source links; they never authorize identity merges, independence or probability multiplication.

Default W10 training does not fabricate absent source-link features or held-out empirical outcomes. Calibration against W10 analytic probabilities is an analytic-label objective, not evidence of real-world probability calibration. Any empirical calibration requires independently sourced held-out outcomes in a separately bound manifest. The H48 Brier loss retains this distinction.

Freeze table: coalition_value_estimator + coalition_proposer, source_calibrator only, or source_linker only. Exact equivalence checking, unique-atom truth evaluation, named dependence declarations and source lineage are not learned parameters. Separate masks/normalizations cover known coalition values, actual allocations, source pairs or claims. All stochastic allocation gradients use explicit score-function estimates; exact Boolean support and duplicate-atom handling use no invented gradient through source identity.

## Optimizer, checkpoints and source boundary
The shared learning.engine is the sole AdamW/accumulation/clipping loop. Each phase activates only its named owners, leaves all other parameters frozen, and keeps input graphs recorded. Every batch is physically split into RoleBatch(sender), RoleBatch(receiver), and SupervisionBatch; only losses receive supervision. JsonlSource verifies shard hashes, the train split and structure signatures, rejects mathematical fixtures, and records its exact position/epoch cursor. Checkpoints bind model, data and configuration digests, semantic versions, named owners, Adam moments and RNG states. Resume is source-reviewed, not empirically tested; serialized edges require fresh forward recomputation. No research runtime has been invoked.

Future commands, NOT_RUN and currently policy-denied except --describe:

    PYTHONPATH=src python -m latent_comm.learning.evidence.train --describe
    PYTHONPATH=src python -m latent_comm.learning.evidence.train --config configs/learning/evidence.json --root .
    PYTHONPATH=src python -m latent_comm.learning.evidence.train --config configs/learning/evidence.json --root . --resume-record RECORD --resume-sha256 SHA256

A future authorized run must bind immutable research-data and model manifests and an exact stage schema first. UNBOUND is deliberately rejected. Source-level completion is not model validation.
