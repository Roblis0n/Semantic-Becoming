"""Loss definitions are first-class; tensor evaluation remains policy-gated."""
from dataclasses import dataclass
from enum import Enum
from .errors import ContractError, ErrorCode

class GradientEstimator(str,Enum):
    EXACT='exact'
    SECOND_ORDER='second_order'
    FIRST_ORDER='first_order_approximation'
    POLICY_GRADIENT='policy_gradient'
    STRAIGHT_THROUGH='biased_straight_through'
    ENUMERATION='finite_enumeration'
    NONDIFFERENTIABLE='nondifferentiable'

@dataclass(frozen=True)
class LossSpec:
    name: str
    mathematical_definition: str
    numerator: str
    denominator: str
    valid_mask: str
    zero_valid_policy: str
    parameter_owners: tuple[str,...]
    requires_grad_inputs: tuple[str,...]
    stop_gradient_edges: tuple[tuple[str,str],...]
    estimated_or_exact: GradientEstimator
    normalization_units: str
    def __post_init__(self) -> None:
        if self.zero_valid_policy not in {'skip_with_reason','differentiable_zero','error'}:
            raise ContractError(ErrorCode.INVALID_SCHEMA,'loss needs explicit empty-batch policy')
        if not all([self.name,self.mathematical_definition,self.numerator,self.denominator,self.valid_mask,self.normalization_units]):
            raise ContractError(ErrorCode.INVALID_SCHEMA,'incomplete gradient/loss ledger')
        if set(self.requires_grad_inputs)&{x[0] for x in self.stop_gradient_edges}:
            raise ContractError(ErrorCode.CONFLICT,'required gradient input is also stopped')

@dataclass(frozen=True)
class LossValue:
    numerator: float
    denominator: float
    value: float | None
    skipped: bool
    reason: str

def finite_masked_mean(values: tuple[float,...],mask: tuple[bool,...], *, zero_valid_policy: str='skip_with_reason') -> LossValue:
    from .finite import finite_scalar
    if len(values)!=len(mask) or len(values)>64 or any(type(x) is not bool for x in mask):
        raise ContractError(ErrorCode.INVALID_SHAPE,'finite loss values/mask mismatch')
    for x in values:finite_scalar(x)
    selected=[v for v,m in zip(values,mask,strict=True) if m]
    if not selected:
        if zero_valid_policy=='error':raise ContractError(ErrorCode.OUT_OF_DOMAIN,'zero valid terms')
        if zero_valid_policy not in {'skip_with_reason','differentiable_zero'}:raise ContractError(ErrorCode.INVALID_SCHEMA,'unknown zero-valid policy')
        return LossValue(0.0,0.0,0.0 if zero_valid_policy=='differentiable_zero' else None,True,'zero valid terms')
    total=sum(selected);return LossValue(total,float(len(selected)),total/len(selected),False,'valid terms')

def masked_tensor_mean(values: object,mask: object, *, zero_valid_policy: str='skip_with_reason') -> object:
    from latent_comm.safety.policy import require_research_action
    require_research_action('model_forward')
    import torch
    if values.shape!=mask.shape:raise ContractError(ErrorCode.INVALID_SHAPE,'loss/mask shapes differ')
    valid=mask.to(dtype=torch.bool)
    count=valid.sum()
    if int(count.detach().cpu())==0:
        if zero_valid_policy=='error':raise ContractError(ErrorCode.OUT_OF_DOMAIN,'zero valid terms')
        if zero_valid_policy=='differentiable_zero':return values.sum()*0.0
        if zero_valid_policy=='skip_with_reason':return LossValue(0.0,0.0,None,True,'zero valid terms')
        raise ContractError(ErrorCode.INVALID_SCHEMA,'unknown zero-valid policy')
    return values.masked_select(valid).sum()/count.to(values.dtype)
