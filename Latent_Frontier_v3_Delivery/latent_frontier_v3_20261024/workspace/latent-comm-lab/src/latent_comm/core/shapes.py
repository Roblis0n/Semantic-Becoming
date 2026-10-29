"""Named tensor axes with explicit masks, role and gradient ownership."""
from dataclasses import dataclass
from enum import Enum
from .errors import ContractError, ErrorCode

class ValueStatus(str,Enum):
    PRESENT='present'
    UNKNOWN='unknown'
    MISSING='missing'
    CONTRADICTION='contradiction'

@dataclass(frozen=True)
class TensorSpec:
    axes: tuple[str,...]
    shape: tuple[int,...]
    dtype: str
    semantic_role: str
    trainable_owner: str | None
    device_policy: str = 'unallocated'
    mask_axes: tuple[str,...] = ()
    status: ValueStatus = ValueStatus.PRESENT
    def __post_init__(self) -> None:
        if len(self.axes)!=len(self.shape) or len(set(self.axes))!=len(self.axes) or any(not a for a in self.axes):
            raise ContractError(ErrorCode.INVALID_SHAPE,'each dimension needs a unique named axis')
        if any(type(d) is not int or d<0 for d in self.shape):
            raise ContractError(ErrorCode.INVALID_SHAPE,'shape dimensions must be nonnegative integers')
        if not set(self.mask_axes)<=set(self.axes):
            raise ContractError(ErrorCode.INVALID_SHAPE,'mask axes must be tensor axes')
        if self.dtype not in {'float16','float32','float64','bfloat16','int32','int64','bool'}:
            raise ContractError(ErrorCode.INVALID_SHAPE,'unbound dtype')
        if not self.semantic_role: raise ContractError(ErrorCode.INVALID_SHAPE,'semantic role required')
    def require_axes(self, axes: tuple[str,...]) -> None:
        if self.axes != axes: raise ContractError(ErrorCode.INVALID_SHAPE,f'expected axes {axes}, got {self.axes}')
    def check_shape(self, shape: tuple[int,...]) -> None:
        if tuple(shape)!=self.shape: raise ContractError(ErrorCode.INVALID_SHAPE,f'expected {self.shape}, got {shape}')
    def axis(self, name: str) -> int:
        if name not in self.axes: raise ContractError(ErrorCode.INVALID_SHAPE,f'unknown axis {name}')
        return self.shape[self.axes.index(name)]
