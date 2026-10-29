# Licensing scope and third-party notices

Semantic Becoming uses different licenses for different content categories. These licenses apply to project-original material to the extent that the maintainers own or are authorized to license the relevant rights. Existing third-party notices and separately identified terms remain in effect.

Project: https://github.com/Roblis0n/Semantic-Becoming

## 1. Project-original software: Apache-2.0

The project-original software is licensed under the **Apache License, Version 2.0**; the complete text is in [LICENSE](LICENSE).

This category includes the Python implementation, command-line tools, build and checking scripts, interactive visualization code, and other original executable source. It also includes configurations, schemas, registries, recipes and fixtures whose function is to configure, compile, execute or check that software. Executable examples and original code blocks in the documentation follow Apache-2.0 unless a specific third-party notice states otherwise.

License scope follows the role of the content, rather than its filename extension. For example, an executable recipe expressed as JSON belongs to this software category; research prose or an explanatory report expressed as JSON belongs to the documentation category below.

## 2. Original documents and self-produced presentation assets: CC BY 4.0

The project-original research prose, theoretical explanations, formal notes, manuscripts, documentation, original annotations, narration text, and explanatory development records are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. The complete legal text is in [LICENSE-CC-BY-4.0](LICENSE-CC-BY-4.0).

The same license applies to self-produced presentation material for which the project can grant the relevant rights: original diagrams, rendered figures, slide decks, images, silent demonstration videos and their original explanatory content. Software used to produce or operate a presentation remains in the software category. Third-party components embedded in a document or presentation retain their own terms.

For attribution of these project-original documents and assets, use **Semantic Becoming contributors**, the project title, and the project URL above. Follow the CC BY 4.0 requirements for a license reference and indication of modifications, and retain any more specific existing attribution. [NOTICE](NOTICE) supplies the project attribution record.

The seven silent demonstration videos currently included in Git are:

- `assets/animations/A01/A01.mp4`
- `assets/animations/A02/A02.mp4`
- `assets/animations/A03/A03.mp4`
- `assets/animations/A04/A04.mp4`
- `assets/animations/A05/A05.mp4`
- `assets/video/intro_90/intro_90_silent_draft.mp4`
- `assets/video/explainer_360/explainer_360_silent_draft.mp4`

The original project-created Logo artwork is included in this presentation-asset category to the extent applicable rights can be licensed. Copyright permissions do not grant trademark rights or imply endorsement.

## 3. Third-party content retains its original terms

Neither project license re-licenses third-party papers, quotations, copied snippets, external images, trademarks, fonts, model weights, datasets or other separately licensed material. A reference to an external work identifies that work; it does not grant rights in the referenced work. Preserve any applicable third-party license and attribution.

This distinction also applies inside mixed-content files. Original explanatory prose can be CC BY 4.0 while a quoted passage retains its original rights, and an original executable example can be Apache-2.0 within the same document. No license for a future external dependency or research dataset is inferred from this repository's licenses.

## 4. TTS speech and videos containing it are explicit exclusions

The delivery records identify synthesized Mandarin narration from **TTS.ai / MeloTTS / ZH**, generated through the free, unauthenticated route. The recorded applicable service terms permit personal, non-commercial use only. Those speech outputs, and every video containing them, are **excluded from both the project's Apache-2.0 grant and its CC BY 4.0 grant** and retain the applicable original service/model terms.

This exclusion includes generated speech under `assets/audio/` and, in particular, the local delivery files:

- `assets/video/intro_90/intro_90_narrated_personal.mp4`
- `assets/video/explainer_360/explainer_360_narrated_personal.mp4`

It also covers intermediate or historical copies containing that speech, regardless of filename or location. Original narration scripts and independently produced silent visuals remain subject to their own content categories above. These TTS audio and narrated-video files are not tracked in the current Git distribution.

Sources and retained provenance:

- [Audio source and license record](assets/audio/README.md).
- [Media permission/source review](reports/permission_review.json).
- [TTS.ai official terms](https://tts.ai/terms/), section 7; the recorded terms were effective 2026-09-14 and checked for the original production on 2026-10-24.

The project does not grant broader rights in these third-party outputs. The restriction on that speech does not automatically extend to independently authored software, documents, slides, figures or silent visuals.

## 5. Packages, preserved records and canonical terms

The Python distribution contains software and accompanying documentation. Its combined license expression is **`Apache-2.0 AND CC-BY-4.0`** because it contains components from both categories; each component has the applicable license described above. This is not a choice between two alternative licenses for every file. The package includes both complete license texts, NOTICE and this scope statement.

The same category rules apply to project-original content in the preserved design inputs. Historical reports and task records retain the license-decision status that was true when they were recorded; the current distribution is licensed as stated here. This does not override any third-party terms or rewrite the recorded history.

This document identifies the applicable content categories and exclusions. The complete Apache-2.0 and CC BY 4.0 legal texts govern the rights they grant.

## 中文范围摘要

- 项目原创代码、脚本、可执行示例及用于运行、编译或检查软件的配置、模式、注册表和配方，使用 **Apache-2.0**。
- 项目原创研究文档、理论说明、论文、原始注释、旁白文本、图表、幻灯片、图像及自制静音展示素材，在维护者有权授权的范围内使用 **CC BY 4.0**。署名为 **Semantic Becoming contributors**，并提供项目、许可链接及修改说明。
- 混合文件按内容用途分别适用；第三方引用、素材及已带独立条款的内容保留原权利与许可。
- TTS.ai 生成语音及包含其音轨的任何版本，均不纳入上述两项项目授权，继续遵守原服务／模型条款。当前 Git 仓库不分发这批语音和配音视频。
- 包元数据中的 `Apache-2.0 AND CC-BY-4.0` 表示发行物包含不同许可的组件，各组件按上述范围适用。
