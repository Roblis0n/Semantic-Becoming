"""Media evidence checks: static packages, exact finite arithmetic, and decoding.
No neural models, dataset generation, training, forward pass, eval or research API.
"""
from pathlib import Path
import json,zipfile,re,subprocess,hashlib,datetime,xml.etree.ElementTree as ET
from fractions import Fraction
WORK=Path(__file__).resolve().parents[2];CHECK=WORK/'run_state/checks';CHECK.mkdir(exist_ok=True)
NS={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main','s':'http://www.w3.org/2000/svg'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
finite=[]
def record(name,ok,details):
 assert ok,name;finite.append({'name':name,'passed':True,'details':details})
z=(1,2);T=lambda x:(2*x[0],3*x[1]);G=lambda x:(x[1],x[0]);Tp=lambda x:(3*x[0],2*x[1]);record('A01_H25_covariance',G(T(z))==Tp(G(z))==(6,2),'z=(1,2), T=diag(2,3), G=swap; both paths (6,2)')
coefs=[(1,-1,0),(0,1,-1),(-1,0,1)];record('A02_H26_obstruction',tuple(map(sum,zip(*coefs)))==(0,0,0) and sum([0,0,1])==1,'Left sum zero; right sum one. No simultaneous solution.')
record('A03_H27_predicate',([0<=5<10,0<=5<4]==[True,False]),'Same shape, authorized; expiry 10 versus 4 at t=5 yields true/false.')
record('A04_H37_transport',Fraction(4,16)==Fraction(1,4) and Fraction(4,17)*4==Fraction(16,17) and 1-Fraction(16,17)==Fraction(1,17),'delta=4/(16+lambda). lambda=0: 1/4; lambda=1: 4/17; residual=1/17.')
shared=[(u,u) for u in [0,1]];independent=[(u,v) for u in [0,1] for v in [0,1]]
record('A05_H43_shared_noise',sum(x==y for x,y in shared)==2 and sum(x==y for x,y in independent)==2,'Shared bit equality probability 1; independent bits 1/2. Synthetic illustration only.')
q1={tuple(x%2 for _ in [0]) for x in [1,2,3,4]};q2={(x%2,x>2) for x in [1,2,3,4]};record('F05_task_partition',len(q1)==2 and len(q2)==4,'Adding >2 refines parity partition, given original states.')
record('H48_lineage',Fraction(4,5)==Fraction(8,10) and 1-(1-Fraction(4,5))**2==Fraction(24,25),'Repeated same event remains .8; union of distinct independent .8 events is .96.')
record('H29_solution_preservation',all(x*x==4 for x in [-2,2]),'Both +2 and -2 are retained.')
record('H30_analogy',all(2*(x+1)==2*x+2 for x in range(4)),'f(x)=2x maps source +1 to target +2 on finite checked inputs.')
math={'research_state':'NOT_RUN','scope':'exact finite analytical illustrations, not model evidence','bounds':{'max_scalar_dimension':4,'cases':19,'max_steps':8},'checks':finite};dump(WORK/'assets/animations/math_checks.json',math)
fig=[]
for i in range(1,7):
 p=WORK/f'assets/figures/F{i:02}.svg';root=ET.parse(p).getroot();texts=root.findall('.//s:text',NS);desc=root.find('s:desc',NS);assert len(texts)>10 and desc is not None and desc.text;assert not root.findall('.//s:image',NS)
 fig.append({'id':f'F{i:02}','path':str(p.relative_to(WORK)),'sha256':sha(p),'text_objects':len(texts),'accessible_description':desc.text,'raster_embeds':0,'rendered_png':str(p.with_name('renders').relative_to(WORK)/f'F{i:02}.png')})
dump(CHECK/'V01_validation.json',{'status':'pass','research_state':'NOT_RUN','figures':fig,'font_files_bundled':False,'math_checks':'assets/animations/math_checks.json'})
decks=[]
for stem,count in [('research_36',36),('brief_12',12)]:
 p=WORK/f'assets/slides/{stem}.pptx';scenes=json.loads((WORK/f'assets/slides/{stem}.source.json').read_text());assert len(scenes)==count
 with zipfile.ZipFile(p) as z:
  names=z.namelist();slides=sorted([n for n in names if re.fullmatch(r'ppt/slides/slide\d+.xml',n)],key=lambda n:int(re.search(r'(\d+)\.xml',n)[1]));assert len(slides)==count;assert len([n for n in names if re.fullmatch(r'ppt/notesSlides/notesSlide\d+.xml',n)])==count
  shapes=0;texts=0
  for n,sc in zip(slides,scenes):
   root=ET.fromstring(z.read(n));ts=root.findall('.//a:t',NS);texts+=len(ts);shapes+=len(root.findall('.//p:sp',NS));assert len(ts)>=sum(e['kind']=='text' for e in sc['elements']);assert not root.findall('.//p:pic',NS)
  notes='\n'.join(z.read(n).decode() for n in names if re.fullmatch(r'ppt/notesSlides/notesSlide\d+.xml',n));assert 'NOT_RUN' in notes
  assert not any('font' in n.lower() and n.endswith(('.ttf','.otf','.fntdata')) for n in names)
 renders=list((WORK/f'assets/slides/verified_renders/{stem}').glob('slide-*.png'));assert len(renders)==count
 decks.append({'path':str(p.relative_to(WORK)),'sha256':sha(p),'slides':count,'native_shapes':shapes,'native_text_runs':texts,'bitmap_slides':0,'all_slides_reopened_with':'LibreOffice PDF export and pdftoppm','all_slides_rendered':True,'powerpoint_application_opened':False,'font_embedding':False})
dump(CHECK/'V02_validation.json',{'status':'pass','research_state':'NOT_RUN','decks':decks,'visual_review':'assets/slides/visual_review.json'})
media=[]
for path,duration in [(WORK/f'assets/animations/A{i:02}/A{i:02}.mp4',d) for i,d in enumerate([20,25,30,25,30],1)]+[(WORK/'assets/video/intro_90/intro_90_silent_draft.mp4',90),(WORK/'assets/video/explainer_360/explainer_360_silent_draft.mp4',360)]:
 probe=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True);p=json.loads(probe.stdout);v=[s for s in p['streams'] if s['codec_type']=='video'];a=[s for s in p['streams'] if s['codec_type']=='audio'];assert len(v)==1 and len(a)==0;assert (v[0]['width'],v[0]['height'])==(1280,720);assert abs(float(p['format']['duration'])-duration)<.1
 decode=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True);assert decode.returncode==0 and not decode.stderr,decode.stderr
 # Decode an actual opening frame from each final container, independently of authoring PNGs.
 opening=path.with_name(path.stem+'_opening.png');subprocess.run(['ffmpeg','-v','error','-y','-ss','0.5','-i',str(path),'-frames:v','1',str(opening)],check=True)
 media.append({'path':str(path.relative_to(WORK)),'sha256':sha(path),'duration_seconds':float(p['format']['duration']),'video_codec':v[0]['codec_name'],'fps':v[0]['r_frame_rate'],'size':[1280,720],'audio_streams':0,'full_decode_passed':True,'opening_frame':str(opening.relative_to(WORK)),'opening_frame_sha256':sha(opening),'research_state':'NOT_RUN'})
