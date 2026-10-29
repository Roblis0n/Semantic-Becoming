# L01: role separation and exact/latent dual interfaces

NOT_RUN. role_operator binds W01 sender operator and receiver state/readout. Explicit RoleTensors retains the sender field provenance. H01 generates the actual low-rank residual operator factors, then learned read/write maps apply it once and in ordered composition. Public executable operator action provides analytic behavior/composition anchors; the hidden source_result is read only in losses. Frame transport is intentionally L03, not silently inferred here.

The dual_channel extension requires sender sender_features, symbol_packet, symbol_features and symbol_mask; receiver latent_slots, latent_handle, latent_scope, verified_symbol_sources, and any verified_target_refs. Each source/target registry record contains exact versions, Scope and visibility. checked_symbol_packet constructs the real ObjectRegistry, resolves every exact symbol source and referenced target as learning_receiver, resolves the matching latent handle, and rejects supervisor-only or expired/stale scoped objects. Exact decimal strings, units, source identities and references are returned unchanged after H16 fusion. H01 separately generates the live latent operation; H16 attention adds contextual information without decoding replacement exact symbols. Category and conflict heads cannot create authority. Supervision fields task_target, symbol_categories and symbol_conflicts enter only losses. This record extension must be explicitly projected/manifest-bound; no W01 field is relabeled as a verified symbol.

The dedicated source graph is sender-visible operator features → H01 factor generator → receiver read map → low-rank operator → write map → behavior; dual mode adds registry-verified exact symbols → symbol embeddings → H16 cross-attention → latent task/conflict heads. The inherited named LEDGER losses are used exactly, never total plus components. All masks and empty policies are inherited from the dedicated losses or explicit normalized task loss.

Freeze table: mechanism_writer owns factor weights/bias; mechanism_reader owns role read/write or attention/task/conflict parameters; symbol_predictor owns the auxiliary classifier. No base model is implicitly owned. inject_role_receiver gives the actual H01 prefix/residual backend path with RoleBatch-derived ModelInputs, revision-bound capabilities and required live input gradients. A future real-model binding must additionally report its frozen base parameters to the shared engine; it is not silently initialized by this adapter recipe. There is no no_grad around the receiver path.

All structural symbol parsing, scope checks and exact registry bindings are nondifferentiable authority checks, not learned gradients. Continuous operator/fusion paths are live. Builder factor biases are nonzero explicit low-rank seeds to avoid an all-zero U/V dead initialization, but were never instantiated in this task.

## Optimizer, checkpoints and source boundary
The shared learning.engine is the sole AdamW/accumulation/clipping loop. Each phase activates only its named owners, leaves all other parameters frozen, and keeps input graphs recorded. Every batch is physically split into RoleBatch(sender), RoleBatch(receiver), and SupervisionBatch; only losses receive supervision. JsonlSource verifies shard hashes, the train split and structure signatures, rejects mathematical fixtures, and records its exact position/epoch cursor. Checkpoints bind model, data and configuration digests, semantic versions, named owners, Adam moments and RNG states. Resume is source-reviewed, not empirically tested; serialized edges require fresh forward recomputation. No research runtime has been invoked.

Future commands, NOT_RUN and currently policy-denied except --describe:

    PYTHONPATH=src python -m latent_comm.learning.views.train --describe
    PYTHONPATH=src python -m latent_comm.learning.views.train --config configs/learning/views.json --root .
    PYTHONPATH=src python -m latent_comm.learning.views.train --config configs/learning/views.json --root . --resume-record RECORD --resume-sha256 SHA256

A future authorized run must bind immutable research-data and model manifests and an exact stage schema first. UNBOUND is deliberately rejected. Source-level completion is not model validation.
