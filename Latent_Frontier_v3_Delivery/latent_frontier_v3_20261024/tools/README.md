# 本包中真正实现的工具

`frontierctl.py`：严格JSON、路径边界、政策闸门、依赖DAG、文件owner重叠、注册表/配方/输入完整性校验、纯计划编译、状态初始化/就绪计算/后代失效函数、产物哈希验证和AST空实现提示。只用标准库，不联网、不调用shell、不加载任何模型。

`math_reference.py`：小维精确矩阵、可逆2×2换基、标量行为更新运输、有限任务等价分区、布尔证据概率、有限联盟Shapley。它们是明确范围的可执行参考算法，不是完整H25–H48神经实现。

测试命令：`python -m unittest discover -s tests -v`。禁止把整个未来research_locked测试集自动执行；当前tests目录只包含本包获准的计划/数学工具测试。

计划validate只检验本包，不检查尚未由Dot生成的科研仓库。compile只导出计划引用。gate返回允许决策但不实际执行动作，更不提供硬安全沙箱。文件状态更新函数由单coordinator调用，多进程互斥与全量科研runtime仍是Dot任务。

所有未来核心科研实现都在task_graph内明确分配；这些工具不是偷换交付范围的替代品。
