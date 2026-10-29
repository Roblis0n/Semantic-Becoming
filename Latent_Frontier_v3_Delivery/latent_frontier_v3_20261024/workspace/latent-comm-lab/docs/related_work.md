# Semantic Becoming v3：近邻工作与候选新颖性边界

> 研究状态：NOT_RUN。D01 是来源与主张审查，不是模型实验、实现验收或全球优先权认证。

## 1. 从计算对象出发，而非从命名出发

本轮不把“潜”“认知”“梦境”等名称当作新机制。每项比较固定四件事：传什么对象、执行什么操作、保持什么不变量、什么例子能区分它与普通答案传递。已有原语必须承认；可能的新组合或新对象保留为条件假说。近期可实验性不作为删除方向的理由。

本任务完整保留 H01–H48。每项同时记录共享原语、候选差异、区分例、未证明桥梁和更激进的延伸。所有区分例在 D01 中仅为审查规格，未被执行为模型实验。

## 2. 来源真实性与核验层次

核验日期为 2026-10-24 UTC。包内 sources 的 checked_on 是供给资料的声明，不是本轮访问证据。本轮实际打开 primary URL；arXiv 记录的标题、作者、首版、当前版本和修订分别记录。近期 2026 条目并未因日期较新被自动判假，也未因包内标题存在就自动采信。

S02、S03、S08、S13、inherited:R06、R13、R14 均已在给定 arXiv URL 核对实际身份。S01 的 Interlat 是方法别名；S03 的完整标题不同于缩写。S15 页面实际是 Verified Functional Synthesis，CEGIS 的具体循环由新核验 N14 支持。

主要依据是一次文献定位与摘要/目标章节阅读，不等于全篇证明复核、源码复现或穷尽所有同类研究。没有找到完全相同工作，也不能写“世界首次”。

动态文档不伪造发表/修订日。PyTorch stable 重定向到 2.14 的目标页面已经单独检查，但文档版本不等于已安装版本。没有安装包、下载权重、初始化网络或运行示例代码。

## 3. 重点修订与创新保留

H39 的事务机制具有直接系统前驱，定位为支撑性集成，不包装为新的智能范式。H47 必须与行为等价、bisimulation 和状态聚合比较，不能把取商本身称原创。H30 的关系类比、H34 的双向消息、H36 的反例循环、H44 的世界内学习也都有明确前驱。

更激进的研究空间仍完整保留：交流能否改变可操作概念、问题与答案关系、学习方向/学习规则、指令集和可执行世界？候选贡献在这些对象如何作为可迁移、可组合、可版本化的跨模型协议，而不是宣称发明全部基础数学。

## 4. 48 项逐项台账

### H01 · 可组合潜算子

- 对象/操作：OperatorPacket；ordered low-rank nonlinear state transformation。

- 不变量：composition is function order, not factor addition。