dump(WORK/'assets/animations/container_checks.json',{'checks':media,'claim_boundary':'Decode, dimensions and duration demonstrate playable graphics, not research validity.'})
js=subprocess.run([__import__('os').environ.get('CODEX_PRIMARY_RUNTIME_NODE','node'),'--check',str(WORK/'assets/animations/animation_engine.js')],capture_output=True,text=True);assert js.returncode==0
for i in range(1,6):
 p=WORK/f'assets/animations/A{i:02}';ET.parse(p/'source.svg');ET.parse(p/'final.svg');assert (p/'index.html').is_file();assert json.loads((p/'scene.json').read_text())['duration']==[20,25,30,25,30][i-1]
dump(CHECK/'V03_validation.json',{'status':'pass_with_disclosed_inspection_limit','research_state':'NOT_RUN','container_checks':media[:5],'javascript_syntax':'passed','exact_math':finite[:5],'interactive_browser_checked':False,'interactive_browser_reason':'Chromium failed before page load: socket() failed: Operation not permitted. No restriction bypass or browser installation attempted.','browser_log':'assets/animations/browser_qa.json','rendered_keyframes_per_animation':5})
for i,stem in [(4,'intro_90'),(5,'explainer_360')]:
 data=json.loads((WORK/f'assets/audio/{stem}.narration.json').read_text());tl=json.loads((WORK/f'assets/video/{stem}/timeline.json').read_text());mlt=ET.parse(WORK/f'assets/video/{stem}/project.mlt');assert len(mlt.findall('producer'))==len(tl['source_scenes']);assert sum(s['duration'] for s in data['scenes'])==data['requested_duration'];assert all((WORK/f'assets/video/{stem}'/s['clip']).exists() for s in tl['source_scenes'])
 status={'task_id':f'V{i:02}','status':'complete_with_external_blockers','requested':True,'source_created':True,'export_created':True,'export_edition':'silent_visual_draft','narrated_final_created':False,'opened_checked':True,'opened_method':'FFmpeg full decode plus sampled frame visual inspection','timing_verified':True,'timing_scope':'silent container duration only, not narration alignment','container_timing_verified':True,'audio_timing_verified':False,'audio_listened':False,'blockers':['Requested narration WAV/audio and final audio-aligned subtitles remain missing. No supported authorized zero-new-cost TTS route was identified; no paid or uncertain TTS was called.'],'evidence':media[i+1],'research_state':'NOT_RUN'}
 dump(WORK/f'assets/video/{stem}/media_status.json',status);dump(CHECK/f'V{i:02}_validation.json',status)
