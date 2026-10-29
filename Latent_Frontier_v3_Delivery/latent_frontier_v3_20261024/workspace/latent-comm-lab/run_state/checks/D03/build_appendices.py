"""D03 documentation assembly only: static JSON/AST reads, no project research import."""
import ast, json, hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[3]
P=W.parent.parent
OUT=W/'docs/research_monograph.md'
base=OUT.read_text().split('\n## 10 条件依赖索引')[0]
def load(p):return json.loads(p.read_text())
hs=load(P/'specs/hypotheses.json');cs=load(P/'specs/combinations.json');xs=load(P/'specs/horizons.json')
nov=load(W/'specs/novelty_ledger.json');ns={x['id']:x for x in nov['mechanisms']}
ass=load(W/'docs/formal_notes/assumption_dependencies.json');smap=load(W/'docs/formal_notes/source_map.json');sm={x['mechanism_id']:x for x in smap['mechanisms']}
branches=load(W/'specs/future_branches.json')['branches']
inputs={}
def register(path):
 inputs[('WORK_ROOT/' if path.is_relative_to(W) else 'PLAN_ROOT/')+str(path.relative_to(W if path.is_relative_to(W) else P))]=hashlib.sha256(path.read_bytes()).hexdigest()
for p in [P/'START_HERE.md',P/'prompts/P00_一次性总控.md',P/'prompts/P15_论文与说明文档.md',P/'tasks/D03_研究总稿与README.md',P/'specs/execution_policy.json',P/'specs/hypotheses.json',P/'specs/combinations.json',P/'specs/horizons.json',W/'specs/novelty_ledger.json',W/'specs/future_branches.json',W/'paper/references.bib']:
 register(p)
for p in (W/'docs/formal_notes').glob('*'):register(p)
for p in (W/'src/latent_comm/learning').glob('*/README.md'):register(p)
for p in [W/'src/latent_comm/learning/joint/AUDIT_INCIDENT.md',W/'src/latent_comm/learning/joint/audit_incident.json',W/'docs/frontier_afterword.md']:register(p)

def val(n,env):
 if isinstance(n,ast.Name):return env.get(n.id,n.id)
 if isinstance(n,ast.Attribute):return ast.unparse(n)
 if isinstance(n,(ast.Tuple,ast.List)):return [val(x,env) for x in n.elts]
 try:return ast.literal_eval(n)
 except (ValueError,TypeError):return ast.unparse(n)
def losses(path):
 tree=ast.parse(path.read_text()); rows=[]
 comprehended=set()
 for node in ast.walk(tree):
  if isinstance(node,ast.GeneratorExp) and isinstance(node.elt,ast.Call) and isinstance(node.elt.func,ast.Name) and node.elt.func.id=='LossSpec':
   assert len(node.generators)==1
   gen=node.generators[0];names=[t.id for t in gen.target.elts]
   for item in ast.literal_eval(gen.iter):rows.append([val(a,dict(zip(names,item))) for a in node.elt.args])
   comprehended.add(node.elt)
 for node in ast.walk(tree):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='LossSpec' and node not in comprehended: rows.append([val(a,{}) for a in node.args])
 assert rows and all(len(r)==11 for r in rows),(path,rows)
 return rows

a=['\n## 10 条件依赖索引\n\n以下23项前提来自当前形式依赖图。条件声明不代表条件已经被真实模型满足；完整消费者与失败语义见 docs/formal_notes/assumption_dependencies.json。\n\n']
for x in ass['assumptions']:
 a.append(f"- {x['id']}：{x['statement']}\n")
