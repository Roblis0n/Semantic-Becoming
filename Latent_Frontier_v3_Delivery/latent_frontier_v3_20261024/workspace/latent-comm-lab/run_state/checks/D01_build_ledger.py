"""D01 reproducible document assembly. Standard library only; never executes models."""
from pathlib import Path
import csv, datetime, hashlib, json, re

WORK = Path(__file__).resolve().parents[2]
PLAN = WORK.parents[1]
CHECK = WORK / 'run_state/checks'
TODAY = '2026-10-24'

def read(path):
    return json.loads(path.read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

OBS = read(CHECK / 'D01_source_observations.json')['observations']
by_url = {}
for ob in OBS:
    if ob['url'] not in by_url or (ob.get('authors') and not by_url[ob['url']].get('authors')):
        by_url[ob['url']] = ob

aliases = {'R01':'S01','R02':'S04','R03':'S05','R04':'S03','R05':'S02','R10':'S10',
           'R15':'S22','R16':'S23','R17':'S24','R18':'S25'}

# Each statement below is a narrow paraphrase of inspected primary metadata/abstract or documentation.
support = {
'S01':'连续隐藏状态通信与学习压缩的已发表方案背景。',
'S02':'共享桥与分离接口用于模型替换后的接口复用。',
'S03':'将轨迹压缩为一次构造的 KV 续接记忆。',
'S04':'在连续潜空间中协作的 LatentMAS 框架。',
'S05':'直接交换和融合模型 KV 缓存。',
'S06':'局部规范变换下的等变网络构造原则。',
'S07':'图上向量空间、限制映射与层扩散。',
'S08':'以表示退化分析层扩散的过平滑现象。',
'S09':'通过程序抽象库增长组织程序合成。',
'S10':'通过根求解处理隐式平衡状态。',
'S11':'利用任务组成结构泛化单演示策略。',
'S12':'以因果抽象解释高层变量与神经行为的对应。',
'S13':'自然变换及组件层次的组合/因果抽象。',
'S14':'压缩输入同时保留与目标变量相关的信息。',
'S15':'功能规格、前后条件及验证与合成的关系。',
'S16':'把优化器设计转为学习问题。',
'S17':'研究联盟操作下的分配规则性质。',
'S18':'环境与求解者配对生成、演化和迁移。',
'S19':'自动环境设计及对抗性课程构造。',
'S20':'以信息准则进行分类和偏好主动学习。',
'S21':'使用来源代数表示逻辑结果的证据组合。',
'S22':'产品能力与权限的官方背景说明，不是研究机制来源。',
'S23':'参数 requires_grad、输入梯度与 no-grad 模式的区别。',
'S24':'不同 KV 缓存类及策略的官方接口说明。',
'S25':'张量存储格式与安全读取的官方文档背景。',
'inherited:R06':'扩散语言模型之间连续隐藏消息及传递时机的研究。',
'inherited:R07':'多智能体强化学习中端到端学习通信协议。',
'inherited:R08':'一个网络生成另一网络参数。',
'inherited:R09':'以共享全局工作空间协调多个神经模块。',
'inherited:R11':'解释性因果变量与分布式神经表示的对齐。',
'inherited:R12':'跨模型与模态表示趋同的假说和研究。',
'inherited:R13':'对表示趋同的规模校准及局部关系再分析。',
'inherited:R14':'区分关系结构与度量几何的趋同研究。',
}

extras = [
('N01','Consensus on Transaction Commit','https://arxiv.org/abs/cs/0408036','Jim Gray and Leslie Lamport',None,'事务提交的一致性、两阶段提交与故障假设。'),
('N02','Nonnegative Decomposition of Multivariate Information','https://arxiv.org/abs/1004.2515','Paul L. Williams and Randall D. Beer',None,'冗余与协同信息的分解结构；不等于本项目任务收益交互项。'),
('N03','Metrics for Finite Markov Decision Processes','https://arxiv.org/abs/1207.4114','Norman Ferns and Prakash Panangaden and Doina Precup','2004','基于 bisimulation 的有限 MDP 状态距离及聚合。'),
('N04','Capability Myths Demolished','https://papers.agoric.com/assets/pdf/papers/capability-myths-demolished.pdf','Mark S. Miller and Ka-Ping Yee and Jonathan Shapiro','2003','对象能力的授权与隔离模型。'),
('N05','Successive Refinement of Information','https://isl.stanford.edu/~cover/papers/paper94.pdf','William H. R. Equitz and Thomas M. Cover','1991-03','逐次细化的率失真条件与非普遍可细化性。'),
('N06','A Truth Maintenance System','https://dspace.mit.edu/entities/publication/5377b306-4ecc-4687-b1f5-78cbb4a0543a','Jon Doyle','1979-06-01','记录信念理由、依赖回溯及前提变化后的修订。'),
('N07','Natural Gradient Works Efficiently in Learning','https://doi.org/10.1162/089976698300017746','Shun-ichi Amari','1998-02-15','仅核验官方出版商检索摘要中的书目与参数几何主题；直接页面 403，未作为机制实质证据。'),
('N08','Distilling the Knowledge in a Neural Network','https://arxiv.org/abs/1503.02531','Geoffrey Hinton and Oriol Vinyals and Jeff Dean',None,'把复杂模型预测行为蒸馏进另一个模型。'),
('N09','World Models','https://arxiv.org/abs/1803.10122','David Ha and Jürgen Schmidhuber',None,'学习环境动态并在内部生成环境中组织策略学习。'),
('N10','Event-triggered real-time scheduling of stabilizing control tasks','https://www.ee.ucla.edu/~tabuada/Papers/EventTriggered.pdf','Paulo Tabuada','2007-09','根据状态事件而非固定时钟调度控制任务。'),
('N11','Structure-Mapping: A Theoretical Framework for Analogy','https://groups.psych.northwestern.edu/gentner/papers/Gentner83.2b.pdf','Dedre Gentner','1983-04','把域间关系结构而非外观属性作为类比对象。'),
('N12','Guarded commands, non-determinacy and formal derivation of programs','https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD472.html','Edsger W. Dijkstra','1975-08','用谓词变换与最弱前置条件描述程序规格。'),
('N13','Factor Graphs and the Sum-Product Algorithm','https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf','Frank R. Kschischang and Brendan J. Frey and Hans-Andrea Loeliger','2001-02','因子图上的双向消息可表达前后向等既有算法。'),
('N14','Introduction to Program Synthesis, Lecture 10: Introduction to Functional Synthesis','https://people.csail.mit.edu/asolar/SynthesisCourse2020/Lecture10.htm','Armando Solar-Lezama',None,'作者教学资料明确说明 CEGIS 的候选、反例与累积约束循环及其失效例。'),
]

def arxiv_meta(ob):
    text = '\n'.join(ob.get('metadata_lines', []))
    submitted = re.search(r'Submitted on (\d+ [A-Za-z]+ \d{4})', text)
    revised = re.search(r'last revised (\d+ [A-Za-z]+ \d{4})', text)
    version = re.search(r'this version, (v\d+)', text)
    iso = lambda m: datetime.datetime.strptime(m.group(1), '%d %b %Y').date().isoformat() if m else None
    return {'first_arxiv_submission':iso(submitted),'latest_revision':iso(revised),
            'current_version':version.group(1) if version else ('v1' if submitted else None)}

def source(record, inherited=False):
    sid = ('inherited:' if inherited else '') + record['id']
    canonical = aliases.get(record['id'], sid) if inherited else sid
    url = record['url']
    canonical_url = 'https://docs.pytorch.org/docs/2.14/notes/autograd.html' if sid == 'inherited:R16' else url
    ob = by_url[canonical_url]
    title = ob['title']
    if canonical == 'S15': title = 'Introduction to Program Synthesis, Lecture 17: Introduction to Verified Functional Synthesis'
    if canonical == 'S22': title = 'Introducing dots'
    status = 'PRIMARY_CHECKED_ALIAS' if canonical != sid else 'PRIMARY_CHECKED'
    date_meta = arxiv_meta(ob)
    pub = '2026-09-29' if canonical == 'S22' else None
    authors = ob.get('authors')
    if authors: authors = re.sub(r'\s*\([^)]*\)', '', authors).replace(', ', ' and ')
    if not authors:
        authors = {'S15':'Armando Solar-Lezama','S22':'{OpenAI}','S23':'{PyTorch contributors}',
                   'S24':'{Hugging Face contributors}','S25':'{Hugging Face contributors}'}.get(canonical)
    identity_note = 'Exact title and identity checked at supplied primary URL.'
    if record['title'].casefold() != title.casefold():
        identity_note = 'Supplied label differs from observed title; use observed_title for citations, preserve supplied_title as provenance.'
    if canonical == 'S15': identity_note += ' CEGIS-specific treatment is explicitly verified in N14, rather than inferring the lecture title from the plan.'
    if sid == 'inherited:R16': identity_note += ' Supplied stable URL only exposed redirect; destination 2.14 was separately inspected.'
    return {'id':sid,'canonical_id':canonical,'origin':'supplied_v2' if inherited else 'supplied_v3',
      'supplied_title':record['title'],'supplied_date':record.get('initial_or_document_date',record.get('date')),
      'supplied_checked_on_claim':record.get('checked_on'),'observed_title':title,'authors':authors,
      'url':url,'canonical_url':canonical_url,'source_status':status,'checked_on':TODAY,
      'check_basis':'New D01 primary URL open, not inherited checked_on metadata.',
      'first_publication_date':pub,**date_meta,'revision_date_known':bool(date_meta['latest_revision']),
      'date_scope':'arXiv submission is not necessarily earliest publication; null means unestablished, not no revision.',
      'snapshot_ids':[o['capture_id'] for o in OBS if o['url'] in {url,canonical_url}],
      'snapshot_scope':'Metadata observation index only, not a complete immutable article snapshot.',
      'identity_note':identity_note,'supported_scope':support.get(canonical,support.get(sid)),
      'unsupported_scope':'Does not establish the novelty, correctness, performance, or universal applicability of any H mechanism.',
      'citation_key':'SBV3_'+canonical.replace('inherited:',''),
      'cite_allowed':True,'priority_status':'not_a_priority_certificate'}

sources = [source(x) for x in read(PLAN/'specs/sources.json')]
sources += [source(x,True) for x in read(PLAN/'inherited_v2/specs/sources.json')]
for sid,title,url,authors,pub,scope in extras:
    ob = by_url[url]
    checked = sid != 'N07'
    sources.append({'id':sid,'canonical_id':sid,'origin':'newly_found_D01','supplied_title':None,
      'supplied_date':None,'supplied_checked_on_claim':None,'observed_title':title,'authors':authors,
      'url':url,'canonical_url':url,'source_status':'PRIMARY_CHECKED' if checked else 'PRIMARY_SEARCH_ONLY_DIRECT_FETCH_FAILED',
      'checked_on':TODAY,'check_basis':'Primary URL opened and metadata/content inspected.' if checked else 'Official publisher search result inspected; DOI fetch returned 403; no access bypass attempted.',
      'first_publication_date':pub,**arxiv_meta(ob),
      'revision_date_known':bool(arxiv_meta(ob)['latest_revision']),
      'date_scope':'Publication date at displayed precision; null revision date is unknown. First public appearance not asserted.',
      'snapshot_ids':[o['capture_id'] for o in OBS if o['url']==url],
      'snapshot_scope':'Metadata observation index only, not full-text archival preservation.',
      'identity_note':'Verified at primary author/publisher/archive source.' if checked else 'Optional lead only; excluded from references.bib and mechanism evidence.',
      'supported_scope':scope,'unsupported_scope':'No direct validation of any project proposal or global-priority claim.',
      'citation_key':'SBV3_'+sid,'cite_allowed':checked,'priority_status':'not_a_priority_certificate'})

source_by_id = {s['id']:s for s in sources}
source_by_id['N01']['date_scope'] += ' Author Microsoft result lists January 2004 report and 2006 journal publication; arXiv was August 2004. Direct Microsoft fetch timed out, so that report date is secondary metadata in this ledger, not the arXiv first date.'
source_by_id['N03']['date_scope'] += ' UAI2004 is explicitly reported on arXiv; the 2012 deposit is not the publication year.'
source_by_id['N05']['date_scope'] += ' Stanford repository also exposes a June 1989 Equitz technical report; do not claim the 1991 journal date is the first conception.'
source_by_id['N10']['date_scope'] += ' The inspected PDF is labelled DRAFT; September 2007 journal date is verified from the author publication list. PDF revision date unknown.'
source_by_id['N10']['additional_primary_url']='https://www.seas.ucla.edu/~tabuada/pub.html'
source_by_id['N04']['additional_primary_url']='https://papers.agoric.com/papers/capability-myths-demolished/full-text/'
source_by_id['N14']['date_scope'] += ' The URL contains course2020 and page copyright says 2018; neither is treated as an exact publication/revision date.'

registry = read(PLAN/'specs/hypotheses.json')
claims = {x['id']:x for x in read(PLAN/'specs/claims.json')}
deltas = {x['id']:x for x in read(WORK/'specs/innovation_deltas.json')['mechanisms']}
reviews = {x['id']:x for x in csv.DictReader((CHECK/'D01_mechanism_review.tsv').open(),delimiter='\t')}
mechanisms=[]
for h in registry:
    row=reviews[h['id']]; d=deltas[h['id']]
    nearest=row['nearest'].split(',')
    mechanisms.append({'id':h['id'],'title':h['title'],'english':h['english'],'design_path':h['design_path'],
      'design_sha256':sha(PLAN/h['design_path']),'object_type':d['object_type'],'operation':d['operation'],
      'invariant':d['invariant'],'supplied_claim':claims[h['id']]['claim'],
      'claim_class':'conditional_mechanism_proposal','supplied_source_refs':claims[h['id']]['source_refs'],
      'nearest_sources':[{'id':i,'status':source_by_id[i]['source_status'],'url':source_by_id[i]['canonical_url'],
                          'citation_key':source_by_id[i]['citation_key']} for i in nearest],
      'comparison_status':'provisional_scoped_comparison_not_exhaustive_priority_search',
      'shared_primitive':row['shared_primitive'],'candidate_difference':row['candidate_delta'],
      'distinct_object_or_invariant':d['object_type']+'; '+d['invariant'],
      'separating_case':row['separating_case'],'separating_case_status':'specified_not_executed_in_D01',
      'unproven_bridge':row['unproven_bridge'],'aggressive_extension':row['aggressive_extension'],
      'innovation_retained':True,'novelty_status':'proposal_not_priority_verified',
      'global_first_claim':False,'research_state':'NOT_RUN',
      'implementation_or_experiment_claim':'D01 verifies sources and claim scope only, not mechanism implementation or efficacy.',
      'next_research_review':'Before any empirical or priority statement, inspect complete nearest papers and test the stated distinguishing case under separate model authorization.'})

snapshot_index=[]
for ob in OBS:
    clean={k:v for k,v in ob.items() if k!='tool_locator'}
    clean['metadata_sha256']=hashlib.sha256(json.dumps(clean,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    snapshot_index.append(clean)

corrections=[
{'source':'S01','correction':'Interlat is the method name; primary title is Enabling Agents to Communicate Entirely in Latent Space. Current v5 is 2026-07-13, not first submission 2025-11-12.'},
{'source':'S03','correction':'Primary title includes for Multi-Agent Systems via Trajectory-to-State Compilation, rather than the shortened supplied through phrase.'},
{'source':'S15','correction':'Actual Lecture17 title is Introduction to Verified Functional Synthesis. CEGIS-specific support is additionally checked at N14 Lecture10.'},
{'source':'S18','correction':'Use full POET title; first arXiv 2019-01-07 and latest v3 2019-02-21, not undifferentiated 2019-01.'},
{'source':'S12,S19,inherited:R09,inherited:R11','correction':'Year/month-only supplied dates are refined using primary arXiv first-submission and latest-revision fields.'},
{'source':'inherited:R16','correction':'Stable docs URL was a redirect; 2.14 destination independently inspected. This does not install or pin the runtime package.'},
{'source':'H39','correction':'Original source list empty. Added N01 transaction commit and N06 dependency maintenance; classify as supporting integration, not invented transaction theory.'},
{'source':'H47','correction':'Added N03 bisimulation/state aggregation. Finite-query equivalence is not automatically recursive bisimulation.'},
{'source':'H30,H34,H36,H44','correction':'Added direct primary predecessors for structure mapping, bidirectional factor messages, CEGIS and learned dream/world environments.'},
]
ledger={'schema_version':1,'task_id':'D01','project':'Semantic Becoming v3','as_of_utc':TODAY,
 'research_state':'NOT_RUN','research_execution_count':0,'model_loading_or_initialization_count':0,
 'scope':'48 registered mechanisms; all supplied source records retained and independently status-labelled; added targeted primary neighbors.',
 'priority_claim_policy':'No global-first, SOTA or validated-capability claims. Checked identity and provisional differentiation do not certify novelty.',
 'evidence_levels':{'supplied':'Design packet assertions, including its checked_on fields, are provenance only.',
                    'primary_checked':'D01 primary metadata and visible abstract/targeted document content inspected.',
                    'primary_search_only':'Publisher search metadata was available but direct fetch failed; not cited as mechanism evidence.',
                    'project_hypothesis':'Object/invariant/counterexample is a proposal, not a result reported by the source.'},
 'search_limitations':['No exhaustive global patent, dissertation, non-English or citation-closure review.',
                       'Most arXiv comparisons are abstract/metadata-level; no claim that complete papers or source implementations were reproduced.',
                       'H28/H33 need further specialized bifurcation and non-equilibrium computing literature before a detailed priority claim.',
                       'Optional natural-gradient full-text verification remained unavailable; N07 is excluded from substantive evidence and bibliography.',
                       'No experimental superiority or practical semantic transfer has been tested.'],
 'sources':sources,'mechanisms':mechanisms,'source_corrections':corrections,
 'source_snapshot_index':snapshot_index,'snapshot_index_policy':'Metadata excerpts/hashes only. Hashes attest this observation record, not the full remote article bytes.',
 'requirements':{'D01-1':'Object/operation-driven primary lookup with nearest_sources for every mechanism.',
                 'D01-2':'Distinct first submission, latest revision, version and known publication date.',
                 'D01-3':'Observed versus supplied identity, scope and correction records.',
                 'P12':'Objects, invariants, counterexamples, retained aggressive extensions and metadata snapshot index.'},
 'check_files':['run_state/checks/D01_dependency_A01.json','run_state/checks/D01_inputs.json',
                'run_state/checks/D01_source_observations.json','run_state/checks/D01_validation.json'],
 'open_research_questions':'All 48 unproven_bridge entries remain open; no mechanism removed for lack of experiment.',
 'task_blockers':[]}
dump(WORK/'specs/novelty_ledger.json',ledger)

# Deduplicated bibliography uses observed canonical titles. Optional unverified N07 is not cited.
canon={s['canonical_id']:s for s in sources if s['canonical_id']==s['id'] and s['cite_allowed']}
bib=['% Semantic Becoming v3 D01. Research NOT_RUN. Metadata checked 2026-10-24.',
     '% arXiv deposit years are not assumed to be first publication. Revisions are noted separately.',
     '% Source status and exact provenance are in specs/novelty_ledger.json.']
def escape(s):
    return str(s).replace('\\','\\textbackslash{}').replace('&','\\&').replace('%','\\%').replace('_','\\_')
for sid,s in canon.items():
    url=s['canonical_url']; arxiv=url.split('/abs/',1)[1] if '/abs/' in url else None
    date=s.get('first_publication_date') or s.get('first_arxiv_submission')
    fields={'title':'{'+escape(s['observed_title'])+'}','author':s['authors'], 'url':url,'urldate':TODAY}
    if date: fields['year']=date[:4]
    note='Primary metadata checked '+TODAY+'. '
    if arxiv:
        fields.update({'archivePrefix':'arXiv','eprint':arxiv})
        note+='First arXiv submission '+str(s['first_arxiv_submission'])+'; current '+str(s['current_version'])+'. '
        if s['latest_revision']: note+='Latest revision '+s['latest_revision']+'. '
    if not date: note+='Dynamic or undated document; publication date not asserted. '
    if sid=='N03': note+='UAI 2004; deposited on arXiv in 2012. '
    if sid=='N10': note+='Author-hosted draft; journal date independently checked from author publication list. '
    fields['note']=note+'Not evidence of project effectiveness.'
    bib.append('@misc{'+s['citation_key']+',\n'+',\n'.join('  '+k+' = {'+str(v)+'}' for k,v in fields.items() if v)+'\n}\n')
(WORK/'paper').mkdir(exist_ok=True)
(WORK/'paper/references.bib').write_text('\n\n'.join(bib)+'\n')

doc=['# Semantic Becoming v3：近邻工作与候选新颖性边界',
 '> 研究状态：NOT_RUN。D01 是来源与主张审查，不是模型实验、实现验收或全球优先权认证。',
 '## 1. 从计算对象出发，而非从命名出发',
 '本轮不把“潜”“认知”“梦境”等名称当作新机制。每项比较固定四件事：传什么对象、执行什么操作、保持什么不变量、什么例子能区分它与普通答案传递。已有原语必须承认；可能的新组合或新对象保留为条件假说。近期可实验性不作为删除方向的理由。',
 '本任务完整保留 H01–H48。每项同时记录共享原语、候选差异、区分例、未证明桥梁和更激进的延伸。所有区分例在 D01 中仅为审查规格，未被执行为模型实验。',
 '## 2. 来源真实性与核验层次',
 '核验日期为 2026-10-24 UTC。包内 sources 的 checked_on 是供给资料的声明，不是本轮访问证据。本轮实际打开 primary URL；arXiv 记录的标题、作者、首版、当前版本和修订分别记录。近期 2026 条目并未因日期较新被自动判假，也未因包内标题存在就自动采信。',
 'S02、S03、S08、S13、inherited:R06、R13、R14 均已在给定 arXiv URL 核对实际身份。S01 的 Interlat 是方法别名；S03 的完整标题不同于缩写。S15 页面实际是 Verified Functional Synthesis，CEGIS 的具体循环由新核验 N14 支持。',
 '主要依据是一次文献定位与摘要/目标章节阅读，不等于全篇证明复核、源码复现或穷尽所有同类研究。没有找到完全相同工作，也不能写“世界首次”。',
 '动态文档不伪造发表/修订日。PyTorch stable 重定向到 2.14 的目标页面已经单独检查，但文档版本不等于已安装版本。没有安装包、下载权重、初始化网络或运行示例代码。',
 '## 3. 重点修订与创新保留',
 'H39 的事务机制具有直接系统前驱，定位为支撑性集成，不包装为新的智能范式。H47 必须与行为等价、bisimulation 和状态聚合比较，不能把取商本身称原创。H30 的关系类比、H34 的双向消息、H36 的反例循环、H44 的世界内学习也都有明确前驱。',
 '更激进的研究空间仍完整保留：交流能否改变可操作概念、问题与答案关系、学习方向/学习规则、指令集和可执行世界？候选贡献在这些对象如何作为可迁移、可组合、可版本化的跨模型协议，而不是宣称发明全部基础数学。',
 '## 4. 48 项逐项台账']
for m in mechanisms:
    links='；'.join('['+x['id']+']('+x['url']+')' for x in m['nearest_sources'])
    doc += ['### '+m['id']+' · '+m['title'],
      '- 对象/操作：'+m['object_type']+'；'+m['operation']+'。',
      '- 不变量：'+m['invariant']+'。',
      '- 已核验近邻：'+links+'。共享原语：'+m['shared_primitive'],
      '- 候选差异：'+m['candidate_difference'],
      '- 区分例（设计，未运行）：'+m['separating_case'],
      '- 未证明桥梁：'+m['unproven_bridge'],
      '- 保留的激进延伸：'+m['aggressive_extension'],
      '- 结论：提出而非证成；优先权未知，研究 NOT_RUN。']
doc += ['## 5. 一手来源目录与版本',
 '以下目录使用核验后的标题。inherited 别名保存在 JSON，BibTeX 按同一来源去重。arXiv 首次收录不是自动认定的历史首发；“修订未知”也不表示从未修订。']
for sid,s in canon.items():
    dates=[]
    if s['first_publication_date']:dates.append('已核验发表/文档日期 '+s['first_publication_date'])
    if s['first_arxiv_submission']:dates.append('arXiv 首版 '+s['first_arxiv_submission'])
    if s['latest_revision']:dates.append('最新修订 '+s['latest_revision']+' '+s['current_version'])
    elif s['current_version']:dates.append('当前 '+s['current_version']+'，未显示另次修订')
    else:dates.append('首版/修订日期未确立')
    doc += ['### '+sid+' · '+s['observed_title'],
            '['+s['observed_title']+']('+s['canonical_url']+')',
            '作者：'+str(s['authors'])+'。'+'；'.join(dates)+'。',
            '支持范围：'+str(s['supported_scope'])+' 边界：不证明本项目机制新颖或有效。',
            '日期解释：'+s['date_scope']]
doc += ['## 6. 不成功访问与开放项',
 'JHU 的能力论文 PDF 返回 502；后续从作者相关 Agoric 论文库的下载链接成功读取同一论文。微软事务论文页面直接抓取超时，但 arXiv 正式记录成功，报告与期刊年份另外标注为元数据而非混作 arXiv 日期。',
 '自然梯度 DOI 返回 403；官方出版商检索摘要仅作为 N07 线索保留，未绕过访问限制，未进入机制证据或 references.bib。H37 的广泛优先权比较仍需后续全文审查。H28/H33 也须扩展分岔、混合系统及非平衡计算近邻。',
 '这些开放研究问题不删除机制，也不阻塞本次准确的来源台账；不能把本次 done 状态解释为研究验证完成。',
 '## 7. 产物、要求与真实检查',
 '- docs/related_work.md：D01-1 与 P12 的逐项比较；48 项对象/不变量/反例/延伸。',
 '- specs/novelty_ledger.json：D01-1/2/3；供给与实际核验字段、源状态、日期、别名修订及元数据快照索引。',
 '- paper/references.bib：D01-3；核验标题、作者、可定位 URL、版本与无重复引用键。',
 '- run_state/checks/D01_validation.json：实际标准库静态检查结果；依赖、输入哈希、覆盖与引用一致性。',
 '- run_state/checks/D01_source_observations.json：实际 primary open 的元数据观察记录。metadata_sha256 仅标识观察记录，不冒充完整网页或论文文件哈希。',
 '本轮没有调用研究模型，没有执行神经网络初始化、推理、训练或评测，没有读取无关私有资料、付费或发布。全部未来研究路径保持 NOT_RUN。']
(WORK/'docs/related_work.md').write_text('\n\n'.join(doc)+'\n')
print(json.dumps({'mechanisms':len(mechanisms),'source_records':len(sources),'canonical_citable_sources':len(canon),'snapshot_records':len(snapshot_index),'research_state':'NOT_RUN'},indent=2))
