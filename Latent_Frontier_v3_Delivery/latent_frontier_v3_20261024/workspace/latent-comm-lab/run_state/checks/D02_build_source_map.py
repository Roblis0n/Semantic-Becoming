import ast,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parents[2];P=W.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hypotheses=json.loads((P/'specs/hypotheses.json').read_text());novel=json.loads((W/'specs/novelty_ledger.json').read_text());nov={m['id']:m for m in novel['mechanisms']}
notes={'F01':['H25','H32'],'F02':['H26'],'F03':['H27','H36'],'F04':['H29','H30'],'F05':['H37','H38'],'F06':['H28','H33','H34'],'F07':['H35','H47'],'F08':['H31','H43','H44','H48'],'F09':['H39','H40','H41','H42'],'F10':['H45','H46']}
files={k:next((W/'docs/formal_notes').glob(k+'*.md')).relative_to(W).as_posix() for k in notes}
mechanisms=[]
for h in hypotheses[24:]:
    mid=h['id'];base=W/h['target_base'];paths=list(sorted(base.glob('*.py')))+[base/'schema.json',W/f'tests/contracts/test_{mid.lower()}.py']
    records=[]
    for p in paths:
        r={'path':p.relative_to(W).as_posix(),'sha256':sha(p),'inspection_scope':'reference.py full read and mathematical comparison; remaining Python AST/symbol inventory unless detailed note states more; no neural path execution'}
        if p.suffix=='.py':
            tree=ast.parse(p.read_text());r['symbols']=[{'name':n.name,'line':n.lineno,'end_line':n.end_lineno,'kind':type(n).__name__} for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))]
        records.append(r)
    mechanisms.append({'mechanism_id':mid,'title':h['title'],'formal_notes':[files[k] for k,v in notes.items() if mid in v],'design_input':h['design_path'],'design_sha256':sha(P/h['design_path']),'source_files':records,'nearest_sources':nov[mid]['nearest_sources'],'shared_primitive':nov[mid]['shared_primitive'],'candidate_difference':nov[mid]['candidate_difference'],'unproven_bridge':nov[mid]['unproven_bridge'],'novelty_status':'proposal_not_priority_verified','research_state':'NOT_RUN'})
used=set(s for b in json.loads((W/'specs/future_branches.json').read_text())['branches'] for s in b['nearest_source_ids'])|{s['id'] for m in mechanisms for s in m['nearest_sources']}
sources=[s for s in novel['sources'] if s['id'] in used]
assert set(s['id'] for s in sources)==used
assert all(s['source_status']=='PRIMARY_CHECKED' and s['cite_allowed'] for s in sources)
inputs=[]
for folder,pattern in [('docs','*.md'),('formal','*.md'),('hypotheses','*.md'),('horizons','*.md')]:
    inputs += [p for p in sorted((P/folder).glob(pattern))]