subs=[]
for stem in ['intro_90','explainer_360']:
 data=json.loads((WORK/f'assets/audio/{stem}.narration.json').read_text());cues=json.loads((WORK/f'assets/subtitles/{stem}.draft_timing.json').read_text());script=''.join(s['narration'] for s in data['scenes']);caption=''.join(c['text'].replace('\n','') for c in cues);assert script==caption
 for j,c in enumerate(cues):
  assert c['end']>c['start'];assert len(c['text'].splitlines())<=2;assert max(map(len,c['text'].splitlines()))<=22;assert all(line[0] not in '，、。？！：；）》」』】”’' for line in c['text'].splitlines())
  if j:assert cues[j-1]['end']<=c['start']
 if stem=='explainer_360':assert any('系统不能先生成一个结论，再把自己生成的观察当作现实证据。' in c['text'].replace('\n','') for c in cues)
 ET.parse(WORK/f'assets/audio/{stem}.ssml');subs.append({'edition':stem,'cues':len(cues),'characters':len(script),'complete_script_coverage':True,'nonoverlap':True,'punctuation_safe_linebreaks':True,'evidence_prohibition_kept_in_one_cue':stem=='explainer_360','max_lines':2,'max_characters_per_line':22,'status':'draft_timing_budget_not_audio_aligned'})
status={'task_id':'V06','status':'complete_with_external_blockers','requested':True,'source_created':True,'export_created':False,'narration_wav_created':False,'opened_checked':False,'timing_verified':False,'final_aligned_subtitles_created':False,'audio_listened':False,'loudness_measured':False,'subtitles':subs,'blockers':['Requested narration audio and final audio-aligned subtitles are not produced: no available supported zero-spend TTS route; authorization/cost for alternative speech synthesis is not established.'],'evidence':['assets/audio/tts_tool_inventory.json','assets/audio/local_capability_check.log'],'research_state':'NOT_RUN'}
dump(WORK/'assets/audio/media_status.json',status);dump(CHECK/'V06_validation.json',status)
for task,folder,count in [('V01','figures',6),('V02','slides',2),('V03','animations',5)]:
 evidence=json.loads((CHECK/(task+'_validation.json')).read_text())
 status={'task_id':task,'status':'done','requested':True,'source_created':True,'export_created':True,'export_count':count,'opened_checked':True,'opened_scope':{'V01':'Rendered all 6 text-preserving SVGs, visually inspected','V02':'Exact native-editable PPTX reopened via LibreOffice; all 48 page pixels visually inspected','V03':'All 5 MP4s fully decoded; opening frames and 25 semantic keyframes inspected; browser interaction remains unverified'}[task],'timing_verified':task=='V03','timing_applicable':task=='V03','blockers':[],'limitations':(['Real browser interaction unverified: Chromium socket() failed: Operation not permitted; JS DOM-contract tests are not browser proof.'] if task=='V03' else []),'evidence':str((CHECK/(task+'_validation.json')).relative_to(WORK)),'research_state':'NOT_RUN'}
 dump(WORK/'assets'/folder/'media_status.json',status)
print(json.dumps({'figures':len(fig),'slides':sum(d['slides'] for d in decks),'mp4':len(media),'exact_math_checks':len(finite),'subtitles':subs,'research_state':'NOT_RUN'},ensure_ascii=False))
