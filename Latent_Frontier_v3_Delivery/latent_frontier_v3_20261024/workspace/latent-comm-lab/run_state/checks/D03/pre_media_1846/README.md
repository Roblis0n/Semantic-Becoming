# Semantic Becoming 可改写认知的跨模型计算

前沿机制提案 / 无模型实测

本仓库把跨模型消息扩展为可执行操作、概念、问题关系、学习方向、可塑性规则和世界动力学。研究按三条线展开：交流产生可计算语言，交流传递学习能力，交流构造可探索世界。

当前交付是源代码、条件理论、有限参考算法、锁定的学习/后端入口及真实制作的展示材料。研究状态始终为 NOT_RUN，不表示模型能力、性能或新颖性已经实证成立。全量封包和外部媒体状态由最终审查决定，本 README 不替未完成任务预先宣布完成。

## 从这里阅读

- [中文研究总稿](docs/research_monograph.md)：三条主线、条件推导与反例、所有机制/组合/配方/终局、127项机制 LossSpec、23项假设、13学习阶段、38条未来分叉及46项去重参考文献。
- [形式推导指南](docs/formal_notes/00_reading_guide.md)：十章数学推导，明确区分定义 D、假设 A、机制 H、愿景 V 和经验 E。E 为空。
- [来源与相关工作](docs/related_work.md)：48机制的近邻与可区分主张；[来源台账](specs/novelty_ledger.json)保留实际核验层级。
- [前沿分叉](docs/frontier_afterword.md)：38个尚未实现的扩展，不因近期资源或 benchmark 难度删除。
- [论文 LaTeX 源](paper/main.tex)与[书目](paper/references.bib)：与总稿相同的完整研究内容，可离线排版，不含虚构实验。LaTeX源已实际排为55页并检查版面；该PDF仅为本任务QA中间件。排版使用XeLaTeX、Noto CJK与DejaVu字体。

## 覆盖范围与对象流

48机制分为基础 H01–H24 和新增 H25–H48；20组合为 C01–C20；68配方等于48加20。12终局 X01–X12 是有限架构入口与假设链，不能另算12个已验证算法。38条新增未来分叉也没有冒充当前实现。

- 概念线：H26 拼合障碍 → H36 可执行反例 → H27 三值谓词和本体迁移 → H29 解关系 → H40 卫生宏与 ISA。冲突允许分域、撤回或保留未决，不强制生成概念。
- 学习线：H25 成套坐标运输 → H37 公共行为方向与可达残差 → H38 支持集更新规则 → H39 版本事务。L13 写出了 H37→H38 的实际 live 源码子图；未运行模型。
- 世界线：H31 因果方程移植 → H43 保共享噪声的联合核 → H44 合成世界 → H29/H42 问题与协议生态 → H48 来源依赖。合成轨迹不能自证现实。

H33/H34 的轨迹计算、H35/H47 的尺度与任务商、H28 的结构分岔、H26 的多域知识保持独立语义，不被一个统一损失或固定点假设覆盖。

## 目录与责任

- src/latent_comm/core、packets：类型、版本、角色视图、作用域、损失与预算。
- src/latent_comm/mechanisms：48套专用对象、有限算法、神经适配源码、loss和迁移合同。
- src/latent_comm/compositions：20条实际类型化对象流；configs/compositions保存编译IR。
- src/latent_comm/worlds、data：12类世界与W13共用投影/分割，研究数据与数学fixture分开。
- src/latent_comm/learning：L01–L13专用目标与共享优化器；完整/一阶元梯度、离散选择和重算边分别声明。
- src/latent_comm/backends、backend_specs：prefix、residual、KV、行为接口与存储能力合同，实际模型绑定仍为 UNBOUND。
- src/latent_comm/compiler、runtime、safety：编译检查、事务恢复和政策边界。
- src/latent_comm/horizon、docs/horizons：12个终局的有限入口和独立说明。
- configs/mechanisms：48份目标机制配置；configs/compositions：20份目标组合配置。原始68份配方在只读设计包 PLAN_ROOT/recipes，不在本仓库根下虚构一个 recipes 目录。
- tests：静态/合同/有限参考检查及未来研究检查定义。不要无筛选地执行全部测试，某些 legacy guard 测试会触及本轮禁止调用的研究入口。
- assets：SVG、可编辑PPT、动画、视频、音频和字幕；各文件的实际生成与验收状态见其 manifest 和 reports/media_qa.json。
- run_state/receipts、run_state/checks：内容寻址任务回执、真实检查和偏差记录。输入变化会使后代回执失效。