a.append('''\n这些前提不能任意互相推出。公共行为坐标不推出可实现读写；转移独立不推出观测独立；宏展开正确不推出新原语可执行；保存完整 detail 的重建不推出无损压缩；同一事务实例的原子性不推出跨进程容错。D02 的72条 D/A/H/V 相关主张节点及依赖另存为机器可检查图，经验结果节点为空。\n
## 11 十三个学习阶段的实际责任

下列是训练源码组织，不是十三次训练。每个阶段均有独立配置、角色合同和受锁入口，研究状态均为 NOT_RUN。公共 optimizer 代码复用不意味着对象计算相同。模型 manifests 保持未绑定。\n''')
learning=[
('L01','views','角色编码与双通道','H01低秩操作生成与H16精确符号绑定分开。机制 writer/reader 学连续作用；symbol_predictor 只作辅助分类，不能覆盖精确来源、金额、单位和引用。'),
('L02','objects','操作 响应与信念','有序函数复合、局部响应适用半径、整序列混合是三种数据合同。响应越域触发刷新而非外推；信念 unknown 支保留质量，不被强制匹配到已知类。'),
('L03','frames','坐标与限制映射','GL校准、矩形跨图映射、硬锚三角拼合分别实现。矩形映射保留不可达读出残差，不声称规范等价；监督全局截面只进入loss。'),
('L04','concept_questions','概念与问题','连续阈值和读出训练与AST枚举分开；问题选择用停止优势的score-function。soundness/completeness标签是学习目标，真正准入仍由有限关系验证决定。'),
('L05','causal_analogy','类比与因果移植','graft 使用明确线性SCM及联合噪声；analogy 使用有类型软匹配和交换残差。硬化重新验证。图记录另需manifest，不假装是W05已有字段。'),
('L06','dynamics_scales','动力 轨迹 边界与尺度','四种变体分别绑定轨迹读出、公开边界解、粗化闭合与残差、分岔事件。结构安装不可微；精确端点赋值不能被写成可优化的虚假梯度。'),
('L07','transport','行为方向运输','运输与行为编码分别拥有参数，公开Jacobian是数据。有限JVP/VJP求解保留非收敛与不可达状态，实际更新效果和局部预测分别归一。'),
('L08','meta_rules','支持集规则与外层查询','只训练规则标量，内层theta为功能式临时状态。full保留Hessian路径，first_order停止支持梯度；固定二次模板不代表统计留出泛化。'),
('L09','isa_search','宏搜索与快速实现','基底展开给停止目标，四项多项式快实现有独立系数。定义与调用字节由离散搜索计费。typed_binding扩展须有单独数据，不从常量绑定伪造分类任务。'),
('L10','worlds','世界核 课程与梦境','联合噪声只求和一次；核概率行使用真实目标质量加权。生态和梦境另有数据schema，proposer由停止回报训练，合成来源不能自证现实。'),
('L11','uncertainty','识别 排除与商空间','无先验W12用minimax区分而不伪造Bayes收益。学习得分不授予硬排除；精确查询分区与软聚类分开，撤回前提恢复原候选。'),
('L12','evidence','联盟与证据','已知子集价值和可行成员策略分别归一。重复、独立、显式联合三种证据语义不同；source_linking只排序链接，不授权合并身份或乘概率。'),
('L13','joint','阶段联合与实际live子图','stagewise边界是序列化后重算；transport_meta_full/first_order确实写出H37到H38的活路径。相位权重、所有者别名、总unroll和恢复随机顺序明确。')]
for tid,d,name,prose in learning:
 p=W/f'configs/learning/{d}.json';register(p)
 a.append(f"\n### {tid} {name}\n\n{prose}\n\n实现：`src/latent_comm/learning/{d}`；配置：`configs/learning/{d}.json`；专用检查定义：`tests/research_locked/test_learning_{d}.py`。模型运行结果：NOT_RUN。\n")

