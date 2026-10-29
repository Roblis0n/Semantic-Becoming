"""Narrow D03 media-status update. No research execution or model imports."""
from pathlib import Path
import json,hashlib,datetime,subprocess
D=Path(__file__).resolve().parent;W=D.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
qa=json.loads((W/'assets/video/explainer_360/narrated_qa.json').read_text());review=json.loads((W/'assets/video/explainer_360/narrated_visual_review.json').read_text());generation=json.loads((W/'assets/audio/tts_ai/generation_summary.json').read_text())
assert qa['video']['full_decode_passed'] and qa['video']['sha256']==review['video_sha256']==sha(W/qa['video']['path'])
assert review['actual_visual_inspection'] and review['sample_count']==len(qa['samples'])
assert generation['accepted_submission_count']==60 and generation['accepted_submission_characters']==1811
assert generation['unique_source_jobs']==58 and generation['unique_source_characters']==1754
now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
media=f'''媒体表达沿用概念、学习、世界三条线，图中的有限数值必须标“解析示意”。媒体、音频和字幕是展示对象，不是研究证据。**媒体状态快照：{now}。** TTS.ai/MeloTTS 普通中文合成声的90.000秒与360.000秒有声MP4、完整WAV均已生成；14段与44段字幕依据实际合成音频片段的PCM边界编排，不按字数估时。两版均有完整解码、时长、响度、削波和画面检查；短版复用未改变的已核验证据，长版完成此次新增检查。这些检查不是人工试听、逐词发音核验或模型效果验证，原静音草稿作为历史保留。

全部58段唯一文案、1,754字已有对应WAV。累计60次请求获受理、1,811字，credits_used=0；增加的两次分别是第29段16字和第36段41字在明确告知可能重复后获准的替代合成。两份原请求的远端结果仍记UNKNOWN，不把它们抹掉或算作新增独立文案；替代音频已经取回，不再缺少旁白。此前目的地与负载拒绝、后续具体授权及实际提交分别留档。现已无待提交的旁白，不重传已完成片段；私密恢复能力和临时下载地址不进入交付包。

实际试听与中文发音审查仍是必需步骤。2026年10月27日再次检查当前音频输入能力，工具明确不支持音频输入，实际听审覆盖仍为零；不把波形、字幕、完整解码或画面检查等同试听。因此媒体素材及客观检查完成，但听觉验收仍单独受阻，不能声称所有验收通过。生成的TTS音频及包含它的视频受 [tts.ai服务条款](https://tts.ai/terms/)（2026年9月14日生效）的个人、非商业使用限制，不代表无限制商用；此限制不扩张为源码、PPT或SVG的许可。当前状态见 [媒体报告](reports/media_qa.json) 和 [合成记录](assets/audio/tts_ai/generation_summary.json)。本文仅作本地文档交付，不对外公开。
'''
mdold=(D/'baseline/research_monograph.md').read_text();a=mdold.index('媒体表达沿用概念、学习、世界三条线');b=mdold.index('\n\n## 10',a);md=mdold[:a]+media.rstrip()+mdold[b:];(W/'docs/research_monograph.md').write_text(md)
fragment=subprocess.run(['pandoc','--from=markdown','--to=latex'],input=media,text=True,capture_output=True,check=True).stdout
texold=(D/'baseline/main.tex').read_text();a=texold.index('媒体表达沿用概念、学习、世界三条线');b=texold.index('\\section{10 ',a);tex=texold[:a]+fragment+'\n'+texold[b:];(W/'paper/main.tex').write_text(tex)
rdold=(D/'baseline/README.md').read_text();a=rdold.index('## 媒体与许可状态');rd=rdold[:a]+f'''## 媒体与许可状态

展示文件以“前沿机制提案 / 无模型实测”标识，图中数学动态为解析示意。SVG、两套可编辑幻灯片、五个机制动画和视频素材不是模型结果。

状态快照：**{now}**。

- **两版实际有声输出已生成**：[90.000秒MP4](assets/video/intro_90/intro_90_narrated_personal.mp4)与[完整WAV](assets/audio/intro_90.narration.wav)，以及[360.000秒MP4](assets/video/explainer_360/explainer_360_narrated_personal.mp4)与[完整WAV](assets/audio/explainer_360.narration.wav)。14段、44段字幕按实测PCM片段边界编排；解码、时长、响度、削波和画面检查均有证据。短版未重做，原静音稿作为历史保留。
- **实际计数与历史分开**：58个唯一文案片段、1,754字已全部取得WAV；累计60次请求获受理、1,811字，credits_used=0。第29段16字及第36段41字的原请求远端结果仍记UNKNOWN，获准重复风险替代合成的两次请求另记。现已无缺失旁白、无待提交文案；此前拒绝与具体授权分别保留，不盲目重传。私密恢复能力和临时下载地址不入包。
- **试听仍单独阻塞**：2026年10月27日工具再次明确不支持音频输入，实际听审覆盖为零。P17要求的试听及中文发音审查未完成；客观解码、波形或字幕检查不是人工试听或逐词核验。媒体素材已存在不等于全部验收通过。当前证据见[媒体报告](reports/media_qa.json)和[合成记录](assets/audio/tts_ai/generation_summary.json)。

**生成的TTS音频及包含它的视频**受[2026年9月14日生效的服务条款](https://tts.ai/terms/)约束，仅限个人、非商业使用，不代表无限制商用授权。此限制不扩张为本项目源码、PPT、SVG的许可，它们的来源权利分开记录。

本轮研究始终NOT_RUN；只做本地交付，不公开发布、不购买、不发外部消息，不读取无关私有资料。关于研究模型的未来执行、外部资源或发布，需要相应新授权。
''';(W/'README.md').write_text(rd)
assert md.split('媒体表达沿用概念、学习、世界三条线')[0]==mdold.split('媒体表达沿用概念、学习、世界三条线')[0]
assert md.split('\n\n## 10',1)[1]==mdold.split('\n\n## 10',1)[1]
assert tex.split('媒体表达沿用概念、学习、世界三条线')[0]==texold.split('媒体表达沿用概念、学习、世界三条线')[0]
assert tex.split('\\section{10 ',1)[1]==texold.split('\\section{10 ',1)[1]
(D/'source_delta.json').write_text(json.dumps({'snapshot':now,'scope':'media prose only; research prefix/suffix byte-equivalent text verified','unchanged_research_content':True,'outputs':[{'path':str(p.relative_to(W)),'sha256':sha(p),'bytes':p.stat().st_size} for p in [W/'README.md',W/'docs/research_monograph.md',W/'paper/main.tex']],'evidence':[{'path':str(p.relative_to(W)),'sha256':sha(p)} for p in [W/'assets/video/explainer_360/narrated_qa.json',W/'assets/video/explainer_360/narrated_visual_review.json',W/'assets/audio/tts_ai/generation_summary.json']],'research_state':'NOT_RUN'},ensure_ascii=False,indent=2)+'\n')
print('D03 media prose updated; all research content preserved.')