## 当前可以做什么

只读源码、解析 JSON/AST、验证回执与执行经审查的标准库有限检查。D03 自身检查只读取文档和源码，不导入研究模块：

    python run_state/checks/D03/validate_documentation.py
    python scripts/task_checkpoint.py verify D03

第一条在依赖重验完成后的最终快照上检查覆盖、来源和文件映射；第二条要求 D03 回执已经提交。如果依赖变化，失败是需要重新核对的信号，不能改成假成功。

有限例的预算是维数≤64、步骤≤128、案例≤64，嵌套调用共享预算。源配置中的未来训练步数不授予当前执行权。本文不提供一条“跑全部”命令，以免把静态验证与研究运行混在一起。

## 明确禁止的研究路径

不得下载权重、加载或随机初始化任何研究神经模型，不得 forward、generate、train、eval、benchmark，也不得调用云端研究模型 API。随机 tiny model 仍然是研究模型，不是获准数学例。当前 model/data manifest 为 UNBOUND，不分配模型设备。

冻结基础权重不等于在 receiver 外包 no_grad；若桥接输入需梯度，该路径必须保留。不同 tokenizer 不直接KL；KV布局不猜；监督标签不进入 sender/receiver；存储记录不保留 autograd，需要重算。这些是源码合同，实际神经后端集成保持 NOT_RUN。

## 证据与来源

标准矩阵、概率、有限程序例只说明指定对象与条件，不证明真实跨模型语义。D02 的24项有限数学检查和46项静态/来源检查属于审查证据，不是模型实验。所有研究结果表为 NOT_RUN，不填 accuracy、speedup 或 SOTA。

D01 共保留57条来源记录，去重可用书目46条。PRIMARY_CHECKED 多数是主要来源元数据、摘要或目标内容核对，并非全文读完或复现。N07直接全文访问受限，未用于实质引用。不存在全球首创认证，动力系统、自然梯度及若干未来分叉邻域仍需专门文献审查。

## 审计偏差没有被删除

L13 初次全学习审查错误选择了三个 legacy 研究入口调用。它们在首个政策闸门被拒绝，神经导入清单为空，没有模型、tensor、初始化、前向、训练、评估或数据生成。但入口尝试本身不符合本轮严格要求，不能声称“零入口尝试”。

详情见 [审计事件](src/latent_comm/learning/joint/AUDIT_INCIDENT.md) 与 run_state/checks/L13_noncompliant_legacy_guard_attempt.txt。纠正后的收集器先做AST预检，116项安全检查另行保存，不把上述尝试计为获准检查通过。

## 媒体与许可状态

展示文件以“前沿机制提案 / 无模型实测”标识，图中数学动态为解析示意。SVG、两套可编辑幻灯片、五个机制动画和视频素材的生成/打开记录各自保留；它们不是模型结果。

当前 freeTTS.ai/MeloTTS 中文旁白通过匿名零新增费用路线生产。不要把已有静音视频或预估字幕当最终有声版本，也不宣称人工试听或中文发音QA已经完成。最终音轨、混流和字幕重对齐请核对最新媒体报告。

tts.ai 输出受[2026年9月14日生效的服务条款](https://tts.ai/terms/)约束，仅限个人、非商业使用，不代表无限制商用授权。音频许可与本项目源码、PPT、SVG的来源权利分开；仓库不因包含书目或媒体而取得第三方资产的额外权利。

本轮只做本地交付，不公开发布、不购买、不发外部消息，不读取无关私有资料。关于研究模型的未来执行、外部资源或发布，需要相应新授权。
