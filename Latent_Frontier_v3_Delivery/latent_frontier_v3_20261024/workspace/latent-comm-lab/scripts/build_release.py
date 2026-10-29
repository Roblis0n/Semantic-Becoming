"""Seal and independently re-extract the portable source/design delivery.

No network, model import, installation, publication or research execution.
The postbuild Z02 receipt and outer ZIP hash are sidecars, never self-hashed.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,stat,subprocess,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath
import task_checkpoint as ck
W=ck.WORK;P=ck.PLAN;TOP='Latent_Frontier_v3_Delivery';PLAN_NAME='latent_frontier_v3_20261024'
OUT=W/'release/latent-comm-lab-source-design.zip'
POSTBUILD={'reports/release_integrity.json','run_state/receipts/Z02.json'}
TRANSIENT_PREFIXES=('run_state/checks/D03/cache/',)
TRANSIENT_FILES={'run_state/checks/D03/render/xelatex.fmt'}
SEAL_EXCLUSIONS={'manifest.json','checksums.sha256','run_state/receipts/Z01.json','run_state/receipts/Z02.json','run_state/ledger.json','run_state/next_actions.json','reports/release_integrity.json','run_state/checks/Z01_seal_validation.json'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n', encoding='utf-8')
def validate_archive_members(infos):
    seen=set();portable=set()
    for info in infos:
        name=info.filename;path=PurePosixPath(name)
        if (not name or info.orig_filename!=name or path.is_absolute() or path.as_posix()!=name or
                any(part in {'.','..'} for part in path.parts) or
                chr(92) in name or any(':' in part or part.rstrip(' .')!=part for part in path.parts) or
                stat.S_ISLNK(info.external_attr>>16)):
            raise ValueError('unsafe or noncanonical ZIP entry')
        key=name.casefold()
        if name in seen or key in portable:raise ValueError('duplicate or case-colliding ZIP entries')
        seen.add(name);portable.add(key)
    return len(seen)
def included(path):
    rel=path.relative_to(W)
    if rel.as_posix().startswith('release/authorization_updates/'):
        return path.is_file() and path.suffix=='.json'
    return path.is_file() and not any(x in {'__pycache__','.git','.pytest_cache','checkpoints','release'} for x in rel.parts) and path.suffix!='.pyc' and rel.as_posix() not in POSTBUILD|TRANSIENT_FILES and not rel.as_posix().startswith(TRANSIENT_PREFIXES)

def work_files():
    files=[]
    for p in sorted(W.rglob('*')):
        if p.is_symlink():raise ValueError('symlink in deliverable workspace: '+str(p.relative_to(W)))
        if included(p):files.append(p)
    return files

def plan_bytes():
    manifest=json.loads((P/'DELIVERY_MANIFEST.json').read_text(encoding='utf-8'));result={}
    for row in manifest['files']:
        rel=PurePosixPath(row['path'])
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe original input manifest path')
        target=P/str(rel)
        if target.is_symlink() or not target.resolve().is_relative_to(P):raise ValueError('original input path escapes its plan')
        raw=target.read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise ValueError('authoritative input changed: '+str(rel))
        result[str(rel)]=raw
    for name in manifest['excluded_from_self_hash']:result[name]=(P/name).read_bytes()
    if any(name.startswith('workspace/') for name in result):raise ValueError('original input collides with generated workspace')
    return result

def prepare():
    state=ck.sync();remaining=[t for t in ck.TASKS if t not in state['done']]
    if set(remaining)!={'Z01','Z02'}:raise ValueError('cannot seal incomplete core/media source tasks: '+repr(remaining))
    originals=plan_bytes();blockers=state['external_blockers']
    publication='''# 发布草案，仅草稿，未发布\n\nLatent Frontier v3 / Semantic Becoming 是前沿机制提案与可继续实现的研究源码包。48个机制、20条组合、68份配方和12个有限终局按类型与版本约束组织。源码、静态审查与有界标准库示例不是模型有效性的实验证明；所有研究模型运行均为 NOT_RUN。\n\n本地可编辑幻灯片、SVG、动画、视频和语音附有真实产物与检查记录。含第三方免费TTS音频的文件仅限个人、非商业使用，尚未完成实际试听与发音复核。独立创作的源码、PPT、SVG和静音视觉版本不因该音频服务自动取得相同限制。本草案没有向任何网站、代码托管或社交平台发布。\n'''
    (W/'docs/publication_draft.md').write_text(publication, encoding='utf-8')
    lines=['# Latent Frontier v3 交付封印报告','', '前沿机制提案 / 无模型实测','', '## 1. 实际生成的范围', '',f'封印时已有 {len(state["done"])} / 133 项任务处于可核对终态。Z01、Z02 是本报告与最终压缩包的封印步骤；它们的最终完成状态、ZIP SHA-256和重新解压结果在随附的 FINAL_DELIVERY_VERIFICATION.json 中记录，不能将压缩包哈希写进压缩包自身。', '', '实现范围保持48机制、20组合、68配方、13世界任务、6后端任务、13学习任务、12有限终局、D01–D04及全部媒体任务。具体完成是源码/结构化内容与已执行的有限检查，不是后端模型集成成功或新经验研究。', '', '入口：README.md；长文：docs/research_monograph.md；论文源：paper/main.tex；形式分叉：docs/frontier_afterword.md及specs/future_branches.json；逐项对象/算法/检查见FILE_INDEX.md和run_state/receipts。', '', '## 2. 实际检查与复现入口', '', '- reports/source_review.json和reports/math_review.md绑定当前AST、类型、梯度账本、机制/组合/终局独立复核与真实检查日志。', '- scripts/check_source_bindings.py只做源名称/枚举解析；scripts/audit_source_contracts.py只做源码结构与回执检查。', '- scripts/run_allowed_contracts.py按明确文件执行有限/静态契约，排除研究入口调用；C/X用--individual-fixture-scopes，由每次组合/终局调用实施端到端预算。', '- reports/permission_review.json披露实际执行边界、无法提供硬沙箱的限制，以及被保留的三次立即拒绝的旧门禁入口尝试。该偏差不计作获准检查。', '- 本ZIP重新解压后对每个条目进行全量SHA-256核对、路径/重复条目/符号链接检查，并在新目录用原始设计输入重验Z01依赖回执。实际结果在包外验收侧车。', '', '## 3. 明确没有运行', '', '所有研究模型初始化、权重下载、加载、神经前向、生成、训练、评估、benchmark和研究云API保持NOT_RUN；没有随机微型神经夹具或大批量数据集生成。有限例只检验其声明域，不证明一般数学命题、模型学习能力、新颖优先权或未来性能。', '', '## 4. 媒体、许可与外部状态', '', '36页研究PPT和12页短版是原生可编辑文件，6张SVG、5段机制动画及两版视频均有源文件与对应检查。实际导出/打开/时长状态以reports/media_qa.json为准，历史静音稿与当前含音轨版明确区分。', '', '免费TTS音频及包含它的视频受服务的个人、非商业许可限制；未进行真实听觉试听，不把波形、解码、字幕一致或响度测量冒充听觉验收。独立创作的源码/PPT/SVG/静音版本不自动受该服务音频许可约束。', '', '当前明确外部/能力阻塞：', '']
    for tid,items in blockers.items():
        for item in items:lines.append(f'- {tid}：{item}')
    if not blockers:lines.append('- 无已记录外部阻塞；这不构成经验研究通过。')
    lines+=['','## 5. 继续入口与风险','','任何后续模型运行都需要另行明确授权和独立执行环境审查；不得通过改配置绕过当前硬拒绝入口。先读取README和run_state/next_actions.json，再用scripts/task_checkpoint.py verify核对输入。原始绝对路径仅为历史来源记录；可移植运行优先使用随包相对计划路径并核对task_graph身份。','','数学的未证桥梁、机制有限适用域、单协调实例事务限制、显式共享噪声与依赖声明、任务相对等价和负知识前提均保留在D02/D03与各机制文档。未来38条分叉是提案，不标成已完成算法。','','docs/publication_draft.md仅为发布草案。未发布网站、未推送公共仓库、未发外部消息、未发生新增付费。','','## 6. 哈希自引用边界','','manifest.json封印静态工作内容；它不自哈希，也排除本节列出的可变封包状态。压缩包顶层DELIVERY_CONTENTS.json另外覆盖实际装入ZIP的每个普通文件，唯独排除自身。最终ZIP、Z02回执、重新解压完整性报告和独立验收是包外侧车。','', '静态manifest排除：'+', '.join(sorted(SEAL_EXCLUSIONS))+'；以及release/中除公开authorization_updates以外的内容、checkpoints/、缓存和.pyc。','','历史原始计划完整保留在上一级；其START_HERE/DELIVERY_REPORT仅描述输入计划，不是本轮实现完成声明。请从ZIP顶层START_HERE.md进入新实现。','']
    short_voice=(W/'assets/video/intro_90/intro_90_narrated_personal.mp4').is_file()
    long_voice=(W/'assets/video/explainer_360/explainer_360_narrated_personal.mp4').is_file()
    lines+=['','## 当前有声版本的精确状态','',f'90秒有声MP4实际存在：{short_voice}；约6分钟有声MP4实际存在：{long_voice}。存在性只说明文件，不替代对应AV报告或听觉检查。']
    permission_event=W/'run_state/permission_events/tts_destination_disclosure_denial.json'
    if permission_event.exists():
        event=json.loads(permission_event.read_text(encoding='utf-8'));lines+=['','已保留TTS目的地/负载授权拒绝记录。拒绝后停止外部活动，不能以此前一般媒体意图或内部通知伪造新授权；没有把此前传输追认成全面合规。详见reports/permission_review.json及权限事件。']
    if not long_voice:lines+=['','长版有声输出尚未完成。现有6分钟静音草稿是降级产物，不能用静音填补旁白而标为有声完成；已合成片段与未完成项均单列保存。']
    (W/'RELEASE_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    candidates={p.relative_to(W).as_posix() for p in work_files()}|{'FILE_INDEX.md','manifest.json','checksums.sha256','run_state/receipts/Z01.json','run_state/checks/Z01_seal_validation.json'}
    index=['# 生成工作区文件索引','','这是实际实现工作区，不是原始计划索引。机器可核对的字节数与SHA-256见manifest.json；原始计划自己的索引另保留。文件是源、导出、检查或历史证据，不将不同副本合并计算成多个研究成果。','']
    for name in sorted(candidates):index.append('- '+name)
    (W/'FILE_INDEX.md').write_text('\n'.join(index)+'\n', encoding='utf-8')
    rows=[]
    for path in work_files():
        name=path.relative_to(W).as_posix()
        if name in SEAL_EXCLUSIONS:continue
        raw=path.read_bytes();rows.append({'path':name,'bytes':len(raw),'sha256':sha(raw)})
    manifest={'schema_version':1,'project':'latent-comm-lab','research_state':'NOT_RUN','seal_time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completed_before_packaging':len(state['done']),'total_tasks':133,'static_file_count':len(rows),'files':rows,'excluded_from_static_hash':sorted(SEAL_EXCLUSIONS),'excluded_tree_prefixes':['release/ (except public authorization_updates JSON)','checkpoints/','__pycache__/','.git/','.pytest_cache/'],'postbuild_authority':'FINAL_DELIVERY_VERIFICATION.json sidecar','original_plan_files':len(originals)}
    manifest['excluded_transient_prefixes']=list(TRANSIENT_PREFIXES);manifest['excluded_transient_files']=sorted(TRANSIENT_FILES)
    dump(W/'manifest.json',manifest);(W/'checksums.sha256').write_text(''.join(r['sha256']+'  '+r['path']+'\n' for r in rows), encoding='utf-8')
    verify_seal()
    dump(W/'run_state/checks/Z01_seal_validation.json',{'static_files_verified':len(rows),'original_plan_files_verified':len(originals),'manifest_sha256':sha((W/'manifest.json').read_bytes()),'research_state':'NOT_RUN','excluded_self_reference':sorted(SEAL_EXCLUSIONS)})
    print(json.dumps({'static_files':len(rows),'original_plan_files':len(originals),'prepackaging_terminal':len(state['done'])}))

def verify_seal():
    manifest=json.loads((W/'manifest.json').read_text(encoding='utf-8'))
    current={p.relative_to(W).as_posix():p for p in work_files() if p.relative_to(W).as_posix() not in SEAL_EXCLUSIONS}
    if set(current)!={r['path'] for r in manifest['files']}:raise ValueError('new/removed sealed file since prepare')
    for row in manifest['files']:
        raw=current[row['path']].read_bytes()
        if sha(raw)!=row['sha256'] or len(raw)!=row['bytes']:raise ValueError('changed sealed file: '+row['path'])
    return manifest

def archive():
    ck.verify_receipt('Z01');manifest=verify_seal();originals=plan_bytes();payload={f'{TOP}/{PLAN_NAME}/{name}':raw for name,raw in originals.items()}
    for path in work_files():payload[f'{TOP}/{PLAN_NAME}/workspace/latent-comm-lab/{path.relative_to(W).as_posix()}']=path.read_bytes()
    landing=f'''# Latent Frontier v3 · 本轮实际交付入口\n\n前沿机制提案 / 无模型实测。\n\n请先打开 [{PLAN_NAME}/workspace/latent-comm-lab/README.md]({PLAN_NAME}/workspace/latent-comm-lab/README.md)，再看该目录的 RELEASE_REPORT.md、reports/source_review.json、reports/media_qa.json。实际源码位于同目录 src/。\n\n上一级 {PLAN_NAME}/START_HERE.md、DELIVERY_REPORT.md 和 DELIVERY_MANIFEST.json 是原样保留的2026-10-24输入计划及其历史自检，不是本次实现状态。此顶层入口优先。\n\n解压后使用Python≥3.11，进入 {PLAN_NAME}/workspace/latent-comm-lab 目录。以下命令只读取设计元数据或编译锁定IR，不加载模型：

    PYTHONPATH=src python -m latent_comm.cli.main design
    PYTHONPATH=src python -m latent_comm.cli.main compile ../../recipes/C13.json --format text
    python scripts/check_source_bindings.py

不需要联网安装、tensor/backend extras或任何模型权重。研究后端依赖及实际模型绑定仍未启用；原始计划相对布局必须一并保留。\n\n真正的外层ZIP SHA-256、Z02封包完成状态和独立最终验收见随附 FINAL_DELIVERY_VERIFICATION.json；无法把ZIP自身哈希放进自身。包内 DELIVERY_CONTENTS.json 校验其他所有实际条目。\n\n媒体中的第三方免费TTS音频及含音轨视频仅供个人、非商业使用，真实听审按用户2026-10-27明确要求移除验收条件，状态USER_WAIVED_NOT_PERFORMED，未试听且不称听审通过；该服务的音频许可限制不自动适用于独立创作的源代码/PPT/SVG/静音视觉文件。所有研究模型路径NOT_RUN，没有公开发布。\n'''
    payload[f'{TOP}/START_HERE.md']=landing.encode()
    rows=[{'path':name,'sha256':sha(raw),'bytes':len(raw)} for name,raw in sorted(payload.items())]
    package_manifest={'schema_version':1,'research_state':'NOT_RUN','file_count_excluding_self':len(rows),'files':rows,'excluded_self_hash':[f'{TOP}/DELIVERY_CONTENTS.json'],'postbuild_sidecars':['FINAL_DELIVERY_VERIFICATION.json','reports/release_integrity.json','run_state/receipts/Z02.json','release/independent_delivery_acceptance.json','release/independent_delivery_acceptance.md']}
    payload[f'{TOP}/DELIVERY_CONTENTS.json']=(json.dumps(package_manifest,ensure_ascii=False,indent=2)+'\n').encode();OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,raw in sorted(payload.items()):
            path=PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name:raise ValueError('unsafe archive path')
            info=zipfile.ZipInfo(name,date_time=(2026,10,24,0,0,0));info.create_system=3;info.external_attr=(stat.S_IFREG|0o644)<<16;info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,raw)
    with tempfile.TemporaryDirectory(prefix='latent-frontier-release-verify-',dir=W/'release') as td:
        target=Path(td)
        with zipfile.ZipFile(OUT) as archive:
            validate_archive_members(archive.infolist())
            archive.extractall(target)
        verified=[]
        for name,raw in payload.items():
            disk=(target/name).read_bytes()
            if sha(disk)!=sha(raw):raise ValueError('re-extracted hash mismatch: '+name)
            verified.append(name)
        project=target/TOP/PLAN_NAME/'workspace/latent-comm-lab'
        result=subprocess.run([sys.executable,'scripts/task_checkpoint.py','verify','Z01'],cwd=project,text=True,capture_output=True)
        if result.returncode:raise ValueError('relocated Z01 receipt verification failed: '+result.stderr[-3000:])
        evidence={'schema_version':1,'archive_file':'release/latent-comm-lab-source-design.zip','archive_sha256':sha(OUT.read_bytes()),'archive_bytes':OUT.stat().st_size,'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive_entries':len(payload),'full_reextracted_sha256_matches':len(verified),'duplicates':0,'unsafe_paths':0,'symlinks':0,'original_plan_files':len(originals),'relocated_Z01_receipt_verification':'PASS','relocation_used_shipped_plan':True,'relocation_stdout_sha256':sha(result.stdout.encode()),'static_manifest_sha256':sha((W/'manifest.json').read_bytes()),'research_state':'NOT_RUN','model_entry_invocations':0,'self_reference_boundary':package_manifest['postbuild_sidecars'],'all_entries_nonempty':all(payload.values())}
        dump(W/'reports/release_integrity.json',evidence)
    print(json.dumps(evidence,ensure_ascii=False,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','verify-seal','archive']);args=parser.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='archive':archive()
    else:print(json.dumps({'verified_static_files':len(verify_seal()['files'])}))
