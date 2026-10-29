from latent_comm.core import ContractError

def tensor_predict(anchor,base,A,B,query,radius):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if anchor.shape!=query.shape or anchor.ndim!=2 or base.ndim!=2 or A.ndim!=3 or B.ndim!=3:raise ContractError('DimensionMismatch','explicit batch/condition/output/rank axes')
    n,d=anchor.shape;r=A.shape[-1]
    if A.shape!=(n,base.shape[1],r) or B.shape!=(n,d,r) or radius.shape!=(n,):raise ContractError('DimensionMismatch','response factor layout')
    if not bool(torch.isfinite(radius).all()) or bool((radius<=0).any()):raise ContractError('OutOfDomain','positive finite local validity radius')
    delta=query-anchor;refresh=delta.norm(dim=-1)>radius
    prediction=base+torch.bmm(A,torch.bmm(B.transpose(1,2),delta.unsqueeze(-1))).squeeze(-1)
    return prediction,~refresh  # Caller must mask or refresh; never treat invalid extrapolation as an answer.

def acquire_response(response_function,anchor,directions,*,method,step=1e-3):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if method not in ('jvp','finite_difference') or directions.ndim!=3 or directions.shape[:2]!=anchor.shape:raise ContractError('DimensionMismatch','directions [B,d,r] and declared derivative method')
    if step<=0:raise ContractError('OutOfDomain','finite difference step must be positive')
    if anchor.ndim!=2 or directions.shape[-1]<1 or directions.shape[-1]>anchor.shape[-1] or not bool(torch.isfinite(directions).all()):raise ContractError('InvalidDirections','finite nonempty rank no greater than condition dimension')
    gram=directions.transpose(-1,-2)@directions
    identity=torch.eye(directions.shape[-1],device=directions.device,dtype=directions.dtype).expand_as(gram)
    if not torch.allclose(gram,identity,atol=1e-6,rtol=1e-6):raise ContractError('InvalidDirections','response factors require an orthonormal direction basis; arbitrary directions need an explicit dual')
    columns=[]
    for v in directions.unbind(-1):
        if method=='jvp':columns.append(torch.func.jvp(response_function,(anchor,),(v,))[1])
        else:columns.append((response_function(anchor+step*v)-response_function(anchor-step*v))/(2*step))
    return response_function(anchor),torch.stack(columns,dim=-1),directions

def predict_response_factors(features,weight,bias,*,condition_dim,output_dim,rank):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    width=(output_dim+condition_dim)*rank+output_dim+1
    if features.ndim!=2 or weight.shape!=(width,features.shape[1]) or bias.shape!=(width,):raise ContractError('DimensionMismatch','response head factor layout')
    raw=torch.nn.functional.linear(features,weight,bias);n=raw.shape[0];a=output_dim*rank;b=a+condition_dim*rank
    return raw[:,a:b].reshape(n,condition_dim,rank),raw[:,:a].reshape(n,output_dim,rank),raw[:,b:b+output_dim],torch.nn.functional.softplus(raw[:,-1])+1e-6