- 已核验近邻：[S01](https://arxiv.org/abs/2511.09149)；[S05](https://arxiv.org/abs/2510.03215)；[inherited:R08](https://arxiv.org/abs/1609.09106)。共享原语：已有隐藏状态传输、缓存融合和参数生成。

- 候选差异：候选区别是有寿命、作用域和有序复合律的状态函数，而非一个已求得的状态。

- 区分例（设计，未运行）：同一消息作用于两个发送时未见输入；先加一再乘二必须区别于先乘二再加一。

- 未证明桥梁：低秩函数可能记答案；接收读写头可能承担全部计算。

- 保留的激进延伸：让跨模型可运输操作形成可执行程序，而不固定单一潜语言。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H02 · 反事实响应包

- 对象/操作：ResponseCapsule；local low-rank response prediction and refresh。

- 不变量：trust radius is enforced; derivative is not automatically causal。

- 已核验近邻：[inherited:R11](https://arxiv.org/abs/2303.02536)；[S12](https://arxiv.org/abs/2106.02997)。共享原语：已有因果表示对齐与局部响应分析。

- 候选差异：传锚点、低秩响应和有效半径，允许接收端预测未发送扰动并要求刷新。

- 区分例（设计，未运行）：在锚点答案相同但导数相反的两个函数必须发送不同响应包；越界返回刷新。

- 未证明桥梁：导数不是因果干预；离散语义不保证可线性化。

- 保留的激进延伸：用可切换的多锚点响应图册传递条件变化规律。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H03 · 多假设信念包

- 对象/操作：BeliefPacket；whole-sequence mixture and prefix posterior update。

- 不变量：branches remain separate; source dependence is explicit。

- 已核验近邻：[N06](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)；[N13](https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf)；[inherited:R06](https://arxiv.org/abs/2610.28905)。共享原语：已有多种信念维护、图上概率消息和连续隐藏消息。

- 候选差异：保持独立分支、整序列混合及来源依赖，而非平均成一个结论向量。

- 区分例（设计，未运行）：两分支只允许 AA 或 BB；逐 token 平均会伪造 AB，整序列混合不能这样做。

- 未证明桥梁：兼容性分数没有似然模型时不能称后验概率。

- 保留的激进延伸：让分歧随新干预保留、分裂或撤销，成为长期可复用计算状态。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H04 · 多主体共享约束场

- 对象/操作：ConstraintField；bounded constrained residual minimization。

- 不变量：retain anchored per-source conflict; do not zero all weights。

- 已核验近邻：[inherited:R09](https://arxiv.org/abs/2103.01197)；[S10](https://arxiv.org/abs/1909.01377)；[N13](https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf)。共享原语：已有共享工作空间、固定点求解和局部因子消息。

- 候选差异：把分源残差及冲突保留为可修改的联合约束对象。

- 区分例（设计，未运行）：一源要求 x=0、另一源要求 x=1；不能把权重全置零并报告成功。

- 未证明桥梁：数值稳定与共同错误可以同时发生；有限迭代不证明收敛。

- 保留的激进延伸：让无法满足的约束触发新增概念而非强迫共识。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H05 · 推理续接胶囊

- 对象/操作：ContinuationPacket；capture and resume remaining computation。

- 不变量：exact same-model and heterogeneous approximation are distinct。

- 已核验近邻：[S03](https://arxiv.org/abs/2610.23056)；[S05](https://arxiv.org/abs/2510.03215)；[S24](https://huggingface.co/docs/transformers/main/en/kv_cache)。共享原语：已有一次构造续接记忆与 KV 状态传输。

- 候选差异：加入完成操作、待满足依赖、时钟和精确/异构近似分界。

- 区分例（设计，未运行）：迁移后保持已完成前缀而只执行剩余步骤；缓存位置偏一必须拒绝。

- 未证明桥梁：映射后可继续生成并不证明保留了源计算进展。

- 保留的激进延伸：支持异构多切点续接及可迁移的未完成计算义务。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H06 · 多图册语义对齐

- 对象/操作：AtlasPacket；route local chart and compose transition maps。

- 不变量：heterodimensional maps are not invertible changes of basis。

- 已核验近邻：[S02](https://arxiv.org/abs/2610.27813)；[inherited:R11](https://arxiv.org/abs/2303.02536)；[inherited:R14](https://arxiv.org/abs/2609.27252)。共享原语：已有桥接接口、分布式因果对齐和关系结构比较。

- 候选差异：局部图册、过渡映射、行为锚与覆盖域进入协议。

- 区分例（设计，未运行）：两个局部域需要不同映射；全局单映射失败，常数塌缩不能通过行为锚。

- 未证明桥梁：循环一致不是语义充分条件；异维映射通常不可逆。

- 保留的激进延伸：允许模型保留不同内部几何，通过路径相关图册协作。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H07 · 类型化潜程序

- 对象/操作：TypedProgram；parse, typecheck and interpret bounded instructions。

- 不变量：no arbitrary Python or shell evaluation。

- 已核验近邻：[S09](https://arxiv.org/abs/2006.08381)；[N12](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)；[N14](https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm)。共享原语：已有程序库、谓词变换和合成/验证循环。

- 候选差异：消息本身是受限有类型 IR，执行潜操作且携带效果与预算。

- 区分例（设计，未运行）：形状合法但越权写入的程序必须拒绝；调换非交换指令必须改变结果。

- 未证明桥梁：类型安全不等于语义正确；潜参数学习与离散结构不同。

- 保留的激进延伸：让协议成为具有版本化操作语义的跨模型语言。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H08 · 关系结构通信

- 对象/操作：RelationPacket；match and exchange typed relational graphs。

- 不变量：preserve relation edges, not merely embedding proximity。

- 已核验近邻：[inherited:R12](https://arxiv.org/abs/2405.07987)；[inherited:R14](https://arxiv.org/abs/2609.27252)；[N11](https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf)。共享原语：已有表示关系比较和关系映射式类比。

- 候选差异：传输带类型关系图、歧义集合及接收操作，而非相似分数。

- 区分例（设计，未运行）：置换节点标签应保持关系作用；同度数但不同边结构不能当同一图。

- 未证明桥梁：同构关系也可能表达不同现实语义。

- 保留的激进延伸：把关系不变量而非坐标距离作为交换计算的基本单位。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H09 · 干预代数通信

- 对象/操作：InterventionPacket；do-operator surgery and ordered interventions。

- 不变量：observational conditioning is not intervention。

- 已核验近邻：[S12](https://arxiv.org/abs/2106.02997)；[S13](https://arxiv.org/abs/2602.16612)；[inherited:R11](https://arxiv.org/abs/2303.02536)。共享原语：已有因果抽象、干预对齐和机制级组合条件。

- 候选差异：交换有顺序及域限制的干预算子并保存跨端干预对应。

- 区分例（设计，未运行）：观测分布相同但 do(X) 后分布不同的两世界不能互换。

- 未证明桥梁：可执行 SCM 的干预正确不等于自然模型因果机制已识别。

- 保留的激进延伸：把因果操作的可移植部分组合成跨模型干预代数。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H10 · 高阶协同超边

- 对象/操作：HyperedgePacket；evaluate higher-order interaction terms。

- 不变量：pairwise decomposition is not presumed sufficient。

- 已核验近邻：[inherited:R07](https://arxiv.org/abs/1605.06676)；[N02](https://arxiv.org/abs/1004.2515)。共享原语：已有可微通信学习以及冗余/协同信息分解。

- 候选差异：显式超边表达多源联合能力并单独记高阶交互。

- 区分例（设计，未运行）：独立两比特的 XOR 单源无信息而联合有信息；不能只筛成对相关性。

- 未证明桥梁：任务收益的交互系数不自动等于某种 PID 协同；额外计算是混杂因素。

- 保留的激进延伸：把不可分解的多模型互补结构作为可重组计算原语。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H11 · 渐进潜编码

- 对象/操作：ProgressiveCode；decode prefix layers with explicit quantization error。

- 不变量：partial decode has explicit precision and pending layers。

- 已核验近邻：[S01](https://arxiv.org/abs/2511.09149)；[N05](https://isl.stanford.edu/~cover/papers/paper94.pdf)。共享原语：已有潜压缩与逐层细化的信息论问题。

- 候选差异：给潜计算前缀可执行语义，计请求、重传、量化和头部开销。

- 区分例（设计，未运行）：仅收到第 1 层时可有限解码，乱序第 3 层不能假装已有第 2 层。

- 未证明桥梁：经典逐次可细化条件不保证学习语义的前缀效果单调。

- 保留的激进延伸：按新问题逐步显露恰好必要的计算细节。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H12 · 多查询持久胶囊

- 对象/操作：PersistentCapsule；versioned multi-query retrieval。

- 不变量：cache keys contain all semantic versions and scope。

- 已核验近邻：[S01](https://arxiv.org/abs/2511.09149)；[S05](https://arxiv.org/abs/2510.03215)；[S14](https://arxiv.org/abs/physics/0004057)。共享原语：已有压缩状态、缓存和任务相关信息保留。

- 候选差异：胶囊与单个答案脱钩，版本化服务声明查询族并追踪失效。

- 区分例（设计，未运行）：同一资料回答两种查询；资料版本更新使受影响胶囊失效而非复用旧答案。

- 未证明桥梁：有限查询充分性不扩展到任意未来问题。

- 保留的激进延伸：长期可询问计算对象能按新查询请求源信息并局部扩容。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H13 · 可分叉潜计算

- 对象/操作：BranchState；copy-on-write fork and conflict-aware merge。

- 不变量：incompatible branches cannot be averaged silently。

- 已核验近邻：[S03](https://arxiv.org/abs/2610.23056)；[N01](https://arxiv.org/abs/cs/0408036)；[N06](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)。共享原语：已有续接、事务和依赖维护。

- 候选差异：复制未完成潜计算并按祖先、读写集合及语义条件合并。

- 区分例（设计，未运行）：两分支写同一变量不同值必须保留冲突，不能逐元素平均。

- 未证明桥梁：复制更多搜索不自动构成计算复用收益。

- 保留的激进延伸：把结构演化路径当作可审查、可分叉的认知历史。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H14 · 潜技能语法

- 对象/操作：SkillGrammar；typed production binding and bounded expansion。

- 不变量：variable binding survives expansion。

- 已核验近邻：[S09](https://arxiv.org/abs/2006.08381)；[inherited:R08](https://arxiv.org/abs/1609.09106)；[N12](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)。共享原语：已有程序抽象库与生成参数的机制。

- 候选差异：有类型产生式绑定潜算子，分开结构学习与参数学习。

- 区分例（设计，未运行）：宏展开时同名局部变量不得捕获外部变量；展开预算必须终止递归。

- 未证明桥梁：语法压缩不自动带来未见组合泛化。

- 保留的激进延伸：让可运输技能形成层级语法并为自举指令集提供底层。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H15 · 接收者无关协议学习

- 对象/操作：ProtocolPopulation；cross-pair adapter sampling and behavior alignment。

- 不变量：model IDs are routing metadata, not training evidence。

- 已核验近邻：[S02](https://arxiv.org/abs/2610.27813)；[inherited:R07](https://arxiv.org/abs/1605.06676)。共享原语：已有共享桥、接口复用和可微通信学习。

- 候选差异：训练图上的群体协议、未见配对及操作保持契约合并研究。

- 区分例（设计，未运行）：都训练过接口但未配对的两模型，与完全未见模型必须分开计成本。

- 未证明桥梁：接口复用不能推出零训练适配任意模型。

- 保留的激进延伸：协议种群持续吸收新模型而保留已持有计算对象。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H16 · 精确符号与潜状态双通道

- 对象/操作：DualChannelPacket；bind exact symbols to latent slots。

- 不变量：exact symbolic commitments cannot be silently overwritten。

- 已核验近邻：[S05](https://arxiv.org/abs/2510.03215)；[S09](https://arxiv.org/abs/2006.08381)；[S21](https://arxiv.org/abs/1910.07910)。共享原语：已有潜状态传输、符号程序与来源代数。

- 候选差异：精确字段和潜槽绑定，并有不可静默覆盖的冲突策略。

- 区分例（设计，未运行）：符号字段金额 1.01 与潜读出 1.10 冲突时不得改写原字段。

- 未证明桥梁：双通道成功可能完全来自符号通道；不可把引用当真值。

- 保留的激进延伸：让精确承诺与开放式计算共同演化但始终可追溯。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H17 · 跨模态坐标接地

- 对象/操作：GroundingFrame；transport coordinates and action-effect anchors。

- 不变量：same dimension does not establish semantic equivalence。

- 已核验近邻：[inherited:R12](https://arxiv.org/abs/2405.07987)；[inherited:R14](https://arxiv.org/abs/2609.27252)；[N11](https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf)。共享原语：已有跨模态关系比较与结构映射。

- 候选差异：加入坐标单位、对象身份、遮挡与动作后果的共同接口。

- 区分例（设计，未运行）：同一向量数值在米/厘米或左/右手系中应产生不同转换，不能按维度匹配。

- 未证明桥梁：人工几何对应不证明视觉语言模型已接地。

- 保留的激进延伸：用可执行行动后果协调不同感知模型的局部世界。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H18 · 通信诱导计算结构

- 对象/操作：TopologyProposal；construct bounded capability-compatible graph。

- 不变量：structural search and parameter gradients are distinct。

- 已核验近邻：[inherited:R07](https://arxiv.org/abs/1605.06676)；[inherited:R09](https://arxiv.org/abs/2103.01197)。共享原语：已有通信学习和模块共享工作空间。

- 候选差异：协议行为同时决定有类型拓扑与计算分工，并记录实际执行成本。

- 区分例（设计，未运行）：训练期全边执行、推理期选一边时不得只报告选中边成本。

- 未证明桥梁：通信拓扑可能退化；非平凡结构不保证新增能力。

- 保留的激进延伸：任务临时形成新的计算层级而不固定 Agent 分工。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H19 · 消息到技能巩固

- 对象/操作：ConsolidationSpec；distill reusable message effects into scoped adapters。

- 不变量：temporary messages and persistent parameter updates differ。

- 已核验近邻：[N08](https://arxiv.org/abs/1503.02531)；[inherited:R08](https://arxiv.org/abs/1609.09106)。共享原语：已有知识蒸馏与参数生成。

- 候选差异：把可复用消息操作固化为有来源、可撤销、限定参数组的适配能力。

- 区分例（设计，未运行）：删去当前消息后仍需在新输入保持操作；训练轨迹不能充当未见证据。

- 未证明桥梁：输出记忆不等于技能；本项基础版就是蒸馏集成而非新学习原理。

- 保留的激进延伸：由操作组合产生可持续迁移的能力组件。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H20 · 异步认知时钟

- 对象/操作：CognitiveClock；event-driven updates with stale-read policy。

- 不变量：time version and causal order are explicit。

- 已核验近邻：[inherited:R06](https://arxiv.org/abs/2610.28905)；[N10](https://www.ee.ucla.edu/~tabuada/Papers/EventTriggered.pdf)。共享原语：已有隐藏消息时机研究及事件触发控制。

- 候选差异：认知事件、因果依赖、过期策略与跨阶段状态传输共同定义。

- 区分例（设计，未运行）：新版本先到、旧版本后到时不得回退；无事件也必须有预算终止。

- 未证明桥梁：物理控制的稳定条件不能直接移植为语义正确性。

- 保留的激进延伸：不同模型不共享固定轮次却能协同未完成计算。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H21 · 反事实分支组合搜索

- 对象/操作：CounterfactualPortfolio；bounded branch selection with ancestry reuse。

- 不变量：search timeout is not an impossibility proof。

- 已核验近邻：[S03](https://arxiv.org/abs/2610.23056)；[N06](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)；[N09](https://arxiv.org/abs/1803.10122)。共享原语：已有续接、依赖维护及在内部世界中探索。

- 候选差异：带祖先共享的潜反事实组合树显式记录复用与失效。

- 区分例（设计，未运行）：两分支共享前缀，修改一支不能改变另一支；超时不能当不存在解。

- 未证明桥梁：额外算力而非新协议可能解释收益。

- 保留的激进延伸：反事实探索产生可传递排除域和新问题而非只选答案。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H22 · 动态模型边界

- 对象/操作：BoundaryPartition；change computation ownership and continuation placement。

- 不变量：external permissions cannot move with a research boundary。

- 已核验近邻：[S02](https://arxiv.org/abs/2610.27813)；[inherited:R09](https://arxiv.org/abs/2103.01197)；[N01](https://arxiv.org/abs/cs/0408036)。共享原语：已有模块协调、接口替换与一致性提交。

- 候选差异：计算所有权、续接位置和 frame 版本随分区一起迁移。

- 区分例（设计，未运行）：边界改变后旧 frame 消息必须失效；宿主权限不能随研究节点移动。

- 未证明桥梁：动态分组不代表融合成单一智能或意识主体。

- 保留的激进延伸：群体可按任务重划计算边界，同时保持对象可追踪。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H23 · 语义残差纠错

- 对象/操作：SemanticResidual；diagnose and transmit scoped correction。

- 不变量：repair is based on explicit residual, not invented truth。

- 已核验近邻：[S01](https://arxiv.org/abs/2511.09149)；[inherited:R06](https://arxiv.org/abs/2610.28905)；[N05](https://isl.stanford.edu/~cover/papers/paper94.pdf)。共享原语：已有潜消息和渐进补充信息。

- 候选差异：接收者请求具体任务残差，发送者补充有作用域差量。

- 区分例（设计，未运行）：字节校验正确但缺一个判断条件时只请求该条件；不能改校验码掩盖损坏。

- 未证明桥梁：双方一致错误不因更多反馈变真；反馈可能泄露信息。

- 保留的激进延伸：协议主动生成最小修正问题并选择最具区分力的回应。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H24 · 有作用域的潜计算能力

- 对象/操作：ScopedCapability；validate and apply declared research effects。

- 不变量：a packet cannot grant host authority。

- 已核验近邻：[N04](https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf)；[S22](https://openai.com/index/introducing-dots/)。共享原语：已有对象能力授权；产品权限说明只是实现背景。

- 候选差异：能力限制作用到潜计算对象的读写、寿命与效果检查。

- 区分例（设计，未运行）：包内自称管理员或通过别名写禁区必须失败，不能授予宿主权限。

- 未证明桥梁：程序隔离不提供统计隐私，潜向量也不是加密。

- 保留的激进延伸：探索只开放指定行为而不开放任意状态读取的计算交换。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H25 · 规范协变的认知接口

- 对象/操作：GaugePacket；conjugate state, operator and readout under invertible frame change。

- 不变量：r G^-1 G T G^-1 G z = r T z only within declared group。

- 已核验近邻：[S06](https://arxiv.org/abs/1902.04615)；[S02](https://arxiv.org/abs/2610.27813)。共享原语：规范变换原则与可复用接口都已有。

- 候选差异：状态、操作和读出一起协变，并将合法变换族/局部域显式化。

- 区分例（设计，未运行）：只变换 z 不变换 T/r 会改变读出；异维压缩不能进入逆矩阵分支。

- 未证明桥梁：换基恒等式不证明任意模型隐藏状态有真实对称性。

- 保留的激进延伸：研究路径相关传输与模型升级下的坐标外交，不先假定存在语义曲率。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H26 · 不可全局拼合的语义层

- 对象/操作：SheafPacket；solve affine overlap constraints and expose obstruction。

- 不变量：nonzero anchors prevent trivial zero-section consensus。

- 已核验近邻：[S07](https://arxiv.org/abs/2202.04579)；[S08](https://arxiv.org/abs/2605.11178)。共享原语：已有层限制映射、全局截面与扩散退化研究。

- 候选差异：在有语义锚的局部知识中保存拼合障碍，并据此提出补变量/问题。

- 区分例（设计，未运行）：相互不容的非零局部锚不能用全零截面伪装共识。

- 未证明桥梁：代数不一致残差不自动是拓扑上同调障碍，更不自动是语义矛盾。

- 保留的激进延伸：让不可统一的知识本身驱动概念和问题结构增生。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H27 · 交互中诞生的新概念

- 对象/操作：ConceptProposal；synthesize executable distinguishing predicates and migrate readers。

- 不变量：unknown differs from false; no candidate preserves the conflict。

- 已核验近邻：[S09](https://arxiv.org/abs/2006.08381)；[N06](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)；[N14](https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm)。共享原语：已有抽象库学习、信念修订和程序合成。

- 候选差异：新增概念须有可执行定义、区分见证和旧引用迁移。

- 区分例（设计，未运行）：只改名字或多加一维而不区分此前不可区别的例子不算新概念。

- 未证明桥梁：相对当前语法的新表达不等于历史首创或一般智能的新概念。

- 保留的激进延伸：让交流改变后续能够提出的问题和可计算概念空间。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H28 · 语义结构的分岔与相变

- 对象/操作：PhaseState；follow control-path branches and structural transitions。

- 不变量：analytic bifurcation is not evidence of neural phase transitions。

- 已核验近邻：[S10](https://arxiv.org/abs/1909.01377)；[N10](https://www.ee.ucla.edu/~tabuada/Papers/EventTriggered.pdf)。共享原语：已有连续动力系统稳定性与固定点计算背景。

- 候选差异：连续控制路径与离散结构事件共同管理分支及迁移。

- 区分例（设计，未运行）：一个准确率跳点不是分岔；必须展示指定动力系统的稳定解结构变化。

- 未证明桥梁：有限示例不能推出神经语义的热力学相变或普适类。

- 保留的激进延伸：探索交流诱发的状态空间增维与多稳态语义结构。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H29 · 问题生成的潜演算

- 对象/操作：QuestionObject；rewrite problems with solution back-translation。

- 不变量：soundness and completeness witnesses are separate。

- 已核验近邻：[N12](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)；[S09](https://arxiv.org/abs/2006.08381)；[S11](https://arxiv.org/abs/1807.03480)。共享原语：问题分解、程序抽象和最弱前置条件都已有。

- 候选差异：问题是带答案关系的对象，变换后保存解的回译及健全/完备见证。

- 区分例（设计，未运行）：把 x²=1 改成 x=1 丢掉负根；不能称等价，必须标有损加强。

- 未证明桥梁：一般程序等价不可判定；有限关系证明不覆盖任意自然问题。

- 保留的激进延伸：模型交换如何重写所问之物并共同创造新的问题族。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H30 · 类比态射编译器

- 对象/操作：AnalogyMorphism；compile partial operation-preserving maps。

- 不变量：unmatched domain and broken commuting squares stay visible。

- 已核验近邻：[N11](https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf)；[S12](https://arxiv.org/abs/2106.02997)；[S13](https://arxiv.org/abs/2602.16612)。共享原语：结构映射式类比和因果/组合抽象有直接前驱。

- 候选差异：类型化部分态射被编译为目标操作，并显式保存不交换方块。

- 区分例（设计，未运行）：外观相似但操作不保持时必须拒绝；有效子域之外不得继续迁移。

- 未证明桥梁：有限锚点通过不证明跨域普遍有效。

- 保留的激进延伸：把部分可迁移思维方法组合成跨域操作网络。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H31 · 因果机制移植

- 对象/操作：CausalModule；graft structural equations through explicit boundaries。

- 不变量：preserve unaffected equations and shared exogenous identity。

- 已核验近邻：[S12](https://arxiv.org/abs/2106.02997)；[S13](https://arxiv.org/abs/2602.16612)。共享原语：已有因果抽象及组件级机制映射。

- 候选差异：消息实际携带可接入局部方程，检查父边界、共享噪声与未受影响方程。

- 区分例（设计，未运行）：把共享外生噪声误作独立会改变干预分布，即使边际相同也应拒绝。

- 未证明桥梁：神经网络中可识别、可移植机制是强假设。

- 保留的激进延伸：不同模型共同重组带因果契约的世界生成机制。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H32 · 视角与目标条件代数

- 对象/操作：ObjectiveFrame；transform cost coordinates and preference covectors。

- 不变量：immutable external goal and hard constraints are unchanged。

- 已核验近邻：[S11](https://arxiv.org/abs/1807.03480)；[N12](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)。共享原语：已有任务结构与满足条件的变换。

- 候选差异：目标坐标和偏好协向量共同转换，外部目标和硬约束只读。

- 区分例（设计，未运行）：只缩放成本不逆变换权重会改排序；禁止偷偷放松硬约束。

- 未证明桥梁：有限线性目标框架不能代表一切偏好，更非价值对齐证明。

- 保留的激进延伸：允许多种内部视角并存而保持同一用户承诺。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H33 · 非梯度的互构认知动力学

- 对象/操作：DynamicsPacket；integrate gradient plus skew-coupled trajectories。

- 不变量：cycles are valid outputs; finite integration does not claim convergence。

- 已核验近邻：[S10](https://arxiv.org/abs/1909.01377)；[N10](https://www.ee.ucla.edu/~tabuada/Papers/EventTriggered.pdf)。共享原语：固定点网络和非平凡动力系统已有；DEQ 不是循环计算的唯一前驱。

- 候选差异：把耦合向量场、读出窗口及有用瞬态作为传输对象，允许非梯度环流。

- 区分例（设计，未运行）：纯旋转场的轨迹可循环而不收敛；若只接受固定点就错误删除输出。

- 未证明桥梁：振荡的存在不等于有用认知；尚需更广泛非平衡计算近邻审查。

- 保留的激进延伸：多个模型改变彼此演化规律而不是轮流追加结论。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H34 · 双边边界条件推理

- 对象/操作：TrajectoryFactorGraph；solve public two-boundary path constraints。

- 不变量：terminal conditions cannot be hidden future observations。

- 已核验近邻：[N13](https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf)；[N12](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)；[S11](https://arxiv.org/abs/1807.03480)。共享原语：双向概率消息、前后向算法和后条件推理早已有之。

- 候选差异：把起终端公开约束与可迁移中间未知状态组成有类型轨迹对象。

- 区分例（设计，未运行）：用测试答案偷偷构造终端条件属于泄漏；给定合法终端约束则可反传。

- 未证明桥梁：双向消息本身不是新算法；候选贡献在跨模型状态/契约实现。

- 保留的激进延伸：共同求解边界间尚未确定的计算路径，而非声称获得未来信息。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H35 · 跨尺度语义重整化

- 对象/操作：ScalePacket；coarsen, lift and measure dynamic closure residual。

- 不变量：a lifting map is not a lossless inverse。

- 已核验近邻：[N03](https://arxiv.org/abs/1207.4114)；[S14](https://arxiv.org/abs/physics/0004057)；[N05](https://isl.stanford.edu/~cover/papers/paper94.pdf)。共享原语：已有状态聚合、任务相关压缩与逐次细化。

- 候选差异：同时交换粗化、宏动态及闭合残差，并提供所需细化条件。

- 区分例（设计，未运行）：两个微状态同粗类但下一步粗状态不同，必须报告闭合失败或记忆项。

- 未证明桥梁：有限 coarse-graining 不证明物理重整化群或无损提升。

- 保留的激进延伸：让模型按任务在不同尺度之间协商计算而非固定表示粒度。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H36 · 以分歧生产结构的认知博弈

- 对象/操作：DisagreementRound；find checked counterexamples and revise finite candidates。

- 不变量：votes are not ground truth; unavailable oracle stays unavailable。

- 已核验近邻：[N14](https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm)；[S09](https://arxiv.org/abs/2006.08381)；[N06](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)。共享原语：反例引导合成、程序抽象和依赖修订都有强近邻。

- 候选差异：反例驱动的是概念/程序结构修改而非投票胜负，保留反例谱系。

- 区分例（设计，未运行）：多数同意一个错误程序不能胜过可执行反例；未找到反例不是全称证明。

- 未证明桥梁：自然任务 oracle 缺失时只能称候选反例；CEGIS 本身非新颖。

- 保留的激进延伸：分歧成为新增变量和改写问题的生产机制。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H37 · 跨模型学习方向运输

- 对象/操作：LearningEffectPacket；transport behavioral tangent by JVP/VJP least squares。

- 不变量：unreachable residual and regularization/rank diagnostics are mandatory。

- 已核验近邻：[N08](https://arxiv.org/abs/1503.02531)；[S16](https://arxiv.org/abs/1606.04474)；[S12](https://arxiv.org/abs/2106.02997)。共享原语：已有行为蒸馏、学习优化器和因果行为对应。

- 候选差异：交换行为切向量并用目标 Jacobian 的正则最小二乘投回参数空间。

- 区分例（设计，未运行）：源方向不在目标 Jacobian 像中时必须保留不可达残差，不能宣称无损。

- 未证明桥梁：有限探针与局部线性化不足以保证更新后全局行为；自然梯度近邻尚须全文复核。

- 保留的激进延伸：不同结构模型交换学习方向而非权重维度，保持可识别的行为效应。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H38 · 可传递的可塑性规则

- 对象/操作：PlasticityProgram；interpret scoped update DSL and unrolled meta-objective。

- 不变量：support/query isolation and estimator kind are explicit。

- 已核验近邻：[S16](https://arxiv.org/abs/1606.04474)；[N04](https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf)。共享原语：学习优化器和有作用域程序执行已有。

- 候选差异：学习规则作为受限可运输 DSL，带可读统计、参数组与寿命。

- 区分例（设计，未运行）：规则试图更新禁写参数组必须被拒绝；支持集信息不得混入查询监督。

- 未证明桥梁：有界更新不保证有效或避免遗忘；跨模型规则迁移仍待研究。

- 保留的激进延伸：模型传授如何学习，形成可组合的可塑性生态。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H39 · 可回滚的跨模型认知事务

- 对象/操作：CognitiveTransaction；optimistic versioned commit or rollback。

- 不变量：only controlled state is reversible, not external world effects。

- 已核验近邻：[N01](https://arxiv.org/abs/cs/0408036)；[N06](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)。共享原语：原子提交、版本冲突、回滚和依赖修订是成熟基础设施。

- 候选差异：将本体/ISA/证据迁移纳入单个受控认知状态事务。

- 区分例（设计，未运行）：读版本过期时提交失败且不留下半迁移；已发外部消息不可声称撤销。

- 未证明桥梁：本项是支撑性集成而非新智能范式；本地原子性不等于分布式容错。

- 保留的激进延伸：重大认知结构候选可分叉试构造后提交，不污染共有状态。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H40 · 自举的潜指令集

- 对象/操作：InstructionProposal；introduce hygienic macros with base-ISA lowering。

- 不变量：base ISA is immutable; learned shortcuts are not definitions。

- 已核验近邻：[S09](https://arxiv.org/abs/2006.08381)；[N12](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)；[N14](https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm)。共享原语：程序库增长、宏展开和合成已有。

- 候选差异：通信指令集与读者版本共同自举，宏有卫生展开、迁移与基底 lowering。

- 区分例（设计，未运行）：只添加新名字但展开仍同程序不能称增加可计算性；旧读者须有合法降级。

- 未证明桥梁：可展开宏只改变描述/搜索复杂度，不突破基底表达能力。

- 保留的激进延伸：协议自身发展新操作层级，重新组织可高效表达的思维结构。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H41 · 互补能力的联盟契约

- 对象/操作：CoalitionContract；compute bounded coalition value and internal contribution。

- 不变量：unknown value is not zero; credit is not money。

- 已核验近邻：[S17](https://arxiv.org/abs/2310.20415)；[N02](https://arxiv.org/abs/1004.2515)。共享原语：联盟价值分配与协同信息结构已有。

- 候选差异：用有类型前置条件/联合产出契约形成互补联盟，未知子集值不记零。

- 区分例（设计，未运行）：两个单体价值零但联合作业有价值时，单体排名不可淘汰它们。

- 未证明桥梁：Shapley 分摊依赖价值定义，不能自动保证公平或因果贡献。

- 保留的激进延伸：能力联盟而非固定模型成为临时计算主体，信用仅为内部资源记账。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H42 · 模型与任务的共演化生态

- 对象/操作：EcologyState；mutate and archive bounded program/world populations。

- 不变量：lineage and semantic version migrations are preserved。

- 已核验近邻：[S18](https://arxiv.org/abs/1901.01753)；[S19](https://arxiv.org/abs/2012.02096)；[S09](https://arxiv.org/abs/2006.08381)。共享原语：环境/解法共演化与抽象库增长都有直接前驱。

- 候选差异：将本体、潜协议、学习规则及世界版本共同纳入生态档案。

- 区分例（设计，未运行）：结构不同但暂时低分的生态位不能自动被单一排行榜清空。

- 未证明桥梁：联合演化可能循环、作弊或漂移；不承诺无界有意义创新。

- 保留的激进延伸：维护不断产生新问题、新语言和互补关系的计算生态。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H43 · 可交换的世界动力学核

- 对象/操作：WorldKernel；compose normalized finite dynamics with explicit noise coupling。

- 不变量：independence requires a certificate; shared noise stays shared。

- 已核验近邻：[S12](https://arxiv.org/abs/2106.02997)；[S13](https://arxiv.org/abs/2602.16612)；[N09](https://arxiv.org/abs/1803.10122)。共享原语：已有因果模块及可用于规划的生成世界模型。

- 候选差异：可交换的是带动作、观测、噪声身份和边界契约的转移核。

- 区分例（设计，未运行）：两个核共享噪声时不能相乘成独立联合分布；每个有限核必须归一化。

- 未证明桥梁：核可执行不等于现实正确；组合的多步误差可能累积。

- 保留的激进延伸：消息成为可行动的小世界并通过机制契约组成新环境。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H44 · 共同构造的反事实梦境

- 对象/操作：DreamWorld；construct executable counterfactual worlds and derived questions。

- 不变量：synthetic evidence cannot support its own real-world truth。

- 已核验近邻：[N09](https://arxiv.org/abs/1803.10122)；[S18](https://arxiv.org/abs/1901.01753)；[S19](https://arxiv.org/abs/2012.02096)。共享原语：在生成世界中学习及自动环境设计已存在。

- 候选差异：多个贡献者的局部核共同合成可追溯、可反事实编辑的世界。

- 区分例（设计，未运行）：自造环境产生的证据不得反过来证明该环境的现实假设。

- 未证明桥梁：共同构造不是观测现实；不能把合成样本当实证研究结果。

- 保留的激进延伸：模型共同创造经验空间以反过来推动概念、协议和学习规则演化。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H45 · 主动可识别性协议

- 对象/操作：IdentificationState；choose allowed queries by information gain or minimax partition。

- 不变量：unknown likelihood is not a fabricated prior。

- 已核验近邻：[S20](https://arxiv.org/abs/1112.5745)；[S12](https://arxiv.org/abs/2106.02997)。共享原语：已有信息收益查询及因果区分思想。

- 候选差异：对允许查询明确计算机制等价类如何分裂，保留未知响应。

- 区分例（设计，未运行）：当前观测相同但可由一项干预区分时选择该干预；禁用查询不能执行。

- 未证明桥梁：候选族遗漏真机制会产生伪自信，信息增益不保证真实识别。

- 保留的激进延伸：通信主动发明最小可区分问题而非被动接受同类数据。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H46 · 不可行域与负知识胶囊

- 对象/操作：ExclusionPacket；apply conditional hard exclusions or soft penalties and retract。

- 不变量：timeout and heuristic scores do not become hard impossibility。

- 已核验近邻：[N06](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)；[N14](https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm)；[N12](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)。共享原语：真值维护、反例剪枝与前置条件有直接近邻。

- 候选差异：条件化排除集合携带证据等级与撤销规则，区分硬证书和软启发式。

- 区分例（设计，未运行）：搜索超时不能排除全部区域；撤销前提后相关排除必须失效。

- 未证明桥梁：模型生成理由未验证时不能升级为不可行性证明。

- 保留的激进延伸：错误探索成为可移植的负知识资产，压缩整簇无效分支。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H47 · 任务相对的语义商空间

- 对象/操作：QuotientPacket；partition by finite behavior signatures and refine with new queries。

- 不变量：epsilon proximity is not automatically an equivalence relation。

- 已核验近邻：[N03](https://arxiv.org/abs/1207.4114)；[S14](https://arxiv.org/abs/physics/0004057)；[N05](https://isl.stanford.edu/~cover/papers/paper94.pdf)。共享原语：行为等价、bisimulation、状态聚合和任务压缩早已有之。

- 候选差异：协议对象是有限查询族的等价类及精化见证，而非固定潜向量。

- 区分例（设计，未运行）：新查询区分旧同类两状态时必须细分；epsilon 相近不满足传递性时不能直接取商。

- 未证明桥梁：有限查询相同不推出递归 bisimulation 或所有未来任务等价。

- 保留的激进延伸：共同发明问题同时创造新的语义区分和动态粒度。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

### H48 · 相关证据的认知谱系代数

- 对象/操作：EvidenceExpression；normalize idempotent support DAG and evaluate declared dependence。

- 不变量：duplicate source .8 stays .8, not independent .96。

- 已核验近邻：[S21](https://arxiv.org/abs/1910.07910)；[N06](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)；[N13](https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf)。共享原语：来源半环、依赖维护及概率图已有。

- 候选差异：将可撤销证据谱系接入潜对象/学习/联盟，并显式建模共享祖先。

- 区分例（设计，未运行）：同一可靠度 0.8 的来源被转述两次仍是一个原子，不能独立合成 0.96。

- 未证明桥梁：谱系不证明来源真实；预训练数据相关性只能局部标识。

- 保留的激进延伸：让概念、世界和能力的支持结构一起可组合、可撤销，而非累计声音数量。

- 结论：提出而非证成；优先权未知，研究 NOT_RUN。

## 5. 一手来源目录与版本

以下目录使用核验后的标题。inherited 别名保存在 JSON，BibTeX 按同一来源去重。arXiv 首次收录不是自动认定的历史首发；“修订未知”也不表示从未修订。

### S01 · Enabling Agents to Communicate Entirely in Latent Space

[Enabling Agents to Communicate Entirely in Latent Space](https://arxiv.org/abs/2511.09149)

作者：Zhuoyun Du and Runze Wang and Huiyu Bai and Zouying Cao and Xiaoyong Zhu and Yu Cheng and Bo Zheng and Wei Chen and Haochao Ying。arXiv 首版 2025-11-12；最新修订 2026-07-13 v5。

支持范围：连续隐藏状态通信与学习压缩的已发表方案背景。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S02 · LatBridge: Efficient and Stable Model Replacement in Latent-Communication Multi-Agent Systems

[LatBridge: Efficient and Stable Model Replacement in Latent-Communication Multi-Agent Systems](https://arxiv.org/abs/2610.27813)

作者：Jiajun Zhu and Haobo Li and Zixin Chen and Huamin Qu and Wenshuo Zhang。arXiv 首版 2026-10-20；当前 v1，未显示另次修订。

支持范围：共享桥与分离接口用于模型替换后的接口复用。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S03 · Thought Blocks: Non-Autoregressive Latent Communication for Multi-Agent Systems via Trajectory-to-State Compilation

[Thought Blocks: Non-Autoregressive Latent Communication for Multi-Agent Systems via Trajectory-to-State Compilation](https://arxiv.org/abs/2610.23056)

作者：Zhenhan Guan and Xiaolong Liu and Hengwei Ye and Zheng Tian。arXiv 首版 2026-10-16；当前 v1，未显示另次修订。

支持范围：将轨迹压缩为一次构造的 KV 续接记忆。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S04 · Latent Collaboration in Multi-Agent Systems

[Latent Collaboration in Multi-Agent Systems](https://arxiv.org/abs/2511.20639)

作者：Jiaru Zou and Ruizhong Qiu and Gaotang Li and Xiyuan Yang and Katherine Tieu and Pan Lu and Ke Shen and Hanghang Tong and Yejin Choi and Jingrui He and James Zou and Mengdi Wang and Ling Yang。arXiv 首版 2025-11-25；最新修订 2026-08-03 v4。

支持范围：在连续潜空间中协作的 LatentMAS 框架。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S05 · Cache-to-Cache: Direct Semantic Communication Between Large Language Models

[Cache-to-Cache: Direct Semantic Communication Between Large Language Models](https://arxiv.org/abs/2510.03215)

作者：Tianyu Fu and Zihan Min and Hanling Zhang and Jichao Yan and Guohao Dai and Wanli Ouyang and Yu Wang。arXiv 首版 2025-10-03；最新修订 2026-03-02 v2。

支持范围：直接交换和融合模型 KV 缓存。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S06 · Gauge Equivariant Convolutional Networks and the Icosahedral CNN

[Gauge Equivariant Convolutional Networks and the Icosahedral CNN](https://arxiv.org/abs/1902.04615)

作者：Taco S. Cohen and Maurice Weiler and Berkay Kicanaoglu and Max Welling。arXiv 首版 2019-02-11；最新修订 2019-05-13 v3。

支持范围：局部规范变换下的等变网络构造原则。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S07 · Neural Sheaf Diffusion: A Topological Perspective on Heterophily and Oversmoothing in GNNs

[Neural Sheaf Diffusion: A Topological Perspective on Heterophily and Oversmoothing in GNNs](https://arxiv.org/abs/2202.04579)

作者：Cristian Bodnar and Francesco Di Giovanni and Benjamin Paul Chamberlain and Pietro Liò and Michael M. Bronstein。arXiv 首版 2022-02-09；最新修订 2023-01-06 v4。

支持范围：图上向量空间、限制映射与层扩散。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S08 · Oversmoothing as Representation Degeneracy in Neural Sheaf Diffusion

[Oversmoothing as Representation Degeneracy in Neural Sheaf Diffusion](https://arxiv.org/abs/2605.11178)

作者：Arif Dönmez and Axel Mosig and Ellen Fritsche and Katharina Koch。arXiv 首版 2026-05-11；当前 v1，未显示另次修订。

支持范围：以表示退化分析层扩散的过平滑现象。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S09 · DreamCoder: Growing generalizable, interpretable knowledge with wake-sleep Bayesian program learning

[DreamCoder: Growing generalizable, interpretable knowledge with wake-sleep Bayesian program learning](https://arxiv.org/abs/2006.08381)

作者：Kevin Ellis and Catherine Wong and Maxwell Nye and Mathias Sable-Meyer and Luc Cary and Lucas Morales and Luke Hewitt and Armando Solar-Lezama and Joshua B. Tenenbaum。arXiv 首版 2020-06-15；当前 v1，未显示另次修订。

支持范围：通过程序抽象库增长组织程序合成。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S10 · Deep Equilibrium Models

[Deep Equilibrium Models](https://arxiv.org/abs/1909.01377)

作者：Shaojie Bai and J. Zico Kolter and Vladlen Koltun。arXiv 首版 2019-09-03；最新修订 2019-10-28 v2。

支持范围：通过根求解处理隐式平衡状态。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S11 · Neural Task Graphs: Generalizing to Unseen Tasks from a Single Video Demonstration

[Neural Task Graphs: Generalizing to Unseen Tasks from a Single Video Demonstration](https://arxiv.org/abs/1807.03480)

作者：De-An Huang and Suraj Nair and Danfei Xu and Yuke Zhu and Animesh Garg and Li Fei-Fei and Silvio Savarese and Juan Carlos Niebles。arXiv 首版 2018-07-10；最新修订 2019-03-06 v2。

支持范围：利用任务组成结构泛化单演示策略。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S12 · Causal Abstractions of Neural Networks

[Causal Abstractions of Neural Networks](https://arxiv.org/abs/2106.02997)

作者：Atticus Geiger and Hanson Lu and Thomas Icard and Christopher Potts。arXiv 首版 2021-06-06；最新修订 2021-10-27 v2。

支持范围：以因果抽象解释高层变量与神经行为的对应。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S13 · Causal and Compositional Abstraction

[Causal and Compositional Abstraction](https://arxiv.org/abs/2602.16612)

作者：Robin Lorenz and Sean Tull。arXiv 首版 2026-02-18；当前 v1，未显示另次修订。

支持范围：自然变换及组件层次的组合/因果抽象。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S14 · The information bottleneck method

[The information bottleneck method](https://arxiv.org/abs/physics/0004057)

作者：Naftali Tishby and Fernando C. Pereira and William Bialek。arXiv 首版 2000-04-24；当前 v1，未显示另次修订。

支持范围：压缩输入同时保留与目标变量相关的信息。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S15 · Introduction to Program Synthesis, Lecture 17: Introduction to Verified Functional Synthesis

[Introduction to Program Synthesis, Lecture 17: Introduction to Verified Functional Synthesis](https://people.csail.mit.edu/asolar/SynthesisCourse/Lecture17.htm)

作者：Armando Solar-Lezama。首版/修订日期未确立。

支持范围：功能规格、前后条件及验证与合成的关系。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S16 · Learning to learn by gradient descent by gradient descent

[Learning to learn by gradient descent by gradient descent](https://arxiv.org/abs/1606.04474)

作者：Marcin Andrychowicz and Misha Denil and Sergio Gomez and Matthew W. Hoffman and David Pfau and Tom Schaul and Brendan Shillingford and Nando de Freitas。arXiv 首版 2016-06-14；最新修订 2016-11-30 v2。

支持范围：把优化器设计转为学习问题。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S17 · Coalitional Manipulations and Immunity of the Shapley Value

[Coalitional Manipulations and Immunity of the Shapley Value](https://arxiv.org/abs/2310.20415)

作者：Christian Basteck and Frank Huettner。arXiv 首版 2023-10-31；当前 v1，未显示另次修订。

支持范围：研究联盟操作下的分配规则性质。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S18 · Paired Open-Ended Trailblazer (POET): Endlessly Generating Increasingly Complex and Diverse Learning Environments and Their Solutions

[Paired Open-Ended Trailblazer (POET): Endlessly Generating Increasingly Complex and Diverse Learning Environments and Their Solutions](https://arxiv.org/abs/1901.01753)

作者：Rui Wang and Joel Lehman and Jeff Clune and Kenneth O. Stanley。arXiv 首版 2019-01-07；最新修订 2019-02-21 v3。

支持范围：环境与求解者配对生成、演化和迁移。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S19 · Emergent Complexity and Zero-shot Transfer via Unsupervised Environment Design

[Emergent Complexity and Zero-shot Transfer via Unsupervised Environment Design](https://arxiv.org/abs/2012.02096)

作者：Michael Dennis and Natasha Jaques and Eugene Vinitsky and Alexandre Bayen and Stuart Russell and Andrew Critch and Sergey Levine。arXiv 首版 2020-12-03；最新修订 2021-02-04 v2。

支持范围：自动环境设计及对抗性课程构造。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S20 · Bayesian Active Learning for Classification and Preference Learning

[Bayesian Active Learning for Classification and Preference Learning](https://arxiv.org/abs/1112.5745)

作者：Neil Houlsby and Ferenc Huszár and Zoubin Ghahramani and Máté Lengyel。arXiv 首版 2011-12-24；当前 v1，未显示另次修订。

支持范围：以信息准则进行分类和偏好主动学习。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S21 · Generalized Absorptive Polynomials and Provenance Semantics for Fixed-Point Logic

[Generalized Absorptive Polynomials and Provenance Semantics for Fixed-Point Logic](https://arxiv.org/abs/1910.07910)

作者：Katrin M. Dannert and Erich Grädel and Matthias Naaf and Val Tannen。arXiv 首版 2019-10-17；最新修订 2020-07-10 v3。

支持范围：使用来源代数表示逻辑结果的证据组合。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S22 · Introducing dots

[Introducing dots](https://openai.com/index/introducing-dots/)

作者：{OpenAI}。已核验发表/文档日期 2026-09-29；首版/修订日期未确立。

支持范围：产品能力与权限的官方背景说明，不是研究机制来源。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S23 · Autograd mechanics — PyTorch 2.14 documentation

[Autograd mechanics — PyTorch 2.14 documentation](https://docs.pytorch.org/docs/2.14/notes/autograd.html)

作者：{PyTorch contributors}。首版/修订日期未确立。

支持范围：参数 requires_grad、输入梯度与 no-grad 模式的区别。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S24 · Cache strategies · Hugging Face

[Cache strategies · Hugging Face](https://huggingface.co/docs/transformers/main/en/kv_cache)

作者：{Hugging Face contributors}。首版/修订日期未确立。

支持范围：不同 KV 缓存类及策略的官方接口说明。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### S25 · Safetensors · Hugging Face

[Safetensors · Hugging Face](https://huggingface.co/docs/safetensors/index)

作者：{Hugging Face contributors}。首版/修订日期未确立。

支持范围：张量存储格式与安全读取的官方文档背景。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### inherited:R06 · Hidden Messages Between Diffusion Language Model Agents: Causal Evidence for Latent Communication

[Hidden Messages Between Diffusion Language Model Agents: Causal Evidence for Latent Communication](https://arxiv.org/abs/2610.28905)

作者：Alan-Barsag Gazzaev and Alexey Gavrilov and Sergey Muravyov and Ilya Makarov。arXiv 首版 2026-10-20；当前 v1，未显示另次修订。

支持范围：扩散语言模型之间连续隐藏消息及传递时机的研究。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### inherited:R07 · Learning to Communicate with Deep Multi-Agent Reinforcement Learning

[Learning to Communicate with Deep Multi-Agent Reinforcement Learning](https://arxiv.org/abs/1605.06676)

作者：Jakob N. Foerster and Yannis M. Assael and Nando de Freitas and Shimon Whiteson。arXiv 首版 2016-05-21；最新修订 2016-05-24 v2。

支持范围：多智能体强化学习中端到端学习通信协议。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### inherited:R08 · HyperNetworks

[HyperNetworks](https://arxiv.org/abs/1609.09106)

作者：David Ha and Andrew Dai and Quoc V. Le。arXiv 首版 2016-09-27；最新修订 2016-12-01 v4。

支持范围：一个网络生成另一网络参数。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### inherited:R09 · Coordination Among Neural Modules Through a Shared Global Workspace

[Coordination Among Neural Modules Through a Shared Global Workspace](https://arxiv.org/abs/2103.01197)

作者：Anirudh Goyal and Aniket Didolkar and Alex Lamb and Kartikeya Badola and Nan Rosemary Ke and Nasim Rahaman and Jonathan Binas and Charles Blundell and Michael Mozer and Yoshua Bengio。arXiv 首版 2021-03-01；最新修订 2022-03-22 v2。

支持范围：以共享全局工作空间协调多个神经模块。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### inherited:R11 · Finding Alignments Between Interpretable Causal Variables and Distributed Neural Representations

[Finding Alignments Between Interpretable Causal Variables and Distributed Neural Representations](https://arxiv.org/abs/2303.02536)

作者：Atticus Geiger and Zhengxuan Wu and Christopher Potts and Thomas Icard and Noah D. Goodman。arXiv 首版 2023-03-05；最新修订 2024-02-21 v4。

支持范围：解释性因果变量与分布式神经表示的对齐。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### inherited:R12 · The Platonic Representation Hypothesis

[The Platonic Representation Hypothesis](https://arxiv.org/abs/2405.07987)

作者：Minyoung Huh and Brian Cheung and Tongzhou Wang and Phillip Isola。arXiv 首版 2024-05-13；最新修订 2024-07-25 v5。

支持范围：跨模型与模态表示趋同的假说和研究。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### inherited:R13 · Revisiting the Platonic Representation Hypothesis: An Aristotelian View

[Revisiting the Platonic Representation Hypothesis: An Aristotelian View](https://arxiv.org/abs/2602.14486)

作者：Fabian Gröger and Shuo Wen and Maria Brbić。arXiv 首版 2026-02-16；最新修订 2026-06-25 v2。

支持范围：对表示趋同的规模校准及局部关系再分析。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### inherited:R14 · What Converges in the Platonic Representation Hypothesis? Structure over Geometry

[What Converges in the Platonic Representation Hypothesis? Structure over Geometry](https://arxiv.org/abs/2609.27252)

作者：Junwon You and Mihyun Jang and Sangwoo Mo and Jae-Hun Jung。arXiv 首版 2026-09-23；当前 v1，未显示另次修订。

支持范围：区分关系结构与度量几何的趋同研究。 边界：不证明本项目机制新颖或有效。

日期解释：arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.

### N01 · Consensus on Transaction Commit

[Consensus on Transaction Commit](https://arxiv.org/abs/cs/0408036)

作者：Jim Gray and Leslie Lamport。arXiv 首版 2004-08-14；当前 v1，未显示另次修订。

支持范围：事务提交的一致性、两阶段提交与故障假设。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted. Author Microsoft result lists January 2004 report and 2006 journal publication; arXiv was August 2004. Direct Microsoft fetch timed out, so that report date is secondary metadata in this ledger, not the arXiv first date.

### N02 · Nonnegative Decomposition of Multivariate Information

[Nonnegative Decomposition of Multivariate Information](https://arxiv.org/abs/1004.2515)

作者：Paul L. Williams and Randall D. Beer。arXiv 首版 2010-04-14；当前 v1，未显示另次修订。

支持范围：冗余与协同信息的分解结构；不等于本项目任务收益交互项。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.

### N03 · Metrics for Finite Markov Decision Processes

[Metrics for Finite Markov Decision Processes](https://arxiv.org/abs/1207.4114)

作者：Norman Ferns and Prakash Panangaden and Doina Precup。已核验发表/文档日期 2004；arXiv 首版 2012-07-11；当前 v1，未显示另次修订。

支持范围：基于 bisimulation 的有限 MDP 状态距离及聚合。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted. UAI2004 is explicitly reported on arXiv; the 2012 deposit is not the publication year.

### N04 · Capability Myths Demolished

[Capability Myths Demolished](https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf)

作者：Mark S. Miller and Ka-Ping Yee and Jonathan Shapiro。已核验发表/文档日期 2003；首版/修订日期未确立。

支持范围：对象能力的授权与隔离模型。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.

### N05 · Successive Refinement of Information

[Successive Refinement of Information](https://isl.stanford.edu/~cover/papers/paper94.pdf)

作者：William H. R. Equitz and Thomas M. Cover。已核验发表/文档日期 1991-03；首版/修订日期未确立。

支持范围：逐次细化的率失真条件与非普遍可细化性。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted. Stanford repository also exposes a June 1989 Equitz technical report; do not claim the 1991 journal date is the first conception.

### N06 · A Truth Maintenance System

[A Truth Maintenance System](https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a)

作者：Jon Doyle。已核验发表/文档日期 1979-06-01；首版/修订日期未确立。

支持范围：记录信念理由、依赖回溯及前提变化后的修订。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.

### N08 · Distilling the Knowledge in a Neural Network

[Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531)

作者：Geoffrey Hinton and Oriol Vinyals and Jeff Dean。arXiv 首版 2015-03-09；当前 v1，未显示另次修订。

支持范围：把复杂模型预测行为蒸馏进另一个模型。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.

### N09 · World Models

[World Models](https://arxiv.org/abs/1803.10122)

作者：David Ha and Jürgen Schmidhuber。arXiv 首版 2018-03-27；最新修订 2018-05-09 v4。

支持范围：学习环境动态并在内部生成环境中组织策略学习。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.

### N10 · Event-triggered real-time scheduling of stabilizing control tasks

[Event-triggered real-time scheduling of stabilizing control tasks](https://www.ee.ucla.edu/~tabuada/Papers/EventTriggered.pdf)

作者：Paulo Tabuada。已核验发表/文档日期 2007-09；首版/修订日期未确立。

支持范围：根据状态事件而非固定时钟调度控制任务。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted. The inspected PDF is labelled DRAFT; September 2007 journal date is verified from the author publication list. PDF revision date unknown.

### N11 · Structure-Mapping: A Theoretical Framework for Analogy

[Structure-Mapping: A Theoretical Framework for Analogy](https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf)

作者：Dedre Gentner。已核验发表/文档日期 1983-04；首版/修订日期未确立。

支持范围：把域间关系结构而非外观属性作为类比对象。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.

### N12 · Guarded commands, non-determinacy and formal derivation of programs

[Guarded commands, non-determinacy and formal derivation of programs](https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html)

作者：Edsger W. Dijkstra。已核验发表/文档日期 1975-08；首版/修订日期未确立。

支持范围：用谓词变换与最弱前置条件描述程序规格。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.

### N13 · Factor Graphs and the Sum-Product Algorithm

[Factor Graphs and the Sum-Product Algorithm](https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf)

作者：Frank R. Kschischang and Brendan J. Frey and Hans-Andrea Loeliger。已核验发表/文档日期 2001-02；首版/修订日期未确立。

支持范围：因子图上的双向消息可表达前后向等既有算法。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.

### N14 · Introduction to Program Synthesis, Lecture 10: Introduction to Functional Synthesis

[Introduction to Program Synthesis, Lecture 10: Introduction to Functional Synthesis](https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm)

作者：Armando Solar-Lezama。首版/修订日期未确立。

支持范围：作者教学资料明确说明 CEGIS 的候选、反例与累积约束循环及其失效例。 边界：不证明本项目机制新颖或有效。

日期解释：Publication date at displayed precision; null revision date is unknown. First public appearance not asserted. The URL contains course2020 and page copyright says 2018; neither is treated as an exact publication/revision date.

## 6. 不成功访问与开放项

JHU 的能力论文 PDF 返回 502；后续从作者相关 Agoric 论文库的下载链接成功读取同一论文。微软事务论文页面直接抓取超时，但 arXiv 正式记录成功，报告与期刊年份另外标注为元数据而非混作 arXiv 日期。

自然梯度 DOI 返回 403；官方出版商检索摘要仅作为 N07 线索保留，未绕过访问限制，未进入机制证据或 references.bib。H37 的广泛优先权比较仍需后续全文审查。H28/H33 也须扩展分岔、混合系统及非平衡计算近邻。

这些开放研究问题不删除机制，也不阻塞本次准确的来源台账；不能把本次 done 状态解释为研究验证完成。

## 7. 产物、要求与真实检查

- docs/related_work.md：D01-1 与 P12 的逐项比较；48 项对象/不变量/反例/延伸。

- specs/novelty_ledger.json：D01-1/2/3；供给与实际核验字段、源状态、日期、别名修订及元数据快照索引。

- paper/references.bib：D01-3；核验标题、作者、可定位 URL、版本与无重复引用键。

- run_state/checks/D01_validation.json：实际标准库静态检查结果；依赖、输入哈希、覆盖与引用一致性。

- run_state/checks/D01_source_observations.json：实际 primary open 的元数据观察记录。metadata_sha256 仅标识观察记录，不冒充完整网页或论文文件哈希。

本轮没有调用研究模型，没有执行神经网络初始化、推理、训练或评测，没有读取无关私有资料、付费或发布。全部未来研究路径保持 NOT_RUN。
