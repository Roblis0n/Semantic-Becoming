import math
from latent_comm.core import ContractError,StepBudget
from latent_comm.core.finite import *

def covers(chart,state,task,model_revision):
    return not chart.invalidated and model_revision==chart.model_revision and task in chart.task_family and len(state)==len(chart.center) and norm(sub(state,chart.center))<=chart.radius

def route(charts,state,*,task,model_revision,mode='hard'):
    if not charts or len(charts)>64 or mode not in ('hard','soft'):raise ContractError('InvalidRouting','bounded chart set and routing mode')
    valid=[c for c in charts if covers(c,state,task,model_revision)]
    if not valid:raise ContractError('NoMatchingChart','no valid covered task/model chart; do not extrapolate')
    scores=[-norm(sub(state,c.center))**2/c.radius**2 for c in valid]
    if mode=='hard':return ((valid[max(range(len(valid)),key=lambda i:scores[i])],1.),)
    weights=[math.exp(s-max(scores)) for s in scores];total=sum(weights)
    return tuple((c,w/total) for c,w in zip(valid,weights))

def encode(chart,state,*,task,model_revision):
    if not covers(chart,state,task,model_revision):raise ContractError('OutOfDomain','chart outside local declared domain')
    return matvec(chart.read_map,state)

def transition(state,edge,source,target,*,task):
    if (edge.source_chart,edge.target_chart,edge.source_frame,edge.target_frame)!=(source.chart_id,target.chart_id,source.versions.frame,target.versions.frame) or task not in edge.tasks:raise ContractError('UnboundTransition','chart IDs/frame versions/task must match')
    if len(state)!=len(source.read_map) or len(edge.mapping)!=len(target.read_map):raise ContractError('DimensionMismatch','partial transition coordinate axes')
    return add(matvec(edge.mapping,state),edge.bias)

def write_back(chart,local):return matvec(chart.write_map,local)
def cycle_error(state,path,charts,*,task,budget=StepBudget()):
    meter=budget.meter();z=vector(state)
    if not path or path[0].source_chart!=path[-1].target_chart:raise ContractError('OpenCycle','cycle regularizer requires a closed declared path')
    if any(a.target_chart!=b.source_chart or a.target_frame!=b.source_frame for a,b in zip(path,path[1:])):raise ContractError('DisconnectedCycle','cycle edges must form a continuous chart/frame path')
    for edge in path:
        meter.consume(steps=1);z=transition(z,edge,charts[edge.source_chart],charts[edge.target_chart],task=task)
    return norm(sub(z,state))
def inverse_transition(edge):
    if edge.information_loss!='none':raise ContractError('IrrecoverableDetail','write map is not an inverse')
    return inverse(edge.mapping)
class AtlasRegistry:
    def __init__(self):self._charts={}
    def register(self,chart):
        if chart.chart_id in self._charts:raise ContractError('VersionConflict','new revisions require new chart IDs')
        self._charts[chart.chart_id]=chart
    def get(self,chart_id):
        if chart_id not in self._charts:raise ContractError('UnknownChart',chart_id)
        return self._charts[chart_id]
