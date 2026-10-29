from dataclasses import replace, asdict
import json, math
from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import vector, matvec, transpose, add, scale, matmul, inverse
from .types import OperatorPacket, OperatorChain

def identity(dimension,domain,versions):
    return OperatorChain((),dimension,domain,domain,versions)
def compose(first,second):
    if first.codomain!=second.domain or first.dimension!=second.dimension or not first.versions.matches(second.versions,('frame','ontology','isa')):
        raise ContractError('TypeViolation','ordered composition needs matching boundary; insert explicit change_frame first')
    return OperatorChain(first.operators+second.operators,first.dimension,first.domain,second.codomain,first.versions)
def chain(packet):
    return OperatorChain((packet,),len(packet.U),packet.domain,packet.codomain,packet.versions)
def apply(state,packet,*,actor='receiver',step=0,budget=StepBudget()):
    program=chain(packet) if isinstance(packet,OperatorPacket) else packet
    z=vector(state);meter=budget.meter();meter.dimension(len(z))
    if len(z)!=program.dimension:raise ContractError('DimensionMismatch','state coordinate dimension')
    trace=[]
    for op in program.operators:
        meter.consume(steps=1);op.scope.check(actor,writes=frozenset({'Z'}),step=step)
        q=add(matvec(transpose(op.V),z),op.bias)
        h=tuple(math.tanh(v) if op.nonlinearity=='tanh' else max(v,0) if op.nonlinearity=='relu' else v for v in q)
        delta=scale(matvec(op.U,h),op.alpha);z=add(z,delta);trace.append(delta)
    return z,tuple(trace)
def restrict_scope(packet,scope):
    return replace(packet,scope=packet.scope.restrict(scope))
def change_frame(packet,gauge,target_versions):
    # For nonlinear T'=G T G^-1: U'=GU, V'=G^-T V, bias unchanged.
    target_versions.require('frame','ontology','isa')
    if not packet.versions.matches(target_versions,('ontology','isa')):raise ContractError('MigrationRequired','frame transport cannot reinterpret ontology or ISA')
    ginv=inverse(gauge)
    return replace(packet,U=matmul(gauge,packet.U),V=matmul(transpose(ginv),packet.V),versions=target_versions)
def serialize(packet):
    obj=asdict(packet);obj['scope']={k:sorted(v) if isinstance(v,frozenset) else v for k,v in obj['scope'].items()}
    return json.dumps(obj,sort_keys=True,allow_nan=False)
