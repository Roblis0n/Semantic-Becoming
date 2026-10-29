from dataclasses import dataclass,field
from decimal import Decimal,InvalidOperation
from latent_comm.core import ContractError,VersionSet,ObjectRef
@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    value: str
    unit: str
    source: ObjectRef
    origin_role: str
    target_ref: ObjectRef | None=field(init=False,default=None)
    def __post_init__(self):
        from latent_comm.core.views import FORBIDDEN_FIELDS
        if not self.name or self.name in FORBIDDEN_FIELDS or self.origin_role not in ('public','sender','receiver'):raise ContractError('RoleLeakage','supervision/identifiers cannot enter exact symbol inputs')
        if self.kind not in ('decimal','entity','reference','relation') or not isinstance(self.value,str):raise ContractError('InvalidSymbol','closed exact symbol types and string payloads')
        try:self.value.encode('utf-8',errors='strict')
        except UnicodeError as error:raise ContractError('InvalidUTF8','invalid Unicode scalar') from error
        if self.kind=='decimal':
            try:number=Decimal(self.value)
            except InvalidOperation as error:raise ContractError('InvalidDecimal','decimal syntax') from error
            if not number.is_finite() or len(number.as_tuple().digits)>64 or abs(number.as_tuple().exponent)>32 or not self.unit:raise ContractError('InvalidDecimal','bounded exact decimal and unit required')
        if self.kind in ('entity','reference'):object.__setattr__(self,'target_ref',ObjectRef(self.value))
        if self.kind=='relation' and self.value not in ('equivalent','sufficient','necessary','partial','heuristic'):raise ContractError('InvalidRelation','closed answer-relation enum')
@dataclass(frozen=True)
class SymbolPacket:
    symbols: tuple[Symbol,...]
    latent_handle: ObjectRef
    versions: VersionSet
    def __post_init__(self):
        if len(self.symbols)>64 or len({s.name for s in self.symbols})!=len(self.symbols):raise ContractError('DuplicateSymbol','finite unique exact fields')
        self.versions.require('ontology','task','evidence')
@dataclass(frozen=True)
class DualReadout:
    exact_symbols: tuple[Symbol,...]
    latent_value: object
    conflicts: tuple[str,...]
    status: str
