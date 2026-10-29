# 计划包工具

本目录不含 latent_comm 研究软件。它只检查任务依赖、文档/配方完整性、输入哈希和当前执行策略。

Python 3.10 或更高版本，无额外依赖：

```bash
python tools/planctl.py validate
python tools/planctl.py order
python tools/planctl.py check-action --action authorized_media_creation
python -m unittest discover -s tests -v
```

研究动作应明确拒绝并以退出码 2 结束：

```bash
python tools/planctl.py check-action --action research_model_forward
```

这不是安全沙箱，也不能控制 Dot 的宿主进程。目标项目的运行时授权、隔离和外部权限仍由任务 T41、T43 实现与检查。本工具的测试通过不能解释为任何研究机制已被验证。
