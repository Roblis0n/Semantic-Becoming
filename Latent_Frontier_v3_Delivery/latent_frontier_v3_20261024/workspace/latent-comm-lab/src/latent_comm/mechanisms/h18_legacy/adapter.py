from latent_comm.core import ContractError

def tensor_candidate_outputs(candidates,inputs):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    from .reference import validate_graph
    outputs=[];actual_cost=0
    for graph in candidates:
        order,cost=validate_graph(graph);values={};nodes={n.node_id:n for n in graph.nodes}
        for key in order:
            op=nodes[key].operation;args=[values[a] for a,b,_ in sorted(graph.edges,key=lambda x:x[2]) if b==key]
            if op=='input':out=inputs[key]
            elif op=='identity':out=args[0]
            elif op=='negate':out=-args[0]
            elif op=='sum':out=args[0]+args[1]
            elif op=='product':out=args[0]*args[1]
            values[key]=out
        outputs.append(values[graph.output_node]);actual_cost+=cost
    return torch.stack(outputs,1),actual_cost

def route_candidates(logits,candidates,inputs,*,mode,generator=None):
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if logits.ndim!=1 or logits.numel()!=len(candidates):raise ContractError('DimensionMismatch','one declared graph selection distribution')
    if mode=='soft':
        outputs,cost=tensor_candidate_outputs(candidates,inputs)
        weights=logits.softmax(-1).reshape((1,len(candidates))+(1,)*(outputs.ndim-2))
        return (outputs*weights).sum(1),cost,logits.log_softmax(-1)
    if mode=='sample':
        index=int(torch.multinomial(logits.softmax(-1),1,generator=generator).item());out,cost=tensor_candidate_outputs((candidates[index],),inputs)
        return out[:,0],cost,logits.log_softmax(-1)[index]
    raise ContractError('UnknownEstimator','soft executes all candidates; sample uses policy gradient')
