"""L06: bifurcation, reciprocal trajectories, public boundaries and scale closure."""
from dataclasses import dataclass,replace
from latent_comm.core import ContractError,ErrorCode
from latent_comm.core.learning import LossSpec,GradientEstimator,LossValue,masked_tensor_mean
from latent_comm.learning.source import tensor_field,tensor_target
from latent_comm.learning.contracts import validate_parameter_ownership
from latent_comm.safety.policy import require_research_action

def spec(name,formula,owners,units,inputs=(),mask='declared valid targets'):
    return LossSpec(name,formula,'sum of masked per-'+units+' errors','number of valid '+units,mask,'skip_with_reason',tuple(owners),tuple(inputs),(),GradientEstimator.EXACT,units)

def public_horizon(view,maximum_unroll):
    steps=view.public_task['steps'];dt=view.public_task['dt']
    if type(steps) is not int or not 1<=steps<=maximum_unroll or not isinstance(dt,(int,float)) or dt<=0:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'positive public time step and bounded horizon required')
    import math
    if not math.isfinite(dt):raise ContractError(ErrorCode.OUT_OF_DOMAIN,'finite timestep required')
    return steps,float(dt)

@dataclass(frozen=True)
class TrajectoryOutput:
    trajectories: tuple
    readouts: tuple
    extras: tuple

class ReciprocalStage:
    def __init__(self,coupling,dissipation,reader,versions,*,device='cpu'):
        require_research_action('model_initialize')
        self.coupling=coupling;self.dissipation=dissipation;self.reader=reader;self.versions=versions;self.device=device
        self.loss_specs=(spec('terminal','mean((trajectory_reader-target_terminal)^2)',('coupling','dissipation_factor','trajectory_reader'),'coordinates'),spec('trajectory','mean((predicted_path-supervised_path)^2)',('coupling','dissipation_factor'),'trajectory coordinates'),spec('stability','mean(relu(norm2_next-norm2_current)^2)',('coupling','dissipation_factor'),'steps'))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'coupling':{'skew_correction':self.coupling},'dissipation_factor':{'factor_delta':self.dissipation},'trajectory_reader':{'window_logits':self.reader}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h33_reciprocal.adapter import tensor_integrate
        trajectories=[];readouts=[];extras=[]
        for s,r in zip(sender.views,receiver.views):
            steps,dt=public_horizon(r,min(maximum_unroll,self.reader.numel()-1))
            if s.features['mode'] not in {'rotation','dissipation'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'reciprocal stage excludes public boundary-only family')
            damping=float(s.features['damping'])
            if damping<0:raise ContractError(ErrorCode.OUT_OF_DOMAIN,'negative damping is not the declared dissipative family')
            initial=torch.as_tensor(r.features['start'],device=self.device,dtype=self.coupling.dtype).reshape(1,2)
            raw=self.coupling+self.coupling.new_tensor([[0.,-1.],[1.,0.]])
            factor=self.dissipation+torch.eye(2,device=self.device,dtype=self.coupling.dtype)*damping**.5
            trajectory,readout=tensor_integrate(initial,factor.unsqueeze(0),raw.unsqueeze(0),dt=dt,steps=steps,readout_weights=self.reader[:steps+1].unsqueeze(0))
            path=trajectory.squeeze(0);trajectories.append(path);readouts.append(readout.squeeze(0));extras.append(path[1:].square().sum(-1)-path[:-1].square().sum(-1))
        return TrajectoryOutput(tuple(trajectories),tuple(readouts),tuple(extras))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        values={'terminal':[],'trajectory':[],'stability':[]}
        for path,readout,increments,view in zip(output.trajectories,output.readouts,output.extras,supervision.views):
            target=torch.as_tensor(view.targets['trajectory'],device=self.device,dtype=path.dtype)
            if target.shape!=path.shape:raise ContractError(ErrorCode.INVALID_SHAPE,'trajectory target length/coordinates differ')
            declared=view.valid_masks.get('trajectory');mask=torch.ones_like(target,dtype=torch.bool) if declared is None else torch.as_tensor(declared,device=self.device,dtype=torch.bool).reshape_as(target)
            for name,value in (('terminal',masked_tensor_mean((readout-target[-1]).square(),mask[-1])),('trajectory',masked_tensor_mean((path-target).square(),mask)),('stability',masked_tensor_mean(increments.clamp_min(0).square(),mask[1:].all(-1)&mask[:-1].all(-1)))):
                if not isinstance(value,LossValue):values[name].append(value)
        return {name:torch.stack(rows).mean() if rows else LossValue(0.,0.,None,True,'no valid trajectory records') for name,rows in values.items()}

