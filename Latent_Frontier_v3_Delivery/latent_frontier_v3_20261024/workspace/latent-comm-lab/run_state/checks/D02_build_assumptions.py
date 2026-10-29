import json
from pathlib import Path
W=Path(__file__).resolve().parents[2]
base=json.loads((W/'specs/assumptions.json').read_text())
sm=json.loads((W/'docs/formal_notes/source_map.json').read_text());branches=json.loads((W/'specs/future_branches.json').read_text())['branches']
extra=[
('A_IMPLEMENTABLE_READWRITE','模型注入器和读出器能够实现所声明的协变变换；矩阵恒等式不能推出。',['H25'],'固定读出反例；保留近似行为误差，不宣称语义对称。'),
('A_CONFLICT_CAUSE','拼合冲突可能来自缺少语境变量，但也可能来自错误观测、单位、映射或过强约束。',['H26','H27','H36'],'分域、扩变量、撤回和未决并存，不强制产生概念。'),
('A_TRAJECTORY_READOUT','不同轨迹或结构分支的读出与所研究任务的有用区别相关。',['H28','H33','H34'],'轨迹数学仍成立，但认知收益不成立；保留 V。'),
('A_CLOSURE_DOMAIN','粗化纤维上的后继粗态相同，或显式保留记忆/残差；闭合仅在声明域。',['H35'],'返回闭合失败或新宏变量，不伪装 Markov。'),
('A_REFINEMENT_INFORMATION','细化可访问旧等价类成员的原始区别或新观测。',['H47','H35'],'请求来源；代表元不能恢复被丢失区别。'),
('A_OBSERVATION_MODEL','许可查询的似然/确定响应覆盖声明候选机制；条件响应模型支持所用序列推断。',['H45'],'模型不匹配/未知似然；族内后验不是真机制保证。'),
('A_REQUIRED_CONSTRAINT','负知识证书中的 required_predicate 确为当前任务在有效前提下的必要条件。',['H46'],'标签和有限检查不足以证明任意任务排除安全。'),
('A_CONDITIONAL_OBSERVATION_INDEPENDENCE','观测核乘积需给定状态后的观测噪声独立，与转移的条件独立分别承担。',['H43','H44'],'扩状态、给联合观测核或保留未知依赖。'),
('A_SINGLE_COORDINATOR','所有 VersionedStore 读写经同一个协调实例；未决日志恢复后才接纳后续写入；底层原子替换/fsync 成立。',['H39'],'不声称跨实例、跨进程或分布式原子性。'),
('A_VALUE_FUNCTION','联盟价值函数对所比较子集有明确语义；未知值不能视为零，来源支持和执行价值分开。',['H41'],'UndefinedValue 或有界估计，不宣称公平/因果/金融价值。'),
('A_LANGUAGE_INFORMATION','新谓词只能用获准可观察字段；纯旧签名函数不能创造新的区分信息。',['H27','H40'],'unknown 与 False 分开；若需要新字段则明确提出信息需求。'),
('A_LOCAL_SMOOTHNESS','行为映射在更新线段邻域可微，定量 Taylor 界另需 Lipschitz Jacobian；裁剪阈值单独处理。',['H37','H38'],'局部更新效果只能条件估计，不把一阶方向当有限真实变化。'),
('A_ECOLOGY_MEANING','结构档案和语法扩张能够产生与目标相关的新操作，而非重复、作弊或无用任务。',['H42'],'只记录结构候选，不宣称神经 competence 或无界创新。')]
assumptions=[dict(a,claim_class='A',origin='specs/assumptions.json',status='explicit_condition_not_empirically_established') for a in base['assumptions']]
assumptions += [{'id':i,'claim_class':'A','statement':s,'consumers':c,'failure':f,'origin':'D02 formal review','status':'explicit_condition_not_empirically_established'} for i,s,c,f in extra]
scope={
'F01':('可逆同域共轭与读出同时运输；一般线性目标满足 Aᵀwprime=w；固定可行域。','D01a 函数作用恒等；D01b 异维协变/路径消去；D01c 目标对偶可表示性。'),
'F02':('有限实仿射系统与可行硬锚；精确可解性与浮点容差分别处理。','最小残差为正交补投影；三环最小值1/3；冲突删除仅包含最小。'),
'F03':('有限可观测签名和确定/同核随机决策；候选语法与信息权限固定。','旧等价状态不可由旧签名区分；新可计算谓词形成有限表达见证。'),
'F04':('回译在目标解纤维全定义；中间实例/操作域相容；精确关系或显式容差。','可靠/完整回译可分别复合；局部操作交换在合法路径上归纳到程序。'),
'F05':('有限共同实行为坐标；lambda>0 正定，lambda=0 单列最小范数选择；C1/C2 及 Lipschitz 条件按结论分开。','ridge 正规方程和残差分解；局部 Taylor 界；完整元梯度与 first_order 不等。'),
'F06':('局部 Lipschitz 场；h>0 线性 skew/PSD Q 中点；固定 alpha pitchfork；显式二维 Hopf 和一维 cubic fold 正规形；有限 Markov 状态的公开边界。','欧氏范数不变量与能量区别；alpha=0 高阶吸引；Hopf 稳定圆与非退化 fold；前后可达集路径条件。'),
'F07':('精确任务查询；确定动力学在粗化纤维一致；记忆展开需 CL=I；概率扩展另需 strong lumpability。','商与单调细化；确定闭合充要条件；粗细残差递推与不可恢复信息。'),
'F08':('共同概率空间和变量身份；DAG 方程；条件独立乘积核；布尔事件与给定联合分布；合成数据 Markov 条件。','未受影响 SCM 节点不变；核归一；合成不自证；幂等/联合概率/Fréchet 界。'),
'F09':('纯无环卫生宏；单协调实例原子版本检查；完整有限联盟价值；固定有界变异。','宏保守扩展；条件串行性；Shapley 效率/dummy；有限生态终止。'),
'F10':('归一有限似然和正预测事件；条件响应序列模型；排除谓词经任务必要条件支持并覆盖精确域。','IG=互信息>=0；相同响应族不可识别；硬排除并集安全及撤回恢复。')}
claims=[]
for f,(condition,statement) in scope.items():
    claims.append({'id':'D02-'+f,'claim_class':'D','statement':statement,'exact_scope':condition,'proof_status':'stepwise_derivation_in_note','proof_file':next(m['formal_notes'][0] for m in sm['mechanisms'] if any(Path(p).name.startswith(f+'_') for p in m['formal_notes'])),'verification_limit':'Finite fixtures illustrate and challenge special cases; not a general proof checker or empirical efficacy test.','research_state':'NOT_RUN'})
