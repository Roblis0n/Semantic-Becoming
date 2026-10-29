"""Independent semantic version axes and exact cache identity."""
from dataclasses import dataclass, fields
import hashlib
import json
from .errors import ContractError, ErrorCode

@dataclass(frozen=True)
class VersionSet:
    schema: str = '3'
    state: str | None = None
    ontology: str | None = None
    isa: str | None = None
    frame: str | None = None
    world: str | None = None
    task: str | None = None
    evidence: str | None = None
    def __post_init__(self) -> None:
        for f in fields(self):
            value = getattr(self,f.name)
            if value is not None and (not isinstance(value,str) or not value.strip()):
                raise ContractError(ErrorCode.VERSION_MISMATCH, f'invalid {f.name} version')
        if self.schema is None: raise ContractError(ErrorCode.VERSION_MISMATCH,'schema version is required')
    def require(self, *axes: str) -> None:
        valid = {f.name for f in fields(self)}
        for axis in axes:
            if axis not in valid or getattr(self,axis) is None:
                raise ContractError(ErrorCode.VERSION_MISMATCH, f'required version is absent: {axis}')
    def matches(self, other: 'VersionSet', axes: tuple[str,...]) -> bool:
        self.require(*axes); other.require(*axes)
        return all(getattr(self,a)==getattr(other,a) for a in axes)
    def as_dict(self) -> dict[str,str | None]:
        return {f.name:getattr(self,f.name) for f in fields(self)}
    def cache_key(self, input_digest: str, deterministic_config: dict[str,object], required_axes: tuple[str,...]) -> str:
        self.require(*required_axes)
        payload={'versions':{a:getattr(self,a) for a in sorted(required_axes)},'input_digest':input_digest,'config':deterministic_config}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