class BoundaryStage:
    """W06 public-goal continuous H34 branch: finite quadratic boundary solve."""
    def __init__(self,transition_drift,goal_scale,versions,*,device='cpu'):
        require_research_action('model_initialize')
        self.transition_drift=transition_drift;self.goal_scale=goal_scale;self.versions=versions;self.device=device
        self.loss_specs=(spec('transition','mean((z[t+1]-z[t]-drift[t])^2)',('transition_messages','backward_constraint_encoder'),'transition coordinates'),spec('boundary','mean((encoded_public_goal-public_goal)^2)',('backward_constraint_encoder',),'boundary coordinates'),spec('task','mean((path-supervised_path)^2)',('transition_messages','backward_constraint_encoder'),'trajectory coordinates'))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'transition_messages':{'time_drift':self.transition_drift},'backward_constraint_encoder':{'goal_scale':self.goal_scale}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        paths=[];readouts=[];extras=[]
        for s,r in zip(sender.views,receiver.views):
            steps,dt=public_horizon(r,min(maximum_unroll,self.transition_drift.shape[0]))
            if s.features['mode']!='boundary' or r.public_task['terminal_source'] not in {'public_goal','public_boundary'}:raise ContractError(ErrorCode.ROLE_LEAKAGE,'only explicitly public boundary targets can constrain the forward')
            if steps<2:raise ContractError(ErrorCode.INVALID_SHAPE,'trainable interior requires at least two transitions')
            start=torch.as_tensor(r.features['start'],device=self.device,dtype=self.goal_scale.dtype);goal=torch.as_tensor(r.public_task['terminal'],device=self.device,dtype=self.goal_scale.dtype);encoded_goal=goal*self.goal_scale
            drift=self.transition_drift[:steps]*dt
            # D maps free interior nodes to time differences; endpoint terms are
            # constants from the public task, never future observations.
            d=torch.zeros(steps,steps-1,device=self.device,dtype=drift.dtype)
            for k in range(steps):
                if k>0:d[k,k-1]-=1
                if k<steps-1:d[k,k]+=1
            endpoint=torch.zeros_like(drift);endpoint[0]=-start;endpoint[-1]=encoded_goal
            interior=torch.linalg.solve(d.T@d,d.T@(drift-endpoint))
            path=torch.cat((start.unsqueeze(0),interior,goal.unsqueeze(0)),0)
            paths.append(path);readouts.append(encoded_goal-goal);extras.append(path[1:]-path[:-1]-drift)
        return TrajectoryOutput(tuple(paths),tuple(readouts),tuple(extras))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        values={'transition':[],'boundary':[],'task':[]}
        for path,boundary,residual,view in zip(output.trajectories,output.readouts,output.extras,supervision.views):
            target=torch.as_tensor(view.targets['trajectory'],device=self.device,dtype=path.dtype)
            if target.shape!=path.shape:raise ContractError(ErrorCode.INVALID_SHAPE,'boundary target shape mismatch')
            declared=view.valid_masks.get('trajectory');mask=torch.ones_like(target,dtype=torch.bool) if declared is None else torch.as_tensor(declared,device=self.device,dtype=torch.bool).reshape_as(target)
            values['transition'].append(residual.square().mean());values['boundary'].append(boundary.square().mean());task=masked_tensor_mean((path-target).square(),mask)
            if not isinstance(task,LossValue):values['task'].append(task)
        return {k:torch.stack(v).mean() if v else LossValue(0.,0.,None,True,'no valid boundary records') for k,v in values.items()}

