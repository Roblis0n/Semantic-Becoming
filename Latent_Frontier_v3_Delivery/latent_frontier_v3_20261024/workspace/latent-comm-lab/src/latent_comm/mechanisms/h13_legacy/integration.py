from dataclasses import replace
from latent_comm.core import ContractError
from latent_comm.core.finite import matvec
from .reference import fork

def bifurcate_structure(branch,transition,*,new_branch_id):
    if branch.concept_structure!=transition.old_structure or branch.versions.state!=transition.source_version:raise ContractError('VersionMismatch','H28 structure/source snapshot must match branch')
    child=fork(branch,new_branch_id)
    return replace(child,base=tuple((slot,matvec(transition.mapping,value)) for slot,value in child.base),concept_structure=transition.new_structure,versions=replace(child.versions,state=transition.target_version))

def rewrite_question_branch(branch,transform,*,new_branch_id):
    from latent_comm.mechanisms.h29_questions.reference import check_relation
    if branch.versions.task!=transform.source.version:raise ContractError('VersionMismatch','H29 source task version differs')
    witness=check_relation(transform)
    if not witness.sound:raise ContractError('RelationUnproven','branch answer backtranslation must be sound')
    return replace(fork(branch,new_branch_id),question_transform=transform.target.question_id,versions=replace(branch.versions,task=transform.target.version)),witness

def advance_transaction_snapshot(branch,commit):
    if commit.status!='committed' or branch.transaction_snapshot!=commit.before_digest:raise ContractError('VersionConflict','H39 commit must match exact branch snapshot')
    return replace(branch,transaction_snapshot=commit.after_digest)
