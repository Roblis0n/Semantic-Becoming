from dataclasses import replace
from itertools import combinations
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import topological_order,finite_scalar
from .types import SearchResult
ARITY={'input':0,'identity':1,'negate':1,'sum':2,'product':2}
def validate_graph(graph,*,budget=StepBudget()):
    nodes={n.node_id:n for n in graph.nodes}
    if len(nodes)!=len(graph.nodes) or graph.output_node not in nodes:raise ContractError('InvalidGraph','unique nodes and bound output')
    if len(set(graph.edges))!=len(graph.edges):raise ContractError('DuplicateEdge','duplicate port edge')
    order=topological_order(tuple(nodes),tuple(sorted({(a,b) for a,b,_ in graph.edges})))
    for name,node in nodes.items():
        ports=[p for _,b,p in graph.edges if b==name]
        if sorted(ports)!=list(range(ARITY[node.operation])):raise ContractError('TypeViolation','each typed input port exactly once',path=name)
        if any(nodes[a].output_type!=node.input_type for a,b,_ in graph.edges if b==name):raise ContractError('TypeViolation','edge type mismatch')
    cost=sum(n.cost for n in graph.nodes)+len(graph.edges)
    if cost>budget.max_steps:raise ContractError('BudgetExhausted','graph execution cost exceeds bound')
    return order,cost

def evaluate_graph(graph,inputs,*,budget=StepBudget()):
    order,cost=validate_graph(graph,budget=budget);nodes={n.node_id:n for n in graph.nodes};values={};meter=budget.meter();meter.consume(steps=cost)
    if set(inputs)!={n.node_id for n in graph.nodes if n.operation=='input'}:raise ContractError('RoleLeakage','only exact declared input nodes supplied')
    for name in order:
        op=nodes[name].operation;args=[values[a] for a,b,_ in sorted(graph.edges,key=lambda x:x[2]) if b==name]
        if op=='input':value=inputs[name]
        elif op=='identity':value=args[0]
        elif op=='negate':value=-args[0]
        elif op=='sum':value=args[0]+args[1]
        elif op=='product':value=args[0]*args[1]
        values[name]=finite_scalar(value)
    return values[graph.output_node],cost

def search_graphs(candidates,fixtures,*,budget=StepBudget()):
    if len(candidates)>64 or len(fixtures)>64:raise ContractError('BudgetExhausted','candidate/case cap')
    best=None;best_loss=None;checked=[];cost=0;meter=budget.meter()
    for graph in candidates:
        try:
            _,graph_cost=validate_graph(graph,budget=budget);meter.consume(steps=graph_cost*len(fixtures),cases=1)
        except ContractError as e:
            if e.failure.code=='BudgetExhausted':return SearchResult(best,best_loss,tuple(checked),cost,False,'search_budget_not_optimality')
            raise
        errors=[]
        for inputs,target in fixtures:
            prediction,used=evaluate_graph(graph,inputs,budget=budget);cost+=used;errors.append((prediction-target)**2)
        if not errors:raise ContractError('NoSupervision','finite search fixture requires declared targets, never fabricated model scores')
        loss=sum(errors)/len(errors);checked.append(graph.candidate_id)
        if best_loss is None or loss<best_loss:best=graph;best_loss=loss
    return SearchResult(best,best_loss,tuple(checked),cost,True,'best_in_declared_candidate_set')
def enumerate_edge_subsets(template,optional_edges,*,max_candidates,budget=StepBudget()):
    meter=budget.meter();out=[]
    for size in range(len(optional_edges)+1):
        for subset in combinations(optional_edges,size):
            meter.consume(steps=1,cases=1)
            candidate=replace(template,candidate_id=template.candidate_id+':'+str(meter.cases),edges=template.edges+tuple(subset))
            try:validate_graph(candidate,budget=budget)
            except ContractError:continue
            out.append(candidate)
            if len(out)>=max_candidates:return tuple(out),False
    return tuple(out),True
def compile_registered_graph(recipe):
    from latent_comm.compiler.pipeline import compile_recipe
    return compile_recipe(recipe,source='H18 registered topology')
