# 形式推导阅读指南

D02 覆盖 24 个新增机制与全部 F01–F08 输入，并补出组织机制、主动识别和负知识的推导。新经验结论 E 为零，研究状态 NOT_RUN。文中数学是明确条件下的定义/恒等式/有限定理，不把标准数学重新命名为本项目原创。

## 阅读次序

- [F01](F01_covariance_and_objectives.md)：H25, H32。
- [F02](F02_affine_gluing_and_obstructions.md)：H26。
- [F03](F03_concepts_counterexamples_and_language.md)：H27, H36。
- [F04](F04_questions_and_partial_morphisms.md)：H29, H30。
- [F05](F05_behavior_transport_and_plasticity.md)：H37, H38。
- [F06](F06_trajectories_bifurcations_and_boundaries.md)：H28, H33, H34。
- [F07](F07_quotients_and_scale_closure.md)：H35, H47。
- [F08](F08_worlds_causality_and_evidence.md)：H31, H43, H44, H48。
- [F09](F09_programs_transactions_coalitions_ecology.md)：H39, H40, H41, H42。
- [F10](F10_identifiability_and_negative_knowledge.md)：H45, H46。

## 五层结论

- D：域、定义、条件命题和本章展示的逐步证明。有限检查能抓实现反例，不替代一般证明。
- A：公共行为坐标、可实现读写接口、语法能力、因果边界、响应模型与证据依赖等显式前提。
- H：模型能否学习并利用这些对象改变跨模型计算。静态和有限数学检查不验证 H。
- V：docs/frontier_afterword.md 与 specs/future_branches.json 的 38 条未来分叉。有限入口存在不代表分叉已实现。
- E：本轮无新经验研究结果。不得从手算、矩阵检查、来源检索或软件契约产生模型分数。

## 当前源码比理论更窄的地方

H25 参考程序仅线性矩阵，非线性共轭是额外理论范围；H26 浮点残差不是上同调证书；H27 当前 unknown 比例不是历史语义漂移；H29 有限容差解集不是一般程序等价；H33 只实现二次耗散与线性 skew 耦合；H35 不强制 lift 为右逆；H39 只保证一个协调实例内的条件原子性；H42 表达候选不是 competence，inverse 标签不保证条件函数真逆；H43 需分别承担转移与观测独立条件；H46 的 required_predicate 必须由任务前提支持；H48 撤回失效不等于结论为假。

这些限制不删除 H/V，而把下一步创造需要解决的对象明确化。分叉不以近期实验难度排序。

## 可复核证据

- assumption_dependencies.json：D/A/H/V 依赖与未证明桥梁；研究 E 列表为空。
- source_map.json：全部 H25–H48 当前真实文件 SHA-256、函数位置、设计输入、D01 来源身份和读取层级。
- run_state/checks/D02_math_fixtures.json：实际有限检查、预算、精确输入/输出和非研究范围。
- run_state/checks/D02_validation.json：覆盖、引用、快照、AST 和结构检查。
- run_state/receipts/D02.json：依赖内容摘要和本任务产物哈希。

文档中的公式和未执行的未来算法可讨论一般有限维/连续域，但任何本轮运行例均预先限制维数≤64、步骤≤128、案例≤64，并用 aggregate_budget 约束嵌套调用。不导入神经库，不下载模型，不调用模型 API，不生成大规模数据。源码 AST 检查不等于后端集成试验。

## 已核验近邻的身份索引

以下保留 D01 真实核验范围。多数条目为元数据与摘要/目标章节读取，未声称全文证明复核；同名未检出不等于优先权。分叉新增的四值逻辑、透镜、并发迹等邻域仍需要专门文献调查。

