from dataclasses import replace
from latent_comm.core import ContractError,StepBudget
from .types import BranchState,MergeResult

def materialize(branch):
    if branch.closed:raise ContractError('BranchClosed','released branch cannot execute')
    return tuple(sorted((dict(branch.base)|dict(branch.updates)).items()))
def fork(branch,new_id):
    return replace(branch,branch_id=new_id,ancestors=branch.ancestors+(branch.branch_id,),base=materialize(branch),updates=(),read_slots=frozenset(),operation_sequence=())
def write_slot(branch,slot,value,*,reads,operation,commutation_class):
    if branch.closed:raise ContractError('BranchClosed','closed branch')
    base=dict(branch.base)
    if slot not in base or len(value)!=len(base[slot]) or not set(reads)<=set(base):raise ContractError('InvalidWrites','slot shape/read scope mismatch')
    return replace(branch,updates=tuple(sorted((dict(branch.updates)|{slot:tuple(value)}).items())),read_slots=branch.read_slots|set(reads),operation_sequence=branch.operation_sequence+(operation,),commutation_class=commutation_class)
def merge(left,right):
    if left.closed or right.closed:raise ContractError('BranchClosed','closed merge participant')
    compatible=bool(left.ancestors) and bool(right.ancestors) and left.branch_id!=right.branch_id and left.base==right.base and left.ancestors==right.ancestors and left.concept_structure==right.concept_structure and left.question_transform==right.question_transform and left.transaction_snapshot==right.transaction_snapshot and left.versions.matches(right.versions,('state','ontology','isa','frame'))
    lw=set(dict(left.updates));rw=set(dict(right.updates));safe=not(lw&rw or lw&right.read_slots or rw&left.read_slots)
    declared=left.commutation_class==right.commutation_class=='independent_slots'
    if not compatible or not safe or not declared:return MergeResult(None,(left,right),'conflict_preserved_not_averaged',left.evidence|right.evidence)
    return MergeResult(tuple(sorted((dict(left.base)|dict(left.updates)|dict(right.updates)).items())),(),'merged_disjoint_commuting',left.evidence|right.evidence)
def release(branch):return replace(branch,closed=True,updates=())
def common_ancestor(left,right):
    shared=[]
    for a,b in zip(left.ancestors,right.ancestors):
        if a!=b:break
        shared.append(a)
    return shared[-1] if shared else None
