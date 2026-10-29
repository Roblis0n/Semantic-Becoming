from dataclasses import replace
from latent_comm.core import ContractError
from latent_comm.core.finite import *

def transform_object(obj,transform,*,target_versions):
    if obj.frame!=transform.source:raise ContractError('FrameMismatch','source physical frame must match exactly')
    if not obj.versions.matches(target_versions,('world',)):raise ContractError('WorldMismatch','coordinate transform cannot change world identity')
    if obj.position is None:return replace(obj,frame=transform.target,versions=target_versions)
    A=matrix_scale(transform.linear,transform.unit_scale)
    position=add(matvec(A,obj.position),transform.translation)
    covariance=matmul(matmul(A,obj.covariance),transpose(A))
    return replace(obj,position=position,covariance=covariance,frame=transform.target,versions=target_versions)
def transform_displacement(displacement,transform):return matvec(matrix_scale(transform.linear,transform.unit_scale),displacement)
def apply_synthetic_action(obj,displacement,*,unit,next_timestamp):
    if unit!=obj.frame.unit or next_timestamp<obj.timestamp:raise ContractError('ActionContract','units and causal timestamp must match')
    if obj.position is None:raise ContractError('UnknownPosition','do not act on an occluded zero placeholder')
    return replace(obj,position=add(obj.position,displacement),timestamp=next_timestamp,status='predicted')
def spatial_relation(a,b):
    if a.frame!=b.frame or a.timestamp!=b.timestamp:raise ContractError('UnalignedObservation','physical frame and observation time must align')
    if a.position is None or b.position is None:return 'unknown'
    delta=sub(b.position,a.position)
    return ('right' if delta[0]>0 else 'left' if delta[0]<0 else 'aligned',norm(delta))
