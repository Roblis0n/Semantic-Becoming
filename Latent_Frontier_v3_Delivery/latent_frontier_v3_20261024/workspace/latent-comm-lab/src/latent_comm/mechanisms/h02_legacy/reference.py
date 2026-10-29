from latent_comm.core import ContractError, StepBudget
from latent_comm.core.finite import *
from .types import ResponseCapsule,ResponsePrediction,QuadraticProgram

def needs_refresh(capsule,delta):
    delta=vector(delta)
    if len(delta)!=len(capsule.anchor):raise ContractError('DimensionMismatch','condition displacement dimension')
    return norm(delta)>capsule.radius

def predict_delta(capsule,delta):
    delta=vector(delta);distance=norm(delta)
    if needs_refresh(capsule,delta):return ResponsePrediction(None,True,distance,'outside declared trust region; refresh anchor')
    return ResponsePrediction(add(capsule.base,matvec(capsule.A,matvec(transpose(capsule.B),delta))),False,distance,capsule.approximation)

def build_capsule(program,anchor,*,directions,step,radius,variables,conditions,versions,budget=StepBudget()):
    if not isinstance(program,QuadraticProgram):raise ContractError('UnsupportedFixture','reference accepts only finite polynomial DSL, not arbitrary model callbacks')
    anchor=vector(anchor);directions=matrix(directions);step=finite_scalar(step)
    if step<=0 or step>radius or len(directions)!=len(anchor):raise ContractError('OutOfDomain','positive in-domain finite difference and [condition,rank] basis')
    # Require orthonormal directions: AB^T is the projected Jacobian, not an unlabelled exact full J.
    gram=matmul(transpose(directions),directions)
    if any(abs(gram[i][j]-float(i==j))>1e-8 for i in range(len(gram)) for j in range(len(gram))):raise ContractError('InvalidBasis','finite difference directions must be orthonormal')
    meter=budget.meter();meter.dimension(len(anchor));columns=[]
    for v in transpose(directions):
        meter.consume(steps=2);columns.append(scale(sub(program.evaluate(add(anchor,scale(v,step))),program.evaluate(sub(anchor,scale(v,step)))),1/(2*step)))
    return ResponseCapsule(anchor,program.evaluate(anchor),transpose(tuple(columns)),directions,radius,variables,conditions,'observational',versions,'central_difference_projected')

def compose_response(first,second):
    if first.base!=second.anchor or not first.versions.matches(second.versions,('world','task')):raise ContractError('UnboundComposition','second anchor must equal first output and world/task match')
    J1=matmul(first.A,transpose(first.B));J2=matmul(second.A,transpose(second.B));J=matmul(J2,J1)
    bound=sum(x*x for row in J1 for x in row)**.5
    radius=min(first.radius,second.radius/bound) if bound else first.radius
    # Radius is a linearized sufficient bound, not a nonlinear guarantee.
    return ResponseCapsule(first.anchor,second.base,J,eye(len(first.anchor)),radius,first.variables,first.observation_conditions+second.observation_conditions,'observational',first.versions,'composed_first_order_error_unbounded_without_curvature')

def predict(capsule,query):
    """Absolute-condition API; predict_delta remains the explicit displacement API."""
    return predict_delta(capsule,sub(vector(query),capsule.anchor))
