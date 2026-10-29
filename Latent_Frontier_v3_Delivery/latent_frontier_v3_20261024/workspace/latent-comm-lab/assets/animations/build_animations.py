"""Five exact mechanism illustrations, driven by an editable time line."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'figures'))
from build_media_sources import Scene,C,WORK,svg,key
ROOT=WORK/'assets/animations'
ANIMS={}
def put(id,s,duration,steps,mechanisms,math_inputs):
    ANIMS[id]={'id':id,'duration':duration,'fps':12,'scene':s.asdict(),'steps':steps,'mechanisms':mechanisms,'math_inputs':math_inputs,'research_state':'NOT_RUN','export_audio':False,'semantic_contract':'Each state is an exact finite mathematical illustration, not a research model output.'}
def at(s,start):
    before=len(s.elements)
    class Mark:
        def __enter__(self):return s
        def __exit__(self,*a):
            for e in s.elements[before:]:e['reveal_at']=start
    return Mark()
def header(s,title,claim,id):
    s.header(title,claim,id,True)
    s.rect(64,600,1152,47,C['paper'],C['line'],r=0,sw=0)

s=Scene('A01 · 换基保持作用','两条路径得到同一个结果 (6,2)。T=diag(2,3)，G 交换坐标。')
header(s,'H25：换基保持作用','两套坐标，同一计算作用','A01')
s.text(70,200,'z = (1, 2)',37,C['blue'],370)
s.text(850,200,'Gz = (2, 1)',37,C['orange'],366)
s.line(455,240,810,240,C['orange'],3,True);s.text(570,190,'交换 G',26,C['orange'],220,align='center')
with at(s,4):
    s.line(250,270,250,365,C['green'],3,True);s.text(290,300,'T = diag(2,3)',26,C['green'],300);s.text(70,395,'Tz = (2, 6)',37,C['green'],450)
with at(s,8):
    s.line(455,435,810,435,C['orange'],3,True);s.text(565,380,'再交换 G',26,C['orange'],230,align='center');s.text(850,395,'GTz = (6, 2)',37,C['green'],366)
with at(s,12):
    s.line(1030,270,1030,365,C['orange'],3,True);s.text(800,300,'T′ = diag(3,2)',26,C['orange'],380)
with at(s,16):s.text(70,520,'T′Gz = GTz = (6, 2)',40,C['green'],1146)
put('A01',s,20,[dict(t=0,fact='给定 z、T 与交换矩阵 G',explanation='坐标变换不等于计算作用改变',next='沿左侧先施加 T'),dict(t=4,fact='Tz = (2, 6)',explanation='第一坐标乘 2，第二坐标乘 3',next='交换结果的坐标'),dict(t=8,fact='GTz = (6, 2)',explanation='左路先作用、后换基',next='检查另一条路径'),dict(t=12,fact='T′ = GTG⁻¹ = diag(3,2)',explanation='换基后也要改写算子',next='将 T′ 作用于 Gz'),dict(t=16,fact='两条路径都得到 (6, 2)',explanation='此例作用关系保持',next='真实模型对应仍待研究')],['H25'],{'z':[1,2],'T':[[2,0],[0,3]],'G':[[0,1],[1,0]],'result':[6,2]})

s=Scene('A02 · 不可全局拼合','三条局部约束求和得到矛盾，保留多域、新变量或语境细分的研究分支。')
header(s,'H26：局部关系可能无法全局拼合','不可满足的约束不会被平均消除','A02')
for t,x,y,label,c in [(0,90,240,'x − y = 0','green'),(5,820,240,'y − z = 0','blue'),(10,460,375,'z − x = 1','orange')]:
    with at(s,t):s.text(x,y,label,41,C[c],400)
with at(s,15):s.text(430,465,'求和：0 = 1',43,C['red'],650)
with at(s,20):
    for i,label in enumerate(['保留多个局部域','检验新增变量','细分适用语境']):s.text(64+i*394,550,label,28,C['muted'],364)
put('A02',s,25,[dict(t=0,fact='局部约束 x − y = 0',explanation='第一对变量相等',next='加入第二个局部域'),dict(t=5,fact='再要求 y − z = 0',explanation='前两条推出 x = z',next='检验第三条约束'),dict(t=10,fact='第三条要求 z − x = 1',explanation='它与前两条不能同时成立',next='构造冲突见证'),dict(t=15,fact='三式相加得到 0 = 1',explanation='这是不可全局拼合见证',next='保留修订分支'),dict(t=20,fact='多域 / 新变量 / 语境细分',explanation='它们是候选路线，不是已解决',next='分别明确条件与反例')],['H26'],{'constraints':['x-y=0','y-z=0','z-x=1'],'sum':'0=1'})

s=Scene('A03 · 概念出生','同形钥匙的有效期差异，通过谓词 AST 形成可计算的新区分，随后迁移旧版本读者。')
header(s,'H27：新概念必须改变计算','同形钥匙，授权有效期不同','A03')
key(s,130,260,'green',1.1);key(s,130,390,'orange',1.1)
s.text(320,235,'K₁：shape_match',28,C['green'],450);s.text(320,365,'K₂：shape_match',28,C['orange'],450)
with at(s,6):s.text(660,235,'能开门',33,C['green'],500);s.text(660,365,'不能开门',33,C['orange'],500)
with at(s,12):s.text(65,475,'valid_at = authorized ∧ (start ≤ t < expiry)',31,C['blue'],1150)
with at(s,18):s.text(925,235,'true',35,C['green'],280);s.text(925,365,'false',35,C['orange'],280)
with at(s,24):s.text(65,537,'v1：key 类型  →  v2：key + valid_at 谓词',29,C['violet'],1150)
put('A03',s,30,[dict(t=0,fact='旧类别只能判断形状',explanation='K₁ 与 K₂ 暂时不可区分',next='寻找行为不同的反例对'),dict(t=6,fact='同形钥匙出现不同行为',explanation='“钥匙”一词不足以解释差异',next='提出可计算的有效期条件'),dict(t=12,fact='新变量进入谓词 AST',explanation='authorized 与期限共同决定行为',next='分别计算两把钥匙'),dict(t=18,fact='K₁ = true；K₂ = false',explanation='此区分现在能影响动作',next='迁移旧版本程序'),dict(t=24,fact='读者从 v1 迁移到 v2',explanation='新概念包含定义和版本后果',next='无候选时保留未决分支')],['H27'],{'keys':[{'id':'K1','shape_match':True,'authorized':True,'start':0,'expiry':10,'t':5},{'id':'K2','shape_match':True,'authorized':True,'start':0,'expiry':4,'t':5}]})

s=Scene('A04 · 行为方向运输','标量目标雅可比为四，目标行为变化为一，最小二乘参数改动为四分之一。加单位正则后为四除十七。')
header(s,'H37：从行为变化求目标更新','J_B = 4，v = 1；仅为标量解析例','A04')
s.text(64,213,'目标行为',30,C['blue'],430);s.text(64,264,'v = 1',53,C['blue'],430)
s.text(500,213,'目标参数变化',30,C['orange'],430);s.text(500,264,'δ = 0',53,C['orange'],430)['dynamic']='delta'
s.text(950,213,'实现的行为',30,C['green'],266);s.text(950,264,'4δ = 0',43,C['green'],266)['dynamic']='achieved'
s.line(135,420,1100,420,C['line'],4)
s.add('polyline',points=[[135,420],[135,420]],stroke=C['green'],sw=7,fill='none',dynamic='behavior_bar')
s.text(120,455,'0',26,C['muted'],100);s.text(1080,455,'1',26,C['muted'],100)
with at(s,14):s.text(64,525,'λ = 1：δ = 4/17，4δ = 16/17，残差 = 1/17',32,C['orange'],1152)
put('A04',s,25,[dict(t=0,fact='源方向映为行为变化 v = 1',explanation='比较发生在行为空间',next='求目标端可实现参数方向'),dict(t=4,fact='无正则目标：min (4δ − 1)²',explanation='参数改动通过 J_B 影响行为',next='到达 δ = 1/4'),dict(t=9,fact='4 × 0.25 = 1',explanation='本标量例的残差为零',next='加入 λ = 1 的正则化'),dict(t=14,fact='最优 δ 变为 4/17',explanation='正则化收缩了参数变化',next='保留未实现的 1/17'),dict(t=20,fact='实现 16/17，残差 1/17',explanation='残差没有被隐藏',next='不把手算示例写成模型结果')],['H37'],{'J_B':4,'v':1,'lambda_values':[0,1],'solutions':['1/4','4/17'],'residuals':['0','1/17']})

s=Scene('A05 · 共享外生变量的世界','核 A 和核 B 使用同一个公平比特 u。有限合成观测附 kernel 来源，不作为独立现实证据。')
header(s,'H43 / H44：共同构造可行动的世界','两个核、一个共享外生变量','A05')
s.node(64,235,310,150,'核 A','x′ = u\n动作 a：读取','blue',34);s.node(905,235,310,150,'核 B','y′ = u\n单位：bit','green',34)
with at(s,6):s.text(400,220,'接口一致：a / bit',29,C['muted'],470,align='center')
with at(s,12):
    s.circle(640,320,47,C['softorange'],C['orange']);s.text(590,292,'u',43,C['orange'],100,align='center');s.line(590,320,390,320,C['orange'],3,True);s.line(690,320,890,320,C['orange'],3,True)
with at(s,18):s.text(64,450,'synthetic：u = 0 ⇒ (x′, y′) = (0, 0)',30,C['violet'],1152)['dynamic']='world_observation';s.text(64,505,'来源：shared_bit_kernel / deterministic_schedule',24,C['muted'],1152)
with at(s,24):s.text(64,550,'新问题：为什么两侧观测总是一致？',30,C['orange'],1152)
put('A05',s,30,[dict(t=0,fact='局部核暴露状态和动作接口',explanation='相同维数不是充分契约',next='核对单位与动作'),dict(t=6,fact='单位 bit，动作 a 已对齐',explanation='接口语义一致',next='保留同一个外生变量 u'),dict(t=12,fact='两核共同读取 u',explanation='不能换成两个独立采样值',next='展示两个有限状态'),dict(t=18,fact='synthetic：同一 u 产生相同输出',explanation='观测带 kernel 来源',next='由世界内经验提出问题'),dict(t=24,fact='新问题：一致性来自何种依赖？',explanation='合成知识仍在 synthetic 域',next='现实主张另行取证')],['H43','H44'],{'external_variable':'u','domain':[0,1],'A':'x_next=u','B':'y_next=u','states':[[0,0,0],[1,1,1]],'P_equal':1})

ENGINE=r'''
(function(){
const clone=x=>JSON.parse(JSON.stringify(x));
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function frame(id,t){
 const a=DATA[id],s=clone(a.scene);t=Math.max(0,Math.min(a.duration,t));
 s.elements=s.elements.filter(e=>(e.reveal_at||0)<=t);
 const step=a.steps.filter(x=>x.t<=t).at(-1);
 const label=step.fact+'。'+step.explanation+'。';
 s.elements.push({kind:'text',id:'phase_feedback',x:77,y:605,w:1125,h:36,text:label,size:23,color:'#606258',font:'Noto Sans CJK SC',align:'left',bold:false});
 // Timeline encodes elapsed media time, not research progress.
 s.elements.push({kind:'rect',id:'time_progress',x:64,y:653,w:1152*t/a.duration,h:3,fill:'#9C5138',stroke:'none',sw:0,r:0});
 if(id==='A04'){
  let d=t<4?0:t<9?.25*(t-4)/5:t<14?.25:4/17;
  s.elements.forEach(e=>{if(e.dynamic==='delta')e.text=t>=14?'δ = 4/17':t>=9?'δ = 1/4':'δ ≈ '+d.toFixed(3);if(e.dynamic==='achieved')e.text=t>=14?'4δ = 16/17':t>=9?'4δ = 1':'4δ ≈ '+(4*d).toFixed(3);if(e.dynamic==='behavior_bar')e.points=[[135,420],[135+965*4*d,420]];});
 }
 if(id==='A05')s.elements.forEach(e=>{if(e.dynamic==='world_observation'){const u=t<21?0:1;e.text=`synthetic：u = ${u} ⇒ (x′, y′) = (${u}, ${u})`;}});
 if(id==='A01'){
  let p=null;
  if(t>=4&&t<8)p=[250,270+(t-4)/4*95];
  else if(t>=8&&t<12)p=[455+(t-8)/4*355,435];
  else if(t>=12&&t<16)p=[1030,270+(t-12)/4*95];
  if(p)s.elements.push({kind:'ellipse',id:'current_object',x:p[0]-9,y:p[1]-9,w:18,h:18,fill:'#9C5138',stroke:'#F4F1E8',sw:2});
 }
 s.description=step.fact+'。'+step.explanation+'。下一步：'+step.next;return s;
}
function svg(s){
 const out=[`<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img" aria-labelledby="title desc"><title id="title">${escape(s.title)}</title><desc id="desc">${escape(s.description)}</desc><rect width="1280" height="720" fill="${s.background}"/>`];
 for(const e of s.elements){const id=escape(e.id||'');
  if(e.kind==='text'){const x=e.x+(e.align==='center'?e.w/2:e.align==='right'?e.w:0);const anchor={left:'start',center:'middle',right:'end'}[e.align||'left'];out.push(`<text id="${id}" x="${x}" y="${e.y+e.size*.92}" font-family="${e.font}" font-size="${e.size}" font-weight="${e.bold?700:400}" fill="${e.color}" text-anchor="${anchor}">`);e.text.split('\n').forEach((l,i)=>out.push(`<tspan x="${x}" dy="${i?e.size*1.35:0}">${escape(l)}</tspan>`));out.push('</text>');}
  else if(e.kind==='rect')out.push(`<rect id="${id}" x="${e.x}" y="${e.y}" width="${e.w}" height="${e.h}" rx="${e.r||0}" fill="${e.fill}" stroke="${e.stroke}" stroke-width="${e.sw}" ${e.dash?'stroke-dasharray="8 6"':''}/>`);
  else if(e.kind==='ellipse')out.push(`<ellipse id="${id}" cx="${e.x+e.w/2}" cy="${e.y+e.h/2}" rx="${e.w/2}" ry="${e.h/2}" fill="${e.fill}" stroke="${e.stroke}" stroke-width="${e.sw}"/>`);
  else if(e.kind==='polyline')out.push(`<${e.closed?'polygon':'polyline'} id="${id}" points="${e.points.map(p=>p.join(',')).join(' ')}" fill="${e.fill||'none'}" stroke="${e.stroke}" stroke-width="${e.sw}" stroke-linejoin="round" stroke-linecap="round" ${e.dash?'stroke-dasharray="8 6"':''}/>`);
 }out.push('</svg>');return out.join('\n');
}
globalThis.FrontierAnimations={data:DATA,frame,svg};
})();
'''
(ROOT/'animation_engine.js').write_text('const DATA = '+json.dumps(ANIMS,ensure_ascii=False)+';\n'+ENGINE)
for id,a in ANIMS.items():
 p=ROOT/id;p.mkdir(exist_ok=True)
 (p/'scene.json').write_text(json.dumps(a,ensure_ascii=False,indent=2))
 (p/'source.svg').write_text(svg(a['scene']))
 (p/'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'''+a['scene']['title']+'''</title><style>body{margin:0;background:#F4F1E8;color:#262A25;font:18px system-ui,sans-serif}main{max-width:1280px;margin:auto}svg{width:100%;height:auto;display:block}nav,p{margin:16px 5%;line-height:1.6}button,input{font:inherit;margin-right:14px}input{width:45%}:focus-visible{outline:3px solid #496974}details{margin:16px 5%}a{color:#496974}</style><main><div id="art"></div><nav aria-label="动画播放控制"><button id="play">播放</button><button id="restart">从头</button><input aria-label="动画时间" id="seek" type="range" min="0" step="0.05"><output id="time"></output></nav><p id="explanation" aria-live="polite"></p><details><summary>动画与研究边界</summary><p>所有数字为解析示意 / 数学示意，无模型实测。无旁白音频。减少动态偏好下默认呈现完整终态，仍可逐步拖动时间线。</p><p><a href="scene.json">可编辑时间线与语义合同</a> · <a href="source.svg">可编辑 SVG</a></p></details></main><script src="../animation_engine.js"></script><script>
const id='''+json.dumps(id)+''',A=FrontierAnimations,a=A.data[id],seek=document.querySelector('#seek'),out=document.querySelector('#time'),button=document.querySelector('#play');seek.max=a.duration;let t=matchMedia('(prefers-reduced-motion: reduce)').matches?a.duration:0,playing=false,last=0,lastStep=-1;
function draw(){document.querySelector('#art').innerHTML=A.svg(A.frame(id,t));seek.value=t;out.textContent=t.toFixed(1)+' / '+a.duration+' 秒';const ix=a.steps.findLastIndex(s=>s.t<=t);if(ix!==lastStep){const s=a.steps[ix];document.querySelector('#explanation').textContent='事实：'+s.fact+'。解释：'+s.explanation+'。下一步：'+s.next+'。';lastStep=ix;}}
function tick(now){if(playing){t=Math.min(a.duration,t+(now-last)/1000);draw();if(t>=a.duration){playing=false;button.textContent='重播';}}last=now;requestAnimationFrame(tick);}button.onclick=()=>{if(t>=a.duration)t=0;playing=!playing;button.textContent=playing?'暂停':'播放';};document.querySelector('#restart').onclick=()=>{playing=false;t=0;button.textContent='播放';draw();};seek.oninput=()=>{playing=false;button.textContent='播放';t=+seek.value;draw();};matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change',e=>{if(e.matches){playing=false;t=a.duration;button.textContent='播放';draw();}});draw();requestAnimationFrame(tick);
</script></html>''')
print('Created exact scene timelines and offline HTML/SVG sources for',list(ANIMS))
