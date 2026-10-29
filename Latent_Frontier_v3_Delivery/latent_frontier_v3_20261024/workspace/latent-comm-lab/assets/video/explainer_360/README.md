# explainer_360：带合成旁白的个人非商业版本

explainer_360_narrated_personal.mp4 是实际 H.264/AAC 容器，时长 360 秒。普通话来自 TTS.ai 的免费 MeloTTS / ZH，无账号、无新增支出。语音及含该语音的视频仅可个人、非商业使用，依据 https://tts.ai/terms/ 第 7(a) 节；没有购买商业许可。

实际音频在 ../../audio/explainer_360.narration.wav。timeline_audio.json 与 project_audio.mlt 保留真实音轨、可编辑视觉片段和字幕引用。字幕在 ../../subtitles/explainer_360.audio_timed.srt / .vtt / .json，以每个合成语音片段的实际 PCM 帧数建立边界，不按字数猜时长，不使用 ASR，也不声称逐词强制对齐。

重要：尚无本版本已完成真实试听的证据，未评估发音或听感。P17 的试听要求仍是未完成的验收项，不能把波形、响度、完整解码或画面检查当成试听。因此本版本明确标“合成旁白（未试听）”。

原来的 explainer_360_silent_draft.mp4、timeline.json、project.mlt 和 draft_timing 字幕保持不变。独立编写的源文件、PPT、SVG 与不含此语音的无声视觉稿，不会自动受该 TTS 音频许可限制。

重建视觉/音轨版本：复用现有已核验 WAV，不重新提交旁白；运行 assemble_narration.py，再运行 build_narrated_projects.py、render_narrated.mjs、validate_narrated.py，使用对应 edition 选项。所有文件位于本项目；不下载研究模型。旧动画目录的脚本重建无声阶段，不是此配音阶段的最终验收入口。

MLT XML 已静态检查，未声称在图形剪辑器中打开。研究模型、训练、评测和 benchmark 始终 NOT_RUN。


## Current acceptance scope — 2026-10-27

User explicitly removed real auditory review as a delivery condition (Sentinel_5503d7e4a82481919968d26a5bc5da75). Status: **USER_WAIVED_NOT_PERFORMED**, not listening PASS. All production and objective QA are complete. Earlier mandatory-audition blockers above are historical and superseded only for delivery acceptance. Research remains NOT_RUN; generated TTS and incorporating videos remain personal/noncommercial only.