- [SBV3_S02 LatBridge: Efficient and Stable Model Replacement in Latent-Communication Multi-Agent Systems](https://arxiv.org/abs/2610.27813)。身份核验 2026-10-24；共享桥与分离接口用于模型替换后的接口复用。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S03 Thought Blocks: Non-Autoregressive Latent Communication for Multi-Agent Systems via Trajectory-to-State Compilation](https://arxiv.org/abs/2610.23056)。身份核验 2026-10-24；将轨迹压缩为一次构造的 KV 续接记忆。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S06 Gauge Equivariant Convolutional Networks and the Icosahedral CNN](https://arxiv.org/abs/1902.04615)。身份核验 2026-10-24；局部规范变换下的等变网络构造原则。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S07 Neural Sheaf Diffusion: A Topological Perspective on Heterophily and Oversmoothing in GNNs](https://arxiv.org/abs/2202.04579)。身份核验 2026-10-24；图上向量空间、限制映射与层扩散。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S08 Oversmoothing as Representation Degeneracy in Neural Sheaf Diffusion](https://arxiv.org/abs/2605.11178)。身份核验 2026-10-24；以表示退化分析层扩散的过平滑现象。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S09 DreamCoder: Growing generalizable, interpretable knowledge with wake-sleep Bayesian program learning](https://arxiv.org/abs/2006.08381)。身份核验 2026-10-24；通过程序抽象库增长组织程序合成。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S10 Deep Equilibrium Models](https://arxiv.org/abs/1909.01377)。身份核验 2026-10-24；通过根求解处理隐式平衡状态。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S11 Neural Task Graphs: Generalizing to Unseen Tasks from a Single Video Demonstration](https://arxiv.org/abs/1807.03480)。身份核验 2026-10-24；利用任务组成结构泛化单演示策略。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S12 Causal Abstractions of Neural Networks](https://arxiv.org/abs/2106.02997)。身份核验 2026-10-24；以因果抽象解释高层变量与神经行为的对应。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S13 Causal and Compositional Abstraction](https://arxiv.org/abs/2602.16612)。身份核验 2026-10-24；自然变换及组件层次的组合/因果抽象。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S14 The information bottleneck method](https://arxiv.org/abs/physics/0004057)。身份核验 2026-10-24；压缩输入同时保留与目标变量相关的信息。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S16 Learning to learn by gradient descent by gradient descent](https://arxiv.org/abs/1606.04474)。身份核验 2026-10-24；把优化器设计转为学习问题。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S17 Coalitional Manipulations and Immunity of the Shapley Value](https://arxiv.org/abs/2310.20415)。身份核验 2026-10-24；研究联盟操作下的分配规则性质。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S18 Paired Open-Ended Trailblazer (POET): Endlessly Generating Increasingly Complex and Diverse Learning Environments and Their Solutions](https://arxiv.org/abs/1901.01753)。身份核验 2026-10-24；环境与求解者配对生成、演化和迁移。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S19 Emergent Complexity and Zero-shot Transfer via Unsupervised Environment Design](https://arxiv.org/abs/2012.02096)。身份核验 2026-10-24；自动环境设计及对抗性课程构造。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S20 Bayesian Active Learning for Classification and Preference Learning](https://arxiv.org/abs/1112.5745)。身份核验 2026-10-24；以信息准则进行分类和偏好主动学习。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_S21 Generalized Absorptive Polynomials and Provenance Semantics for Fixed-Point Logic](https://arxiv.org/abs/1910.07910)。身份核验 2026-10-24；使用来源代数表示逻辑结果的证据组合。 范围：Metadata observation index only, not a complete immutable article snapshot.。

- [SBV3_N01 Consensus on Transaction Commit](https://arxiv.org/abs/cs/0408036)。身份核验 2026-10-24；事务提交的一致性、两阶段提交与故障假设。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N02 Nonnegative Decomposition of Multivariate Information](https://arxiv.org/abs/1004.2515)。身份核验 2026-10-24；冗余与协同信息的分解结构；不等于本项目任务收益交互项。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N03 Metrics for Finite Markov Decision Processes](https://arxiv.org/abs/1207.4114)。身份核验 2026-10-24；基于 bisimulation 的有限 MDP 状态距离及聚合。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N04 Capability Myths Demolished](https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf)。身份核验 2026-10-24；对象能力的授权与隔离模型。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N05 Successive Refinement of Information](https://isl.stanford.edu/~cover/papers/paper94.pdf)。身份核验 2026-10-24；逐次细化的率失真条件与非普遍可细化性。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N06 A Truth Maintenance System](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)。身份核验 2026-10-24；记录信念理由、依赖回溯及前提变化后的修订。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N08 Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531)。身份核验 2026-10-24；把复杂模型预测行为蒸馏进另一个模型。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N09 World Models](https://arxiv.org/abs/1803.10122)。身份核验 2026-10-24；学习环境动态并在内部生成环境中组织策略学习。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N10 Event-triggered real-time scheduling of stabilizing control tasks](https://www.ee.ucla.edu/~tabuada/Papers/EventTriggered.pdf)。身份核验 2026-10-24；根据状态事件而非固定时钟调度控制任务。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N11 Structure-Mapping: A Theoretical Framework for Analogy](https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf)。身份核验 2026-10-24；把域间关系结构而非外观属性作为类比对象。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N12 Guarded commands, non-determinacy and formal derivation of programs](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)。身份核验 2026-10-24；用谓词变换与最弱前置条件描述程序规格。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N13 Factor Graphs and the Sum-Product Algorithm](https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf)。身份核验 2026-10-24；因子图上的双向消息可表达前后向等既有算法。 范围：Metadata observation index only, not full-text archival preservation.。

- [SBV3_N14 Introduction to Program Synthesis, Lecture 10: Introduction to Functional Synthesis](https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm)。身份核验 2026-10-24；作者教学资料明确说明 CEGIS 的候选、反例与累积约束循环及其失效例。 范围：Metadata observation index only, not full-text archival preservation.。
