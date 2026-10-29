<h1 align="center">Latent Frontier · Semantic Becoming</h1>
<p align="center"><strong>Kommunikation, die neue Möglichkeiten der Kognition eröffnet.</strong></p>

[中文](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

Was wäre, wenn kommunizierende Modelle gemeinsam Begriffe erfinden, Fragen umgestalten, Lernweisen austauschen und Welten erschaffen könnten?

**Semantic Becoming erforscht Kommunikation als Prozess, durch den kognitive Systeme neue Strukturen und Handlungsmöglichkeiten gewinnen.** Das Forschungsprogramm verbindet latente Kommunikation, ausführbare Semantik, übertragbare Lerndynamiken und gemeinsame Weltkonstruktion in einer erweiterbaren Rechenarchitektur.

Die Vision ist eine neue Ebene der KI: Systeme, deren Zusammenarbeit das Repertoire dessen erweitert, was sie darstellen, fragen, lernen und erschaffen können.

## Drei Forschungsfronten, ein Programm

| Forschungsfront | Leitgedanke | Neue Möglichkeiten |
| --- | --- | --- |
| **Kommunikation schafft Sprache** | Begriffe, Fragen, Gegenbeispiele und Programme werden zu Objekten, die Modelle gemeinsam konstruieren und transformieren können. | Begriffe, die in der Interaktion entstehen, ausführbare Neuformulierungen von Problemen und sich entwickelnde Rechensprachen. |
| **Kommunikation trägt Lernen** | Update-Richtungen, Lerngeometrien und Plastizitätsregeln werden zwischen kognitiven Systemen übertragen. | Zusammenarbeit, die verändert, wie Beteiligte sich anpassen, Erfahrungen organisieren und neue Fähigkeiten entwickeln. |
| **Kommunikation gestaltet Welten** | Kausale Mechanismen werden zusammengesetzt, gemeinsame Unsicherheit bleibt erhalten und kontrafaktische Umgebungen entstehen. | Gemeinsame Räume für Exploration, kollektive Vorstellungskraft und die Erfindung neuer Aufgaben. |

## Die Architektur des Werdens

Das Projekt behandelt Begriffe, Fragen, Lernupdates und Weltmechanismen als unterschiedliche Rechenobjekte mit eigener Semantik und eigenen Transformationen. Typen, Koordinatensysteme, Versionen, Geltungsbereiche und Herkunftsnachweise bilden die Struktur, in der diese Objekte zusammenwirken können.

So lassen sich weitreichende Entwicklungspfade formulieren:

- **Vom Dissens zum neuen Begriff.** Lokale Perspektiven legen einen Konflikt offen; ein ausführbares Gegenbeispiel klärt ihn; eine Ontologie kann sich verzweigen, revidieren oder eine hilfreiche Unterscheidung einführen.
- **Von einer Frage zu einem Raum möglicher Fragen.** Typisierte Transformationen verbinden Formulierungen über explizite Antwortrelationen und machen die Erfindung von Problemen zu einem Teil der Berechnung.
- **Vom Update zu einer Lernweise.** Eine übertragene Richtung wird Teil einer Plastizitätsregel und eröffnet einen Weg zu Kommunikation, die künftige Anpassung verändert.
- **Von kausalen Komponenten zur gemeinsamen Vorstellungskraft.** Mechanismen und gemeinsame Rauschstrukturen fügen sich zu Welten, in denen Agenten Erfahrungen erzeugen, neue Fragen stellen und alternative Dynamiken erkunden können.

Unterschiedliche Perspektiven behalten ihre eigenen Geltungsbereiche. Gemeinsame Berechnung kann Vielfalt bewahren und zugleich produktive Verbindungen zwischen ihnen schaffen.

## Eine Forschungslandschaft zum Erkunden

| Ebene | Umfang | Einstieg |
| --- | --- | --- |
| Mechanismen | **48** typisierte Mechanismusmodule | [Mechanismusquellcode](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/mechanisms) |
| Kompositionen | **20** Routen, die Mechanismen durch konkrete Objektflüsse verbinden | [Kompositionsquellcode](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/compositions) |
| Rezepte | **68** deklarative Mechanismus- und Kompositionsrezepte | [Rezeptbibliothek](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/recipes) |
| Horizonte | **12** Architekturrichtungen für künftige kognitive Systeme | [Horizontarchitekturen](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/horizon) |
| Weitere Verzweigungen | **38** Erweiterungen der Forschungslandschaft | [Ausblick auf weitere Forschungsfronten](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/frontier_afterword.md) |

Das Repository vereint den Forschungsentwurf, formale Ausarbeitungen, endliche Referenzalgorithmen, Compiler, Laufzeitumgebung, Datenverträge sowie Lern- und Backend-Schnittstellen. Der nächste Forschungsschritt verbindet diese Strukturen mit empirischen Programmen über Modelle und Anwendungsbereiche hinweg.

## Den Quellcode erkunden

Voraussetzung: **Python 3.11 oder neuer**. Die folgenden Einstiegspunkte verwenden die Standardbibliothek.

```bash
cd Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab

# Register der Mechanismen, Kompositionen und Horizonte erkunden
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['design'])"

# Ein Forschungsrezept in eine typisierte IR kompilieren
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['compile', '../../recipes/C13.json', '--format', 'text'])"

# Lokale Quellcodebindungen überprüfen
python -X utf8 -B scripts/check_source_bindings.py
```

Der [technische Leitfaden](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/README.md) beschreibt die aktuellen Ausführungsschnittstellen und Entwicklungsbedingungen.

## Die Forschung kennenlernen

- [Forschungsmonografie](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/research_monograph.md) — die drei Forschungsfronten, die Mechanismenlandschaft und die langfristige Agenda.
- [Leitfaden zu den formalen Grundlagen](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/formal_notes/00_reading_guide.md) — mathematische Objekte, Annahmen und Transformationen.
- [Theoriearchitektur](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/theory_architecture.md) — die rechnerische Struktur, die die Mechanismusfamilien verbindet.
- [Verwandte Arbeiten](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/related_work.md) — fachliche Verbindungen und Abgrenzungen.
- [Manuskriptquelle](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/paper/main.tex) — ein zusammenhängendes Forschungsmanuskript in LaTeX.

## Die nächste Forschungsfront gestalten

Wir freuen uns über Beiträge zu neuen kognitiven Objekten, ausdrucksstärkeren Äquivalenzrelationen, alternativen Lerngeometrien, kombinierbaren Weltdynamiken und Brücken zwischen Modellarchitekturen. Ein Beitrag kann ein Mechanismus, eine mathematische Ausarbeitung, ein aufschlussreiches Gegenbeispiel, eine Kompositionsroute oder eine empirische Studie sein.

**Die Leitfrage bleibt offen: Welche neuen Formen der Kognition werden möglich, wenn Kommunikation selbst die Beteiligten verändern kann?**

---

Umfang des Repositorys: Forschungsquellcode, Entwurfsdokumente und Entwicklungsnachweise. Generierte Audio- und Videodateien sowie temporäre Rendering-Ergebnisse liegen in der separaten lokalen Lieferung. Die Manifeste der Gesamtauslieferung beschreiben diesen vollständigen Artefaktbestand. Die Lizenz für den Quellcode wird von der Projektverantwortung noch gewählt. Für Medien gelten die dokumentierten Bedingungen.
