from latent_comm.core import LossSpec, GradientEstimator, ContractError
LEDGER=(
    LossSpec('task','stage normalized task loss after dedicated mechanism','sum valid task losses','valid task count','stage-normalized valid tasks','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('task_loss',),(),GradientEstimator.EXACT,'task instances'),
    LossSpec('reconstruction','mean squared reconstruct(state)-state','sum of valid terms','count of valid terms','encoded_valid[:,None].expand_as(state)','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('reconstructed', 'state'),(),GradientEstimator.EXACT,'state coordinates'),
    LossSpec('effect','mean behavioral anchor squared error','sum of valid terms','count of valid terms','effect_valid','differentiable_zero',('mechanism_writer', 'mechanism_reader'),('effect',),(('target', 'target_or_return'),),GradientEstimator.EXACT,'behavior coordinates'),
    LossSpec('cycle','mean declared overlap cycle squared error','sum of valid terms','count of valid terms','overlap_valid','differentiable_zero',('mechanism_reader',),('cycled', 'original'),(),GradientEstimator.EXACT,'chart elements'),
    LossSpec('variance','mean relu(min_std-std(valid chart encodings))','sum coordinate standard-deviation hinge penalties','chart dimension; active only with >=2 valid rows','encoded_valid; at least two rows','differentiable_zero',('mechanism_writer',),('encoded',),(),GradientEstimator.EXACT,'chart coordinates'),
)

def tensor_losses(effect,target,effect_valid,cycled,original,overlap_valid,encoded,encoded_valid,reconstructed,state,*,task_loss,min_std=.1):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from latent_comm.core.learning import masked_tensor_mean as mean
    effect_loss=mean((effect-target.detach()).square(),effect_valid,zero_valid_policy='differentiable_zero')
    cycle=mean((cycled-original).square(),overlap_valid,zero_valid_policy='differentiable_zero')
    selected=encoded[encoded_valid.bool()]
    variance=(min_std-selected.var(0,unbiased=False).add(1e-8).sqrt()).relu().mean() if selected.shape[0]>=2 else encoded.sum()*0.
    reconstruction=mean((reconstructed-state).square(),encoded_valid[:,None].expand_as(state),zero_valid_policy='differentiable_zero')
    return {'task':task_loss,'total':task_loss+effect_loss+cycle+variance+reconstruction,'effect':effect_loss,'cycle':cycle,'variance':variance,'reconstruction':reconstruction}
