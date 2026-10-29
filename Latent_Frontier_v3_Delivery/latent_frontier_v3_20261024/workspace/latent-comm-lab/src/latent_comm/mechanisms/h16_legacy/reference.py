from dataclasses import asdict
from decimal import Decimal
import json
from latent_comm.core import ContractError,ObjectRef,VersionSet,Visibility
from latent_comm.compiler.source import SourceDocument
from .types import *

def parse_symbols(raw):
    if isinstance(raw,bytes):
        try:raw=raw.decode('utf-8',errors='strict')
        except UnicodeError as error:raise ContractError('InvalidUTF8','symbol wire must be UTF-8') from error
    obj=SourceDocument(raw,'H16').value
    if set(obj)!={'symbols','latent_handle','versions'}:raise ContractError('InvalidSchema','no arbitrary command or answer fields')
    symbols=[]
    for row in obj['symbols']:
        if set(row)!={'name','kind','value','unit','source','origin_role'}:raise ContractError('InvalidSchema','symbol fields exact')
        row=dict(row);row['source']=ObjectRef(row['source']);symbols.append(Symbol(**row))
    return SymbolPacket(tuple(symbols),ObjectRef(obj['latent_handle']),VersionSet(**obj['versions']))
def fuse(packet,latent_value,proposed_symbols):
    authoritative={s.name:s for s in packet.symbols};conflicts=[]
    for proposal in proposed_symbols:
        if proposal.name not in authoritative:conflicts.append(proposal.name+':unverified_new_symbol');continue
        original=authoritative[proposal.name]
        equal=original.kind==proposal.kind and original.unit==proposal.unit and (Decimal(original.value)==Decimal(proposal.value) if original.kind==proposal.kind=='decimal' else original.value==proposal.value)
        if not equal:conflicts.append(proposal.name+':exact_latent_conflict')
    return DualReadout(packet.symbols,latent_value,tuple(conflicts),'conflict_requires_resolution' if conflicts else 'exact_channel_preserved')
def resolve_latent(packet,registry,*,actor,expected_type,role=Visibility.RECEIVER):
    return registry.resolve(packet.latent_handle,expected_type=expected_type,versions=packet.versions,actor=actor,role=role)
def wire_size(packet,latent_bytes):
    if type(latent_bytes) is not int or latent_bytes<0:raise ContractError('InvalidCost','latent wire byte count required')
    rows=[{'name':s.name,'kind':s.kind,'value':s.value,'unit':s.unit,'source':s.source.value,'origin_role':s.origin_role} for s in packet.symbols]
    return len(json.dumps({'symbols':rows,'latent_handle':packet.latent_handle.value,'versions':packet.versions.as_dict()},ensure_ascii=False).encode('utf-8'))+latent_bytes
