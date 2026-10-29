"""D03 documentation/static provenance audit. No research module imports or entry calls."""
import ast, hashlib, json, re, sys
from pathlib import Path
W=Path(__file__).resolve().parents[3];P=W.parent.parent
checks=[]
def check(name,ok,detail=None):
 checks.append({'name':name,'passed':bool(ok),'detail':detail})
def read(p):
 text=p.read_text(encoding='utf-8')
 if p.suffix!='.md':return text
 # Compare equivalent TeX delimiters and formatting; provenance hashes stay raw.
 delimiters={'lVert':r'\|','rVert':r'\|','lbrace':r'\{','rbrace':r'\}'}
 def math(match):
  body=re.sub(r'\\(lVert|rVert|lbrace|rbrace)\b[ \t]*',lambda token:delimiters[token[1]],match[1])
  return '$'+body+'$'
 text=re.sub(r'(?<!\$)\$(?!\$)([^\n]*?)(?<!\$)\$(?!\$)',math,text)
 return re.sub(r'([：，])[ \t]+(?=\$)',r'\1',text)
def js(p):return json.loads(read(p))
md=read(W/'docs/research_monograph.md');tex=read(W/'paper/main.tex').replace('\\_','_');rd=read(W/'README.md')
snapshot=js(W/'run_state/checks/D03/source_snapshot.json')
h=js(P/'specs/hypotheses.json');c=js(P/'specs/combinations.json');x=js(P/'specs/horizons.json');b=js(W/'specs/future_branches.json')['branches'];n=js(W/'specs/novelty_ledger.json')
check('three_owned_deliverables_substantive',len(md.encode())>150000 and len(tex.encode())>150000 and len(rd.encode())>6000,[len(md),len(tex),len(rd)])
for label,ids in [('mechanisms',[i['id'] for i in h]),('compositions',[i['id'] for i in c]),('horizons',[i['id'] for i in x])]:
 expected=set(ids);seen=set(re.findall(r'^### ([HCX]\d{2}) ',md,re.M)) & expected
 check(label+'_full_distinct_sections',seen==expected,sorted(expected-seen))
check('thirty_eight_future_branches',set(re.findall(r'^#### (X\d{2}-B\d+) ',md,re.M))=={i['id'] for i in b})
check('thirteen_learning_sections',set(re.findall(r'^### (L\d{2}) ',md,re.M))=={f'L{i:02d}' for i in range(1,14)})
check('sixty_eight_explicit_original_recipes',set(re.findall(r'PLAN_ROOT/recipes/([HC]\d{2})\.json',md))=={i['id'] for i in h+c})
check('all_forty_eight_bound_configs',all(f'configs/mechanisms/{i["id"]}.json' in md for i in h))
check('all_twenty_bound_configs',all(f'configs/compositions/{i["id"]}.json' in md for i in c))
check('all_forty_eight_algorithm_contract_paths',all(i['target_base'] in md and f'tests/contracts/test_{i["id"].lower()}.py' in md for i in h))
for phrase in ['主线一','主线二','主线三','完整元梯度','不可达分量','观测噪声独立','required_predicate','单进程内同一协调实例','conditional','projection_residual','first_order','W13 负责']:
 check('semantic_topic_'+phrase,phrase in md)
