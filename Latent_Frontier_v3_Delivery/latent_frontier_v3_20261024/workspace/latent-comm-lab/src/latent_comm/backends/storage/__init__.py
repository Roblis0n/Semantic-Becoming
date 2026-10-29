"""Safe tensor-only persistence, explicit device placement and typed checkpoints."""
from dataclasses import dataclass,asdict
import hashlib
import json
import os
from pathlib import Path
import tempfile
import re
import uuid
from latent_comm.core import ContractError,ErrorCode,VersionSet
from latent_comm.packets.storage import resolve_workspace_path,save_finite_json,load_finite_json
from latent_comm.safety.policy import require_research_action

@dataclass(frozen=True)
class DevicePlan:
    device: str
    dtype: str
    offload_device: str | None=None
    max_bytes: int | None=None
    def __post_init__(self):
        if self.device!='cpu' and not (self.device.startswith('cuda:') and self.device[5:].isdigit()):raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'device must be explicit cpu or cuda:index, never auto allocation')
        if self.dtype not in {'float32','float64','float16','bfloat16'}:raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unbound precision')
        if self.max_bytes is not None and (type(self.max_bytes) is not int or self.max_bytes<=0):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'memory budget must be positive')

@dataclass(frozen=True)
class CheckpointMetadata:
    run_id: str
    step: int
    model_manifest_digest: str
    data_manifest_digest: str
    config_digest: str
    versions: VersionSet
    parameter_owners: tuple[str,...]
    replay_requires_recompute: bool=True
    def __post_init__(self):
        if type(self.step) is not int or self.step<0 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',self.run_id) or not self.replay_requires_recompute:raise ContractError(ErrorCode.INVALID_SCHEMA,'checkpoint must identify step and recomputation boundary')


def place_model(model,plan: DevicePlan):
    require_research_action('model_initialize')
    import torch
    if plan.device.startswith('cuda:') and not torch.cuda.is_available():raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'declared CUDA device unavailable')
    estimated=sum(p.numel()*p.element_size() for p in model.parameters())
    if plan.max_bytes is not None and estimated>plan.max_bytes:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'parameters exceed explicit device memory budget')
    return model.to(device=plan.device,dtype=getattr(torch,plan.dtype))

def save_tensor_checkpoint(root: Path,relative_directory: str,tensors: dict,metadata: CheckpointMetadata,optimizer_tensors: dict | None=None,optimizer_scalars: dict | None=None) -> dict:
    require_research_action('model_train')
    from safetensors.torch import save_file
    directory=resolve_workspace_path(root,relative_directory);directory.mkdir(parents=True,exist_ok=True)
    # A generation pointer is committed only after both content files are durable.
    generation=f'{metadata.run_id}-{metadata.step}-{uuid.uuid4().hex}'
    target=directory/(generation+'.safetensors');fd,temp=tempfile.mkstemp(dir=directory,suffix='.safetensors');os.close(fd)
    values={name:value.detach().cpu().contiguous().clone() for name,value in tensors.items()}
    values.update({'optimizer.'+name:value.detach().cpu().contiguous().clone() for name,value in (optimizer_tensors or {}).items()})
    try:
        save_file(values,temp)
        with open(temp,'rb') as stream:os.fsync(stream.fileno())
        digest=hashlib.sha256(Path(temp).read_bytes()).hexdigest();os.replace(temp,target)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    record={'metadata':asdict(metadata),'tensor_file':target.name,'tensor_sha256':digest,'optimizer_scalars':optimizer_scalars or {},'format':'safetensors_plus_json','no_autograd_graph_persisted':True}
    record_name=relative_directory+'/'+generation+'.json';record_digest=save_finite_json(root,record_name,record)
    save_finite_json(root,relative_directory+'/CURRENT.json',{'record':record_name,'sha256':record_digest})
    return {'record':record_name,'sha256':record_digest,'tensor_sha256':digest}

def load_tensor_checkpoint(root: Path,record_path: str,record_digest: str, *, expected_model_digest: str,expected_data_digest: str,device: str):
    require_research_action('model_load')
    from safetensors.torch import load_file
    record=load_finite_json(root,record_path,record_digest);meta=record['metadata']
    if meta['model_manifest_digest']!=expected_model_digest or meta['data_manifest_digest']!=expected_data_digest:raise ContractError(ErrorCode.VERSION_MISMATCH,'checkpoint model/data identity changed')
    parent=Path(record_path).parent;path=resolve_workspace_path(root,(parent/record['tensor_file']).as_posix())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=record['tensor_sha256']:raise ContractError(ErrorCode.CONFLICT,'checkpoint tensor digest mismatch')
    values=load_file(str(path),device=device)
    parameters={k:v for k,v in values.items() if not k.startswith('optimizer.')};optimizer={k[len('optimizer.'):]:v for k,v in values.items() if k.startswith('optimizer.')}
    return parameters,optimizer,record['optimizer_scalars'],meta
