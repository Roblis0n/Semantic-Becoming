"""Editable mechanism artwork and slide scene sources. No research model execution.
All numerical examples below are finite analytical constructions from PLAN/media.
"""
from pathlib import Path
import json, math, re, hashlib, html
WORK = Path(__file__).resolve().parents[2]
PLAN = WORK.parents[1]
C = dict(bg='#F4F1E8', paper='#FFFCF5', ink='#262A25', muted='#606258', line='#CECDBF', orange='#9C5138', softorange='#F0DDD1', green='#536647', softgreen='#E4EAD9', blue='#496974', softblue='#E1E9EA', violet='#725D7C', softviolet='#E9E1EC', red='#9C4540')
FONT='Noto Sans CJK SC'; SERIF='Noto Serif CJK SC'
class Scene:
    def __init__(self,title='',description=''):
        self.title=title; self.description=description; self.elements=[]; self.bg=C['bg']; self.notes=''; self.sources=[]
    def add(self,kind,**kw):
        kw.update(kind=kind,id=kw.get('id',f'e{len(self.elements)+1:03}')); self.elements.append(kw); return kw
    def text(self,x,y,text,size=30,color=None,w=1100,align='left',bold=False,font=FONT):
        return self.add('text',x=x,y=y,w=w,h=(text.count('\n')+1)*size*1.43,text=text,size=size,color=color or C['ink'],align=align,bold=bold,font=font)
    def rect(self,x,y,w,h,fill=None,stroke=None,r=0,sw=2,dash=False):
        return self.add('rect',x=x,y=y,w=w,h=h,fill=fill or 'none',stroke=stroke or C['line'],sw=sw,r=r,dash=dash)
    def circle(self,x,y,r,fill=None,stroke=None,sw=2):
        return self.add('ellipse',x=x-r,y=y-r,w=r*2,h=r*2,fill=fill or 'none',stroke=stroke or C['ink'],sw=sw)
    def line(self,x1,y1,x2,y2,color=None,sw=3,arrow=False,dash=False):
        self.add('polyline',points=[[x1,y1],[x2,y2]],stroke=color or C['ink'],sw=sw,fill='none',dash=dash)
        if arrow:
            a=math.atan2(y2-y1,x2-x1); length=12; width=5
            self.add('polyline',points=[[x2-length*math.cos(a)+width*math.sin(a),y2-length*math.sin(a)-width*math.cos(a)],[x2,y2],[x2-length*math.cos(a)-width*math.sin(a),y2-length*math.sin(a)+width*math.cos(a)]],stroke=color or C['ink'],sw=sw,fill='none')
    def path(self,points,color=None,sw=3,fill='none',closed=False):
        return self.add('polyline',points=points,stroke=color or C['ink'],sw=sw,fill=fill,closed=closed)
    def node(self,x,y,w,h,title,sub='',color='green',size=30):
        self.rect(x,y,w,h,C['soft'+color],C[color],r=8)
        self.text(x+15,y+15,title,size,C[color],w-30,bold=True)
        if sub:self.text(x+15,y+23+size*1.25,sub,23,C['ink'],w-30)
    def footer(self,index='',analytical=False,detail=''):
        self.line(64,658,1216,658,C['line'],1)
        self.text(64,675,detail or ('解析示意 / 数学示意 · 无模型实测' if analytical else '前沿机制提案 / 无模型实测'),18,C['muted'],1000)
        self.text(1100,675,str(index),18,C['muted'],116,align='right')
    def header(self,title,claim='',index='',analytical=False):
        self.title=title
        size=44 if len(title)<26 else 40
        self.text(64,42,title,size,w=1152,font=SERIF)
        if claim:self.text(64,116,claim,33,C['muted'],1152)
        self.footer(index,analytical)
    def takeaway(self,text):self.text(64,607,text,26,C['orange'],1152)
    def asdict(self):return dict(title=self.title,description=self.description,width=1280,height=720,background=self.bg,elements=self.elements,notes=self.notes,sources=self.sources,research_state='NOT_RUN')
    def svg(self):return svg(self.asdict())

