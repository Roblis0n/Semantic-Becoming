# Future model-side templates: NOT_RUN

D04 implements four fixed templates and a standard-library compiler. No Jinja
engine, arbitrary expression, model client, network call, or dataset generation is
used. Run the source contract checks with `PYTHONPATH=src python -m unittest
discover -s prompts/model_templates -p 'test_*.py'`.

The compiler accepts an already projected RoleView, never the complete world.
Sender and world proposer retain sender visibility; receiver and critic retain
receiver visibility. The critic therefore cannot silently inspect sender secrets
or supervisory answers. Public fields are those explicitly approved by each
world's ProjectionContract, with field-level justification; templates cannot
widen that contract. Versions carry only semantic version axes, not sample IDs.
Unresolved references are rejected. An application wishing to display referenced
content must first resolve using the typed registry and separately project the
allowed payload. Tokens, seeds, labels and supervisor records are never added.

The output schema includes explicit unknown, missing and contradiction. Its
validation is structural, not proof of a correct operator, normalized world
kernel, or sound answer map. Dedicated compiler/mechanism validators remain
mandatory. Model-proposed worlds are synthetic and cannot bootstrap evidence.

A future adapter must send `CompiledTemplate.messages()` as separate system and
user messages through a policy-gated backend. Untrusted text remains JSON data;
this separation is not a claim that prompt injection is solved. The runtime must
never grant host actions, reinterpret policy, or execute generated Python.
No template was tried on a research model, and no prompt-quality result is claimed.
