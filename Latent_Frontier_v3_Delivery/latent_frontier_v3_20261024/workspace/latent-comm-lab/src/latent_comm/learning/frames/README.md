# L03: coordinate and restriction learning source

Research state: NOT_RUN. `python -m latent_comm.learning.frames.train --describe`
only reports metadata. Every initializer, forward, loss, data read and optimizer
entry gates before importing a tensor library. Future execution requires separate
authorization, bound manifests and an environment with the declared backends.

Three concrete variants use W01/W02 projected roles. The GL variant learns a
low-rank map calibration around the explicitly observed frame and readout
calibration. It is not evidence of discovering an unobserved frame. The
rectangular cross-map variant computes a minimum-norm reachable readout and
reports the unreachable readout residual and map rank; it never calls that map a
gauge equivalence. The anchored triangle variant learns only declared sparse
restriction incidences and biases, solves hard-anchor elimination with H26, and
retains nonzero overlap residuals for obstruction prediction. Supervisor global
sections and gluing labels enter only the loss, not the forward.

Parameter owners are cross_map/read_write_heads or restriction_maps/conflict_head.
Losses normalize by coordinate, behavior element or graph count. Empty masks skip
with an explicit reason. There are no detached bridge inputs or fake neural
fixtures. The shared optimizer uses phase-specific owners, AdamW, explicit
weights, valid-microbatch accumulation, finite clipping, cursor/hash-checked
resume, tensor-only optimizer persistence, CPU/CUDA/Python RNG states and
checkpoint recomputation boundaries. No blanket no_grad is used in a receiver.

Data sources reject math fixtures and non-training splits. No training shard was
created. Source budgets are research configuration, distinct from the executed
fixture caps. Singularity rejection, rectangular loss of observability, and the
non-gluable cycle are mathematical checks, not empirical model measurements.