check('no_invented_W14','W14' not in md+rd)
check('model_result_rows_not_run',all('NOT_RUN' in line for line in md.split('### 9.2 模型研究结果表')[1].split('有限证明示例')[0].splitlines() if line.startswith('| ') and '研究对象' not in line))
check('honest_incident',all(t in md+rd for t in ['三次','L13_noncompliant_legacy_guard_attempt.txt','116','没有模型','零入口尝试']))
check('noncommercial_audio_disclosure',all('非商业' in t and 'tts.ai/terms' in t and '人工试听' in t for t in (md,rd)))
check('media_snapshot_1846_dated',all('2026-10-24 18:46 UTC' in t for t in (md,rd)))
check('media_short_real_long_incomplete',all('90.000秒' in t and '14段字幕' in t and '6分钟静音草稿' in t and '长版有声' in t and '未完成' in t for t in (md,rd)))
check('media_denial_stopped_uncertain_pending',all(all(term in t for term in ['被拒绝','493字','回复待定','43个任务','42个WAV','1,261字','credits_used=0','16字','远端结果未知','15段','均已停止' if t is md else '已停止','不支持']) for t in (md,rd)))
previous=read(W/'run_state/checks/D03/pre_media_1846/research_monograph.md')
media_start='媒体表达沿用概念、学习、世界三条线';media_end='\n\n## 10'
check('media_only_monograph_delta',md.split(media_start)[0]==previous.split(media_start)[0] and md.split(media_end,1)[1]==previous.split(media_end,1)[1])
check('source_evidence_limits',all(t in md for t in ['PRIMARY_CHECKED','N07','全文','优先权','57条','46条']))
check('all_research_not_run',all('NOT_RUN' in t and re.search(r'前沿机制提案\s*/\s*无模型实测',t) for t in (md,rd,tex)))
known=set(re.findall(r'@\w+\{([^,]+),',read(W/'paper/references.bib')))
used=set(re.findall(r'SBV3_[SRN]\d+',md));check('bibliography_all_46_resolve',len(known)==46 and used==known,{'known':len(known),'used':len(used),'missing':sorted(used-known)})
check('no_N07_substantive_citation','SBV3_N07' not in used)
# Bibliographic dates preserve distinct D01 source fields, including null publication dates.
bibliography=md.split('## 15 文献身份与证据层级')[1].split('## 16 结语与可复核交付')[0]
source_rows={}
for source in n['sources']:
 if source.get('cite_allowed'):source_rows.setdefault(source['citation_key'],source)
date_failures=[]
for key,source in source_rows.items():
 line=next((line for line in bibliography.splitlines() if line.startswith(f'- [{key}] ')),'')
 publication=source.get('first_publication_date')
 label='出版年份' if publication and len(publication)==4 else '出版年月' if publication and len(publication)==7 else '出版日期'
 expected=f"{label}：{publication or '未知'}"
 if expected not in line:date_failures.append([key,'publication',expected])
 arxiv=source.get('first_arxiv_submission')
 if arxiv and f'arXiv首次提交：{arxiv}' not in line:date_failures.append([key,'arxiv',arxiv])
 if not arxiv and 'arXiv首次提交：' in line:date_failures.append([key,'invented_arxiv_date'])
check('all_46_bibliography_date_fields_preserved',not date_failures,{'sources':len(source_rows),'failures':date_failures})
check('no_conflated_first_public_date','首次公开日期字段' not in md+tex)
check('N03_UAI2004_not_2012_deposit','出版年份：2004；arXiv首次提交：2012-07-11' in bibliography)
check('graft_original_new_descendant_union',all(t in md for t in ['原图与新图的后代并集','并包括移植节点自身','保留相同外生赋值与未受影响根变量并施加同一干预']))
check('joint_kernel_conditional_independence_and_locality','给定完整当前状态、动作和 U 后局部下一状态条件独立，且各局部核只依赖声明的 $s_i$ 边界' in md)
check('adaptive_identifiability_sequence_condition','每轮响应仅由当前查询和假设 H 按同一已声明条件模型产生' in md and '相同的单次边缘分布不排除跨轮相关性不同' in md)
assumption_tex=re.split(r'\\section\{10\s',tex,maxsplit=1)[1];assumption_tex=re.split(r'\\section\{11\s',assumption_tex,maxsplit=1)[0]
check('23_assumptions_render_as_real_list',assumption_tex.count('\\item')==23 and '\\begin{itemize}' in assumption_tex,{'latex_items':assumption_tex.count('\\item')})
missing=[]
for path in re.findall(r'`([^`]+)`',md):
 if path.startswith('PLAN_ROOT/'):
  if not (P/path.removeprefix('PLAN_ROOT/')).exists():missing.append(path)
 elif path.startswith(('src/','configs/','tests/','docs/','paper/','run_state/')) and not (W/path).exists():missing.append(path)
