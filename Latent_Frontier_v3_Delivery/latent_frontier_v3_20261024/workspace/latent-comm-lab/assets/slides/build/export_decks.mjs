import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const skill='/home/agent/.codex/skills/builtins/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const mode=process.argv[2]||'all';
const revision=process.env.MEDIA_EXPORT_REVISION||new Date().toISOString().replaceAll(':','').replaceAll('.','');
function add(slide,e){
  const name=e.id+'_'+(e.text||e.kind).slice(0,35);
  const line={style:e.dash?'dashed':'solid',fill:e.stroke||'none',width:e.sw||0};
  if(e.kind==='text'){
    const sh=slide.shapes.add({name,geometry:'textbox',position:{left:e.x,top:e.y,width:e.w,height:e.h},fill:'none',line:{style:'solid',fill:'none',width:0}});
    sh.text=e.text;sh.text.style={fontSize:e.size,typeface:e.font,color:e.color,bold:e.bold,alignment:e.align,verticalAlignment:'top',wrap:'none',autoFit:'none',insets:0,lineSpacing:1.35};
  } else if(e.kind==='rect'||e.kind==='ellipse'){
    slide.shapes.add({name,geometry:e.kind==='rect'?'rect':'ellipse',position:{left:e.x,top:e.y,width:e.w,height:e.h},fill:e.fill,line,...(e.r?{borderRadius:e.r}:{})});
  } else if(e.kind==='polyline'){
    const xs=e.points.map(p=>p[0]),ys=e.points.map(p=>p[1]);const x=Math.min(...xs),y=Math.min(...ys),w=Math.max(...xs)-x,h=Math.max(...ys)-y;
    const commands=e.points.map((p,i)=>({[i?'lineTo':'moveTo']:{x:p[0]-x,y:p[1]-y}}));if(e.closed)commands.push({close:{}});
    slide.shapes.add({name,geometry:'custom',position:{left:x,top:y,width:Math.max(w,.01),height:Math.max(h,.01)},fill:e.fill||'none',line,customPaths:[{width:Math.max(w,.01),height:Math.max(h,.01),commands}]});
  }
}
for(const stem of (mode==='sample'?['research_36']:['research_36','brief_12'])){
  let scenes=JSON.parse(await fs.readFile(path.join(root,stem+'.source.json'),'utf8'));if(mode==='sample')scenes=scenes.slice(0,1);
  const deck=Presentation.create({slideSize:{width:1280,height:720}});
  for(const sc of scenes){const slide=deck.slides.add();slide.background.fill=sc.background;for(const e of sc.elements)add(slide,e);slide.speakerNotes.text=sc.notes;}
  const build=path.join(root,'build',stem+'_'+revision);await fs.mkdir(build,{recursive:true});
  const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);console.log('candidate',stem,scenes.length);
  const renderDir=path.join(root,'renders',stem);await fs.mkdir(renderDir,{recursive:true});
  for(let i=0;i<scenes.length;i++){
    const blob=await deck.export({slide:deck.slides.getItem(i),format:'png',scale:1});await fs.writeFile(path.join(renderDir,`${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
    console.log('render',stem,i+1);
  }
  if(mode==='sample')continue;
  const final=path.join(root,'exports_'+revision,stem+'.pptx');await fs.mkdir(path.dirname(final),{recursive:true});
  const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],explicitTotalSlideCount:scenes.length,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Noto Sans CJK SC','Noto Serif CJK SC']},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
  await fs.copyFile(final,path.join(root,stem+'.pptx')); console.log('finalized',stem,JSON.stringify(result));
}
