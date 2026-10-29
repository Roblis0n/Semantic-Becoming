"""Record current narrated export evidence without concealing mandatory unauditioned QA.
Version 2: explicit actual submission counters; preserved prior QA and immutable history.
Run only after BOTH narrated validation and actual still-frame review; commits are separate.
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
# Source cardinality is not provider submission cardinality: an explicitly authorized
# replacement for outcome-unknown 029 is an additional accepted submission.
generation=read('assets/audio/tts_ai/generation_summary.json')
assert generation['status']=='all_audio_downloaded', 'Incomplete generation summary'
assert generation['unique_source_jobs']==len(manifest['chunks'])==58
assert generation['unique_source_characters']==sum(c['characters'] for c in manifest['chunks'])==1754
jobs=generation['accepted_submission_count']; characters=generation['accepted_submission_characters']
assert type(jobs) is int and type(characters) is int
assert (jobs,characters) in [(58,1754),(59,1770)], 'Unexpected scope: investigate rather than normalize counters'
assert generation['credits_used_total']==0
unknown_prior=generation['outcome_unknown_prior_submissions']
assert type(unknown_prior) is int and unknown_prior in [0,1]
assert unknown_prior==0 or (jobs,characters)==(59,1770)
if jobs==59:
 assert unknown_prior==1, 'Approved replacement must retain original 029 remote uncertainty'
 auth_rel=generation['resynthesis_authorization_record']
 history_receipt_rel=generation['original_unknown_029_receipt']
 for relative in [auth_rel,history_receipt_rel]:
  assert isinstance(relative,str) and not Path(relative).is_absolute()
  assert (W/relative).resolve().is_relative_to(W), 'Only public durable project records accepted'
 auth=read(auth_rel);old029=read(history_receipt_rel)
 assert auth['cue_id']=='explainer_360_029' and auth['duplication_risk_consent'] is True
 assert auth['user_authorized'] is True and auth['source_message_id'], 'Explicit user evidence required'
 assert old029['id']=='explainer_360_029' and old029['characters']==16
 assert old029['status']!='downloaded', 'Do not silently rewrite original unknown outcome'
 assert old029['response']['credits_used']==0
# Validate every downstream artifact BEFORE any status/source mutations.
for stem in ['intro_90','explainer_360']:
 qa=read(f'assets/video/{stem}/narrated_qa.json')
 review=read(f'assets/video/{stem}/narrated_visual_review.json')
 a=read(f'assets/audio/tts_ai/{stem}.assembly.json')
 assert qa['video']['full_decode_passed'] and qa['video']['sha256']==file(qa['video']['path'])['sha256']==review['video_sha256']
 assert review['actual_visual_inspection'] and review['sample_count']==len(qa['samples'])
 assert len(a['cues'])==(14 if stem=='intro_90' else 44)
 assert a['actual_audio_duration_seconds']==(90 if stem=='intro_90' else 360)
 assert qa['research_state']==a['research_state']=='NOT_RUN'
 assert qa['audio_listened'] is False and a['audio_listened'] is False
 assert a['audio']['sha256']==file(a['audio']['path'])['sha256']
# Keep the exact preceding aggregate and independent-review evidence immutable.
prior_qa=read('reports/media_qa.json')
prior_qa_path=W/'reports/media_qa.json'
prior_digest=hashlib.sha256(prior_qa_path.read_bytes()).hexdigest()
history_rel=f'assets/audio/history/pre_complete_narration_{prior_digest[:16]}/media_qa.json'
history_path=W/history_rel
history_path.parent.mkdir(parents=True,exist_ok=True)
if history_path.exists():
 assert hashlib.sha256(history_path.read_bytes()).hexdigest()==prior_digest
else:
 with history_path.open('xb') as f:f.write(prior_qa_path.read_bytes())
prior_evidence=file(history_rel)
qas=[];assemblies=[];statuses=[]
for stem,task in [('intro_90','V04'),('explainer_360','V05')]:
 qa=read(f'assets/video/{stem}/narrated_qa.json');a=read(f'assets/audio/tts_ai/{stem}.assembly.json');review=read(f'assets/video/{stem}/narrated_visual_review.json')
 assert qa['video']['full_decode_passed'] and qa['video']['sha256']==file(qa['video']['path'])['sha256']==review['video_sha256'];assert review['actual_visual_inspection'] and review['sample_count']==len(qa['samples'])
 status={'task_id':task,'status':'complete_with_external_blockers','requested':True,'source_created':True,'export_created':True,'export_edition':'narrated_personal_noncommercial_unauditioned','narrated_export_created':True,'narrated_final_acceptance':False,'narration_wav_created':True,'opened_checked':True,'opened_scope':'Actual A/V container full decode and all cue-midpoint still frames; no auditory review','timing_verified':True,'timing_scope':'Exact synthesized PCM chunk/scene boundaries, container duration and nonoverlapping caption margins','audio_timing_verified':True,'audio_listened':False,'pronunciation_assessed':False,'word_level_alignment_verified':False,'blockers':[block],'research_state':'NOT_RUN','license':'PERSONAL AND NONCOMMERCIAL USE ONLY for generated speech and this speech-containing video','export':qa['video'],'evidence':[file(f'assets/video/{stem}/narrated_qa.json'),file(f'assets/audio/tts_ai/{stem}.assembly.json'),file(f'assets/video/{stem}/narrated_visual_review.json')],'silent_visual_history_preserved':f'assets/video/{stem}/{stem}_silent_draft.mp4'}
 dump(f'assets/video/{stem}/media_status.json',status);dump(f'run_state/checks/{task}_validation.json',status);qas.append(qa);assemblies.append(a);statuses.append(status)
 # Preserve source-budget documents, while removing obsolete claims that no audio exists.
 for suffix in ['.narration.json','.ssml']:
  src=W/f'assets/audio/{stem}{suffix}';hist=W/f'assets/audio/history/pre_narration_20261024/{stem}{suffix}'
  if not hist.exists():
   hist.parent.mkdir(parents=True,exist_ok=True)
   with hist.open('xb') as f:f.write(src.read_bytes())
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
audio_status={'task_id':'V06','status':'complete_with_external_blockers','requested':True,'source_created':True,'export_created':True,'opened_checked':True,'opened_scope':'All raw and final WAVs parsed; actual audio streams decoded and objectively measured, not listened','timing_verified':True,'timing_scope':'Measured exact PCM cue and scene boundaries','narration_wav_created':True,'audio_timed_subtitles_created':True,'final_acceptance_pending_audition':True,'audio_listened':False,'pronunciation_assessed':False,'word_level_alignment_verified':False,'actual_narration_editions':2,'actual_scene_wavs':17,'source_chunk_wavs':58,'unique_source_jobs':58,'unique_source_characters':1754,'accepted_submission_count':jobs,'characters_transmitted':characters,'outcome_unknown_prior_submissions':unknown_prior,'credits_used':0,'blockers':[block],'license':'PERSONAL AND NONCOMMERCIAL USE ONLY for generated speech and speech-containing derivatives','evidence':[file('assets/audio/tts_ai/generation_summary.json'),file('assets/audio/tts_ai/sanitization.json')]+[file(f'assets/audio/tts_ai/{s}.assembly.json') for s in ['intro_90','explainer_360']],'research_state':'NOT_RUN'}
dump('assets/audio/media_status.json',audio_status);dump('run_state/checks/V06_validation.json',audio_status)
(W/'assets/audio/README.md').write_text(f'''# 旁白源、实际音频与许可边界

intro_90.narration.wav 与 explainer_360.narration.wav 是实际生成并编排的 90 秒、360 秒单声道 PCM WAV。tts_ai/raw 保存 58 个原始语音片段，tts_ai/scenes 保存 17 个实际场景 WAV。完整 TXT、JSON、SSML、发音指南和原 draft_timing 字幕保留。新 audio_timed 字幕由实际 PCM 片段边界建立，不用字数比例估算；没有逐词 ASR 或强制对齐。

TTS.ai / MeloTTS / ZH，普通合成声，不模仿真人。{jobs} 次已受理提交共 {characters:,} 个字符，对应 58 段、1,754 个不重复源字符；额外提交（如有）仅为明确批准的缺失音频替代，不能抹掉原任务。仍有 {unknown_prior} 个历史提交远端结果未知；这是原提交状态，不表示最终音频缺失。实际响应 credits_used 均为 0。请求证明已经移除临时下载 URL 与能力标识，只保留公开输入、设置、状态、费用计数、许可与音频哈希。

许可：生成语音及含语音的视频仅可个人、非商业使用。https://tts.ai/terms/ 第 7(a) 节，2026-09-14 生效，2026-10-24 核对。没有购买商业许可。此限制不自动扩张到独立创作的源文件、PPT、SVG 或不含语音的无声视觉稿。

真实边界：环境不支持音频输入，实际试听、专有词发音和听感审查尚未完成。已测响度、削波、静音段，已完整解码；这些不等于试听。P17 的强制试听仍是明确验收阻塞。

每个语音片段的裁切、0.80–1.10 范围内的实际语速因子、停顿、PCM 帧数与字幕边界均保存在 tts_ai/*assembly.json。没有新增音乐或混响。不通过无限加速凑时长。

旧 build_narration_sources.py 重建原始文字/脚本预算；新的实际语音流程位于 tts_ai/。SSML 是可编辑制作源，并未提交给供应商。只有 produce_narration.py 会访问已经授权的匿名免费 TTS 端点，其余处理均在本地。

所有研究模型、训练、评测与 benchmark 保持 NOT_RUN。
''')
base=prior_qa
base.setdefault('prior_aggregate_evidence',[])
if prior_evidence not in base['prior_aggregate_evidence']:base['prior_aggregate_evidence'].append(prior_evidence)
base.update(schema_version='latent-frontier-media-qa.v2',status='complete_with_external_blockers',checked_at_utc=now,opened_checked=True,timing_verified=True,timing_scope='Silent and voiced container durations plus exact synthesized PCM cue boundaries; no word-level alignment or listening',production_statuses=base['production_statuses'][:3]+statuses+[audio_status])
base['opened_scope']='Actual A/V full decodes and all measured cue-midpoint still frames for both narrated editions; no auditory review'
base['editable_sources']['videos']='Both editions: preserved silent timeline.json/project.mlt and separate narrated timeline_audio.json/project_audio.mlt, source renderer and measured captions'
base['editable_sources']['subtitles']='Original draft timing preserved; both editions have exact PCM chunk-boundary audio_timed SRT/VTT/JSON, not word-level alignment'
base['new_narrated_exports']={'wav_editions':2,'scene_wavs':17,'source_chunk_wavs':58,'audio_timed_subtitle_cues':[14,44],'voiced_mp4':2,'seconds':[90,360],'license':'PERSONAL AND NONCOMMERCIAL USE ONLY','audition':'NOT_PERFORMED_REQUIRED'}
current_artifacts={a['path']:a for a in base['artifacts']}
for artifact in [file(f'assets/audio/{s}.narration.wav') for s in ['intro_90','explainer_360']]+[file(f'assets/video/{s}/{s}_narrated_personal.mp4') for s in ['intro_90','explainer_360']]:current_artifacts[artifact['path']]=artifact
base['artifacts']=list(current_artifacts.values())
base['narrated_container_checks']=qas;base['audio_generation_provenance']={'provider':'TTS.ai','model':'melotts','voice':'ZH','authentication':'none','unique_source_characters':1754,'unique_source_jobs':58,'characters':characters,'requests':jobs,'outcome_unknown_prior_submissions':unknown_prior,'credits_used':0,'official_api':'https://tts.ai/api/','terms':'https://tts.ai/terms/','terms_effective_date':'2026-09-14','license':'PERSONAL AND NONCOMMERCIAL USE ONLY','evidence':[file('assets/audio/tts_ai/manifest.json'),file('assets/audio/tts_ai/generation_summary.json'),file('assets/audio/tts_ai/sanitization.json')],'research_model_execution':False}
base['validation'].update(audio_listened=False,audio_loudness_measured=True,subtitles_audio_aligned=True,subtitle_alignment_scope='exact generated audio chunk boundaries, not word-level forced alignment',spoken_word_accuracy_checked=False,long_subtitles_audio_aligned=True,short_subtitles_pcm_timed=True,all_voiced_containers_full_decodes=True,narrated_frame_visual_reviews=[file(f'assets/video/{s}/narrated_visual_review.json') for s in ['intro_90','explainer_360']])
base['resolved_audio_blocker']='Scoped TTS continuation and any separately authorized duplicate-risk replacement are recorded in generation provenance; actual unique-source audio and narrated containers now exist. Prior permission denials and unknown-job history are preserved, not erased.'
base['blockers']=[{'code':'MANDATORY_AUDITION_UNAVAILABLE','affected_tasks':['V04','V05','V06','V07'],'missing_files':[],'pending_requirement':'Actual auditory review of every narration segment, including specialized words and formulas','reason':'The runtime does not support audio input. No listening or pronunciation assessment was performed.','already_completed':'Actual free TTS WAVs, precise chunk-boundary captions, 90/360-second narrated containers, measured loudness/clipping/silence, full A/V decoding, editable timelines and actual sampled-frame visual review.','next_action':'A capable listener must audition every scene, assess pronunciation and sound quality, repair only verified problems, then update acceptance receipts.','license_scope':'Generated speech and videos containing it are personal/noncommercial only; independently authored source/PPT/SVG are not automatically restricted.'}]
base['limitations']=[x for x in base['limitations'] if 'audio listening' not in x]+['Mandatory audio audition remains unperformed because audio input is unsupported; objective waveform/stream checks are not listening.','Audio-timed subtitles use exact generated chunk boundaries; word-level alignment and spoken-word accuracy have not been checked.']
base['claim_boundary']='All requested media files now exist, including actual narrated editions. Required auditory acceptance remains blocked and is not waived. TTS is authorized media production, not research-model evidence. Research_state remains NOT_RUN.'
base['preserved_historical_submission_uncertainty']={'count':unknown_prior,'does_not_imply_missing_current_audio':True,'source':'assets/audio/tts_ai/generation_summary.json'}
# Dependency references are refreshed separately after current V04–V06 commits.
base['dependency_receipts_verified']=[]
dump('reports/media_qa.json',base)
print('Narrated statuses and QA assembled; mandatory audition remains blocked.')
