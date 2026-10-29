"""Structured failures preserve kind, location and recoverable obligations."""
from dataclasses import dataclass
from enum import Enum

class ErrorCode(str, Enum):
    UNSUPPORTED_CAPABILITY = 'UnsupportedCapability'
    OUT_OF_DOMAIN = 'OutOfDomain'
    CONFLICT = 'Conflict'
    NON_IDENTIFIABLE = 'NonIdentifiable'
    BUDGET_EXHAUSTED = 'BudgetExhausted'
    UNBOUND_REFERENCE = 'UnboundReference'
    VERSION_MISMATCH = 'VersionMismatch'
    SCOPE_VIOLATION = 'ScopeViolation'
    ROLE_LEAKAGE = 'RoleLeakage'
    INVALID_SHAPE = 'InvalidShape'
    INVALID_SCHEMA = 'InvalidSchema'
    RESEARCH_FORBIDDEN = 'ResearchForbidden'
    MIGRATION_CONFLICT = 'MigrationConflict'

@dataclass(frozen=True)
class Failure:
    code: str
    message: str
    path: str = ''
    recoverable: bool = False
    obligations: tuple[str, ...] = ()

class ContractError(ValueError):
    def __init__(self, code: str | ErrorCode, message: str, path: str = '', *, recoverable: bool = False, obligations: tuple[str, ...] = ()) -> None:
        self.failure = Failure(code.value if isinstance(code, ErrorCode) else code, message, path, recoverable, obligations)
        super().__init__(f'{self.failure.code} at {path or "<root>"}: {message}')

def require(condition: bool, code: str | ErrorCode, message: str, path: str = '') -> None:
    if not condition:
        raise ContractError(code, message, path)
