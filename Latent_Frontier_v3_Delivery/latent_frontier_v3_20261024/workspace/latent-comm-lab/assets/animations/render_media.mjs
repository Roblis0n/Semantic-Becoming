/* Deterministic graphical rendering only. No model/API/research execution. */
import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createRequire} from 'node:module';import {spawn,spawnSync} from 'node:child_process';import {once} from 'node:events';
const dir=path.dirname(fileURLToPath(import.meta.url)),work=path.resolve(dir,'../..');
const require=createRequire(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'sharp','package.json'));const sharp=require('sharp');
await import('./animation_engine.js');const A=globalThis.FrontierAnimations;
const mode=process.argv[2]||'all';const FPS=12;
async function encode(out,duration,sceneAt){
 await fs.mkdir(path.dirname(out),{recursive:true});
 const ff=spawn('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','image2pipe','-vcodec','mjpeg','-framerate',String(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',out]);
 let err='';ff.stderr.on('data',x=>err+=x);const done=once(ff,'close');
 for(let i=0;i<Math.round(duration*FPS);i++){
   const s=sceneAt(i/FPS);const jpg=await sharp(Buffer.from(A.svg(s))).jpeg({quality:92}).toBuffer();if(!ff.stdin.write(jpg))await once(ff.stdin,'drain');
 }
 ff.stdin.end();const [exit]=await done;if(exit!==0)throw new Error('ffmpeg '+out+': '+err);console.log('ENCODED',out,duration);
}
async function png(out,sc){await fs.mkdir(path.dirname(out),{recursive:true});await sharp(Buffer.from(A.svg(sc))).png().toFile(out);}
if(mode==='all'||mode==='animations'){
 for(const [id,a]of Object.entries(A.data)){
  if(process.env.ANIMATION_REPAIR_ONLY && id!==process.env.ANIMATION_REPAIR_ONLY)continue;
  const p=path.join(dir,id);await encode(path.join(p,id+'.mp4'),a.duration,t=>A.frame(id,t));
  for(const step of a.steps)await png(path.join(p,'renders',String(step.t).padStart(2,'0')+'.png'),A.frame(id,Math.min(a.duration,step.t+1)));
  await fs.writeFile(path.join(p,'final.svg'),A.svg(A.frame(id,a.duration)));
 }
}
const slideScenes=JSON.parse(await fs.readFile(path.join(work,'assets/slides/research_36.source.json'),'utf8'));
const figureScenes={};for(let i=1;i<=6;i++){const id='F'+String(i).padStart(2,'0');figureScenes[id]=JSON.parse(await fs.readFile(path.join(work,'assets/figures',id+'.json'),'utf8'));}
function graphicScene(cut,t){
 if(cut.kind==='figure')return JSON.parse(JSON.stringify(figureScenes[cut.source]));
 if(cut.kind==='communication'){
  const progress=(t-cut.start)/(cut.end-cut.start),s={title:'从文字消息到认知对象',description:'按分镜将答案消息变为可操作对象，再显示概念、问题、学习和世界。理论示意，无模型实测。',background:'#F4F1E8',elements:[]};
  const txt=(x,y,text,size=32,w=1100,color='#262A25')=>s.elements.push({kind:'text',x,y,w,h:size*1.5,size,text,color,font:'Noto Sans CJK SC',align:'left',bold:false});
  const box=(x,y,w,h,fill,stroke)=>s.elements.push({kind:'rect',x,y,w,h,fill,stroke,sw:2,r:8});
  const arrow=(x1,y,x2)=>{s.elements.push({kind:'polyline',points:[[x1,y],[x2,y]],stroke:'#536647',sw:3,fill:'none'});s.elements.push({kind:'polyline',points:[[x2-12,y-5],[x2,y],[x2-12,y+5]],stroke:'#536647',sw:3,fill:'none'});};
  txt(64,42,'通信的旧边界与新的研究对象',44);txt(64,116,'文字消息可以进一步成为可操作对象',33,1152,'#606258');
  box(64,250,260,130,'#E1E9EA','#496974');txt(90,286,'发送方 A',34,225,'#496974');
  box(956,250,260,130,'#E4EAD9','#536647');txt(983,286,'接收方 B',34,225,'#536647');
  arrow(340,315,466);arrow(812,315,940);
  box(480,240,320,150,progress<.45?'#FFFCF5':'#F0DDD1','#9C5138');txt(506,262,progress<.45?'答案消息':'可操作的对象',34,280,'#9C5138');txt(506,320,progress<.45?'解释一段文字':'状态 / 算子 / 程序',25,280);
  if(progress>.72){for(const [i,name]of ['概念','问题','学习','世界'].entries()){txt(64+i*293,470,name,36,260,['#536647','#9C5138','#496974','#725D7C'][i]);}txt(64,533,'研究命题：交流能否改变可思考的对象？',30);}
  return s;
 }

 if(cut.kind==='animation'){const a=A.data[cut.source];return A.frame(cut.source,Math.min(a.duration,(t-cut.start)/(cut.end-cut.start)*a.duration));}
 const s=JSON.parse(JSON.stringify(slideScenes[cut.source-1]));
 // Sequential reveal follows the source geometry; no synthetic performance signal.
 const elapsed=(t-cut.start)/(cut.end-cut.start);s.elements=s.elements.filter(e=>e.kind!=='polyline'||elapsed>=.15);
 return s;
}
function forVideo(scene,cue,title){
 const s=JSON.parse(JSON.stringify(scene));s.elements=s.elements.filter(e=>e.id!=='phase_feedback'&&e.id!=='time_progress'&&(e.kind==='polyline'?Math.min(...e.points.map(p=>p[1]))<590:e.y<590));
 for(const e of s.elements){if(e.kind==='polyline')e.points=e.points.map(([x,y])=>[x,30+y*.87]);else{e.y=30+e.y*.87;e.h*=.87;if(e.kind==='text')e.size*=.93;}}
 const txt=(text,x,y,w,size,color)=>({kind:'text',x,y,w,h:size*2.9,size,text,color,font:'Noto Sans CJK SC',align:'left',bold:false});
 s.elements.push({kind:'rect',x:0,y:575,w:1280,h:145,fill:'#262A25',stroke:'none',sw:0,r:0});
 s.elements.push(txt(cue?.text||'',64,589,1152,29,'#FFFCF5'));
 s.elements.push(txt('无声视觉稿 / 字幕按脚本预算 · 数学示意 / 无模型实测',64,684,1152,16,'#E4EAD9'));
 s.elements.push(txt(title,64,5,1152,17,'#606258'));return s;
}
if(mode==='all'||mode==='videos'){
 for(const stem of ['intro_90','explainer_360']){
  const root=path.join(work,'assets/video',stem),timeline=JSON.parse(await fs.readFile(path.join(root,'timeline.json'),'utf8')),narr=JSON.parse(await fs.readFile(path.join(work,'assets/audio',stem+'.narration.json'),'utf8'));
  for(const scene of timeline.source_scenes){
   if(process.env.MEDIA_SCENES && !process.env.MEDIA_SCENES.split(',').includes(stem+':'+scene.scene_id))continue;
   if(process.env.MEDIA_REPAIR_ONLY && !(stem==='intro_90'&&['S01','S04','S06','S07'].includes(scene.scene_id)) && !(stem==='explainer_360'&&['S01','S04','S05','S07','S08'].includes(scene.scene_id)))continue;
   function frame(local){const t=scene.start+local,cut=scene.cuts.find(c=>t>=c.start&&t<c.end)||scene.cuts.at(-1),cue=narr.cues.find(c=>t>=c.start&&t<c.end);return forVideo(graphicScene(cut,t),cue,scene.scene_id+' · '+scene.title);}
   await encode(path.join(root,scene.clip),scene.duration,frame);await png(path.join(root,'renders',scene.scene_id+'.png'),frame(scene.duration*.45));
  }
  const list=timeline.source_scenes.map(s=>`file '${s.clip}'`).join('\n');await fs.writeFile(path.join(root,'concat.txt'),list);
  const r=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i','concat.txt','-c','copy','-movflags','+faststart',stem+'_silent_draft.mp4'],{cwd:root,encoding:'utf8'});if(r.status)throw new Error(r.stderr);
  console.log('FINAL VIDEO',stem,timeline.requested_duration);
 }
}
if(mode==='all'||mode==='figures')for(let i=1;i<=6;i++){const id='F'+String(i).padStart(2,'0');const s=JSON.parse(await fs.readFile(path.join(work,'assets/figures',id+'.json'),'utf8'));await png(path.join(work,'assets/figures/renders',id+'.png'),s);}
