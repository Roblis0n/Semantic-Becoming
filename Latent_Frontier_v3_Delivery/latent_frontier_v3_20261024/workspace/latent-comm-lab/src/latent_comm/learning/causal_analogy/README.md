# L05: analogy and causal grafting

Status: NOT_RUN. Two dedicated variants share optimizer infrastructure, not mechanism computations.

- graft binds W05 exactly: sender source_module, receiver target_module/boundary_scale, public noise_contract. Public shared-bit versus independent-bit noise determines the enumerated support. Only the source structural coefficient and boundary reader can change; the unaffected target equation is structurally identical before/after. Source coefficient → transplanted equation → joint effect is a live path; boundary scale → parent input → same equation is another. Labels enter only effect/defect losses. Boundary calibration prevents the zero-map degeneracy. This is the explicit linear SCM family, not a claim to identify arbitrary hidden causal modules.
- analogy accepts a separately declared graph-record schema: sender source_operator/state; receiver target_operators/type_compatible/readout; supervisor matched_target, commuting_reference (its valid mask declares squares), target_behavior. Those graph features must be projected using W13 rules before writing research shards. Sinkhorn matching uses the type-compatible partial domain; a soft operation mixture is separately owned. A matrix residual computes F A − B F and the mapped operation is executed into the target readout. All three losses normalize their own valid units. Hardening has no gradient and must call harden_and_verify, which reruns the exact H30 graph check and retains broken squares/unmapped objects.

Freeze table: graft phase trains source_module_generator and boundary_reader; analogy phase trains object_map, operation_map and target_readout. There is no base model in these finite adapter families. Inactive variant parameters are not instantiated. Matching hardening is nondifferentiable, soft matching/operation mixtures use exact continuous gradients; no straight-through estimator is asserted.

The graph schema is not fabricated as W05: the default W05 recipe is graft; future graph records must be separately manifest-bound. Dedicated loss specs in the source record numerator/denominator/masks/owners and empty-policy. Graft joint masks require an entire normalized distribution row; partial atom observations need a different likelihood contract rather than renormalization by accident.

## Optimizer, checkpoints and source boundary
The shared learning.engine is the sole AdamW/accumulation/clipping loop. Each phase activates only its named owners, leaves all other parameters frozen, and keeps input graphs recorded. Every batch is physically split into RoleBatch(sender), RoleBatch(receiver), and SupervisionBatch; only losses receive supervision. JsonlSource verifies shard hashes, the train split and structure signatures, rejects mathematical fixtures, and records its exact position/epoch cursor. Checkpoints bind model, data and configuration digests, semantic versions, named owners, Adam moments and RNG states. Resume is source-reviewed, not empirically tested; serialized edges require fresh forward recomputation. No research runtime has been invoked.

Future commands, NOT_RUN and currently policy-denied except --describe:

    PYTHONPATH=src python -m latent_comm.learning.causal_analogy.train --describe
    PYTHONPATH=src python -m latent_comm.learning.causal_analogy.train --config configs/learning/causal_analogy.json --root .
    PYTHONPATH=src python -m latent_comm.learning.causal_analogy.train --config configs/learning/causal_analogy.json --root . --resume-record RECORD --resume-sha256 SHA256

A future authorized run must bind immutable research-data and model manifests and an exact stage schema first. UNBOUND is deliberately rejected. Source-level completion is not model validation.
