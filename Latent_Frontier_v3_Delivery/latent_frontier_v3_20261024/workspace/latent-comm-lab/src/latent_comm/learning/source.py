"""Future immutable, cursor-addressed dataset access; never generated in this task."""
from pathlib import Path
import hashlib
import json
from latent_comm.core import ContractError,ErrorCode,RoleView,Visibility,VersionSet
from latent_comm.data.records import SupervisionView
from latent_comm.data.splits import StructureSignature,TemplateAssignment,SplitManifest
from latent_comm.packets.storage import resolve_workspace_path
from latent_comm.data.collate import RoleBatch,SupervisionBatch
from latent_comm.safety.policy import require_research_action
from .contracts import TrainingBatch


def validate_dataset_manifest(manifest: dict) -> SplitManifest:
    """Bind shard declarations to the actual, immutable structural partition.

    The data manifest carries `split_manifest` (assignments, policy_version,
    salt) and `split_manifest_digest` equal to SplitManifest.digest. Merely
    declaring a shard as train is not evidence that its structures belong there.
    """
    try:
        raw=manifest['split_manifest']
        assignments=tuple(TemplateAssignment(StructureSignature(**row['signature']),row['split']) for row in raw['assignments'])
        partition=SplitManifest(assignments,raw['policy_version'],raw['salt'])
        if manifest['split_manifest_digest']!=partition.digest:
            raise ContractError(ErrorCode.CONFLICT,'structural split manifest digest mismatch')
        partition.dataset_manifest(manifest['shards'])
        return partition
    except (KeyError,TypeError,AttributeError) as error:
        raise ContractError(ErrorCode.INVALID_SCHEMA,'dataset manifest requires a bound structural split manifest and shard declarations') from error


def validate_training_record(record: dict,structures,split: str,partition_digest: str) -> None:
    """Verify finite provenance metadata before any role inputs are assembled."""
    try:
        signature=record['structure_signature'];provenance=record['split_provenance']
        if (record['purpose']!='research_data' or record['not_research_data'] is not False or
                provenance['split']!=split or signature not in structures or
                provenance['template_signature']!=signature or provenance['manifest_digest']!=partition_digest):
            raise ContractError(ErrorCode.ROLE_LEAKAGE,'record purpose or structural split provenance mismatch')
    except (KeyError,TypeError) as error:
        raise ContractError(ErrorCode.INVALID_SCHEMA,'record lacks required split provenance') from error


class JsonlSource:
    def __init__(self,root: Path,manifest: dict,batch_size: int,*,split='train'):
        require_research_action('model_train')
        if split!='train' or batch_size<=0:raise ContractError(ErrorCode.ROLE_LEAKAGE,'optimizer source must be a training split with positive batch size')
        self.root=root.resolve();self.manifest=manifest;self.batch_size=batch_size;self.split=split
        self.partition=validate_dataset_manifest(manifest)
        self.identity=hashlib.sha256(json.dumps(manifest,sort_keys=True,allow_nan=False).encode()).hexdigest()
        self.records=[]
        for shard in manifest['shards']:
            if shard['split']!=split:continue
            p=resolve_workspace_path(self.root,shard['path'])
            if hashlib.sha256(p.read_bytes()).hexdigest()!=shard['sha256']:raise ContractError(ErrorCode.CONFLICT,'immutable dataset shard changed')
            # Index byte offsets only, not full dataset contents or a model input cache.
            with p.open('rb') as stream:
                while True:
                    offset=stream.tell();line=stream.readline()
                    if not line:break
                    self.records.append((shard['path'],offset,hashlib.sha256(line).hexdigest(),tuple(shard['structure_signatures'])))
        if not self.records:raise ContractError(ErrorCode.UNBOUND_REFERENCE,'no training shards available')
        self.position=0;self.epoch=0
    def seek(self,cursor):
        require_research_action('model_train')
        if cursor is None:self.position=0;self.epoch=0;return
        if cursor['manifest_digest']!=self.identity or cursor['split']!=self.split or not 0<=cursor['position']<len(self.records) or cursor['epoch']<0:raise ContractError(ErrorCode.VERSION_MISMATCH,'invalid dataset resume cursor')
        self.position=cursor['position'];self.epoch=cursor['epoch']
    def next_batch(self):
        require_research_action('model_train')
        sender=[];receiver=[];supervisor=[]
        for _ in range(self.batch_size):
            relative,offset,line_digest,structures=self.records[self.position]
            path=resolve_workspace_path(self.root,relative)
            with path.open('rb') as stream:stream.seek(offset);line=stream.readline()
            if hashlib.sha256(line).hexdigest()!=line_digest:raise ContractError(ErrorCode.CONFLICT,'indexed dataset record changed')
            record=json.loads(line)
            validate_training_record(record,structures,self.split,self.partition.digest)
            def role(name):
                raw=record[name+'_view'];return RoleView(Visibility(name),raw['public_task'],raw['features'],VersionSet(**raw['versions']))
            sender.append(role('sender'));receiver.append(role('receiver'))
            raw=record['supervision'];supervisor.append(SupervisionView(raw['targets'],{k:tuple(v) for k,v in raw['valid_masks'].items()},raw['source_kind']))
            self.position+=1
            if self.position==len(self.records):self.position=0;self.epoch+=1
        return TrainingBatch(RoleBatch(Visibility.SENDER,tuple(sender)),RoleBatch(Visibility.RECEIVER,tuple(receiver)),SupervisionBatch(tuple(supervisor)),{'manifest_digest':self.identity,'split':self.split,'position':self.position,'epoch':self.epoch})


def tensor_field(batch: RoleBatch,name: str,*,device: str,dtype='float32',public=False):
    require_research_action('model_forward')
    import torch
    if not isinstance(batch,RoleBatch):raise ContractError(ErrorCode.ROLE_LEAKAGE,'field encoder accepts only RoleBatch')
    values=[(view.public_task if public else view.features)[name] for view in batch.views]
    try:return torch.as_tensor(values,device=device,dtype=getattr(torch,dtype))
    except (TypeError,ValueError) as error:raise ContractError(ErrorCode.INVALID_SHAPE,'field encoder requires a homogeneous numeric field') from error


def tensor_target(batch: SupervisionBatch,name: str,*,device: str,dtype='float32'):
    require_research_action('model_forward')
    import torch
    if not isinstance(batch,SupervisionBatch):raise ContractError(ErrorCode.ROLE_LEAKAGE,'target encoder accepts only supervisor batch')
    values=torch.as_tensor([view.targets[name] for view in batch.views],device=device,dtype=getattr(torch,dtype))
    masks=[]
    for view in batch.views:
        declared=view.valid_masks.get(name)
        if declared is None:masks.append(None)
        else:masks.append(declared)
    if all(m is None for m in masks):valid=torch.ones_like(values,dtype=torch.bool)
    elif any(m is None for m in masks):raise ContractError(ErrorCode.INVALID_SCHEMA,'mixed missing/explicit target masks')
    else:
        valid=torch.as_tensor(masks,device=device,dtype=torch.bool)
        if valid.numel()!=values.numel():raise ContractError(ErrorCode.INVALID_SHAPE,'supervision mask has wrong cardinality')
        valid=valid.reshape(values.shape)
    return values,valid