check('all_code_formatted_paths_exist',not missing,missing)
changed=[]
for path,digest in snapshot['inputs'].items():
 p=(W/path.removeprefix('WORK_ROOT/')) if path.startswith('WORK_ROOT/') else P/path.removeprefix('PLAN_ROOT/')
 if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changed.append(path)
check('source_snapshot_current',not changed,{'files':len(snapshot['inputs']),'changed':changed})
loss=js(W/'run_state/checks/D03/loss_snapshot.json');check('127_static_loss_specs',len(loss)==127 and {r['mechanism'] for r in loss}=={i['id'] for i in h})
check('all_loss_fields_recorded',all(set(['formula','numerator','denominator','valid_mask','zero_valid_policy','parameter_owners','requires_grad_inputs','stop_gradient_edges','estimator','units'])<=set(r) for r in loss))
# Exact renderer token sequence preserves original LossSpec formula whitespace.
def rendered_formula(formula):
 parts=re.split(r'(\s+)',formula.replace('ᵀ','^T'))
 return '{\\small'+''.join('\\hspace{0.333em}'*len(part) if part.isspace() else '\\nolinkurl{'+part+'}' for part in parts if part)+'}'
check('all_127_loss_formulas_preserve_source_spacing',all(rendered_formula(row['formula']) in tex for row in loss),{'formulas':len(loss),'with_whitespace':sum(bool(re.search(r'\s',row['formula'])) for row in loss)})
check('latex_full_content_coverage',all(i['id'] in tex and i['title'] in tex for i in h+c+x) and all(i['id'] in tex for i in b))
check('latex_real_document',all(t in tex for t in ['\\documentclass','\\begin{document}','\\end{document}','\\tableofcontents']))
check('balanced_markdown_math',md.count('$')%2==0,md.count('$'))
expected_paper_input=md.split('\n',1)[1].replace('前沿机制提案 / 无模型实测\n\n研究总稿，2026年10月24日。研究状态：NOT_RUN。','研究总稿，2026年10月24日。研究状态：NOT_RUN。',1)
check('paper_input_matches_current_monograph',read(W/'run_state/checks/D03/paper_input.md')==expected_paper_input)
render_log=read(W/'run_state/checks/D03/latex_pass6.txt')
check('latex_compiles_without_glyph_or_box_errors','Output written on' in render_log and 'Missing character:' not in render_log and 'Overfull' not in render_log)
check('no_unsafe_getting_started',not any(t in rd for t in ['pytest','unittest discover','pip install','from_pretrained']))
# Static parsing is not importing executable research source.
count=0
for i in h:
 for p in (W/i['target_base']).glob('*.py'):ast.parse(p.read_text());count+=1
check('mechanism_source_ast_parse',True,count)
sys.path.insert(0,str(W/'scripts'))
import task_checkpoint as tc
memo={};deps=[]
try:
 for dep in tc.dependencies_for('D03'):
  r=tc.verify_receipt(dep,memo=memo);deps.append({'task_id':dep,'status':r['status'],'input_digest':r['input_digest'],'sha256':tc.digest(W/'run_state/receipts'/f'{dep}.json')})
 check('all_current_dependency_receipts',True,{'direct':len(deps),'transitive':len(memo)})
except (OSError,ValueError,KeyError) as e:check('all_current_dependency_receipts',False,str(e))
(W/'run_state/checks/D03/dependencies_final.json').write_text(json.dumps({'dependencies':deps,'transitive':len(memo),'research_state':'NOT_RUN'},ensure_ascii=False,indent=2)+'\n')
report={'task_id':'D03','scope':'static documentation/source/AST/provenance only','research_state':'NOT_RUN','research_entries_invoked_by_D03':0,'neural_imports':[],'check_count':len(checks),'passed':sum(c['passed'] for c in checks),'checks':checks,'outputs':[{'path':p,'sha256':hashlib.sha256((W/p).read_bytes()).hexdigest(),'bytes':(W/p).stat().st_size} for p in ['docs/research_monograph.md','README.md','paper/main.tex']]}
(W/'run_state/checks/D03/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if all(c['passed'] for c in checks) else 1)