def svg(sc):
    esc=html.escape
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img" aria-labelledby="title desc"><title id="title">{esc(sc["title"])}</title><desc id="desc">{esc(sc.get("description", ""))}</desc><rect width="1280" height="720" fill="{sc["background"]}"/>']
    for e in sc['elements']:
        if e['kind']=='text':
            x=e['x']+(e['w']/2 if e['align']=='center' else e['w'] if e['align']=='right' else 0)
            anchor={'left':'start','center':'middle','right':'end'}[e['align']]
            lines=e['text'].split('\n')
            out.append(f'<text id="{e["id"]}" x="{x}" y="{e["y"]+e["size"]*.92}" font-family="{e["font"]}" font-size="{e["size"]}" font-weight="{700 if e["bold"] else 400}" fill="{e["color"]}" text-anchor="{anchor}">')
            for i,txt in enumerate(lines):out.append(f'<tspan x="{x}" dy="{e["size"]*1.35 if i else 0}">{esc(txt)}</tspan>')
            out.append('</text>')
        elif e['kind']=='rect':
            out.append(f'<rect id="{e["id"]}" x="{e["x"]}" y="{e["y"]}" width="{e["w"]}" height="{e["h"]}" rx="{e.get("r",0)}" fill="{e["fill"]}" stroke="{e["stroke"]}" stroke-width="{e["sw"]}" '+('stroke-dasharray="8 6"' if e.get('dash') else '')+'/>')
        elif e['kind']=='ellipse':out.append(f'<ellipse id="{e["id"]}" cx="{e["x"]+e["w"]/2}" cy="{e["y"]+e["h"]/2}" rx="{e["w"]/2}" ry="{e["h"]/2}" fill="{e["fill"]}" stroke="{e["stroke"]}" stroke-width="{e["sw"]}"/>')
        elif e['kind']=='polyline':
            pts=' '.join(f'{p[0]:.3f},{p[1]:.3f}' for p in e['points']); tag='polygon' if e.get('closed') else 'polyline'
            out.append(f'<{tag} id="{e["id"]}" points="{pts}" fill="{e.get("fill","none")}" stroke="{e["stroke"]}" stroke-width="{e["sw"]}" stroke-linejoin="round" stroke-linecap="round" '+('stroke-dasharray="8 6"' if e.get('dash') else '')+'/>')
    out.append('</svg>');return '\n'.join(out)