for m in sm['mechanisms']:
    mid=m['mechanism_id'];claims.append({'id':mid,'claim_class':'H','statement':m['candidate_difference'],'depends_on':[c['id'] for c in claims if c['claim_class']=='D' and any(Path(p).name.startswith(c['id'][4:]+'_') for p in m['formal_notes'])]+[a['id'] for a in assumptions if mid in a['consumers']],'unproved_bridge':m['unproven_bridge'],'research_state':'NOT_RUN','source_implemented_is_not_validated':True})
for b in branches:
    h=next(h for h in json.loads((W.parent.parent/'specs/horizons.json').read_text()) if h['id']==b['parent_horizon'])
    claims.append({'id':b['id'],'claim_class':'V','statement':b['new_object'],'depends_on':h['mechanisms'],'additional_assumptions':b['additional_assumptions'],'unproved_bridge':b['unproved_bridge'],'research_state':'NOT_RUN','implementation_status':'future_proposal_not_implemented'})
value={'schema_version':1,'task_id':'D02','claim_classes':base['claim_classes'],'research_state':'NOT_RUN','empirical_results':[],'assumptions':assumptions,'claims':claims,'dependency_semantics':'An edge is an explicit logical/research prerequisite, not evidence that the child is true. D proofs do not depend on A_MODEL_BRIDGE. H/V keep open bridges.','external_legacy_nodes':['H02','H05','H07','H10','H13','H18','H20','H22'],'non_unifications':base['not_unified'],'global_control_invariants':['user goal unchanged','no research execution','no permissions/spend/publication expansion','synthetic evidence not independent reality','shared budgets across nested finite calls']}
(W/'docs/formal_notes/assumption_dependencies.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
