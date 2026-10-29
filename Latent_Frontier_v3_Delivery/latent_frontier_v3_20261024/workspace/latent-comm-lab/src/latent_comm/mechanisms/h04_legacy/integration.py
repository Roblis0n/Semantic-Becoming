from latent_comm.core import ContractError
from latent_comm.core.finite import eye,matmul,transpose,matvec,inverse,add,scale,sub
from .reference import energy

def field_feasibility_sheaf(field):
    from latent_comm.mechanisms.h26_sheaf.types import LocalDomain,AffineRestriction,Anchor,SheafPacket
    if field.domain=='constant':raise ContractError('DomainCollision','constant feasibility anchor needs a distinct source domain')
    domains=(LocalDomain(field.domain,len(field.anchor)),LocalDomain('constant',1))
    restrictions=tuple(AffineRestriction(s.source_id,field.domain,'constant',s.A,tuple((0.,) for _ in s.b),s.b,tuple(sorted(s.evidence_support))) for s in field.sources)
    return SheafPacket(domains,restrictions,(Anchor('constant',0,0.),),field.versions.state)

def field_as_centered_dynamics(field,*,step_size,steps):
    from latent_comm.mechanisms.h33_reciprocal.types import DynamicsPacket
    d=len(field.anchor);h=[list(row) for row in eye(d)];h=[[2*field.anchor_strength*x for x in row] for row in h];rhs=scale(field.anchor,2*field.anchor_strength)
    for source in field.sources:
        gram=matmul(transpose(source.A),source.A);h=[[h[i][j]+source.temperature*gram[i][j] for j in range(d)] for i in range(d)];rhs=add(rhs,scale(matvec(transpose(source.A),source.b),source.temperature))
    center=matvec(inverse(tuple(tuple(r) for r in h)),rhs);zero=tuple((0.,)*d for _ in range(d))
    return DynamicsPacket(tuple(tuple(r) for r in h),zero,sub(field.anchor,center),field.versions.state,step_size,steps,(0,steps+1)),center

def score_trajectory_states(field,trajectory,candidate_coordinates):
    if trajectory.version!=field.versions.state or trajectory.terminal.task_version!=field.versions.task or set(candidate_coordinates)!=set(trajectory.states):raise ContractError('VersionMismatch','H34 public trajectory boundaries and explicit field-state coordinates')
    return tuple((state,energy(field,candidate_coordinates[state])) for state in trajectory.states)