a.append('''\n## 12 四十八机制的对象与实现索引

每个条目把当前算法、区分见证、来源近邻与尚未证明的桥梁放在同一处。英文对象名和不变量沿用代码/台账的精确标识，中文解释说明其研究意义。loss条目由专用 losses.py 的 LossSpec 静态读取，不导入模块、不构造tensor。括号内所有者、输入梯度、停止边、单位和零有效策略均为源码声明，未通过模型运行验证。\n''')
loss_records=[]
for h in hs:
 id=h['id'];n=ns[id];bp=W/h['target_base']
 for fn in ['README.md','types.py','reference.py','adapter.py','losses.py','schema.json']:
  register(bp/fn)
 for extra in ['serialization.py','migration.py']:
  if (bp/extra).exists():register(bp/extra)
 register(P/h['design_path']);register(P/h['recipe_path']);register(W/f'configs/mechanisms/{id}.json');register(W/f'tests/contracts/test_{id.lower()}.py')
 if h.get('integration_path'):register(P/h['integration_path'])
 a.append(f"\n### {id} {h['title']}\n\n对象为 {n['object_type']}，核心操作为 {n['operation']}；保持关系为 {n['invariant']}。{n['candidate_difference']}\n\n区分见证：{n['separating_case']} 该见证是机制规格，不等于模型已通过。未证明桥梁：{n['unproven_bridge']}\n")
 if id in sm:
  notes='、'.join(Path(p).name.split('_')[0] for p in sm[id]['formal_notes'])
  a.append(f"\n形式讨论对应 D02 {notes}，详见 `docs/formal_notes/00_reading_guide.md`。")
 a.append(f"\n\n实现根：`{h['target_base']}`，其中 types.py 定义对象，reference.py 给有限语义，adapter.py 为锁定神经接入源码，专用迁移模块与 schema.json 约束持久化与版本。专用合同：`tests/contracts/test_{id.lower()}.py`。原配方：`PLAN_ROOT/{h['recipe_path']}`；绑定配置：`configs/mechanisms/{id}.json`。研究结果：NOT_RUN。\n")
 rows=losses(bp/'losses.py')
 for r in rows:
  owners=', '.join(r[6]) or '无可训练所有者';grad=', '.join(r[7]) or '无路径输入';stops='; '.join('→'.join(v) for v in r[8]) or '无声明停止边';est=r[9].split('.')[-1]
  a.append(f"\n- 目标 {r[0]}：`{r[1]}`。分子 {r[2]}；分母 {r[3]}；mask {r[4]}。所有者 {owners}；需梯度输入 {grad}；停止边 {stops}；估计器 {est}；单位 {r[10]}；零有效策略 {r[5]}。\n")
  loss_records.append({'mechanism':id,'name':r[0],'formula':r[1],'numerator':r[2],'denominator':r[3],'valid_mask':r[4],'zero_valid_policy':r[5],'parameter_owners':r[6],'requires_grad_inputs':r[7],'stop_gradient_edges':r[8],'estimator':r[9],'units':r[10],'source':str((bp/'losses.py').relative_to(W))})
 refs=', '.join(dict.fromkeys(s['citation_key'] for s in n['nearest_sources'] if s.get('citation_key')))
 a.append(f"\n已有原语：{n['shared_primitive']} 近邻 [{refs}]。保留的激进延伸：{n['aggressive_extension']} 这些来源不提供本机制的优先权或效果认证。\n")

