from decimal import Decimal
from latent_comm.core import ContractError

def checked_answer_relation(symbol,witness):
    if symbol.kind!='relation' or symbol.value!=witness.relation or not witness.sound:raise ContractError('RelationUnproven','H29 exact relation symbol must match checked answer-map witness')
    return symbol.value

def exact_symbol_intervention(symbol,world,*,allowed_variables):
    from latent_comm.mechanisms.h09_legacy.types import Intervention
    modules={m.output:m for m in world.modules}
    if symbol.kind!='decimal' or symbol.name not in modules or modules[symbol.name].unit!=symbol.unit:raise ContractError('UnitConflict','H31 exact symbol must name a typed structural variable')
    value=float(Decimal(symbol.value))
    if Decimal.from_float(value)!=Decimal(symbol.value):raise ContractError('PrecisionLoss','finite SCM float conversion is not exact; explicit approximation adapter required')
    return Intervention(symbol.name,value,symbol.unit,frozenset(allowed_variables),world.version)

def symbol_source_atoms(symbol,provenance):
    atoms=tuple(a for a in provenance.atoms if a.source_handle==symbol.source.value)
    if not atoms:raise ContractError('MissingSource','H48 exact field source handle has no evidence atom')
    return atoms
