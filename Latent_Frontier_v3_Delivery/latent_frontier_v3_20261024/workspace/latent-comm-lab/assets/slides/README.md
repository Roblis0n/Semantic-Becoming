# Semantic Becoming V3：可编辑演示文稿

research_36.pptx 是 36 页研究版，brief_12.pptx 是按当前 12 页脚本选择主线并重组备注的精简版。所有标题、正文、标签、箭头和机制图都是 PowerPoint 原生可编辑对象，不是整页截图。幻灯片备注保留完整讲稿、对应原始文件路径及已核验的近邻来源 URL。

源文件：research_36.source.json、brief_12.source.json、source/ 逐页 JSON/SVG、build/export_decks.mjs。生成器位于 ../figures/build_media_sources.py。build/rebuild.sh 使用当前已安装 Artifact Tool 运行时重建。每次导出使用独立验证目录，不修改原始输入包。

精确导出的 PPTX 已通过 LibreOffice 转 PDF，再将全部 48 页渲染为 PNG 并逐页视觉复核。PDF 在 pdf_verified/，最终检查图在 verified_renders/。这不是“在 Microsoft PowerPoint 中测试”的声明。不同客户端仍可能替换未安装字体。

字体使用系统 Noto Sans CJK SC 与 Noto Serif CJK SC，只引用字体名称，没有打包字体文件。默认暖底、墨色、少量强调来自上传研究报告的原创迁移方向，不声称是 Anthropic 或 Duolingo 官方模板或 token。

研究状态：NOT_RUN。全部数字是解析示意或结构计数，不含模型性能图。封面明确“前沿机制提案 / 无模型实测”。
