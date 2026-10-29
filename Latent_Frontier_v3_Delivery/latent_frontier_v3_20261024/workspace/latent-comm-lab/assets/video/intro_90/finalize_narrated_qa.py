"""Record current narrated export evidence without concealing mandatory unauditioned QA.
Run after both narrated validation and actual still-frame review; commits are separate.
"""
from pathlib import Path
import json,hashlib,datetime,xml.etree.ElementTree as ET,shutil
W=Path(__file__).resolve().parents[3]
def read(p):return json.loads((W/p).read_text())
def dump(p,j):(W/p).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def file(p):
 q=W/p;return {'path':p,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'bytes':q.stat().st_size}
now=datetime.datetime.now(datetime.timezone.utc).isoformat();block='Mandatory actual audition, pronunciation and sound-quality assessment remain unperformed: this runtime does not support audio input. Waveform measurements, decoding and visual frames are not listening.'
san=read('assets/audio/tts_ai/sanitization.json');assert san['status']=='sanitized'
manifest=read('assets/audio/tts_ai/manifest.json');assert len(manifest['chunks'])==58 and sum(c['characters'] for c in manifest['chunks'])==1754
receipts=[read('assets/audio/tts_ai/receipts/'+c['id']+'.json') for c in manifest['chunks']];assert all(r['status']=='downloaded' and r['response']['credits_used']==0 for r in receipts)
for r in receipts:assert file('assets/audio/tts_ai/raw/'+r['id']+'.wav')['sha256']==r['audio']['sha256']
qas=[];assemblies=[];statuses=[]
for stem,task in [('intro_90','V04'),('explainer_360','V05')]:
 qa=read(f'assets/video/{stem}/narrated_qa.json');a=read(f'assets/audio/tts_ai/{stem}.assembly.json');review=read(f'assets/video/{stem}/narrated_visual_review.json')
 assert qa['video']['full_decode_passed'] and qa['video']['sha256']==file(qa['video']['path'])['sha256']==review['video_sha256'];assert review['actual_visual_inspection'] and review['sample_count']==len(qa['samples'])
 status={'task_id':task,'status':'complete_with_external_blockers','requested':True,'source_created':True,'export_created':True,'export_edition':'narrated_personal_noncommercial_unauditioned','narrated_export_created':True,'narrated_final_acceptance':False,'narration_wav_created':True,'opened_checked':True,'opened_scope':'Actual A/V container full decode and all cue-midpoint still frames; no auditory review','timing_verified':True,'timing_scope':'Exact synthesized PCM chunk/scene boundaries, container duration and nonoverlapping caption margins','audio_timing_verified':True,'audio_listened':False,'pronunciation_assessed':False,'word_level_alignment_verified':False,'blockers':[block],'research_state':'NOT_RUN','license':'PERSONAL AND NONCOMMERCIAL USE ONLY for generated speech and this speech-containing video','export':qa['video'],'evidence':[file(f'assets/video/{stem}/narrated_qa.json'),file(f'assets/audio/tts_ai/{stem}.assembly.json'),file(f'assets/video/{stem}/narrated_visual_review.json')],'silent_visual_history_preserved':f'assets/video/{stem}/{stem}_silent_draft.mp4'}
 dump(f'assets/video/{stem}/media_status.json',status);dump(f'run_state/checks/{task}_validation.json',status);qas.append(qa);assemblies.append(a);statuses.append(status)
 # Preserve source-budget documents, while removing obsolete claims that no audio exists.
 for suffix in ['.narration.json','.ssml']:
  src=W/f'assets/audio/{stem}{suffix}';hist=W/f'assets/audio/history/pre_narration_20261024/{stem}{suffix}'
  if not hist.exists():shutil.copyfile(src,hist)
 source=read(f'assets/audio/{stem}.narration.json');source.update(narration_audio_created=True,listened=False,timing_status='original_script_budget_preserved_separately_from_measured_audio',audio_timing_source=f'assets/audio/tts_ai/{stem}.assembly.json',generated_audio=f'assets/audio/{stem}.narration.wav')
 dump(f'assets/audio/{stem}.narration.json',source)
 ssml=W/f'assets/audio/{stem}.ssml';tree=ET.parse(ssml)
 for meta in tree.findall('meta'):meta.set('content','Original narration source. Actual generated audio and exact PCM cue timings are recorded separately; SSML itself was not submitted.')
 ssml.write_text(ET.tostring(tree.getroot(),encoding='unicode'))
 (W/f'assets/video/{stem}/README.md').write_text(f'''# {stem}：带合成旁白的个人非商业版本

{stem}_narrated_personal.mp4 是实际 H.264/AAC 容器，时长 {a['requested_duration']} 秒。普通话来自 TTS.ai 的免费 MeloTTS / ZH，无账号、无新增支出。语音及含该语音的视频仅可个人、非商业使用，依据 https://tts.ai/terms/ 第 7(a) 节；没有购买商业许可。

实际音频在 ../../audio/{stem}.narration.wav。timeline_audio.json 与 project_audio.mlt 保留真实音轨、可编辑视觉片段和字幕引用。字幕在 ../../subtitles/{stem}.audio_timed.srt / .vtt / .json，以每个合成语音片段的实际 PCM 帧数建立边界，不按字数猜时长，不使用 ASR，也不声称逐词强制对齐。

重要：运行环境不支持音频输入，尚未实际试听，未评估发音或听感。P17 的试听要求仍是未完成的验收项，不能把波形、响度、完整解码或画面检查当成试听。因此本版本明确标“合成旁白（未试听）”。

原来的 {stem}_silent_draft.mp4、timeline.json、project.mlt 和 draft_timing 字幕保持不变。独立编写的源文件、PPT、SVG 与不含此语音的无声视觉稿，不会自动受该 TTS 音频许可限制。

重建新配音版本：先完成 assets/audio/tts_ai/produce_narration.py，再运行 assemble_narration.py，随后 build_narrated_projects.py、render_narrated.mjs、validate_narrated.py。所有文件位于本项目；不下载研究模型。旧动画目录的脚本重建无声阶段，不是此配音阶段的最终验收入口。

MLT XML 已静态检查，未声称在图形剪辑器中打开。研究模型、训练、评测和 benchmark 始终 NOT_RUN。
''')
audio_status={'task_id':'V06','status':'complete_with_external_blockers','requested':True,'source_created':True,'export_created':True,'opened_checked':True,'opened_scope':'All raw and final WAVs parsed; actual audio streams decoded and objectively measured, not listened','timing_verified':True,'timing_scope':'Measured exact PCM cue and scene boundaries','narration_wav_created':True,'audio_timed_subtitles_created':True,'final_acceptance_pending_audition':True,'audio_listened':False,'pronunciation_assessed':False,'word_level_alignment_verified':False,'actual_narration_editions':2,'actual_scene_wavs':17,'source_chunk_wavs':58,'characters_transmitted':1754,'credits_used':0,'blockers':[block],'license':'PERSONAL AND NONCOMMERCIAL USE ONLY for generated speech and speech-containing derivatives','evidence':[file('assets/audio/tts_ai/generation_summary.json'),file('assets/audio/tts_ai/sanitization.json')]+[file(f'assets/audio/tts_ai/{s}.assembly.json') for s in ['intro_90','explainer_360']],'research_state':'NOT_RUN'}
dump('assets/audio/media_status.json',audio_status);dump('run_state/checks/V06_validation.json',audio_status)
(W/'assets/audio/README.md').write_text('''# 旁白源、实际音频与许可边界

intro_90.narration.wav 与 explainer_360.narration.wav 是实际生成并编排的 90 秒、360 秒单声道 PCM WAV。tts_ai/raw 保存 58 个原始语音片段，tts_ai/scenes 保存 17 个实际场景 WAV。完整 TXT、JSON、SSML、发音指南和原 draft_timing 字幕保留。新 audio_timed 字幕由实际 PCM 片段边界建立，不用字数比例估算；没有逐词 ASR 或强制对齐。

TTS.ai / MeloTTS / ZH，普通合成声，不模仿真人。58 次请求共 1,754 个原始公开/合成叙事字符，实际响应 credits_used 均为 0。请求证明已经移除临时下载 URL 与能力标识，只保留公开输入、设置、状态、费用计数、许可与音频哈希。

许可：生成语音及含语音的视频仅可个人、非商业使用。https://tts.ai/terms/ 第 7(a) 节，2026-09-14 生效，2026-10-24 核对。没有购买商业许可。此限制不自动扩张到独立创作的源文件、PPT、SVG 或不含语音的无声视觉稿。

真实边界：环境不支持音频输入，实际试听、专有词发音和听感审查尚未完成。已测响度、削波、静音段，已完整解码；这些不等于试听。P17 的强制试听仍是明确验收阻塞。

每个语音片段的裁切、0.80–1.10 范围内的实际语速因子、停顿、PCM 帧数与字幕边界均保存在 tts_ai/*assembly.json。没有新增音乐或混响。不通过无限加速凑时长。

旧 build_narration_sources.py 重建原始文字/脚本预算；新的实际语音流程位于 tts_ai/。SSML 是可编辑制作源，并未提交给供应商。只有 produce_narration.py 会访问已经授权的匿名免费 TTS 端点，其余处理均在本地。

所有研究模型、训练、评测与 benchmark 保持 NOT_RUN。
''')
base=read('assets/audio/history/pre_narration_20261024/media_qa.json');base.update(schema_version='latent-frontier-media-qa.v2',status='complete_with_external_blockers',checked_at_utc=now,opened_checked=True,timing_verified=True,timing_scope='Silent and voiced container durations plus exact synthesized PCM cue boundaries; no word-level alignment or listening',production_statuses=base['production_statuses'][:3]+statuses+[audio_status])
base['new_narrated_exports']={'wav_editions':2,'scene_wavs':17,'source_chunk_wavs':58,'audio_timed_subtitle_cues':[14,44],'voiced_mp4':2,'seconds':[90,360],'license':'PERSONAL AND NONCOMMERCIAL USE ONLY','audition':'NOT_PERFORMED_REQUIRED'}
base['artifacts'] += [file(f'assets/audio/{s}.narration.wav') for s in ['intro_90','explainer_360']]+[file(f'assets/video/{s}/{s}_narrated_personal.mp4') for s in ['intro_90','explainer_360']]
base['narrated_container_checks']=qas;base['audio_generation_provenance']={'provider':'TTS.ai','model':'melotts','voice':'ZH','authentication':'none','characters':1754,'requests':58,'credits_used':0,'official_api':'https://tts.ai/api/','terms':'https://tts.ai/terms/','terms_effective_date':'2026-09-14','license':'PERSONAL AND NONCOMMERCIAL USE ONLY','evidence':[file('assets/audio/tts_ai/manifest.json'),file('assets/audio/tts_ai/generation_summary.json'),file('assets/audio/tts_ai/sanitization.json')],'research_model_execution':False}
base['validation'].update(audio_listened=False,audio_loudness_measured=True,subtitles_audio_aligned=True,subtitle_alignment_scope='exact generated audio chunk boundaries, not word-level forced alignment',spoken_word_accuracy_checked=False,all_voiced_containers_full_decodes=True,narrated_frame_visual_reviews=[file(f'assets/video/{s}/narrated_visual_review.json') for s in ['intro_90','explainer_360']])
base['resolved_audio_blocker']='The prior absence of a supported TTS route was resolved by verified official anonymous free MeloTTS/ZH; actual audio and narrated containers now exist.'
base['blockers']=[{'code':'MANDATORY_AUDITION_UNAVAILABLE','affected_tasks':['V04','V05','V06','V07'],'missing_files':[],'pending_requirement':'Actual auditory review of every narration segment, including specialized words and formulas','reason':'The runtime does not support audio input. No listening or pronunciation assessment was performed.','already_completed':'Actual free TTS WAVs, precise chunk-boundary captions, 90/360-second narrated containers, measured loudness/clipping/silence, full A/V decoding, editable timelines and actual sampled-frame visual review.','next_action':'A capable listener must audition every scene, assess pronunciation and sound quality, repair only verified problems, then update acceptance receipts.','license_scope':'Generated speech and videos containing it are personal/noncommercial only; independently authored source/PPT/SVG are not automatically restricted.'}]
base['limitations']=[x for x in base['limitations'] if 'audio listening' not in x]+['Mandatory audio audition remains unperformed because audio input is unsupported; objective waveform/stream checks are not listening.','Audio-timed subtitles use exact generated chunk boundaries; word-level alignment and spoken-word accuracy have not been checked.']
base['claim_boundary']='All requested media files now exist, including actual narrated editions. Required auditory acceptance remains blocked and is not waived. TTS is authorized media production, not research-model evidence. Research_state remains NOT_RUN.'
# Dependency references are refreshed separately after current V04–V06 commits.
base['dependency_receipts_verified']=[]
dump('reports/media_qa.json',base)
print('Narrated statuses and QA assembled; mandatory audition remains blocked.')
