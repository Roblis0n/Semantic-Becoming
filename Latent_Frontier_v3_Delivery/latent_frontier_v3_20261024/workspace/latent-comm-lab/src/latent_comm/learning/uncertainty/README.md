# L11: legal queries, negative knowledge and task-relative quotients

NOT_RUN. identification and exclusions bind W12; quotient binds the finite query domain underlying W07 and uses a frame-aware variant version record.

Identification: public allowed_queries is the entire local action domain. The sender supplies only the declared y=x/y=−x programs. A dedicated response encoder predicts categorical responses in the public finite outcome alphabet; a separate proposer scores numerical query features and samples only allowed candidates. W12 explicitly has no prior, so proposal credit is the independently checked minimax partition reduction, not invented Bayesian information gain. Response NLL and stopped policy-gradient reward have separate normalizations. No query is actually sent to an external service. Queries that cannot distinguish hypotheses retain zero reduction rather than false certainty; an absent hypothesis remains outside the finite family.

Negative knowledge: H46's actual proposal function trains predicate and scope scores. Hard pruning is generated only by certified_domain, which builds a complete executable finite witness for the exact {1,2,3,4} domain and checks current assumptions/version through H46 apply_exclusions. Learned confidence grants no hard authority. Deactivated assumptions restore all candidates; soft even preferences never hard-prune. Verified excluded-domain labels train the predicate classifier only while the hard scope is active; inactive or merely soft scopes do not provide hard-predicate labels. Scope applicability is an explicit known public fact. Retraction and dependency verification remain symbolic, not falsely differentiable.

Quotient: state/query projections and learned prototypes predict task behavior and soft information rate using H47's actual task-relative encoder. Public parity / greater-than-two queries on the explicitly finite W07 {1,2,3,4} domain supply executable target responses; raw input reconstruction is not the objective. The output is approximate learned clusters, never asserted to be exact equivalence. exact_partition separately checks executable signatures, retaining the source domain so adding a query can refine classes. No gradient flows through this exact class creation/refinement.

Freeze table: response_encoder + query_proposer; exclusion_generator + scope_predictor; or state_encoder + task_conditioner + prototypes, depending on variant. Proof checker, host action mask, domain identity and exact equivalence are never trainable. Loss source lists all valid-mask and denominator units; supervision stays outside forward_roles.

## Optimizer, checkpoints and source boundary
The shared learning.engine is the sole AdamW/accumulation/clipping loop. Each phase activates only its named owners, leaves all other parameters frozen, and keeps input graphs recorded. Every batch is physically split into RoleBatch(sender), RoleBatch(receiver), and SupervisionBatch; only losses receive supervision. JsonlSource verifies shard hashes, the train split and structure signatures, rejects mathematical fixtures, and records its exact position/epoch cursor. Checkpoints bind model, data and configuration digests, semantic versions, named owners, Adam moments and RNG states. Resume is source-reviewed, not empirically tested; serialized edges require fresh forward recomputation. No research runtime has been invoked.

Future commands, NOT_RUN and currently policy-denied except --describe:

    PYTHONPATH=src python -m latent_comm.learning.uncertainty.train --describe
    PYTHONPATH=src python -m latent_comm.learning.uncertainty.train --config configs/learning/uncertainty.json --root .
    PYTHONPATH=src python -m latent_comm.learning.uncertainty.train --config configs/learning/uncertainty.json --root . --resume-record RECORD --resume-sha256 SHA256

A future authorized run must bind immutable research-data and model manifests and an exact stage schema first. UNBOUND is deliberately rejected. Source-level completion is not model validation.