@dataclass(frozen=True)
class ScaleOutput:
    coarse: object
    closure: object
    detail: object
    predicted_detail: object
    task: object
    task_reference: object

class ScaleStage:
    def __init__(self,coarse_delta,macro,lift,detail_memory,task_reader,versions,*,device='cpu'):
        require_research_action('model_initialize')
        self.coarse_delta=coarse_delta;self.macro=macro;self.lift=lift;self.detail_memory=detail_memory;self.task_reader=task_reader;self.versions=versions;self.device=device
        self.loss_specs=(spec('commute','mean((C Fmicro z-Fmacro C z)^2)',('coarse_map','macro_dynamics'),'macro coordinates'),spec('task','mean((reader(Cz)-public_Cz)^2)',('coarse_map','task_reader'),'macro observables'),spec('residual','mean((memory(Cz)-(z-lift(Cz)))^2)',('coarse_map','lift','detail_memory'),'micro coordinates'))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'coarse_map':{'delta':self.coarse_delta},'macro_dynamics':{'matrix':self.macro},'lift':{'matrix':self.lift},'detail_memory':{'matrix':self.detail_memory},'task_reader':{'matrix':self.task_reader}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h35_renormalization.adapter import tensor_multiscale,tensor_memory_step
        c=tensor_field(sender,'coarse_map',device=self.device);f=tensor_field(sender,'micro_dynamics',device=self.device);z=tensor_field(receiver,'microstate',device=self.device)
        if maximum_unroll<1:raise ContractError(ErrorCode.BUDGET_EXHAUSTED,'one scale transition required')
        rows=[]
        for ci,fi,zi in zip(c,f,z):
            learned=ci+self.coarse_delta;coarse,detail,residual=tensor_multiscale(zi.unsqueeze(0),learned,self.lift,fi,torch.zeros_like(zi),self.macro,self.macro.new_zeros(self.macro.shape[0]))
            # Residual remains a live object; no claim of an inverse from coarse.
            next_coarse,next_detail=tensor_memory_step(coarse,detail,self.lift,fi,torch.zeros_like(zi),learned)
            rows.append((coarse.squeeze(0),residual.squeeze(0),next_detail.squeeze(0),(next_coarse@self.detail_memory.T).squeeze(0),(coarse@self.task_reader.T).squeeze(0),ci@zi))
        columns=tuple(torch.stack(v) for v in zip(*rows));return ScaleOutput(*columns)
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        # Public coarse observables define the anchoring task, not hidden labels.
        return {'commute':masked_tensor_mean(output.closure.square(),torch.ones_like(output.closure,dtype=torch.bool)),'task':masked_tensor_mean((output.task-output.task_reference).square(),torch.ones_like(output.task,dtype=torch.bool)),'residual':masked_tensor_mean((output.predicted_detail-output.detail).square(),torch.ones_like(output.detail,dtype=torch.bool))}

@dataclass(frozen=True)
class BifurcationOutput:
    readout: object
    before: object
    after: object
    events: object

