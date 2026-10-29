"""L03 small analytic objective checks, not model evaluation or a training loop."""
from latent_comm.core.finite import matrix,vector,matvec,matmul,inverse,sub
from latent_comm.core.learning import finite_masked_mean

def gauge_objectives(state,operator,readout,observed_frame,predicted_map):
    z=vector(state);g=matrix(observed_frame);p=matrix(predicted_map);t=matrix(operator);r=matrix(readout)
    gi=inverse(g);tg=matmul(matmul(g,t),gi);rg=matmul(r,gi)
    covariance=sub(matvec(p,z),matvec(g,z))
    effect=sub(matvec(rg,matvec(tg,matvec(p,z))),matvec(r,matvec(t,z)))
    return {'covariance':finite_masked_mean(tuple(x*x for x in covariance),(True,)*len(covariance)),'effect':finite_masked_mean(tuple(x*x for x in effect),(True,)*len(effect))}