inputs += [P/'START_HERE.md',P/'prompts/P00_一次性总控.md',P/'prompts/P20_形式推导.md',P/'prompts/P24_极限想法复审.md',P/'tasks/D02_形式推导与极限分叉.md']+[P/f'specs/{n}.json' for n in ['hypotheses','combinations','horizons','task_graph','execution_policy']]
extra=[W/p for p in ['docs/theory_architecture.md','specs/assumptions.json','docs/related_work.md','specs/novelty_ledger.json','paper/references.bib','run_state/receipts/D01.json','src/latent_comm/core/budgets.py','src/latent_comm/core/finite.py']]
value={'schema_version':1,'task_id':'D02','research_state':'NOT_RUN','source_evidence_policy':'D01 verified primary identities and visible abstracts/targeted content. D02 reuses the verified ledger, does not relabel metadata reads as full-paper reads, and derives its finite mathematics self-contained.','formal_note_map':notes,'mechanisms':mechanisms,'citations':sources,'input_snapshots':[{'root':'PLAN_ROOT','path':p.relative_to(P).as_posix(),'sha256':sha(p)} for p in inputs]+[{'root':'WORK_ROOT','path':p.relative_to(W).as_posix(),'sha256':sha(p)} for p in extra],'unrun_paths':['all model initialization, loading, inference, training, eval, benchmark and neural imports','all 38 future branch implementations']}
(W/'docs/formal_notes/source_map.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
# Keep D01 citations local to the reading guide with direct primary URLs.
lines=['# 形式推导阅读指南','','D02 覆盖 24 个新增机制与全部 F01–F08 输入，并补出组织机制、主动识别和负知识的推导。新经验结论 E 为零，研究状态 NOT_RUN。文中数学是明确条件下的定义/恒等式/有限定理，不把标准数学重新命名为本项目原创。','','## 阅读次序','']
for k,ids in notes.items():lines.append(f'- [{k}]({Path(files[k]).name})：'+', '.join(ids)+'。')
lines+=['','## 五层结论','','- D：域、定义、条件命题和本章展示的逐步证明。有限检查能抓实现反例，不替代一般证明。','- A：公共行为坐标、可实现读写接口、语法能力、因果边界、响应模型与证据依赖等显式前提。','- H：模型能否学习并利用这些对象改变跨模型计算。静态和有限数学检查不验证 H。','- V：docs/frontier_afterword.md 与 specs/future_branches.json 的 38 条未来分叉。有限入口存在不代表分叉已实现。','- E：本轮无新经验研究结果。不得从手算、矩阵检查、来源检索或软件契约产生模型分数。','','## 当前源码比理论更窄的地方','','H25 参考程序仅线性矩阵，非线性共轭是额外理论范围；H26 浮点残差不是上同调证书；H27 当前 unknown 比例不是历史语义漂移；H29 有限容差解集不是一般程序等价；H33 只实现二次耗散与线性 skew 耦合；H35 不强制 lift 为右逆；H39 只保证一个协调实例内的条件原子性；H42 表达候选不是 competence，inverse 标签不保证条件函数真逆；H43 需分别承担转移与观测独立条件；H46 的 required_predicate 必须由任务前提支持；H48 撤回失效不等于结论为假。','','这些限制不删除 H/V，而把下一步创造需要解决的对象明确化。分叉不以近期实验难度排序。','','## 可复核证据','','- assumption_dependencies.json：D/A/H/V 依赖与未证明桥梁；研究 E 列表为空。','- source_map.json：全部 H25–H48 当前真实文件 SHA-256、函数位置、设计输入、D01 来源身份和读取层级。','- run_state/checks/D02_math_fixtures.json：实际有限检查、预算、精确输入/输出和非研究范围。','- run_state/checks/D02_validation.json：覆盖、引用、快照、AST 和结构检查。','- run_state/receipts/D02.json：依赖内容摘要和本任务产物哈希。','','文档中的公式和未执行的未来算法可讨论一般有限维/连续域，但任何本轮运行例均预先限制维数≤64、步骤≤128、案例≤64，并用 aggregate_budget 约束嵌套调用。不导入神经库，不下载模型，不调用模型 API，不生成大规模数据。源码 AST 检查不等于后端集成试验。','','## 已核验近邻的身份索引','','以下保留 D01 真实核验范围。多数条目为元数据与摘要/目标章节读取，未声称全文证明复核；同名未检出不等于优先权。分叉新增的四值逻辑、透镜、并发迹等邻域仍需要专门文献调查。']
for s in sources:
    lines += ['',f"- [{s['citation_key']} {s['observed_title']}]({s['canonical_url']})。身份核验 {s['checked_on']}；{s.get('supported_scope','近邻定位')} 范围：{s.get('snapshot_scope','D01 可见页面内容')}。"]
(W/'docs/formal_notes/00_reading_guide.md').write_text('\n'.join(lines)+'\n')