def save(scene,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.with_suffix('.json').write_text(json.dumps(scene.asdict(),ensure_ascii=False,indent=2))
    path.with_suffix('.svg').write_text(scene.svg())

def key(s,x,y,color='green',scale=1):
    s.circle(x,y,24*scale,None,C[color],5)
    s.line(x+24*scale,y,x+103*scale,y,C[color],6)
    s.line(x+80*scale,y,x+80*scale,y+20*scale,C[color],6)
    s.line(x+100*scale,y,x+100*scale,y+20*scale,C[color],6)

def objects(s,y=340):
    names=[('概念','新谓词','green'),('问题','解关系','orange'),('学习','更新规则','blue'),('世界','可执行动力学','violet')]
    for i,(t,sub,c) in enumerate(names):
        x=64+i*293;s.node(x,y,260,135,t,sub,c,36)
        if i<3:s.line(x+267,y+67,x+286,y+67,C['muted'],2,True)

def figure1():
    s=Scene(description='三层研究图谱。基础二十四机制产生可计算对象，新增二十四机制研究认知结构改写，十二远期方向通过二十条组合路线连接；不是二十个模型。')
    s.header('从潜通信到认知构造','三层研究对象，二十条组合路线', 'F01')
    rows=[(205,'01','基础 24 机制','H01–H24','状态 · 算子 · 响应 · 信念 · 约束 · 续接','green'),(340,'02','新增 24 机制','H25–H48','概念 · 问题 · 学习规则 · 指令集 · 世界','orange'),(475,'03','12 个远期终局','X01–X12','认知连续体 · 可塑性网络 · 语义编译生态','violet')]
    for y,n,t,ids,sub,c in rows:
        s.text(70,y+20,n,48,C[c],80,font=SERIF);s.text(175,y,t,35,C[c],400,bold=True);s.text(175,y+50,ids,24,C['muted'],300)
        s.text(565,y+17,sub,28,C['ink'],650)
        if n!='03':s.line(1190,y+75,1190,y+118,C[c],2,True)
    s.text(995,302,'objects',20,C['green'],170,align='right');s.text(995,437,'rewrites',20,C['orange'],170,align='right')
    s.takeaway('compositions：20 条组合路线连接机制，不代表 20 个独立模型')
    return s

def figure2():
    s=Scene(description='钥匙有效期例：旧类别有冲突，反例区分行为，定义授权有效期谓词，旧读者迁移。若无候选概念则保留未决分支。')
    s.header('概念诞生的四步','每一步都输出可计算对象', 'F02',True)
    for i,(t,sub,c) in enumerate([('局部冲突','同形钥匙，行为不同','orange'),('操作反例','K₁ 能开 / K₂ 不能','blue'),('新谓词','valid_at(key, t)','green'),('版本迁移','v1 读者转入 v2','violet')]):
        x=64+i*296;s.node(x,240,264,130,t,sub,c,31)
        if i<3:s.line(x+270,305,x+288,305,C['muted'],2,True)
    key(s,105,445,'orange',.8);key(s,245,445,'orange',.8)
    s.text(64,495,'形状相同 ≠ 授权相同',25,C['muted'],340)
    s.text(650,420,'shape_match ∧ authorized\n∧ (start ≤ t < expiry)',27,C['green'],540)
    s.line(490,375,490,455,C['orange'],2,True,True);s.text(365,475,'没有可用候选\n保留未决 / 多域',26,C['orange'],260)
    s.takeaway('新变量必须带定义程序；新名字本身不增加可区分性')
    return s

def figure3():
    s=Scene(description='源参数方向通过源雅可比映射到有限行为空间，目标最小二乘求可实现的参数方向，未实现部分保留为残差。两模型参数维数不要求相同。')
    s.header('行为方向运输','用共同可观察行为连接不同参数空间', 'F03',True)
    s.node(64,248,300,150,'源参数空间','Δθ_A ∈ Rᵖ','blue',32)
    s.node(490,248,300,150,'有限行为空间','v = J_A Δθ_A ∈ Rᵐ','orange',31)
    s.node(916,248,300,150,'目标参数空间','δ_B ∈ Rᑫ；p 可不同于 q','green',28)
    s.line(370,320,478,320,C['blue'],3,True);s.text(376,270,'源 JVP',22,C['blue'],110)
    s.line(802,320,904,320,C['green'],3,True);s.text(794,270,'最小二乘',22,C['green'],125)
    s.text(155,452,'δ* = argminδ ‖J_B δ − v‖² + λ‖δ‖²',34,C['ink'],1000)
    s.text(155,512,'r = v − J_B δ*：不可达或正则化残差仍然保留',28,C['orange'],1000)
    s.takeaway('行为坐标是否具有跨模型对应关系，仍是未证的研究假设')
    return s

def figure4():
    s=Scene(description='两个世界核共享外生变量和动作接口，产生带来源的合成观测与新问题。现实证据在独立命名空间，不接受合成观测作为独立现实证据回流。')
    s.header('世界核的共同梦境','共享噪声是语义的一部分', 'F04',True)
    s.node(64,250,260,150,'模块 A','x′ = f(x, a, u)\n单位与接口','blue',30)
    s.node(470,250,260,150,'模块 B','y′ = g(y, a, u)\n动作接口 a','green',30)
    s.circle(395,220,35,C['softorange'],C['orange']);s.text(363,197,'u',35,C['orange'],64,align='center')
    s.line(365,239,280,250,C['orange'],2,True);s.line(425,239,500,250,C['orange'],2,True)
    s.text(320,165,'同一个外生变量',23,C['orange'],230)
    s.line(194,400,194,430,C['violet'],2);s.line(194,430,800,430,C['violet'],2);s.line(800,430,800,330,C['violet'],2);s.line(735,330,850,330,C['violet'],3,True);s.node(860,250,356,150,'synthetic 世界','观测 O → 新问题 Q\n携带 kernel / seed 来源','violet',30)
    s.rect(64,466,666,98,None,C['muted'],dash=True);s.text(90,486,'现实证据：独立命名空间与来源',28,C['muted'],620)
    s.text(850,465,'无回流为独立现实证据',25,C['red'],366)
    s.line(1035,420,1035,450,C['red'],2);s.line(1018,450,1052,450,C['red'],4)
    s.takeaway('有限示意：x′ = u，y′ = u；共享公平比特使 P(x′ = y′) = 1')
    return s

def figure5():
    s=Scene(description='任务相对语义：奇偶查询将一三与二四分别归类。添加大于二查询并拥有原始信息后，细化为四个单元素类；粗表示不能无中生有恢复已丢信息。')
    s.header('多尺度任务语义','等价类由可问的问题决定', 'F05',True)
    s.text(64,210,'问题族 Q₁：是否为奇数？',31,C['green'],570)
    s.node(64,284,245,110,'{1, 3}','奇数','green',36);s.node(344,284,245,110,'{2, 4}','偶数','blue',36)
    s.text(710,210,'Q₂ = Q₁ ＋「是否大于 2？」',29,C['orange'],506)
    for i,(t,c) in enumerate([('{1}','green'),('{3}','orange'),('{2}','blue'),('{4}','violet')]):s.node(710+(i%2)*262,284+(i//2)*134,244,110,t,'保留原始值',c,34)
    s.line(610,328,688,328,C['orange'],3,True);s.text(604,278,'细化',22,C['orange'],100,align='center')
    s.line(688,503,610,503,C['muted'],3,True);s.text(604,530,'粗化',22,C['muted'],100,align='center')
    s.text(64,452,'细化所需：\n原始状态，或新的可用查询',30,C['muted'],530)
    s.takeaway('粗化会丢信息；仅有奇偶类别无法判断原值是否大于 2')
    return s

def figure6():
    s=Scene(description='执行权限平面：只读计划进入任务图，文件所有者约束工作区写入，账本保存哈希和回执，动作代理拦截模型运行、付费和发布。这是应用级边界，不是已验证硬沙箱。')
    s.header('执行与权限平面','自动推进保留明确边界与可核验状态', 'F06')
    s.node(64,230,270,120,'PLAN_ROOT','只读设计与政策','blue')
    s.node(475,230,310,120,'任务 DAG / owner','每文件只有一个写入者','green')
    s.node(925,230,290,120,'WORK_ROOT','授权范围内写入','orange')
    s.line(340,290,463,290,C['blue'],3,True)
    s.node(64,425,380,126,'ledger / receipt','输入摘要、产物哈希、真实检查','violet',29)
    s.node(564,425,652,126,'action broker','禁止：研究模型运行 / 新增付费 / 公开发布','orange',30)
    s.line(630,360,630,410,C['green'],2,True);s.line(1070,415,1070,362,C['orange'],2,True);s.line(565,488,456,488,C['violet'],2,True)
    s.takeaway('这是应用级权限控制，不声称已经建立或验证硬沙箱')
    return s

FIGURES=[figure1,figure2,figure3,figure4,figure5,figure6]

def slide_content():
    raw=next((PLAN/'media').glob('01_*')).read_text()
    parts=re.split(r'## 第(\d+)页 · ',raw)[1:]
    slides=[]
    for i in range(0,len(parts),2):
        n=int(parts[i]); block=parts[i+1];title=block.splitlines()[0]
        def field(name):return re.search(r'\*\*'+name+r'：\*\*\s*([^\n]+)',block).group(1)
        slides.append(dict(number=n,title=title,claim=field('主张'),visual=field('画面'),narration=field('讲稿')))
    assert len(slides)==36
    return slides

def flow(s,items,y=285,h=150,size=29):
    gap=32; w=(1152-gap*(len(items)-1))/len(items)
    for i,item in enumerate(items):
        t,sub,c=item;x=64+i*(w+gap);s.node(x,y,w,h,t,sub,c,size)
        if i<len(items)-1:s.line(x+w+6,y+h/2,x+w+gap-6,y+h/2,C['muted'],2,True)

def diagram(n,s):
    if n in (1,36):
        objects(s,330)
        s.text(64,230,'可操作的认知对象',42,C['orange'],1152,font=SERIF)
        s.takeaway('研究命题：交流能否扩展系统能够表达、提问和学习的对象集合？')
    elif n==2:
        for i,(t,c) in enumerate([('模型个体','green'),('概念词汇','orange'),('问题集合','blue'),('更新规则','violet')]):
            x=90+i*290;s.text(x,290,'可改写',25,C[c],230);s.text(x,340,t,37,C['ink'],230,font=SERIF)
        s.rect(64,230,1152,235,None,C['ink'],sw=2);s.text(90,497,'外层不变：用户目标、权限和运行预算',34,C['orange'],1100)
        s.takeaway('开放内部结构，不授予系统修改用户任务或账号权限的权力')
    elif n==3:
        for i,(t,sub,c) in enumerate([('状态','可续接的内部对象','green'),('算子','有序复合的作用','orange'),('响应','带局部有效域','blue'),('信念','保留不确定性','violet'),('约束','限制可行域','green'),('续接','移交未完成计算','blue')]):
            x=64+(i%3)*394;y=230+(i//3)*165;s.node(x,y,364,133,t,sub,c,34)
        s.takeaway('H01–H24 保留：消息到达后，接收方能继续操作')
    elif n==4:
        for x in range(120,590,70):s.line(x,235,x,520,C['line'],1)
        for y in range(240,530,70):s.line(120,y,610,y,C['line'],1)
        s.line(120,520,610,520,C['green'],3,True);s.line(120,520,120,225,C['green'],3,True)
        s.text(150,535,'原有表示空间',27,C['green'],460)
        s.line(640,375,740,375,C['orange'],3,True)
        s.text(800,255,'新增可计算区分',36,C['orange'],400,font=SERIF)
        s.text(800,330,'新变量\n新类型\n新操作',35,C['ink'],400)
        s.takeaway('结构变化须给出定义与迁移，不能只添一根装饰性坐标轴')
    elif n==5:
        for y,t,start,end,c in [(215,'基础对象',1,24,'green'),(340,'认知结构',25,48,'orange')]:
            s.text(64,y,t,31,C[c],210,bold=True)
            for i in range(24):s.text(280+(i%12)*78,y+(i//12)*43,f'H{start+i:02}',25,C['ink'],75)
        s.text(64,480,'远期架构',31,C['violet'],210,bold=True)
        for i in range(12):s.text(280+i*78,480,f'X{i+1:02}',25,C['violet'],75)
        s.takeaway('20 条组合路线连接机制；图谱表达研究覆盖，不是性能排名')
    elif n==6:
        key(s,150,300,'green',1.5);key(s,150,470,'orange',1.5)
        s.text(370,264,'K₁：形状匹配，授权有效',32,C['green'],800);s.text(370,430,'K₂：形状匹配，授权过期',32,C['orange'],800)
        s.text(370,320,'可以开门',30,C['green'],800);s.text(370,486,'不能开门',30,C['orange'],800)
        s.takeaway('下一步：定义“授权有效期”，使新概念改变可执行判断')
    elif n==7:
        for x,y,txt,c in [(250,245,'x − y = 0','green'),(820,245,'y − z = 0','blue'),(525,460,'z − x = 1','orange')]:s.text(x,y,txt,39,C[c],400)
        s.line(470,300,810,300,C['line'],2);s.line(290,325,530,440,C['line'],2);s.line(980,325,760,440,C['line'],2)
        s.text(525,340,'求和：0 = 1',38,C['red'],430)
        s.takeaway('冲突见证保留；最小二乘近似不会让不一致约束同时成立')
    elif n==8:
        flow(s,[('命题','明确域与前提','green'),('候选反例','输入与失败后果','orange'),('执行检查','有限对象见证','blue'),('修订','保留失败分支','violet')],280,150,30)
        s.text(90,495,'只有文字争论、没有可检查见证：未证',30,C['muted'],1100)
        s.takeaway('下一步：为反例写出输入、操作与原命题失效的位置')
    elif n==9:
        s.text(64,225,'valid_at(key, t)',42,C['green'],600)
        s.text(64,300,'AND\n  shape_match\n  authorized\n  start ≤ t < expiry',31,C['ink'],540)
        s.line(625,365,755,365,C['green'],3,True)
        s.node(790,252,426,125,'K₁：true','授权期内，允许开门','green',34)
        s.node(790,415,426,125,'K₂：false','授权过期，拒绝开门','orange',34)
        s.takeaway('新变量＋定义程序＋版本迁移，共同构成新概念的最小承诺')
    elif n==10:
        s.text(64,235,'重复结构',31,C['muted'],380)
        s.text(64,300,'检查授权\n检查时间范围\n执行动作',33,C['ink'],400)
        s.line(430,365,600,365,C['orange'],3,True)
        s.node(650,265,566,140,'宏：authorized_action','可扩展指令，带类型与前置条件','orange',33)
        s.line(935,420,935,490,C['orange'],3,True)
        s.text(650,510,'lower：还原到旧 ISA 的同一语义',29,C['green'],566)
        s.takeaway('宏可以压缩程序，不能隐藏无法解释的“万能函数”')
    elif n==11:
        flow(s,[('Conflict','局部约束冲突','orange'),('Witness','反例输入与轨迹','blue'),('Concept','谓词与新变量','green'),('Migration','v1 → v2 映射','violet')],260,150,30)
        s.line(491,415,491,486,C['orange'],2,True,True);s.text(360,507,'无候选：保留多域',29,C['orange'],520)
        s.takeaway('C10 的条件命题：通信能否生产可执行的中介语言？')
    elif n==12:
        flow(s,[('答案消息','当前问题的输出','green'),('行为方向','改变哪些可观察行为','blue'),('更新规则','怎样产生局部修改','orange')],275,190,36)
        s.takeaway('共同可观察行为是桥梁；参数空间无需相同')
    elif n==13:
        f=figure3();s.elements += [e for e in f.elements if (200 <= e.get('y',-1) < 600) or (e['kind']=='polyline' and min(p[1] for p in e['points'])>=200 and max(p[1] for p in e['points'])<600)]
        s.takeaway('J_A 与 J_B 的行为坐标对应，必须作为条件假设单独陈述')
    elif n==14:
        s.text(64,220,'无正则化：λ = 0',31,C['green'],550)
        s.text(64,295,'4 × 0.25 = 1',60,C['green'],550,font=SERIF)
        s.text(64,400,'目标行为变化 1\n目标参数改动 δ = 1/4',32,C['ink'],550)
        s.line(640,230,640,550,C['line'],2)
        s.text(700,220,'加入正则化：λ = 1',31,C['orange'],516)
        s.text(700,295,'δ = 4/17',60,C['orange'],516,font=SERIF)
        s.text(700,400,'实现变化 16/17\n残差 1/17 仍保留',32,C['ink'],516)
        s.takeaway('解析式 δ = 4 / (16 + λ)；手算正确不代表真实模型运输有效')
    elif n==15:
        flow(s,[('support','只供局部更新','green'),('规则 AST','受限读取与写入','orange'),('局部更新','仅授权参数域','blue'),('query','仅供外层目标','violet')],270,170,31)
        s.line(936,235,936,490,C['red'],2);s.text(850,515,'标签与数据边界隔离',29,C['red'],366)
        s.takeaway('query 不得泄漏到 support 更新；本轮不运行训练')
    elif n==16:
        flow(s,[('快照 v₀','概念 / ISA / adapter','blue'),('候选 v₁','同一事务边界','orange'),('提交 / 分叉','保留来源与回滚点','green')],260,170,34)
        s.line(1040,450,1040,525,C['muted'],2);s.line(1040,525,240,525,C['muted'],2,True)
        s.text(420,540,'失败时回滚到 v₀',28,C['muted'],500,align='center')
        s.takeaway('事务属于既有系统原语；此处研究它如何支撑认知结构演化')
    elif n==17:
        flow(s,[('共同有限行为锚','规定可比较的变化','blue'),('方向运输 H37','可实现部分与残差','orange'),('规则协议 H38','生成受限局部更新','green')],260,170,31)
        s.rect(64,485,1152,75,None,C['red'],dash=True);s.text(90,499,'研究入口锁定：模型初始化、前向、训练、评测均 NOT_RUN',28,C['red'],1100)
        s.takeaway('C13 的远期目标：交流形成能力的方法，而非直接叠加参数')
    elif n==18:
        flow(s,[('局部核 A','状态、动作与转移','blue'),('局部核 B','观测与依赖语义','green'),('可行动的新世界','synthetic，保留谱系','violet')],270,175,33)
        s.text(64,500,'消息的对象：一小块可执行动力学',35,C['orange'],1152)
        s.takeaway('合成世界能提出新问题，不能自行制造现实证据')
    elif n==19:
        flow(s,[('输入 x','共同单位与干预域','blue'),('模块 A','y = 2x','orange'),('模块 B','z = y + 1','green')],280,170,35)
        s.text(64,505,'接口契约：变量 / 单位 / 噪声 / 干预',31,C['muted'],1152)
        s.takeaway('维数一致不足以构成合法因果移植')
    elif n==20:
        s.text(64,210,'共享同一 u',33,C['green'],520)
        s.circle(310,290,32,C['softorange'],C['orange']);s.text(280,265,'u',32,C['orange'],60,align='center')
        s.line(285,317,180,390,C['green'],3,True);s.line(335,317,455,390,C['green'],3,True)
        s.text(95,415,'x′ = u',34,C['green'],220);s.text(395,415,'y′ = u',34,C['green'],220)
        s.text(64,500,'公平比特：P(x′ = y′) = 1',30,C['green'],550)
        s.line(640,230,640,555,C['line'],2)
        s.text(710,210,'错误拆成独立噪声',33,C['red'],506)
        s.text(710,310,'x′ = u₁       y′ = u₂',35,C['muted'],506)
        s.text(710,400,'P(x′ = y′) = 1/2',35,C['red'],506)
        s.text(710,500,'这是另一个联合世界',29,C['red'],506)
        s.takeaway('共享依赖属于可观察语义，不能仅作为附属 metadata')
    elif n==21:
        flow(s,[('synthetic 世界','可执行转移核','violet'),('可行动轨迹','生成来源可追溯','blue'),('新问题','在世界内探索','orange')],260,170,34)
        s.rect(64,485,1152,75,None,C['muted'],dash=True);s.text(90,500,'现实证据另行取证；合成观察不作为独立现实支持',29,C['red'],1100)
        s.takeaway('可生成经验空间，不等于可以宣告现实世界也如此')
    elif n==22:
        flow(s,[('world vₖ','动力学与任务域','violet'),('ontology vₖ','概念与关系','green'),('ISA vₖ','受限指令语义','orange'),('population vₖ','候选解法集合','blue')],250,170,27)
        s.line(1090,440,1090,510,C['muted'],2);s.line(1090,510,190,510,C['muted'],2,True)
        s.text(330,530,'每轮预算、停止条件、版本归档',30,C['muted'],740,align='center')
        s.takeaway('问题与语言一起演化；开放式研究不意味着无限运行')
    elif n==23:
        flow(s,[('世界核','保留依赖','violet'),('新问题','带答案关系','blue'),('语言变异','可执行定义','orange'),('有限检查','预算内见证','green'),('归档','版本与来源','violet')],270,160,28)
        s.text(64,495,'synthetic / real：命名空间和证据边界始终分离',30,C['red'],1152)
        s.takeaway('C16 研究能生产问题空间的生态，而非自动生成现实“事实”')
    elif n==24:
        s.text(64,205,'作用保持：T′ = G T G⁻¹',39,C['orange'],1152)
        for x,y,t in [(100,305,'z'),(820,305,'Tz'),(100,490,'Gz'),(820,490,'GTz')]:s.text(x,y,t,39,C['ink'],200,align='center')
        s.line(300,337,810,337,C['green'],3,True);s.text(500,286,'T',31,C['green'],100,align='center')
        s.line(300,522,810,522,C['orange'],3,True);s.text(440,462,'T′ = GTG⁻¹',31,C['orange'],260,align='center')
        s.line(190,365,190,475,C['blue'],3,True);s.text(105,405,'G',28,C['blue'],70)
        s.line(915,365,915,475,C['blue'],3,True);s.text(945,405,'G',28,C['blue'],70)
        s.takeaway('坐标可不同，作用关系须保持；真实模型上的对应仍是假设')
    elif n==25:
        f=figure5();s.elements+= [e for e in f.elements if e.get('y',0)>=200 and e.get('y',0)<600 and e['kind']!='polyline'];
        s.line(610,328,688,328,C['orange'],3,True);s.line(688,503,610,503,C['muted'],3,True)
        s.takeaway('细化需要原始信息或新查询；粗表示不能凭空恢复已丢差别')
    elif n==26:
        s.node(64,300,350,145,'问题：x² = 4','保留全部解的关系','blue',37)
        s.line(430,370,600,265,C['green'],3,True);s.line(430,380,600,490,C['orange'],3,True)
        s.text(650,220,'x = +2',48,C['green'],500);s.text(650,450,'x = −2',48,C['orange'],500)
        s.text(650,337,'只保留 +2 会丢解',30,C['red'],500)
        s.takeaway('每条变换明确：保持全部解、保持部分解，或仅作启发')
    elif n==27:
        for x,y,t,c in [(80,265,'x','green'),(850,265,'x + 1','green'),(80,475,'2x','orange'),(850,475,'2x + 2','orange')]:s.text(x,y,t,42,C[c],250,align='center')
        s.line(350,300,820,300,C['green'],3,True);s.text(540,245,'源操作 +1',29,C['green'],240,align='center')
        s.line(350,510,820,510,C['orange'],3,True);s.text(540,452,'目标操作 +2',29,C['orange'],240,align='center')
        s.line(205,338,205,455,C['blue'],3,True);s.text(65,375,'f(x) = 2x',24,C['blue'],170)
        s.line(965,338,965,455,C['blue'],3,True)
        s.takeaway('映射对象与操作，并检查复合关系；只像外观不足以构成可执行类比')
    elif n==28:
        cx,cy,r=340,375,122
        pts=[[cx+r*math.cos(t*math.pi/30),cy+r*math.sin(t*math.pi/30)] for t in range(61)]
        s.path(pts,C['green'],4);s.circle(cx+r,cy,9,C['green'],C['green']);s.text(135,535,'相位 / 顺序 / 事件读出',29,C['green'],460)
        pts=[[760+i*6.5,480-i*3+25*math.sin(i/8)] for i in range(61)];s.path(pts,C['blue'],4)
        s.circle(760,480,8,C['blue'],C['blue']);s.circle(1150,480-60*3+25*math.sin(60/8),8,C['orange'],C['orange'])
        s.text(730,535,'双端约束，不偷用未来信息',28,C['blue'],500)
        s.takeaway('有界非收敛轨迹可有意义；数值发散仍是失败，而非更深的智能')
    elif n==29:
        s.text(64,205,'V(z) = z⁴/4 − αz²/2',38,C['orange'],1152)
        for i,a in enumerate([-1,0,1]):
            x0=92+i*392;y0=480;s.line(x0,y0,x0+320,y0,C['line'],1);s.line(x0+160,300,x0+160,535,C['line'],1)
            pts=[]
            for k in range(61):
                z=-1.35+k*.045;v=z**4/4-a*z*z/2;pts.append([x0+(z+1.35)/2.7*320,y0-v*100])
            s.path(pts,C[['blue','orange','green'][i]],3);s.text(x0,540,f'α = {a}',29,C['ink'],320,align='center');s.text(x0+303,486,'z',22,C['muted'],30);s.text(x0+170,288,'V',22,C['muted'],30)
        s.takeaway('解析势能结构分岔，仅用于说明路线；不是神经智能相变的实测')
    elif n==30:
        flow(s,[('候选假设集','哪些仍然可行？','blue'),('合法查询','怎样划分候选？','green'),('条件排除','何假设下不可能？','orange')],270,170,33)
        s.text(64,500,'无合法查询 / 超时未找到：unknown',34,C['violet'],1152)
        s.takeaway('“尚未找到”不等于“不可能”；负知识必须带前提与见证')
    elif n==31:
        s.node(64,285,280,140,'来源事件 e','P(e) = 0.8','green',36)
        s.line(360,350,560,280,C['green'],3,True);s.line(360,365,560,470,C['green'],3,True)
        s.node(580,225,240,100,'转述 A','仅引用 e','blue',30);s.node(580,440,240,100,'转述 B','仅引用 e','orange',30)
        s.text(895,230,'e ∨ e = e',38,C['green'],321)
        s.text(895,312,'仍为 0.8',36,C['green'],321)
        s.text(895,430,'独立误算 0.96',30,C['red'],321);s.line(890,468,1200,468,C['red'],3)
        s.takeaway('0.96 仅适用于两个不同、独立、各为 0.8 的事件之并')
    elif n==32:
        titles=['认知连续体','局部集体知识','问题研究引擎','可塑性互联网','潜语言生态','跨尺度思想','轨迹即思想','未完成发现','共同梦境','能力公共品','概念出生与死亡','语义编译生态']
        for i,t in enumerate(titles):
            x=64+(i%3)*394;y=207+(i//3)*92;s.text(x,y,f'X{i+1:02}',22,C['orange'],65);s.text(x+74,y-3,t,29,C['ink'],305)
            s.line(x,y+62,x+360,y+62,C['line'],1)
        s.takeaway('12 个远期方向各有假设链与有限化入口，不是 12 个已证算法')
    elif n==33:
        flow(s,[('目标源码','48 机制 / 20 组合\n12 世界 / 13 学习阶段','green'),('Typed IR','未来研究计算图\n类型、依赖与权限','orange'),('任务 DAG','当前生产调度\n文件 owner 与回执','blue')],255,210,33)
        s.text(64,515,'研究计算图 ≠ 产物生产任务图',36,C['violet'],1152)
        s.takeaway('源码准备与静态检查不推出模型研究结果')
    elif n==34:
        f=figure6();s.elements += [e for e in f.elements if (200 <= e.get('y',-1) < 600) or (e['kind']=='polyline' and min(p[1] for p in e['points'])>=200 and max(p[1] for p in e['points'])<600)];
        s.takeaway('应用级权限防线，不声称已验证硬沙箱；未授权动作不执行')
    elif n==35:
        flow(s,[('研究设计','对象、条件、反例\n候选创新与来源','green'),('源码与工程准备','具体模块与静态检查\n可编辑媒体及真实导出','blue'),('研究模型未运行','初始化 / 推理 / 训练\n评测 / benchmark\n运行次数为 0','orange')],250,220,32)
        s.takeaway('实际文件、检查回执与外部阻塞分别记录，不用完成标签替代证据')
    else:raise ValueError(n)

def source_notes(n,d):
    hs={6:['H26','H27','H36'],7:['H26'],8:['H36'],9:['H27'],10:['H40'],11:['H26','H27','H36','H40'],12:['H37','H38'],13:['H37'],14:['H37'],15:['H38'],16:['H39'],17:['H37','H38','H39'],18:['H43','H44'],19:['H31'],20:['H43'],21:['H44'],22:['H42'],23:['H42','H43','H44'],24:['H25'],25:['H35','H47'],26:['H29'],27:['H30'],28:['H33','H34'],29:['H28'],30:['H45','H46'],31:['H48']}.get(n,[])
    paths=[str(next((PLAN/'media').glob('01_*')).relative_to(PLAN))+'#第%02d页'%n]
    for h in hs: paths.extend(str(p.relative_to(PLAN)) for p in (PLAN/'hypotheses').glob(h+'_*'))
    related=(WORK/'docs/related_work.md').read_text()
    urls=[]
    for h in hs:
        m=re.search(r'### '+h+r' · .*?(?=\n### |\n## |\Z)',related,re.S)
        if m:urls += re.findall(r'\]\((https?://[^)]+)\)',m.group())
    return d['narration']+'\n\n原稿画面要求：'+d['visual']+'\n\n来源（PLAN_ROOT 相对路径）：\n'+'\n'.join(paths)+'\n\n已核验近邻来源（仅支持先行工作，不证明本项目效果）：\n'+'\n'.join(dict.fromkeys(urls))+'\n\n研究状态：NOT_RUN。此页是定义、条件命题或解析示意，无模型实测。'

def main():
    for i,fn in enumerate(FIGURES,1):
        s=fn();s.sources=['media/07_图形与动画规范.md','docs/related_work.md'];save(s,WORK/f'assets/figures/F{i:02}')
    rows=[]
    for d in slide_content():
        n=d['number'];s=Scene(d['title'],d['visual']);s.header(d['title'],d['claim'],f'{n:02} / 36',n in [7,9,13,14,19,20,24,25,26,27,28,29,31]);diagram(n,s);s.notes=source_notes(n,d);s.sources=['media/01_36页研究版逐页脚本.md',f'research_slide_{n:02}'];
        if n==1:
            s=Scene('Semantic Becoming','前沿机制提案 / 无模型实测。可改写认知的跨模型计算。');s.text(64,74,'Semantic\nBecoming',67,C['ink'],650,font=SERIF);s.text(64,285,'可改写认知的\n跨模型计算',50,C['ink'],700,font=SERIF);s.text(64,465,'前沿机制提案 / 无模型实测',31,C['orange'],700)
            for j,(t,sub,c) in enumerate([('概念','可计算区分','green'),('问题','答案关系','orange'),('学习','更新规则','blue'),('世界','可执行动力学','violet')]):s.node(835,85+j*132,380,112,t,sub,c,32)
            s.footer('01 / 36');s.notes=source_notes(n,d);s.sources=['media/01_36页研究版逐页脚本.md']
        rows.append(s.asdict());save(s,WORK/f'assets/slides/source/research_{n:02}')
    (WORK/'assets/slides/research_36.source.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    short=[1,4,5,6,10,12,17,18,23,28,33,36];brief=[]
    for i,n in enumerate(short,1):
        sc=json.loads(json.dumps(rows[n-1]));sc['source_research_slide']=n
        for e in sc['elements']:
            if e.get('text')==f'{n:02} / 36':e['text']=f'{i:02} / 12'
        # Brief edition preserves one central diagram, full explanation is in notes.
        sc['notes']='精简版第 %d 页，对应研究版第 %d 页。\n\n'%(i,n)+sc['notes'];brief.append(sc)
        p=WORK/f'assets/slides/source/brief_{i:02}';p.with_suffix('.svg').write_text(svg(sc));p.with_suffix('.json').write_text(json.dumps(sc,ensure_ascii=False,indent=2))
    (WORK/'assets/slides/brief_12.source.json').write_text(json.dumps(brief,ensure_ascii=False,indent=2))
    (WORK/'assets/figures/figure_captions.json').write_text(json.dumps([dict(id=f'F{i:02}',title=fn().title,alt=fn().description) for i,fn in enumerate(FIGURES,1)],ensure_ascii=False,indent=2))
    print('Created 6 text SVG figures and 36 + 12 editable scene sources.')
if __name__=='__main__':main()