a.append('''\n## 13 二十条组合与六十八份配方的闭合映射

本节20条组合与上一节48个机制逐一绑定原配方，合计68份。每条组合的节点名称与输出类型直接来自当前 configs/compositions 的 compiled_ir；它们是有限/符号对象流和未来路径元数据，不是20次神经管线运行。所有组合的研究结果均为 NOT_RUN。\n''')
cnarr={
'C01':'先解析带类型依赖图再绑定图册，按操作顺序派发，最后由目标读出。临时计算体的边界由能力和义务决定，不能把任意后端自动拉入。',
'C02':'局部响应先检查有效半径与观测条件，再更新公共场；残差刷新产生新的信息需求。场驻点不保证各源都正确，越域响应不得被静默使用。',
'C03':'多假设按独立分支保存，条件更新与兼容合并分开。共享证据只消费一次，不把不同语境的候选向量直接平均。',
'C04':'切点保存程序计数器、未完成依赖与来源；目标端检查版本再续接，异步时钟仅调度成熟事件。摘要相同不等于精确续接。',
'C05':'关系提取、锚点匹配与图册绑定之后才执行模态动作。物理坐标、潜坐标、可见对象与遮挡不混成一个hidden size。',
'C06':'技能先解析与绑定，联合消息使用真正高阶超边，读出后可另有持久化训练计划。单体分数相加不是联合能力定义。',
'C07':'长期胶囊先通过作用域与版本校准，再查询残差、应用或撤回。查询超出预定族时需要来源，不从旧缓存编造答案。',
'C08':'类型语言编译后卫生展开宏，预算检查涵盖展开后的实际动作。宏不授予新权限，定义字节也计入通信成本。',
'C09':'frame、尺度和指令集分别绑定；操作运输后检查目标行为。异维粗化与可逆换基不同，闭合残差和丢失细节均需保留。',
'C10':'冲突定位后产生可执行反例，提出概念并准备迁移；无法证明全局一致时保留多域信念，不因有概念候选就强制提交。',
'C11':'问题IR先检查解关系，再形成任务商和类比程序；目标执行后必须把答案沿合法关系回译到原问题。目标端好答案不必是源端合法答案。',
'C12':'源方程经物理边界与单位转换后移植，联合核保共享噪声，输出是明确世界内的假想后果。不能把代码接枝成功写成现实因果识别。',
'C13':'公共锚绑定后取源学习效果，再投影到目标可达方向并编译更新规则；最终是锁定的未来trainer计划。live学习实现另由L13承担。',
'C14':'读取快照、形成分岔候选、改写结构并准备迁移后，核对所有读版本再提交或恢复。版本冲突不是改写外部目标的理由。',
'C15':'公开边界与局部动力学形成双向约束，续接和异步调度最后返回轨迹读出。未来答案不能成为终端输入，第一条路径不能冒充唯一解。',
'C16':'兼容核集合产生明确合成世界，生成新问题并变异/编译协议，最后归档谱系。世界ID不进入solver特征，档案新颖不等于实测能力。',
'C17':'候选族先应用有前提的排除，再对许可查询形成分区，获取局部有限响应并细化信念。没有合法区分查询时应保持未知。',
'C18':'先绑定证据DAG、规范重复来源，再形成联盟和显式价值表，最后分配内部信用。未知价值不是零，信用不是金钱。',
'C19':'冻结外部目标后改变内部视角、构造任务商和宏观演化；细化依赖信息可用性，最后在原目标域复核。',
'C20':'问题与概念进入语义IR，类型操作和宏展开之后才跨域/跨坐标运输，分别规划参数所有者与后端能力。未绑定的研究后端保持锁定。'}
for c in cs:
 id=c['id'];cfg=load(W/f'configs/compositions/{id}.json');nodes=cfg['compiled_ir']['nodes'];register(W/f'configs/compositions/{id}.json');register(W/f'src/latent_comm/compositions/{id.lower()}.py');register(P/c['recipe_path']);register(P/c['design_path']);register(W/f'tests/contracts/test_{id.lower()}.py')
 a.append(f"\n### {id} {c['title']}\n\n参与机制：{', '.join(c['mechanisms'])}。{cnarr[id]}\n\n实际节点与输出：\n")
 for node in nodes:
  out=', '.join(t['name'] for _,t in node['output_types']);a.append(f"\n- {node['node_id']} → {out}；读取 {','.join(node['read_set']) or '无'}，写入 {','.join(node['write_set']) or '无'}；声明 {node['differentiability']}。\n")
 a.append(f"\n配置：`configs/compositions/{id}.json`；算法：`src/latent_comm/compositions/{id.lower()}.py`；合同：`tests/contracts/test_{id.lower()}.py`；原配方：`PLAN_ROOT/{c['recipe_path']}`。有限解释器的元数据可微标签不意味着该参考执行已构建tensor图；训练实际边界以L13和各学习阶段为准。研究结果：NOT_RUN。\n")

a.append('''\n## 14 十二终局与三十八条保留分叉

终局现有代码是有限架构入口，不是开放世界终态。以下分叉为新的V对象，implementation_status均为future_proposal_not_implemented；现有入口锚定其讨论，但没有实现这些新增算法。分叉的完整步骤、条件和反例见 docs/frontier_afterword.md 与 specs/future_branches.json。本节保存每一分叉的对象差异，避免用总数代替研究内容。\n''')
for x in xs:
 id=x['id'];register(P/x['design_path']);register(W/x['target_path']);register(W/f'docs/horizons/{id}.md')
 a.append(f"\n### {id} {x['title']}\n\n有限范围：{x['finite_scope']} 依赖 {', '.join(x['mechanisms'])}。入口 `{x['target_path']}`；独立说明 `docs/horizons/{id}.md`。研究结果：NOT_RUN。\n")
 for b in [b for b in branches if b['parent_horizon']==id]:
  a.append(f"\n#### {b['id']} {b['title']}\n\n释放假设：{b['released_assumption']}。对象：{b['new_object']}\n\n区分见证：{b['separating_witness']} 未证明桥梁：{b['unproved_bridge']} 保持条件：{b['preserved_invariant']} 当前仅为V提案，研究结果：NOT_RUN。\n")

