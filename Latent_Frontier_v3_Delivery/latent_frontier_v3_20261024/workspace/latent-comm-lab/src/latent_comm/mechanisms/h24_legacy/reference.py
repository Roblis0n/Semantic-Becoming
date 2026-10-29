from dataclasses import replace
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import matvec,add
from .types import EffectAudit

class CapabilityAuthority:
    """Installed out-of-band by host. Message payloads can name, never create, grants."""
    def __init__(self,grants,*,session_id):
        self.session_id=session_id;self.grants={g.capability_id:g for g in grants};self.revoked=set();self.parents={}
        if len(self.grants)!=len(grants) or any(g.session_id!=session_id for g in grants):raise ContractError('CrossSessionReference','unique trusted bootstrap grants per session')
    def resolve(self,capability_id,*,principal,step,versions,withdrawn=frozenset()):
        current=capability_id;ancestors=set()
        while current in self.parents:
            if current in ancestors:raise ContractError('ScopeEscalation','cyclic grant derivation')
            ancestors.add(current);current=self.parents[current]
        ancestors.add(current)
        if capability_id not in self.grants or ancestors&self.revoked:raise ContractError('CapabilityDenied','header cannot manufacture or revive authority')
        grant=self.grants[capability_id]
        if principal!=grant.principal or step>grant.expires_step or grant.evidence_handles&withdrawn:raise ContractError('CapabilityDenied','wrong principal, expiry or retracted supporting evidence')
        if not grant.versions.matches(versions,('state','frame','ontology','isa','task','evidence')):raise ContractError('VersionMismatch','scope is bound to exact semantic versions')
        return grant
    def narrow(self,parent_id,child):
        if parent_id not in self.grants or parent_id in self.revoked:raise ContractError('CapabilityDenied','parent authority absent')
        parent=self.grants[parent_id]
        fields=('readable_slots','writable_slots','allowed_types','target_views','update_parameters','macro_capabilities','transaction_writes')
        if any(not getattr(child,k)<=getattr(parent,k) for k in fields) or child.expires_step>parent.expires_step or child.principal!=parent.principal or child.session_id!=parent.session_id or child.immutable_goal_digest!=parent.immutable_goal_digest or child.versions!=parent.versions or not parent.evidence_handles<=child.evidence_handles:raise ContractError('ScopeEscalation','derived grant may only narrow and retain all provenance dependencies')
        if child.capability_id in self.grants:raise ContractError('ScopeEscalation','grant id immutable')
        self.grants[child.capability_id]=child;self.parents[child.capability_id]=parent_id;return child
    def revoke(self,capability_id):
        self.revoked.add(capability_id)
        changed=True
        while changed:
            children={child for child,parent in self.parents.items() if parent in self.revoked}-self.revoked
            changed=bool(children);self.revoked|=children

class ScopedStateStore:
    def __init__(self,cells,aliases=()):
        self.cells={c.slot_id:c for c in cells};self.aliases=dict(aliases)
        if len(self.cells)!=len(cells) or len(self.aliases)!=len(aliases) or set(self.aliases)&set(self.cells):raise ContractError('AliasConflict','unique canonical cells and nonshadowing aliases')
        for alias in self.aliases:self.canonical(alias)
    def canonical(self,name):
        seen=set()
        while name in self.aliases:
            if name in seen:raise ContractError('AliasCycle','cyclic alias cannot authorize access')
            seen.add(name);name=self.aliases[name]
        if name not in self.cells:raise ContractError('UnboundReference','canonical slot not registered')
        return name
    def apply(self,effect,authority,*,principal,step,versions,new_version,withdrawn=frozenset(),budget=StepBudget()):
        grant=authority.resolve(effect.capability_id,principal=principal,step=step,versions=versions,withdrawn=withdrawn)
        reads=tuple(self.canonical(s) for s in effect.read_slots);writes=tuple(self.canonical(s) for s in effect.write_slots)
        if len(set(reads))!=len(reads) or len(set(writes))!=len(writes):raise ContractError('AliasConflict','same canonical slot cannot appear twice through aliases')
        if not set(reads)<=grant.readable_slots or not set(writes)<=grant.writable_slots or effect.type_tag not in grant.allowed_types:raise ContractError('CapabilityDenied','canonical access exceeds installed grant')
        cells=[self.cells[s] for s in set(reads+writes)]
        if any(c.session_id!=authority.session_id or c.type_tag!=effect.type_tag or c.version!=versions.state for c in cells):raise ContractError('CrossSessionReference','cell type/session/state version differs')
        if new_version==versions.state:raise ContractError('VersionConflict','effect must advance written cell version')
        x=tuple(v for key in reads for v in self.cells[key].value);lengths=[len(self.cells[key].value) for key in writes]
        meter=budget.meter();meter.dimension(len(x));meter.consume(steps=len(reads)+len(writes))
        if len(effect.matrix[0])!=len(x) or len(effect.matrix)!=sum(lengths):raise ContractError('ShapeMismatch','typed read/write flatten axes do not match affine effect')
        output=add(matvec(effect.matrix,x),effect.bias);updated=dict(self.cells);offset=0
        for key,length in zip(writes,lengths):
            value=output[offset:offset+length];offset+=length
            if effect.operation=='add_affine':value=add(self.cells[key].value,value)
            updated[key]=replace(self.cells[key],value=value,version=new_version)
        audit=EffectAudit(grant.capability_id,principal,reads,writes,tuple((k,self.cells[k].version) for k in writes),tuple((k,new_version) for k in writes),'committed_local_effect')
        # No mutation until every type, capability and arithmetic operation has succeeded.
        self.cells=updated;return audit

def check_objective_view(grant,view,*,view_id):
    if view.goal_digest!=grant.immutable_goal_digest or view_id not in grant.target_views:raise ContractError('GoalMutation','H32 may change only authorized internal view, never external goal')
    return view

def check_update_rule(grant,rule):
    from latent_comm.mechanisms.h38_plasticity.reference import validate_rule
    validate_rule(rule.ast)
    if not set(rule.writable_groups)<=grant.update_parameters:raise ContractError('WriteScopeViolation','H38 parameter whitelist exceeds grant')
    return rule

def check_transaction(grant,transaction):
    if transaction.external_effects or not {w.key for w in transaction.writes}<=grant.transaction_writes:raise ContractError('WriteScopeViolation','H39 write set exceeds installed local capabilities')
    return transaction

def check_macro(grant,*,required_capabilities,expanded_read_slots,expanded_write_slots):
    if not set(required_capabilities)<=grant.macro_capabilities or not set(expanded_read_slots)<=grant.readable_slots or not set(expanded_write_slots)<=grant.writable_slots:raise ContractError('CapabilityDenied','H40 macro expansion cannot hide additional primitive effects')
    return True
