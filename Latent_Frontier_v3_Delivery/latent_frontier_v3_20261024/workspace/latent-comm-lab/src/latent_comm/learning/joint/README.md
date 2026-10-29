# L13: composition-aware training organization

NOT_RUN. This module uses the shared engine as its only outer optimizer and provides two concrete kinds of composition training. It does not pretend that the finite C01–C20 reference interpreter is a neural autograd executor.

## Stagewise composition phases

JointStage constructs actual registered L01–L12 stages using a closed module whitelist. Every parameter and objective is namespaced by its component alias; identity validation rejects an accidental shared trainable Parameter under two owners. Frozen model parameters are separately gathered. Each phase lists the active namespaced owners and separately normalized losses with explicit weights. There is no default unweighted global sum. The example alternates transport training and rule training with their other owners frozen.

The JSONL record has outer sender/receiver versions for the joint task, and sender/receiver features.components[alias] contains exactly public_task, features and versions. project_component_role creates a fresh physical RoleView and checks that component's full semantic axes before its real forward_roles. Supervision targets.components[alias] contains exactly targets, valid_masks and source_kind and is projected only inside losses. A component never receives another component's supervisor or the full world record. Component-specific unroll allocations sum to the global cap.

BoundaryContract records producer, consumer, object type, required version axes, scope, gradient mode and reason. Stagewise source records are already stopped/recomputed boundaries. A live edge is explicitly rejected here: serialization cannot preserve a computation graph. Policy-gradient components retain their own score-function losses and stopped rewards. Structure choices and exact proofs are outside pathwise AD. The complete C-route symbolic contracts remain in compositions/; this trainer does not relabel their exact/discrete edges.

## Actual live H37 → H38 subgraph

transport_meta_full and transport_meta_first_order implement the concrete differentiable part of C13, not just a stage name sequence. W08 public source/target Jacobians, source direction and matching probes enter the actual H37 JVP/VJP solve. Its scoped target update is trust-clipped and added to a public initial_adapter tensor without detachment. Receiver support_inputs/query_inputs and explicit distinct public support_partition/query_partition IDs are separate; labels remain in supervision support_targets/query_targets. The H38 whitelisted AST performs fixed-horizon support-only adaptation, and only then reads query labels for the outer objective.

The live path is transport residual/direction calibration → clipped target update → functional initial adapter → support-gradient AST steps → held-out query loss. Full mode retains Hessian terms; first-order mode detaches only support gradients while preserving the direct live transport-initialization edge. Pre-clipping rule update norms and actual post-clipping transport behavior each have their own objective. The remaining H19 trace provenance and H25 coordinate-basis validity are semantic preconditions established by C13's typed compilation, not fabricated observations. This finite linear behavior family is not claimed to have run on unrelated language-model parameters.

Freeze table: transport-only phases activate transport.transport_operator / transport.behavior_encoder; rule-only phases activate plasticity_rule_parameters (temporary functional inner theta may require gradients but is not an optimizer owner); coupled phases explicitly activate all three. The configured estimator chooses exactly one query loss name, never both approximations at once.

## Resume and backend boundary

The aggregate stage has a stable namespaced parameter inventory and full component recipe digest. Component construction and execution always use sorted aliases, so a harmless JSON object-key reorder cannot change which component consumes a restored RNG draw under the same sort-key-normalized digest. Shared engine checkpoints preserve every owned tensor, optimizer moment, RNG state and source cursor at optimizer boundaries; ephemeral inner memory is deliberately recomputed. Backend storage uses tensor-only safetensors plus JSON identity metadata. Loading is separately gated. Frozen model input paths remain differentiable; no generic no_grad wrapper is introduced. Backend-specific model/revision/capability manifests remain explicitly UNBOUND until future authorization.

The approved tests are stdlib projections, namespace/ownership/phase contracts and AST checks. No tensor object, neural fixture or optimizer has been invoked. An initial all-learning audit mistakenly selected three policy-guarded entry calls; all were denied before backend import. This noncompliant attempt is recorded separately in AUDIT_INCIDENT.md and excluded from approved checks. The corrected audit preflights entry-call test names and passes 116 safe checks with no neural imports.

## Optimizer, checkpoints and source boundary
The shared learning.engine is the sole AdamW/accumulation/clipping loop. Each phase activates only its named owners, leaves all other parameters frozen, and keeps input graphs recorded. Every batch is physically split into RoleBatch(sender), RoleBatch(receiver), and SupervisionBatch; only losses receive supervision. JsonlSource verifies shard hashes, the train split and structure signatures, rejects mathematical fixtures, and records its exact position/epoch cursor. Checkpoints bind model, data and configuration digests, semantic versions, named owners, Adam moments and RNG states. Resume is source-reviewed, not empirically tested; serialized edges require fresh forward recomputation. No research runtime has been invoked.

Future commands, NOT_RUN and currently policy-denied except --describe:

    PYTHONPATH=src python -m latent_comm.learning.joint.train --describe
    PYTHONPATH=src python -m latent_comm.learning.joint.train --config configs/learning/joint.json --root .
    PYTHONPATH=src python -m latent_comm.learning.joint.train --config configs/learning/joint.json --root . --resume-record RECORD --resume-sha256 SHA256

A future authorized run must bind immutable research-data and model manifests and an exact stage schema first. UNBOUND is deliberately rejected. Source-level completion is not model validation.
