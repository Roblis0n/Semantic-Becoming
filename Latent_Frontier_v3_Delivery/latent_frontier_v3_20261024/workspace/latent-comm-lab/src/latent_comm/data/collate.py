"""Model collators accept role-only batches, never full WorldRecord objects."""
from dataclasses import dataclass
from collections.abc import Mapping
from latent_comm.core import RoleView,Visibility,ContractError,ErrorCode
from .records import SupervisionView
from latent_comm.packets.envelope import LiveTensor

@dataclass(frozen=True)
class RoleBatch:
    role: Visibility
    views: tuple[RoleView,...]
    def __post_init__(self) -> None:
        if self.role not in {Visibility.SENDER,Visibility.RECEIVER} or not self.views:
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'role batch must be nonempty sender/receiver views')
        if any(not isinstance(v,RoleView) or v.role!=self.role for v in self.views):
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'mixed role or full record passed to model collator')
        schemas={(tuple(sorted(v.features)),tuple(sorted(v.public_task))) for v in self.views}
        if len(schemas)!=1:raise ContractError(ErrorCode.INVALID_SCHEMA,'inconsistent role feature/public schema')
        if len({v.versions for v in self.views})!=1:raise ContractError(ErrorCode.VERSION_MISMATCH,'batch mixes semantic versions')
    def model_records(self) -> tuple[Mapping[str,object],...]:
        return tuple({'public_task':v.public_task,'features':v.features} for v in self.views)

@dataclass(frozen=True)
class EncodedRoleBatch:
    """Live encoder outputs attached to validated role inputs, not serialized values."""
    origin: RoleBatch
    field: str
    tensors: tuple[LiveTensor,...]
    def __post_init__(self) -> None:
        if not isinstance(self.origin,RoleBatch) or len(self.tensors)!=len(self.origin.views):
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'encoded batch needs aligned validated role origins')
        if any(self.field not in v.features for v in self.origin.views):
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'encoded field was not whitelisted')
        required_role=self.origin.role.value+'_feature'
        for live in self.tensors:
            live.spec.require_axes(('item','channel'))
            if live.spec.semantic_role!=required_role:
                raise ContractError(ErrorCode.ROLE_LEAKAGE,'encoded tensor has wrong semantic role')

@dataclass(frozen=True)
class SupervisionBatch:
    views: tuple[SupervisionView,...]
    def __post_init__(self) -> None:
        if any(not isinstance(v,SupervisionView) for v in self.views):raise ContractError(ErrorCode.INVALID_SCHEMA,'supervision batch needs supervision-only values')

@dataclass(frozen=True)
class PaddedField:
    values: tuple[tuple[float,...],...]
    valid_mask: tuple[tuple[bool,...],...]
    lengths: tuple[int,...]
    padding_value: float
    axes: tuple[str,str] = ('batch','item')

def collate_finite_numeric(batch: RoleBatch,field: str, *, padding_value: float=0.0) -> PaddedField:
    from latent_comm.core.finite import finite_scalar
    if not isinstance(batch,RoleBatch) or len(batch.views)>64:raise ContractError(ErrorCode.ROLE_LEAKAGE,'finite collator requires bounded RoleBatch')
    rows=[]
    for v in batch.views:
        if field not in v.features:raise ContractError(ErrorCode.INVALID_SCHEMA,'collator field not in whitelisted features')
        row=tuple(finite_scalar(x) for x in v.features[field])
        if len(row)>64:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'finite collation dimension exceeded')
        rows.append(row)
    width=max(map(len,rows));pad=finite_scalar(padding_value)
    return PaddedField(tuple(r+(pad,)*(width-len(r)) for r in rows),tuple((True,)*len(r)+(False,)*(width-len(r)) for r in rows),tuple(map(len,rows)),pad)

def collate_tensor(batch: RoleBatch | EncodedRoleBatch,field: str, *, device: str,dtype_name: str,padding_value: float=0.0) -> dict:
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    # Identity-preserving tensor path: pad and stack without detach, JSON or list conversion.
    if isinstance(batch,EncodedRoleBatch):
        if field!=batch.field:raise ContractError(ErrorCode.ROLE_LEAKAGE,'encoded field mismatch')
        tensors=[live.value for live in batch.tensors]
    elif isinstance(batch,RoleBatch):
        tensors=[torch.as_tensor(v.features[field],device=device,dtype=getattr(torch,dtype_name)) for v in batch.views]
        tensors=[t.unsqueeze(-1) if t.ndim==1 else t for t in tensors]
    else:
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'tensor collator requires a validated or encoded role batch')
    if any(t.ndim!=2 for t in tensors):raise ContractError(ErrorCode.INVALID_SHAPE,'encoded role tensors require item/channel axes')
    lengths=[t.shape[0] for t in tensors]
    padded=torch.nn.utils.rnn.pad_sequence(tensors,batch_first=True,padding_value=padding_value).to(device=device,dtype=getattr(torch,dtype_name))
    positions=torch.arange(padded.shape[1],device=device).unsqueeze(0)
    mask=positions<torch.tensor(lengths,device=device).unsqueeze(1)
    return {'values':padded,'valid_mask':mask,'axes':('batch','item','channel')}
