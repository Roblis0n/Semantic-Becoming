<p align="center">
  <img src="Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/assets/brand/semantic-becoming-banner.png" alt="Semantic Becoming — latent-comm-lab" width="960">
</p>

<h1 align="center">Semantic Becoming</h1>
<p align="center"><strong>Communication that creates new possibilities for cognition.</strong></p>
[中文](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

What if communicating models could invent concepts, reshape questions, exchange ways of learning, and construct worlds together?

**Semantic Becoming explores communication as a process through which cognitive systems acquire new structures and new possibilities for action.** Its research agenda connects latent communication, executable semantics, transferable learning dynamics and shared world construction within one extensible computational architecture.

The ambition is a new layer of AI: systems whose collaboration expands the repertoire of what they can represent, ask, learn and create.

## Three frontiers, one research program

| Frontier | Central idea | What it opens up |
| --- | --- | --- |
| **Communication creates language** | Turn concepts, questions, counterexamples and programs into objects that models can construct and transform together. | Concepts that emerge through interaction, executable problem reformulation, evolving computational languages. |
| **Communication carries learning** | Transport update directions, learning geometry and plasticity rules across cognitive systems. | Collaboration that changes how participants adapt, organize experience and develop new capabilities. |
| **Communication builds worlds** | Compose causal mechanisms, preserve shared uncertainty and construct counterfactual environments. | Shared spaces for exploration, collective imagination and the invention of new tasks. |

## The architecture of becoming

The project treats a concept, a question, a learning update and a world mechanism as distinct computational objects, each with its own semantics and transformations. Types, coordinate frames, versions, scopes and provenance provide the structure through which these objects can interact.

This makes several ambitious trajectories expressible:

- **From disagreement to a new concept.** Local perspectives expose a conflict; an executable counterexample clarifies it; an ontology can branch, revise or introduce a useful distinction.
- **From a question to a space of questions.** Typed transformations connect formulations through explicit answer relations, making problem invention part of computation.
- **From an update to a way of learning.** A transported direction becomes part of a plasticity rule, opening a route toward communication that changes future adaptation.
- **From causal components to shared imagination.** Mechanisms and joint noise structures compose into worlds where agents can generate experiences, pose new questions and explore alternative dynamics.

Different perspectives retain their own domains. Shared computation can preserve plurality while building productive connections among them.

## A research landscape you can navigate

| Layer | Scope | Entry point |
| --- | --- | --- |
| Mechanisms | **48** typed mechanism modules | [Mechanism source](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/mechanisms) |
| Compositions | **20** routes connecting mechanisms through concrete object flows | [Composition source](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/compositions) |
| Recipes | **68** declarative mechanism and composition recipes | [Recipe library](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/recipes) |
| Horizons | **12** architectural directions for future cognitive systems | [Horizon architectures](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/horizon) |
| Further branches | **38** extensions across the research landscape | [Frontier afterword](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/frontier_afterword.md) |

The repository brings together the research proposal, formal development, finite reference algorithms, compiler, runtime, data contracts and learning/backend interfaces. The next research stage is to connect these structures to empirical programs across models and domains.

## Explore the source

Requires **Python 3.11+**. The following entry points use the standard library.

```bash
cd Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab

# Explore the mechanism, composition and horizon registry
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['design'])"

# Compile a research recipe into typed IR
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['compile', '../../recipes/C13.json', '--format', 'text'])"

# Check local source bindings
python -X utf8 -B scripts/check_source_bindings.py
```

The [technical guide](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/README.md) describes the current execution interfaces and development conditions.

## Read the research

- [Research monograph](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/research_monograph.md) — the three frontiers, mechanism landscape and long-term agenda.
- [Formal reading guide](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/formal_notes/00_reading_guide.md) — the mathematical objects, assumptions and transformations.
- [Theory architecture](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/theory_architecture.md) — the computational structure connecting the mechanism families.
- [Related work](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/related_work.md) — intellectual connections and distinctions.
- [Paper source](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/paper/main.tex) — a continuous research manuscript in LaTeX.

## Build the next frontier

We welcome work on new cognitive objects, richer equivalence relations, alternative learning geometries, composable world dynamics and bridges between model architectures. A contribution can be a mechanism, a mathematical development, a revealing counterexample, a composition route or an empirical study.

**The guiding question is open: what new forms of cognition become possible when communication itself can transform the participants?**

---

Repository scope: research source, design documents and development evidence. Generated audio/video and temporary rendering outputs remain in the separate local delivery. Full-delivery manifests describe that complete artifact set. Source license: awaiting maintainer selection. Media retain their documented terms.
