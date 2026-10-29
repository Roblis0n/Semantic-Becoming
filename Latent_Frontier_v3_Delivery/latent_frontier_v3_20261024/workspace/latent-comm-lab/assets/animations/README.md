# 五个机制动画：可编辑源与真实导出

A01–A05 分别为 20、25、30、25、30 秒。每个目录有离线 index.html、scene.json、source.svg、final.svg、H.264 MP4、五个语义关键帧与接触表。动画源、精确数学输入和事实→解释→下一步反馈都可编辑。

在本项目根目录运行 python assets/animations/build_animations.py 重建源；使用已安装运行时执行 assets/animations/render_media.mjs animations 重建媒体。需要现有 sharp、ffmpeg 与系统字体，不下载研究模型或打包字体。

所有 MP4 已经 ffprobe 检查并完整解码，开头实际解码帧与 25 个语义关键帧已查看。时长与可播放性不证明研究命题有效。数字只表示有限解析示意，研究状态 NOT_RUN。

HTML 支持播放、暂停、重播、拖动、减少动态效果；无自动播放。JavaScript 语法、35 项语义状态和模拟 DOM 控件契约检查已通过。实际 Chromium 在载入页面前因 socket() failed: Operation not permitted 失败，因此不声称已在真实浏览器中操作验证，也不把模拟 DOM 视为浏览器测试。

当前五个机制动画为无声数学演示，不包含旁白。两部解释视频和旁白的未完成音频事项见各自 media_status.json。
