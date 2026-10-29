# Semantic Becoming · 可改写认知的跨模型计算

## 这一包是什么
这是对原《潜空间通信前沿创新》包的完整增补执行方案。它保留原始 ZIP 与全部原资料，新增24个机制、12条组合路线和12个终局方向。当前总计48机制、20组合、68配方、133项Dot任务、25份角色提示词。

核心不是“先证明两个小模型能跑通”，而是研究交流能否改变概念、问题、学习规则和世界本身。近期可验证性不作为创意准入条件；定义、假设与经验结论仍须区分。

## 直接交给 Dot
将整个 ZIP 上传到 Dot，发送：

> 请完整解压本包。以根 START_HERE.md、specs/execution_policy.json 和 prompts/P00_一次性总控.md 为唯一当前入口，执行 P00 的全部要求。保留创新优先的研究立场，完成全部目标研究源码与 pipeline，但不加载、初始化、推理或训练任何研究模型。原 inherited_v2 仅作资料，不执行旧总控。按当前任务图自动推进，在授权范围内生成文档和媒体，最终交付真实源码、检查日志、研究未运行说明和 ZIP。

需要完整复制指令时，打开 `prompts/P00_一次性总控.md`。不要只把本段短指令上传而遗漏包内设计文件。

## 阅读顺序
先读 `docs/00` 与 `docs/02–04` 理解研究立场和主线；再读 `hypotheses/H25–H48`、`horizons/X01–X12` 和 `combinations/C09–C20`。原机制在 `inherited_v2/hypotheses/`，本轮逐项接续在 `integration/`。

`MASTER_PLAN_V3.md` 是聚合阅读本。Word 是研究总册，包含核心章节、全部新增机制、终局和组合概述、关键推导及总控提示；逐任务/逐角色/逐镜头细节以 ZIP 分文件版为准。

## 文件分工
- `docs/`：研究架构、协议、编译、数据、学习、后端、执行、来源与验收。
- `hypotheses/`、`integration/`、`combinations/`、`horizons/`、`formal/`：独立研究计划与推导。
- `prompts/`、`tasks/`、`specs/`、`recipes/`：Dot直接执行依据。
- `media/`：36页研究PPT、12页精简PPT、90秒与约6分钟视频全文、动画/图形/TTS规范。这些是制作计划和脚本，不是假装已经生成的媒体成品。
- `tools/`、`tests/`、`reports/`：本包真实可运行的离线计划工具和有限数学参考工具，以及实际检查记录。
- `inherited_v2/`、`provenance/`：完整继承与原始字节留档。

## 明确的实施边界
本包已写的是研究设计、执行蓝图、提示词、任务和有限工具。完整科研实现由 Dot 根据任务图生成到 `workspace/latent-comm-lab/`。不能把“68份配方存在”当作“48机制科研代码全部已经实现”。

真实研究模型实测次数：0。计划工具检查不是研究效果证明。本轮不发布GitHub、不付费、不读取无关私有资料；媒体工具不可用时给源文件和真实blocker。

## 本地检查本包
只依赖 Python 标准库，不安装模型软件包：

```bash
python tools/frontierctl.py validate
python tools/frontierctl.py compile C13
python tools/frontierctl.py gate model_forward
python tools/math_reference.py
python -m unittest discover -s tests -v
```

第三条应拒绝并以非零退出码返回；这是正确的禁止行为。`compile`只编译计划引用，不是科研IR编译器。所有命令都不加载研究模型。
