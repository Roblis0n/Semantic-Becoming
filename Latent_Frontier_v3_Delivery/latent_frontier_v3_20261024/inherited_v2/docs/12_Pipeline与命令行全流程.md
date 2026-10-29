# 12｜Pipeline与命令行全流程


## 12.1 三个不同 DAG
研发 DAG 管 Dot 的研究与编码任务；配方 DAG 描述未来模型训练和计算；数学示意 DAG 执行固定函数和小张量。它们可以共享调度器，不能共享成功状态或证据命名。

## 12.2 配方 DAG 标准节点
world_generate→split→view_build→state_extract→message_build→channel→receive_or_apply→decode→loss_or_score→artifact_export。复杂路线增加 branch、field_iterate、chart_route、continuation_resume 或 policy_select。真实 state_extract/decode/train 节点当前均 locked，不转换成 fixture 后继续叫同一个 run。

## 12.3 命令契约
`lcomm ideas list`：列出 H01—H24 与源码映射。`lcomm recipe inspect FILE`：解释参数、对象与训练项。`lcomm pipeline compile FILE`：输出 execution_plan，不加载模型。`lcomm fixture run FILE`：仅固定数学示意。`lcomm packet inspect FILE`：检验并展示结构，不暴露全部潜内容。`lcomm model train FILE` 与 `lcomm model run FILE`：源码完整，当前返回策略拒绝。`lcomm export bundle`：只汇总既有产物。

每条命令提供人读文本与 --json 模式；日志走 stderr，机器结果走 stdout。非零退出码区分格式、策略、资源、实现错误。路径含空格与中文可用，不依赖调用 shell 的工作目录。

## 12.4 NodeSpec
node_id、operation、depends_on、inputs、outputs、mode、required_capabilities、scope、implementation_hash、config_hash、retry、cache。NodeResult 记录 status、artifact_refs、error_code、actual_mode 和 research_model_executed。状态包括 planned、running、done、failed、blocked_policy、blocked_tool、interrupted。

## 12.5 缓存与幂等
缓存依据内容、实现、配置与对象版本。模型状态缓存还需 checkpoint、tokenizer、模板和位置规格。当前不能读取旧模型激活来变相开展语义实验。数学示意缓存单独 namespace。输出先临时写入、校验，再原子提交。

## 12.6 恢复
启动时识别未完成节点，校验上游 artifact 与 fingerprint；running 不等于完成。恢复同一 run 不重复计费、不覆盖旧证据。代码变化后只使受影响节点失效，保持依赖可追溯。

## 12.7 一条无需模型的完整展示
编译 H01+H06+H07 配方→生成已知矩阵与局部坐标→执行 typed program→导出 operator composition trace→生成概念图与报告。它展示软件如何组织机制，不展示语言模型能力。模型模式继续锁定，构成诚实而完整的当前演示。
