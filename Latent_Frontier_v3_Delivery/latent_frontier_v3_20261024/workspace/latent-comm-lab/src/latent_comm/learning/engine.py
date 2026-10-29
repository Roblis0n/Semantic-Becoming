"""Finite configured future training loop, AdamW, exact resume and owner freezing.

No invocation in the current task can pass the research gate. A stage provides a
concrete forward_roles(sender, receiver, maximum_unroll) and loss computation.
Only the latter receives SupervisionBatch. Data sources expose cursor-aware next
batch access; no world metadata or IDs are passed to a model.
"""
from pathlib import Path
import json
import random
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import LossValue
from latent_comm.safety.policy import require_research_action
from .contracts import validate_parameter_ownership,validate_phase,validate_batch_versions


def _optimizer_pack(optimizer,named):
    require_research_action('model_train')
    import torch
    reverse={id(p):name for name,p in named.items()};tensors={};scalars={}
    for parameter,state in optimizer.state.items():
        if id(parameter) not in reverse:raise ContractError(ErrorCode.SCOPE_VIOLATION,'optimizer state has an unowned parameter')
        name=reverse[id(parameter)]
        for key,value in state.items():
            entry=name+'/'+key
            if isinstance(value,torch.Tensor):tensors[entry]=value
            elif value is None or isinstance(value,(bool,int,float,str)):scalars[entry]=value
            else:raise ContractError(ErrorCode.INVALID_SCHEMA,'optimizer contains unsupported opaque state')
    return tensors,scalars


def _optimizer_restore(optimizer,named,tensors,scalars):
    require_research_action('model_train')
    active={id(p) for group in optimizer.param_groups for p in group['params']}
    for key,value in {**scalars,**tensors}.items():
        name,field=key.rsplit('/',1)
        if name not in named:raise ContractError(ErrorCode.VERSION_MISMATCH,'optimizer parameter name no longer exists')
        if id(named[name]) in active:optimizer.state[named[name]][field]=value


def _tuple_tree(x):return tuple(_tuple_tree(v) for v in x) if isinstance(x,list) else x


