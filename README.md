<h1 align="center">Latent Frontier · Semantic Becoming</h1>
<p align="center"><strong>让交流成为认知生长的计算过程。</strong></p>

[中文](README.md) · [English](README.en.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

当模型开始共同创造概念、改写问题、交换学习方式、构造新的世界时，交流本身就成为一种认知生长的过程。

**Semantic Becoming 探索一种可改写认知的人工智能架构：让协作进入概念形成、问题生成、学习能力与世界构造的内部。** 项目把潜空间通信、可执行语义、可运输的学习动力学与共同世界组织为一套可扩展的计算体系。

我们面向的前景，是能够在交流中持续拓展自身认知空间的智能系统：新的表示方式、新的提问方式、新的适应机制，以及共同创造的探索空间。

## 三条前沿，构成一个研究计划

| 研究前沿 | 核心思想 | 打开的可能性 |
| --- | --- | --- |
| **交流生成语言** | 把概念、问题、反例与程序变成模型可以共同构造和变换的计算对象。 | 在交互中涌现的新概念、可执行的问题重构、持续演化的计算语言。 |
| **交流传递学习** | 在不同认知系统之间运输更新方向、学习几何与可塑性规则。 | 让协作改变参与者适应环境、组织经验和形成新能力的方式。 |
| **交流构造世界** | 组合因果机制、保留共享不确定性、建立反事实环境。 | 为共同探索、集体想象与新任务的创造提供空间。 |

## 可改写认知的计算架构

概念、问题、学习更新与世界机制，各自拥有独立的语义和变换规则。类型、坐标系、版本、作用域与来源关系，为它们的相互作用建立结构。

这使几条富有想象力的认知路径能够进入具体研究：

- **从分歧走向新概念。** 不同视角暴露冲突，可执行反例使冲突变得清晰，本体由此产生分支、修订或新的区分。
- **从一个问题走向问题空间。** 类型化变换以明确的答案关系连接不同表述，让问题的创造与重组成为计算的一部分。
- **从一次更新走向学习方式的交流。** 可运输的方向进入可塑性规则，为改变未来适应过程的协作打开路径。
- **从因果组件走向共同想象。** 机制与联合噪声结构组成新的世界，使智能体能够生成经验、提出问题并探索不同动力学。

不同视角可以保持各自的领域与结构，共同计算则在这些差异之间建立富有生产力的连接。

## 一张可以深入探索的研究版图

| 层级 | 范围 | 入口 |
| --- | --- | --- |
| 机制 | **48** 个类型化机制模块 | [机制源码](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/mechanisms) |
| 组合 | **20** 条连接具体对象流的组合路线 | [组合源码](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/compositions) |
| 配方 | **68** 份机制与组合的声明式配方 | [配方库](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/recipes) |
| 终局 | **12** 个面向未来认知系统的架构方向 | [终局架构](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/src/latent_comm/horizon) |
| 延伸 | **38** 条进一步展开研究版图的前沿分叉 | [前沿后记](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/frontier_afterword.md) |

仓库汇集研究提案、形式推导、有限参考算法、编译器、运行时、数据合同及学习与后端接口。这些组件共同构成继续开展跨模型、跨领域研究的计算基础。

## 进入源码

需要 **Python 3.11+**。以下入口使用 Python 标准库。

```bash
cd Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab

# 浏览机制、组合与终局注册表
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['design'])"

# 把研究配方编译为类型化 IR
python -X utf8 -B -c "import sys; sys.path.insert(0, 'src'); from latent_comm.cli.main import main; main(['compile', '../../recipes/C13.json', '--format', 'text'])"

# 检查本地源码绑定
python -X utf8 -B scripts/check_source_bindings.py
```

[技术指南](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/README.md)介绍当前执行接口与开发条件。

## 深入阅读

- [中文研究总稿](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/research_monograph.md)：三条主线、机制版图与长期研究议程。
- [形式推导指南](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/formal_notes/00_reading_guide.md)：数学对象、基本假设与变换关系。
- [理论架构](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/theory_architecture.md)：连接不同机制家族的计算结构。
- [相关工作](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/docs/related_work.md)：思想脉络与可区分的研究主张。
- [论文源码](Latent_Frontier_v3_Delivery/latent_frontier_v3_20261024/workspace/latent-comm-lab/paper/main.tex)：以 LaTeX 组织的连续研究论述。

## 一起拓展下一条前沿

新的认知对象、更丰富的等价关系、不同的学习几何、可组合的世界动力学，以及模型架构之间的新桥梁，都是这项研究可以继续生长的方向。一个新机制、一段数学发展、一个有揭示力的反例、一条组合路线或一项经验研究，都可以推动这张版图向前。

**我们持续追问：当交流能够改变参与者自身，哪些新的认知形式将由此成为可能？**

---

仓库收录研究源码、设计文档与开发记录。生成的音视频及临时渲染产物保留在独立的本地交付材料中；完整交付清单对应那套产物。源码许可待维护者确定，媒体沿用其已有条款。