class BifurcationStage:
    """H28 dedicated control-path schema, distinct from W06 rotation records."""
    def __init__(self,potential,readout,migration,trigger_weight,trigger_bias,versions,*,device='cpu'):
        require_research_action('model_initialize')
        self.potential=potential;self.readout=readout;self.migration=migration;self.trigger_weight=trigger_weight;self.trigger_bias=trigger_bias;self.versions=versions;self.device=device
        self.loss_specs=(spec('task','mean((readout(trajectory)-task_target)^2)',('potential_coefficients','readout'),'task coordinates'),spec('migration','mean((readout(Mz)-readout(z))^2)',('structure_map','potential_coefficients','readout'),'behavior coordinates'),spec('event','mean(CE(trigger(stability),event_label))',('trigger_policy','potential_coefficients'),'events'))
        validate_parameter_ownership(self.parameter_groups(),{})
    def parameter_groups(self):return {'potential_coefficients':{'raw_cubic':self.potential},'readout':{'matrix':self.readout},'structure_map':{'matrix':self.migration},'trigger_policy':{'weight':self.trigger_weight,'bias':self.trigger_bias}}
    def frozen_parameters(self):return {}
    def forward_roles(self,sender,receiver,*,maximum_unroll):
        require_research_action('model_forward')
        import torch
        from latent_comm.mechanisms.h28_bifurcation.adapter import tensor_dynamics,tensor_migrate
        initial=tensor_field(receiver,'initial_state',device=self.device);control=tensor_field(sender,'control_path',device=self.device)
        if not torch.equal(control,control[:1].expand_as(control)):raise ContractError(ErrorCode.INVALID_SCHEMA,'one public control grid per homogeneous batch required')
        dt=float(receiver.views[0].public_task['dt']);steps=int(receiver.views[0].public_task['steps_per_control'])
        if any(v.public_task['dt']!=dt or v.public_task['steps_per_control']!=steps for v in receiver.views):raise ContractError(ErrorCode.INVALID_SCHEMA,'mixed integrators require separate batches')
        coefficient=torch.nn.functional.softplus(self.potential)+1e-6
        trajectory=tensor_dynamics(initial,control[0],coefficient,dt=dt,steps_per_control=steps,max_unroll=maximum_unroll);terminal=trajectory[:,-1];after=tensor_migrate(terminal,self.migration)
        stability=control[:,-1].unsqueeze(-1)-3*coefficient*terminal.square();features=torch.cat((terminal,stability),-1)
        return BifurcationOutput(terminal@self.readout.T,terminal@self.readout.T,after@self.readout.T,torch.nn.functional.linear(features,self.trigger_weight,self.trigger_bias))
    def losses(self,output,supervision):
        require_research_action('model_forward')
        import torch
        target,mask=tensor_target(supervision,'task_target',device=self.device);events,event_mask=tensor_target(supervision,'structure_event',device=self.device,dtype='int64')
        return {'task':masked_tensor_mean((output.readout-target).square(),mask),'migration':masked_tensor_mean((output.after-output.before).square(),torch.ones_like(output.after,dtype=torch.bool)),'event':masked_tensor_mean(torch.nn.functional.cross_entropy(output.events,events,reduction='none'),event_mask)}

def build_stage(variant,versions,*,maximum_horizon=16,state_dim=2,observations=2,device='cpu',dtype='float32'):
    require_research_action('model_initialize')
    import torch
    def p(value):return torch.nn.Parameter(torch.as_tensor(value,device=device,dtype=getattr(torch,dtype)))
    if maximum_horizon<2:raise ContractError(ErrorCode.INVALID_SHAPE,'at least two time slots required')
    if variant=='reciprocal':return ReciprocalStage(p(torch.zeros(2,2)),p(torch.zeros(2,2)),p(torch.zeros(maximum_horizon+1)),versions,device=device)
    if variant=='boundary':return BoundaryStage(p(torch.zeros(maximum_horizon,2)),p(torch.ones(2)),versions,device=device)
    if variant=='scales':return ScaleStage(p(torch.zeros(2,4)),p(torch.eye(2)),p([[1.,0.],[1.,0.],[0.,1.],[0.,1.]]),p(torch.zeros(4,2)),p(torch.eye(2)),versions,device=device)
    if variant=='bifurcation':return BifurcationStage(p(torch.zeros(state_dim)),p(torch.eye(observations,state_dim)),p(torch.eye(state_dim)),p(torch.zeros(3,2*state_dim)),p(torch.zeros(3)),versions,device=device)
    raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'unknown dynamics/scales stage')
