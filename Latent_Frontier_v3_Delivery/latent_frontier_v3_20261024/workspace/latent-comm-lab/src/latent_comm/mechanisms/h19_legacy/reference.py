from dataclasses import asdict
import json
from latent_comm.core import ContractError,VersionSet,StepBudget
from latent_comm.core.finite import matmul,matvec,eye,add,matrix,vector
from .types import ConsolidatedAdapter,AffineSkill

def compile_affine_operations(operations,*,budget=StepBudget()):
    # Exact finite algebra, NOT a neural training run or evidence of generalization.
    if not operations:raise ContractError('EmptyOperations','at least one explicit affine operation')
    dim=len(operations[0][1]);w=eye(dim);b=(0.,)*dim;ids=[];meter=budget.meter();meter.dimension(dim)
    for name,a,c in operations:
        meter.consume(steps=1);a=matrix(a);c=vector(c)
        if len(a)!=dim or len(a[0])!=dim or len(c)!=dim:raise ContractError('ShapeMismatch','operation coordinates must agree')
        w=matmul(a,w);b=add(matvec(a,b),c);ids.append(name)
    return AffineSkill(w,b,tuple(ids))
def apply_skill(skill,state):return add(matvec(skill.weight,vector(state)),skill.bias)
def validate_training_partition(traces,unseen_instance_ids,*,step,versions):
    if not traces:raise ContractError('NoTrainingSource','explicit source traces required')
    if len({t.trace_id for t in traces})!=len(traces):raise ContractError('DuplicateTrace','one trace counted once')
    for trace in traces:
        if trace.instance_id in unseen_instance_ids:raise ContractError('SplitLeakage','training trace cannot count as unseen transfer evidence')
        if step>trace.expires_step:raise ContractError('ExpiredTeacher','message teacher has expired')
        if not trace.versions.matches(versions,('ontology','isa','task','evidence')):raise ContractError('VersionMismatch','teacher trace semantics changed')
    return frozenset(t.trace_id for t in traces)
class AdapterHistory:
    def __init__(self):self.versions={};self.active={};self.withdrawn=set()
    def register(self,adapter):
        key=(adapter.adapter_id,adapter.version)
        if key in self.versions:raise ContractError('VersionConflict','immutable adapter version')
        if adapter.parent_version is not None and (adapter.adapter_id,adapter.parent_version) not in self.versions:raise ContractError('MissingAncestor','rollback chain must be complete')
        self.versions[key]=adapter
    def activate(self,adapter_id,version,*,base_revision,versions):
        key=(adapter_id,version)
        if key not in self.versions:raise ContractError('UnknownAdapter','missing parameter artifact')
        a=self.versions[key]
        if a.evidence_sources&self.withdrawn:raise ContractError('RetractedSource','invalid consolidated skill')
        if a.base_revision!=base_revision or not a.versions.matches(versions,('ontology','isa','task','evidence')):raise ContractError('MigrationRequired','adapter is bound to base and semantic versions')
        self.active[adapter_id]=version;return a
    def rollback(self,adapter_id,*,base_revision,versions):
        a=self.versions[(adapter_id,self.active[adapter_id])]
        if a.parent_version is None:raise ContractError('MissingAncestor','already at oldest version')
        return self.activate(adapter_id,a.parent_version,base_revision=base_revision,versions=versions)
    def withdraw(self,sources):
        self.withdrawn.update(sources)
        affected=tuple(k for k,a in self.versions.items() if a.evidence_sources&self.withdrawn)
        for aid,version in affected:
            if self.active.get(aid)==version:self.active.pop(aid)
        return affected
    def persist(self,workspace):
        rows=[]
        for a in self.versions.values():
            row=asdict(a)
            for k in ('trained_trace_ids','trained_instance_ids','evidence_sources','writable_groups'):row[k]=sorted(row[k])
            rows.append(row)
        return workspace.commit({'skills.json':json.dumps({'versions':rows,'active':self.active,'withdrawn':sorted(self.withdrawn)},sort_keys=True,allow_nan=False)},expected_generation=workspace.generation)
    @classmethod
    def restore(cls,workspace):
        obj=json.loads(workspace.read('skills.json'));store=cls();remaining=list(obj['versions'])
        while remaining:
            ready=[r for r in remaining if r['parent_version'] is None or (r['adapter_id'],r['parent_version']) in store.versions]
            if not ready:raise ContractError('MissingAncestor','missing or cyclic stored ancestry')
            for row in ready:
                remaining.remove(row);row=dict(row);row['versions']=VersionSet(**row['versions'])
                for k in ('trained_trace_ids','trained_instance_ids','evidence_sources','writable_groups'):row[k]=frozenset(row[k])
                store.register(ConsolidatedAdapter(**row))
        store.withdrawn=set(obj['withdrawn'])
        for aid,version in obj['active'].items():
            if (aid,version) not in store.versions or store.versions[(aid,version)].evidence_sources&store.withdrawn:raise ContractError('RetractedSource','invalid active stored skill')
        store.active=dict(obj['active']);return store

def bind_learning_effect(adapter,linearization):
    # H37's parameter coordinates are explicit; no cross-model parameter identity assumption.
    if linearization.parameter_version!=adapter.version or not set(linearization.parameter_names)<=adapter.writable_groups:raise ContractError('AnchorMismatch','learning effect must reference exact consolidated parameter version and whitelist')
    return linearization

def bind_update_rule(adapter,rule):
    from latent_comm.mechanisms.h38_plasticity.reference import validate_rule
    validate_rule(rule.ast)
    if not set(rule.writable_groups)<=adapter.writable_groups:raise ContractError('WriteScopeViolation','H38 rule exceeds consolidation whitelist')
    return rule

def macro_provenance(adapter,macro,*,source_trace_ids,isa_version):
    if not set(source_trace_ids)<=adapter.trained_trace_ids or isa_version!=adapter.versions.isa:raise ContractError('VersionMismatch','H40 macro provenance and ISA must bind explicitly')
    return {'adapter_version':adapter.version,'macro':macro,'source_trace_ids':tuple(sorted(source_trace_ids)),'isa_version':isa_version}