def train(stage,source,plan,root: Path,*,resume=None):
    require_research_action('model_train')
    import torch
    from latent_comm.backends.storage import CheckpointMetadata,save_tensor_checkpoint,load_tensor_checkpoint
    groups=stage.parameter_groups();frozen=stage.frozen_parameters()
    named=validate_parameter_ownership(groups,frozen)
    for phase in plan.phases:validate_phase(phase,groups,stage.loss_specs)
    # Keep receiver operations differentiable even while its base parameters are frozen.
    for parameter in frozen.values():parameter.requires_grad_(False)
    step=0;phase_index=0;phase_step=0;cursor=None;carry_tensors={};carry_scalars={}
    if resume is not None:
        parameters,carry_tensors,saved,meta=load_tensor_checkpoint(root,resume['record'],resume['sha256'],expected_model_digest=plan.model_manifest_digest,expected_data_digest=plan.data_manifest_digest,device=stage.device)
        if meta['config_digest']!=plan.config_digest or meta['run_id']!=plan.run_id:raise ContractError(ErrorCode.VERSION_MISMATCH,'resume recipe/run differs')
        if set(parameters)-{'rng.cpu'}-{k for k in parameters if k.startswith('rng.cuda.')}!=set(named):raise ContractError(ErrorCode.VERSION_MISMATCH,'checkpoint owner names changed')
        # Tensor data copy occurs only at the serialization boundary, never on a live edge.
        with torch.no_grad():
            for name,parameter in named.items():
                if parameter.shape!=parameters[name].shape:raise ContractError(ErrorCode.INVALID_SHAPE,'checkpoint parameter shape changed')
                parameter.copy_(parameters[name])
        torch.set_rng_state(parameters['rng.cpu'].cpu())
        cuda_states=[parameters[k].cpu() for k in sorted(parameters) if k.startswith('rng.cuda.')]
        if cuda_states:torch.cuda.set_rng_state_all(cuda_states)
        random.setstate(_tuple_tree(saved['python_rng']))
        carry_scalars=saved['optimizer'];step=meta['step'];phase_index=saved['phase_index'];phase_step=saved['phase_step'];cursor=saved['data_cursor']
    source.seek(cursor)
    journal=root/'research_runs'/plan.run_id/'training.jsonl';journal.parent.mkdir(parents=True,exist_ok=True)
    last_checkpoint=None
    def log(record):
        with journal.open('a',encoding='utf-8') as stream:stream.write(json.dumps(record,sort_keys=True,allow_nan=False)+'\n');stream.flush()
    for pi in range(phase_index,len(plan.phases)):
        phase=plan.phases[pi];active=set(phase.parameter_owners)
        for owner,parameters in groups.items():
            for parameter in parameters.values():parameter.requires_grad_(owner in active)
        optimizer=torch.optim.AdamW([{'params':list(groups[owner].values()),'name':owner} for owner in phase.parameter_owners],lr=phase.learning_rate,weight_decay=phase.weight_decay)
        _optimizer_restore(optimizer,named,carry_tensors,carry_scalars)
        start=phase_step if pi==phase_index else 0
        for local_step in range(start,phase.optimizer_steps):
            optimizer.zero_grad(set_to_none=True);losses=[];observed=[]
            for micro in range(plan.accumulation):
                batch=source.next_batch()
                validate_batch_versions(batch,stage.versions,getattr(stage,'required_version_axes',None))
                # The forward never receives the training batch or supervisor object.
                output=stage.forward_roles(batch.sender,batch.receiver,maximum_unroll=plan.maximum_unroll)
                terms=stage.losses(output,batch.supervision)
                if set(dict(phase.loss_weights))-set(terms):raise ContractError(ErrorCode.INVALID_SCHEMA,'stage omitted a configured loss')
                weighted=[];row={}
                for name,weight in phase.loss_weights:
                    value=terms[name]
                    if isinstance(value,LossValue):
                        if not value.skipped:raise ContractError(ErrorCode.INVALID_SCHEMA,'finite LossValue cannot impersonate a live objective')
                        row[name]={'skipped':True,'reason':value.reason};continue
                    if value.ndim!=0 or not bool(torch.isfinite(value)):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'nonfinite or non-scalar loss')
                    row[name]={'value':float(value.detach().cpu()),'weight':weight}
                    if weight:weighted.append(weight*value)
                if weighted:losses.append(torch.stack(weighted).sum())
                observed.append(row);cursor=batch.cursor_after
            if losses:
                # Normalize by valid microbatches, not requested accumulation when empty.
                objective=torch.stack(losses).mean()
                if objective.ndim!=0 or not bool(torch.isfinite(objective)):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'weighted aggregate objective is nonfinite')
                if not objective.requires_grad:raise ContractError(ErrorCode.CONFLICT,'phase contains only nondifferentiable objective values')
                objective.backward()
                parameters=[p for group in optimizer.param_groups for p in group['params']]
                gradient_norm=torch.nn.utils.clip_grad_norm_(parameters,plan.gradient_clip,error_if_nonfinite=True)
                if not any(p.grad is not None for p in parameters):raise ContractError(ErrorCode.CONFLICT,'objective has no owned gradient path')
                optimizer.step();status='updated'
            else:gradient_norm=None;status='skipped_zero_valid'
            step+=1;log({'step':step,'phase':phase.name,'status':status,'objectives':observed,'gradient_norm':None if gradient_norm is None else float(gradient_norm.detach().cpu()),'cursor':cursor})
            if step%plan.checkpoint_interval==0 or local_step+1==phase.optimizer_steps:
                fresh_tensors,fresh_scalars=_optimizer_pack(optimizer,named);carry_tensors.update(fresh_tensors);carry_scalars.update(fresh_scalars)
                tensors={**named,'rng.cpu':torch.get_rng_state()}
                if torch.cuda.is_initialized():tensors.update({f'rng.cuda.{i:04d}':s for i,s in enumerate(torch.cuda.get_rng_state_all())})
                metadata=CheckpointMetadata(plan.run_id,step,plan.model_manifest_digest,plan.data_manifest_digest,plan.config_digest,stage.versions,tuple(sorted(groups)))
                last_checkpoint=save_tensor_checkpoint(root,'research_runs/'+plan.run_id+'/checkpoints',tensors,metadata,carry_tensors,{'optimizer':carry_scalars,'python_rng':random.getstate(),'phase_index':pi,'phase_step':local_step+1,'data_cursor':cursor})
        phase_step=0
    return {'optimizer_steps':step,'last_checkpoint':last_checkpoint,'research_state':'EXECUTED_ONLY_UNDER_FUTURE_AUTHORIZATION'}
