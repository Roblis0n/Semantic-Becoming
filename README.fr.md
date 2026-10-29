<p align="center">
  <img src="Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/assets/brand/semantic-becoming-banner.png" alt="Semantic Becoming — latent-comm-lab" width="960">
</p>

<h1 align="center">Semantic Becoming</h1>
<p align="center"><strong>Une communication qui ouvre de nouvelles possibilités pour la cognition.</strong></p>

[中文](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

Et si des modèles capables de communiquer pouvaient inventer des concepts, reformuler des questions, échanger des façons d’apprendre et construire des mondes ensemble ?

**Semantic Becoming explore la communication comme un processus par lequel les systèmes cognitifs acquièrent de nouvelles structures et de nouvelles possibilités d’action.** Son programme de recherche réunit la communication latente, la sémantique exécutable, la dynamique transférable de l’apprentissage et la construction de mondes partagés au sein d’une architecture computationnelle extensible.

L’ambition est de faire émerger une nouvelle couche de l’IA : des systèmes dont la collaboration élargit le champ de ce qu’ils peuvent représenter, interroger, apprendre et créer.

## Trois frontières, un programme de recherche

| Frontière | Idée centrale | Perspectives ouvertes |
| --- | --- | --- |
| **La communication crée le langage** | Faire des concepts, des questions, des contre-exemples et des programmes des objets que les modèles peuvent construire et transformer ensemble. | Des concepts issus de l’interaction, des reformulations exécutables de problèmes, des langages computationnels évolutifs. |
| **La communication transmet l’apprentissage** | Transporter les directions de mise à jour, les géométries d’apprentissage et les règles de plasticité entre systèmes cognitifs. | Une collaboration qui transforme la manière dont les participants s’adaptent, organisent l’expérience et développent de nouvelles capacités. |
| **La communication construit des mondes** | Composer des mécanismes causaux, préserver l’incertitude partagée et construire des environnements contrefactuels. | Des espaces communs d’exploration, d’imagination collective et d’invention de nouvelles tâches. |

## L’architecture du devenir

Le projet considère un concept, une question, une mise à jour d’apprentissage et un mécanisme du monde comme des objets computationnels distincts, chacun doté de sa propre sémantique et de ses propres transformations. Les types, les repères de coordonnées, les versions, les portées et la provenance structurent leurs interactions.

Plusieurs trajectoires ambitieuses deviennent ainsi formulables :

- **Du désaccord à un nouveau concept.** Des perspectives locales révèlent un conflit ; un contre-exemple exécutable le précise ; une ontologie peut se ramifier, se réviser ou introduire une distinction utile.
- **D’une question à un espace de questions.** Des transformations typées relient différentes formulations par des relations explicites entre leurs réponses : l’invention de problèmes devient une partie du calcul.
- **D’une mise à jour à une façon d’apprendre.** Une direction transportée prend place dans une règle de plasticité, ouvrant la voie à une communication qui transforme l’adaptation future.
- **De composantes causales à une imagination partagée.** Des mécanismes et des structures conjointes de bruit se composent en mondes où des agents peuvent générer des expériences, poser de nouvelles questions et explorer d’autres dynamiques.

Chaque perspective conserve son propre domaine. Le calcul partagé peut préserver cette pluralité tout en établissant entre elles des liens féconds.

## Une carte de recherche à explorer

| Couche | Étendue | Point d’entrée |
| --- | --- | --- |
| Mécanismes | **48** modules de mécanismes typés | [Code des mécanismes](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/mechanisms) |
| Compositions | **20** parcours reliant des mécanismes par des flux d’objets concrets | [Code des compositions](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/compositions) |
| Recettes | **68** recettes déclaratives de mécanismes et de compositions | [Bibliothèque de recettes](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/recipes) |
| Horizons | **12** orientations architecturales pour les futurs systèmes cognitifs | [Architectures des horizons](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/horizon) |
| Prolongements | **38** extensions du paysage de recherche | [Épilogue des frontières](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/frontier_afterword.md) |

Le dépôt réunit la proposition de recherche, les développements formels, les algorithmes de référence finis, le compilateur, le moteur d’exécution, les contrats de données et les interfaces d’apprentissage et de backend. La prochaine étape de recherche consiste à relier ces structures à des programmes empiriques portant sur différents modèles et domaines.

## Explorer le code

Nécessite **Python 3.11 ou une version ultérieure**. Les points d’entrée suivants utilisent la bibliothèque standard.

```bash
cd Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab

# Explorer le registre des mécanismes, compositions et horizons
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['design'])"

# Compiler une recette de recherche en représentation intermédiaire typée
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['compile', '../../recipes/C13.json', '--format', 'text'])"

# Vérifier les liaisons locales du code source
python -X utf8 -B scripts/check_source_bindings.py
```

Le [guide technique](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/README.md) décrit les interfaces d’exécution et les conditions de développement actuelles.

## Lire la recherche

- [Monographie de recherche](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/research_monograph.md) — les trois frontières, les mécanismes et le programme à long terme.
- [Guide de lecture formelle](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/formal_notes/00_reading_guide.md) — les objets mathématiques, les hypothèses et les transformations.
- [Architecture théorique](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/theory_architecture.md) — la structure computationnelle reliant les familles de mécanismes.
- [Travaux connexes](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/related_work.md) — les rapprochements intellectuels et les distinctions.
- [Source de l’article](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/paper/main.tex) — un manuscrit de recherche continu en LaTeX.

## Construire la prochaine frontière

Nous accueillons les travaux sur de nouveaux objets cognitifs, des relations d’équivalence plus riches, d’autres géométries d’apprentissage, des dynamiques de mondes composables et des passerelles entre architectures de modèles. Une contribution peut prendre la forme d’un mécanisme, d’un développement mathématique, d’un contre-exemple révélateur, d’une voie de composition ou d’une étude empirique.

**La question qui guide cette recherche reste ouverte : quelles nouvelles formes de cognition deviennent possibles lorsque la communication elle-même peut transformer ses participants ?**

---

Périmètre du dépôt : code de recherche, documents de conception et éléments de suivi du développement. Les fichiers audio et vidéo générés ainsi que les rendus temporaires restent dans la livraison locale distincte. Les manifestes de livraison décrivent cet ensemble complet. Licence du code : en attente du choix du responsable du projet. Les médias conservent les conditions d’utilisation qui leur sont propres.
