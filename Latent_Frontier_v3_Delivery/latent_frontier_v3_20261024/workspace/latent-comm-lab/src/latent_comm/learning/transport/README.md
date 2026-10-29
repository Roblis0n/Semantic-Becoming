# L07: behavior-coordinate direction transport

NOT_RUN. The default source is W08: source_jacobian/source_direction are sender-visible, target_jacobian receiver-visible, and public_probes must match exactly with the task version. Coordinate order is identity-bearing; tokenizer logits are never treated as a shared behavior space.

H37 computes v=J_A Δθ_A by JVP, solves (J_BᵀJ_B+λI)δ=J_Bᵀv using matrix-free JVP/VJP, and separately reports the unregularized unreachable residual. The λ=0 zero-initialized normal-equation iteration has a minimum-norm interpretation conditional on convergence; rank remains explicitly unidentified by the matrix-free solver. Nonconvergence is not silently labeled successful. The learned transport residual is scoped to target external-state coordinates, and a separately owned source-direction calibration has an anchor-preservation penalty against collapse. Actual post-update behavior, JVP linearized behavior, ridge norm and anchor calibration use distinct normalized losses. For this linear family the local residual is identically zero, correctly treated as a diagnostic objective with no spurious empirical claim; nonlinear future behavior probes may make it nonzero.

functional_probe binds the H37 functional_call path for future real models using declared adapter/reader layouts and role-whitelisted kwargs. Frozen model weights must remain frozen by the caller's parameter scope, while the readout input graph stays live. It is not an automatically loaded model binding. The default recipe intentionally remains the concrete W08 family.

Freeze table: transport_operator and behavior_encoder are trained; observed source/target Jacobians and public probes are data, not parameters. No base weights are updated. No discrete estimator is used: numerical solver stopping is a detached control decision, gradients differentiate the executed finite solver path, not an unconditional implicit optimum. Full model binding remains future authorization work, not a fabricated successful experiment.

## Optimizer, checkpoints and source boundary
The shared learning.engine is the sole AdamW/accumulation/clipping loop. Each phase activates only its named owners, leaves all other parameters frozen, and keeps input graphs recorded. Every batch is physically split into RoleBatch(sender), RoleBatch(receiver), and SupervisionBatch; only losses receive supervision. JsonlSource verifies shard hashes, the train split and structure signatures, rejects mathematical fixtures, and records its exact position/epoch cursor. Checkpoints bind model, data and configuration digests, semantic versions, named owners, Adam moments and RNG states. Resume is source-reviewed, not empirically tested; serialized edges require fresh forward recomputation. No research runtime has been invoked.

Future commands, NOT_RUN and currently policy-denied except --describe:

    PYTHONPATH=src python -m latent_comm.learning.transport.train --describe
    PYTHONPATH=src python -m latent_comm.learning.transport.train --config configs/learning/transport.json --root .
    PYTHONPATH=src python -m latent_comm.learning.transport.train --config configs/learning/transport.json --root . --resume-record RECORD --resume-sha256 SHA256

A future authorized run must bind immutable research-data and model manifests and an exact stage schema first. UNBOUND is deliberately rejected. Source-level completion is not model validation.
