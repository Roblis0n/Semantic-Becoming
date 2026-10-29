"""Safe fixed-placeholder compilation, without Jinja evaluation or model calls.

Auxiliary critic/world_proposer roles retain a receiver/sender visibility envelope.
A future caller receives separate system/data messages and must still use a gated
model entry. Rendering is not execution and does not implement any mechanism.
"""
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping
import json
import math
import re
from latent_comm.core.errors import ContractError, ErrorCode
from latent_comm.core.views import RoleView, freeze_public, FORBIDDEN_FIELDS
from latent_comm.core.refs import ObjectRef

ROOT=Path(__file__).resolve().parent
CONTRACTS=json.loads((ROOT.parents[1]/'specs/role_view_contracts.json').read_text())
@dataclass(frozen=True)
class CompiledTemplate:
    role: str
    system: str
    data: str
    output_schema: dict
    research_state: str='NOT_RUN'
    def messages(self):
        return ({'role':'system','content':self.system},{'role':'user','content':self.data})

def _wire(value):
    if isinstance(value,ObjectRef):
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'prompt references require upstream validated projection, not implicit resolution')
    if isinstance(value,Mapping):
        if set(value)&FORBIDDEN_FIELDS:raise ContractError(ErrorCode.ROLE_LEAKAGE,'metadata/supervision field cannot enter template data')
        return {k:_wire(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_wire(v) for v in value]
    if isinstance(value,float) and not math.isfinite(value):
        raise ContractError(ErrorCode.INVALID_SHAPE,'nonfinite prompt value')
    if value is None or isinstance(value,(str,int,float,bool)):return value
    raise ContractError(ErrorCode.ROLE_LEAKAGE,'opaque payload rejected')

def compile_template(role: str, view: RoleView) -> CompiledTemplate:
    if role not in CONTRACTS['roles']:
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'unknown template role')
    c=CONTRACTS['roles'][role]
    if not isinstance(view,RoleView) or view.role.value != c['accepted_view_role']:
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'template requires its own physically projected role view')
    view.versions.require(*c['required_version_axes'])
    # Revalidation protects against a caller constructing an object outside the constructor.
    values={'versions':view.versions.as_dict(),'public_task':freeze_public(view.public_task),'features':freeze_public(view.features)}
    template=(ROOT/(role+'.jinja')).read_text()
    system,body=template.split('\nDATA_ONLY\n',1)
    placeholders=re.findall(r'{{\s*(.*?)\s*}}',body)
    if set(placeholders)!=set(c['input_keys']) or len(placeholders)!=len(c['input_keys']):
        raise ContractError(ErrorCode.ROLE_LEAKAGE,'template field contract mismatch')
    # Single substitution pass: braces in user data are never evaluated recursively.
    data=re.sub(r'{{\s*(.*?)\s*}}',lambda m:json.dumps(_wire(values[m.group(1)]),ensure_ascii=False,allow_nan=False,separators=(',',':')),body).strip()
    parsed=json.loads(data)
    if set(parsed)!=set(c['input_keys']):raise ContractError(ErrorCode.ROLE_LEAKAGE,'unexpected rendered field')
    return CompiledTemplate(role,system,data,c['output_schema'])

def validate_response(role: str, response: str) -> dict:
    """Structural output check only. Dedicated semantic validators must run later."""
    if role not in CONTRACTS['roles']:raise ContractError(ErrorCode.ROLE_LEAKAGE,'unknown template role')
    from latent_comm.packets.schema import SchemaValidator,load_json
    value=load_json(response)
    SchemaValidator(CONTRACTS['roles'][role]['output_schema']).validate(value)
    return value
