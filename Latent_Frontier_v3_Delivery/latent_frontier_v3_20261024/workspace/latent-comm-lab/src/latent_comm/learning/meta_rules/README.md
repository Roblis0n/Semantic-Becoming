# L08: support-only update rules and query-only outer objectives

NOT_RUN. H38's restricted AST (read gradient → running mean → clip → scale) is interpreted by its actual tensor_interpret, not an arbitrary Python string or a replacement generic optimizer. Scalar reparameterizations preserve negative step size, memory decay in (0,1), and positive clipping thresholds. The inner loop updates only a functional adapter.theta tensor with fresh per-episode memory; no in-place model update or base weight change occurs. The outer shared engine owns only plasticity_rule_parameters.

The four variants separate two batch schemas and two gradient estimators:
- quadratic_full / quadratic_first_order bind the W08 public quadratic family, shared public probes, sender rule and receiver query_condition. Initial theta=(1,2) and zero quadratic target are the published analytic template. Support and query namespaces are distinct to prevent accidental data plumbing; this deterministic family is explicitly not evidence of statistical held-out generalization.
- episodic_full / episodic_first_order require sender support_inputs, receiver query_inputs, public initial_adapter plus distinct support_partition/query_partition IDs. support_targets and query_targets remain in SupervisionBatch. They are separated into typed H38 SupportBatch and QueryBatch only within losses. Query labels never enter a support gradient or AST local environment. This schema must be separately projected and manifest-bound before a future run.

The full estimator creates the support gradient graph; first order explicitly detaches support gradients and drops Hessian terms while retaining rule-parameter paths. Neither is mislabeled as the other. Each episode's support objective is a sum of squared residuals divided by 2, matching the W08 gradient theta; outer query losses are normalized by valid query targets and then equally weighted per valid episode. Empty support or query episodes are skipped with a reason. Pre-clipping update norms are retained for the update-budget penalty, not reconstructed from already clipped updates. Fixed inner_steps and lifetime are enforced before unroll.

Discrete AST choice uses choose_rule_structure: bounded finite validation enumeration with deterministic ties, no gradient through selection and no final-test selection. Continuous scalar training and discrete structure choice are separate. The default fixed AST requires no structure search. Rule/base/inner parameter aliases cannot arise in this construction; only the three raw rule scalars enter the outer optimizer. Exact resume at outer optimizer boundaries recreates episode memory, and shared source cursor/RNG/config hashing restores the same episode ordering. This is source-reviewed only.

## Optimizer, checkpoints and source boundary
The shared learning.engine is the sole AdamW/accumulation/clipping loop. Each phase activates only its named owners, leaves all other parameters frozen, and keeps input graphs recorded. Every batch is physically split into RoleBatch(sender), RoleBatch(receiver), and SupervisionBatch; only losses receive supervision. JsonlSource verifies shard hashes, the train split and structure signatures, rejects mathematical fixtures, and records its exact position/epoch cursor. Checkpoints bind model, data and configuration digests, semantic versions, named owners, Adam moments and RNG states. Resume is source-reviewed, not empirically tested; serialized edges require fresh forward recomputation. No research runtime has been invoked.

Future commands, NOT_RUN and currently policy-denied except --describe:

    PYTHONPATH=src python -m latent_comm.learning.meta_rules.train --describe
    PYTHONPATH=src python -m latent_comm.learning.meta_rules.train --config configs/learning/meta_rules.json --root .
    PYTHONPATH=src python -m latent_comm.learning.meta_rules.train --config configs/learning/meta_rules.json --root . --resume-record RECORD --resume-sha256 SHA256

A future authorized run must bind immutable research-data and model manifests and an exact stage schema first. UNBOUND is deliberately rejected. Source-level completion is not model validation.
