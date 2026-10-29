<h1 align="center">Latent Frontier · Semantic Becoming</h1>
<p align="center"><strong>Una comunicación que abre nuevas posibilidades para la cognición.</strong></p>

[中文](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

¿Qué ocurriría si los modelos pudieran crear conceptos, reformular preguntas, intercambiar maneras de aprender y construir mundos juntos a través de la comunicación?

**Semantic Becoming explora la comunicación como un proceso mediante el cual los sistemas cognitivos adquieren nuevas estructuras y nuevas posibilidades de acción.** Su programa de investigación conecta la comunicación latente, la semántica ejecutable, las dinámicas de aprendizaje transferibles y la construcción compartida de mundos en una arquitectura computacional extensible.

La ambición es abrir una nueva dimensión de la inteligencia artificial: sistemas cuya colaboración amplíe el repertorio de lo que pueden representar, preguntar, aprender y crear.

## Tres fronteras, un programa de investigación

| Frontera | Idea central | Posibilidades que abre |
| --- | --- | --- |
| **La comunicación crea lenguajes** | Convertir conceptos, preguntas, contraejemplos y programas en objetos que los modelos pueden construir y transformar conjuntamente. | Conceptos que emergen de la interacción, reformulaciones ejecutables de problemas y lenguajes computacionales en evolución. |
| **La comunicación transmite aprendizaje** | Transportar direcciones de actualización, geometrías de aprendizaje y reglas de plasticidad entre sistemas cognitivos. | Colaboraciones que transforman cómo los participantes se adaptan, organizan la experiencia y desarrollan nuevas capacidades. |
| **La comunicación construye mundos** | Componer mecanismos causales, preservar la incertidumbre compartida y construir entornos contrafactuales. | Espacios compartidos de exploración, imaginación colectiva e invención de nuevas tareas. |

## La arquitectura del devenir

El proyecto considera los conceptos, las preguntas, las actualizaciones de aprendizaje y los mecanismos de un mundo como objetos computacionales distintos, cada uno con su propia semántica y sus propias transformaciones. Los tipos, marcos de coordenadas, versiones, ámbitos y datos de procedencia dan estructura a la interacción entre estos objetos.

Así es posible formular trayectorias ambiciosas:

- **Del desacuerdo a un concepto nuevo.** Las perspectivas locales revelan un conflicto; un contraejemplo ejecutable lo esclarece; una ontología puede bifurcarse, revisarse o introducir una distinción útil.
- **De una pregunta a un espacio de preguntas.** Las transformaciones tipadas conectan formulaciones mediante relaciones explícitas entre respuestas, incorporando la invención de problemas a la computación.
- **De una actualización a una forma de aprender.** Una dirección transportada pasa a formar parte de una regla de plasticidad y abre un camino hacia una comunicación que transforma la adaptación futura.
- **De componentes causales a la imaginación compartida.** Los mecanismos y las estructuras conjuntas de ruido se componen en mundos donde los agentes pueden generar experiencias, plantear nuevas preguntas y explorar dinámicas alternativas.

Las distintas perspectivas conservan sus propios ámbitos. La computación compartida puede preservar esa pluralidad y, al mismo tiempo, construir conexiones fructíferas entre ellas.

## Un panorama de investigación por explorar

| Capa | Alcance | Punto de entrada |
| --- | --- | --- |
| Mecanismos | **48** módulos de mecanismos tipados | [Código de mecanismos](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/mechanisms) |
| Composiciones | **20** rutas que conectan mecanismos mediante flujos concretos de objetos | [Código de composiciones](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/compositions) |
| Recetas | **68** recetas declarativas de mecanismos y composiciones | [Biblioteca de recetas](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/recipes) |
| Horizontes | **12** direcciones arquitectónicas para futuros sistemas cognitivos | [Arquitecturas de horizonte](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/horizon) |
| Nuevas ramificaciones | **38** extensiones del panorama de investigación | [Epílogo de nuevas fronteras](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/frontier_afterword.md) |

El repositorio reúne la propuesta de investigación, los desarrollos formales, algoritmos finitos de referencia, el compilador, el entorno de ejecución, los contratos de datos y las interfaces de aprendizaje y de backend. La siguiente etapa de investigación busca conectar estas estructuras con programas empíricos en distintos modelos y dominios.

## Explorar el código

Se requiere **Python 3.11 o posterior**. Los siguientes puntos de entrada utilizan la biblioteca estándar.

```bash
cd Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab

# Explorar el registro de mecanismos, composiciones y horizontes
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['design'])"

# Compilar una receta de investigación a una representación intermedia tipada
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['compile', '../../recipes/C13.json', '--format', 'text'])"

# Comprobar las vinculaciones locales del código
python -X utf8 -B scripts/check_source_bindings.py
```

La [guía técnica](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/README.md) describe las interfaces de ejecución y las condiciones actuales de desarrollo.

## Leer la investigación

- [Monografía de investigación](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/research_monograph.md) — las tres fronteras, el panorama de mecanismos y la agenda a largo plazo.
- [Guía de lectura formal](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/formal_notes/00_reading_guide.md) — los objetos matemáticos, las hipótesis y las transformaciones.
- [Arquitectura teórica](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/theory_architecture.md) — la estructura computacional que conecta las familias de mecanismos.
- [Trabajos relacionados](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/related_work.md) — conexiones y diferencias intelectuales.
- [Fuente del artículo](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/paper/main.tex) — un manuscrito de investigación continuo en LaTeX.

## Construir la próxima frontera

Son bienvenidas las contribuciones sobre nuevos objetos cognitivos, relaciones de equivalencia más ricas, geometrías de aprendizaje alternativas, dinámicas de mundos componibles y puentes entre arquitecturas de modelos. Una contribución puede ser un mecanismo, un desarrollo matemático, un contraejemplo revelador, una ruta de composición o un estudio empírico.

**La pregunta que guía este proyecto sigue abierta: ¿qué nuevas formas de cognición se hacen posibles cuando la propia comunicación puede transformar a quienes participan en ella?**

---

Alcance del repositorio: código de investigación, documentos de diseño y registros de desarrollo. El audio, el vídeo y los archivos temporales de renderizado generados permanecen en la entrega local independiente; sus manifiestos describen ese conjunto completo. Licencia del código: pendiente de elección por la persona responsable. Los materiales multimedia conservan las condiciones documentadas para ellos.
