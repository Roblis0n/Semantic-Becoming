"""Future tensor/model integration. Source only, never executed in this task.

Batch, coordinate, branch and observation axes are checked by each entry point.
No implicit detachment of receiver inputs; caller supplies physically isolated role views.
"""
from __future__ import annotations
from latent_comm.core import ContractError

def exact_support_tensor(atom_probabilities,assignments,truth_values,*,dependence_mode,declaration_id,joint_probabilities=None):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if dependence_mode not in ('declared_independent','explicit_joint') or not declaration_id:raise ContractError('UnknownDependence','learned link/dependence scores cannot authorize factorization')
    if atom_probabilities.ndim!=2 or assignments.ndim!=2 or assignments.shape[-1]!=atom_probabilities.shape[-1] or truth_values.shape!=(assignments.shape[0],) or assignments.dtype!=torch.bool:raise ContractError('UnsupportedCalibration','unique atom B,A; compiled assignments C,A bool and truth C required')
    if bool(((atom_probabilities<0)|(atom_probabilities>1)).any()):raise ContractError('UnsupportedCalibration','atom marginals outside simplex')
    if dependence_mode=='declared_independent':
        if assignments.shape[0]!=2**assignments.shape[1] or torch.unique(assignments,dim=0).shape[0]!=assignments.shape[0]:raise ContractError('UnsupportedCalibration','independent exact calculation needs complete unique assignment table')
        factors=torch.where(assignments[None,:,:],atom_probabilities[:,None,:],1-atom_probabilities[:,None,:]);weights=factors.prod(-1)
    else:
        if joint_probabilities is None or joint_probabilities.shape!=(atom_probabilities.shape[0],assignments.shape[0]) or bool((joint_probabilities<0).any()) or not bool(torch.allclose(joint_probabilities.sum(-1),torch.ones_like(joint_probabilities.sum(-1)))):raise ContractError('UnsupportedCalibration','explicit normalized joint B,C required')
        if torch.unique(assignments,dim=0).shape[0]!=assignments.shape[0]:raise ContractError('UnsupportedCalibration','joint assignment table has duplicates')
        joint_marginals=joint_probabilities@assignments.to(joint_probabilities.dtype)
        if not bool(torch.allclose(joint_marginals,atom_probabilities)):raise ContractError('UnsupportedCalibration','joint contradicts provided marginal axes')
        weights=joint_probabilities
    return (weights*truth_values.to(weights.dtype)[None,:]).sum(-1)

def source_link_scores(source_features,source_projection,*,temperature=1.):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if source_features.ndim!=3 or source_projection.ndim!=2 or temperature<=0:raise ContractError('MissingSource','B,A,F source features and projection F,Z required')
    features=torch.nn.functional.normalize(source_features@source_projection,dim=-1)
    return torch.einsum('baz,bcz->bac',features,features)/temperature

def train_link_step(features,projection,optimizer,link_targets,link_mask):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_train')
    import torch
    from .losses import link_loss
    from latent_comm.core.learning import LossValue
    actual=[id(p) for g in optimizer.param_groups for p in g['params']]
    if actual!=[id(projection)]:raise ContractError('UnsupportedCalibration','link optimizer owns only source projection, not evidence atoms or declared dependence')
    logits=source_link_scores(features,projection);loss=link_loss(logits,link_targets,link_mask)
    if isinstance(loss,LossValue) and loss.skipped:return {'status':'skipped','reason':loss.reason,'link_loss':loss,'independence_authority':False}
    if loss.ndim!=0 or not bool(torch.isfinite(loss)):raise ContractError('InvalidLoss','finite scalar link objective required')
    optimizer.zero_grad();loss.backward();optimizer.step();return {'status':'updated','link_loss':loss,'independence_authority':False}
