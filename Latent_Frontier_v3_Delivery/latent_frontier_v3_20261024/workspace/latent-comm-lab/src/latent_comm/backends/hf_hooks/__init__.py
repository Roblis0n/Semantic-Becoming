"""Scoped residual hooks with strict shape checks and finally cleanup."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from latent_comm.core import TensorSpec,ContractError,ErrorCode
from latent_comm.safety.policy import require_research_action

_ACTIVE_MODELS=ContextVar('latent_comm_active_residual_models',default=frozenset())
@dataclass(frozen=True)
class ResidualInjection:
    layer_path: str
    tensor: object
    spec: TensorSpec
    output_layout: str
    def validate_declaration(self,capabilities) -> None:
        capabilities.require('residual');self.spec.require_axes(('batch','sequence','channel'))
        if self.layer_path not in capabilities.residual_layer_paths or self.output_layout!=capabilities.residual_output_layout:
            raise ContractError(ErrorCode.UNSUPPORTED_CAPABILITY,'layer or output layout not source-bound')
        if self.spec.axis('channel')!=capabilities.hidden_size:raise ContractError(ErrorCode.INVALID_SHAPE,'residual width differs from capability contract')

@contextmanager
def residual_injections(model,injections: tuple[ResidualInjection,...], *, capabilities):
    require_research_action('model_forward')
    key=id(model);active=_ACTIVE_MODELS.get()
    if key in active:raise ContractError(ErrorCode.CONFLICT,'nested injection into the same model is explicitly unsupported')
    token=_ACTIVE_MODELS.set(active|{key});handles=[]
    try:
        for injection in injections:
            injection.validate_declaration(capabilities)
            module=model.get_submodule(injection.layer_path)
            def hook(_module,_inputs,output,injection=injection):
                hidden=output if injection.output_layout=='tensor' else output[0]
                injection.spec.check_shape(tuple(hidden.shape));injection.spec.check_shape(tuple(injection.tensor.shape))
                delta=injection.tensor.to(device=hidden.device,dtype=hidden.dtype)
                changed=hidden+delta
                return changed if injection.output_layout=='tensor' else (changed,*output[1:])
            handles.append(module.register_forward_hook(hook))
        yield
    finally:
        for handle in reversed(handles):handle.remove()
        _ACTIVE_MODELS.reset(token)

def forward_with_residuals(model,injections,inputs: dict, *, capabilities):
    require_research_action('model_forward')
    from latent_comm.backends.capabilities import ModelInputs
    if not isinstance(inputs,ModelInputs):raise ContractError(ErrorCode.ROLE_LEAKAGE,'residual forward requires role-bound ModelInputs')
    with residual_injections(model,tuple(injections),capabilities=capabilities):
        return model(**inputs.kwargs())