a.append('''\n## 15 文献身份与证据层级

以下为D01去重后允许引用的46项来源。作者、标题、链接与日期均沿用实际台账，不补写未经核验DOI。checked_on是身份/可见内容核验日期。出版年、出版年月或出版日期只取 first_publication_date 并保留其精度；arXiv首次提交只取 first_arxiv_submission，不能代替出版日期或最早公开时间。出版字段为空时明确标为未知；未列出arXiv日期只表示台账未建立该字段，不断言从未提交。后续修订另见台账 latest_revision，不与前两者合并。这里引用既有原语和比较对象，不声称已完整阅读全部论文、复现其代码或建立全球优先权。完整BibTeX在 paper/references.bib。\n''')
seen=set()
for s in nov['sources']:
 if not s.get('cite_allowed') or s['citation_key'] in seen:continue
 seen.add(s['citation_key'])
 publication=s.get('first_publication_date')
 label='出版年份' if publication and len(publication)==4 else '出版年月' if publication and len(publication)==7 else '出版日期'
 date=f"{label}：{publication or '未知'}"
 if s.get('first_arxiv_submission'):date+=f"；arXiv首次提交：{s['first_arxiv_submission']}"
 a.append(f"\n- [{s['citation_key']}] {s['authors']}。{s['observed_title']}。[主要来源]({s['canonical_url']})。{date}；核验：{s['checked_on']}，{s['source_status']}。支持范围：{s['supported_scope']}\n")
a.append('''\n## 16 结语与可复核交付

这里提出的强命题不是“更多模型讨论就更聪明”，而是让概念、问题、学习规律和世界成为有语义、有版本、有作用域的可交换对象。其成立需要逐项建立可实现读写、可识别行为、合理语言信息、正确联合依赖和可迁移义务。数学反例帮助选择条件或保留分支，不承担替代实验的功能。

48机制、20组合、68配方、13学习阶段与12终局的源级映射完整，不意味着研究验证完成。38条更激进分叉继续保留，既不以近期资源删除，也不因文字宏大而提前算成功。未来应按独立主张组织研究：先补明确对象与近邻审查，再在另行获准的模型条件下检验区别性预测。

本稿、README与LaTeX源由D03负责；文献库沿用D01，完整条件推导及分叉来自当前D02，学习合同来自L01–L13，组合索引来自当前编译配置。D03 的静态覆盖、来源哈希、依赖复验和排版检查保存在 run_state/checks/D03，任务回执在 run_state/receipts/D03.json。回执证明某一输入快照下交付物的内容与检查，不证明模型结果。后续源码改变时必须重新核对相关段落，不能把旧哈希对应的文稿继续称为当前。
''')
assert len(hs)==48 and len(cs)==20 and len(xs)==12 and len(branches)==38 and len(seen)==46
OUT.write_text(base+''.join(a))
(W/'run_state/checks/D03/source_snapshot.json').write_text(json.dumps({'research_state':'NOT_RUN','inspection':'static document/JSON/AST only; no imported mechanism or neural backend','inputs':inputs,'counts':{'mechanisms':len(hs),'compositions':len(cs),'recipes':len(hs)+len(cs),'horizons':len(xs),'branches':len(branches),'bibliography':len(seen),'loss_specs':len(loss_records)}},ensure_ascii=False,indent=2)+'\n')
(W/'run_state/checks/D03/loss_snapshot.json').write_text(json.dumps(loss_records,ensure_ascii=False,indent=2)+'\n')
print('written',OUT,OUT.stat().st_size,'loss_specs',len(loss_records),'source_files',len(inputs))
