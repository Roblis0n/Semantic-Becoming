"""Private typed branches with ancestry and optimistic, non-averaging merges."""
from dataclasses import dataclass
from types import MappingProxyType
from latent_comm.core import ContractError, StepBudget
from .transactions import Snapshot, Transaction
from .journal import canonical, sha256

@dataclass
class Branch:
    branch_id: str
    parent: str | None
    transaction: Transaction
    state: str = 'open'

class BranchManager:
    def __init__(self,store, *, scope,actor,budget=StepBudget()):
        self.store=store;self.scope=scope;self.actor=actor;self.meter=budget.meter();self.branches={}
    @staticmethod
    def _view(tx):
        cells=dict(tx.snapshot.cells);versions=dict(tx.snapshot.versions)
        for key,cell in tx.pending.items():
            if cell is None:cells.pop(key,None)
            else:cells[key]=cell
            versions[key]=versions.get(key,0)+1
        return Snapshot(tx.snapshot.revision,MappingProxyType(cells),MappingProxyType(versions),sha256(canonical({'cells':{k:v.to_dict() for k,v in cells.items()},'versions':versions})))
    def _get(self,branch_id):
        if branch_id not in self.branches:raise ContractError('UnboundReference','branch missing',branch_id)
        branch=self.branches[branch_id]
        if branch.state!='open':raise ContractError('BranchClosed',branch.state,branch_id)
        return branch
    def fork(self,branch_id, *, parent=None):
        if not isinstance(branch_id,str) or not branch_id or branch_id in self.branches:raise ContractError('DuplicateBranch','branch IDs must be unique')
        snapshot=self.store.snapshot() if parent is None else self._view(self._get(parent).transaction)
        self.meter.consume(branches=1)
        branch=Branch(branch_id,parent,Transaction(self.store,snapshot,self.scope,self.actor,'branch:'+branch_id));self.branches[branch_id]=branch;return branch
    def ancestry(self,branch_id):
        if branch_id not in self.branches:raise ContractError('UnboundReference','branch missing')
        path=[];current=branch_id
        for _ in range(len(self.branches)):
            path.append(current);parent=self.branches[current].parent
            if parent is None:return tuple(reversed(path))
            current=parent
        raise ContractError('BranchCycle','invalid ancestry')
    def merge(self,branch_id):
        branch=self._get(branch_id);tx=branch.transaction
        if any(b.parent==branch_id and b.state=='open' for b in self.branches.values()):raise ContractError('OpenChildBranch','merge or discard children first')
        if branch.parent is None:
            result=tx.commit();branch.state='committed';return result
        parent=self._get(branch.parent);current=self._view(parent.transaction)
        for key in tx.read_versions:
            if current.cells.get(key)!=tx.snapshot.cells.get(key) or current.versions.get(key,0)!=tx.snapshot.versions.get(key,0):raise ContractError('VersionConflict','parent changed after child fork',key)
        # Validate every write before publishing the new parent draft.
        backup=dict(parent.transaction.pending);reads=dict(parent.transaction.read_versions);migrations=list(parent.transaction.migrations);prior_state=parent.transaction.state
        try:
            for key in tx.read_versions:parent.transaction._observe(key)
            for key,cell in tx.pending.items():
                if cell is None:parent.transaction.delete(key)
                else:parent.transaction.write(key,cell.value(),type_name=cell.type_name,component=cell.component,versions=cell.versions,migration=dict(tx.migrations).get(key,dict(parent.transaction.migrations).get(key)))
        except BaseException:
            parent.transaction.pending=backup;parent.transaction.read_versions=reads;parent.transaction.migrations=migrations;parent.transaction.state=prior_state;raise
        branch.state='merged';tx.state='merged';return {'branch':branch_id,'parent':branch.parent,'writes':tuple(sorted(tx.pending)),'termination_reason':'merged_private_draft'}
    def discard(self,branch_id):
        branch=self._get(branch_id)
        if any(b.parent==branch_id and b.state=='open' for b in self.branches.values()):raise ContractError('OpenChildBranch','discard children first')
        result=branch.transaction.abort('branch_discarded');branch.state='discarded';return result
