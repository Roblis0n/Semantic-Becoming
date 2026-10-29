"""A deliberately finite JSON Schema subset matching the package's wire schema.

This performs structural validation only. Mechanism validators still establish
invertibility, noise coupling, answer relations and executable semantics.
"""
from __future__ import annotations
import json
import math
import re
from collections.abc import Mapping
from latent_comm.core import ContractError, ErrorCode

class SchemaValidator:
    def __init__(self,schema: dict) -> None:
        self.schema=schema
    def validate(self,value: object,schema: dict | None=None,path: str='$') -> None:
        if path=='$':validate_finite_json_tree(value)
        s=self.schema if schema is None else schema
        if '$ref' in s:
            ref=s['$ref']
            if not ref.startswith('#/'):
                raise ContractError(ErrorCode.INVALID_SCHEMA,'remote schema references forbidden',path)
            target=self.schema
            for key in ref[2:].split('/'):
                try:target=target[key.replace('~1','/').replace('~0','~')]
                except KeyError as e:raise ContractError(ErrorCode.INVALID_SCHEMA,'unbound schema reference',path) from e
            self.validate(value,target,path)
        types=s.get('type',[]);types=[types] if isinstance(types,str) else types
        checks={'object':lambda x:isinstance(x,Mapping),'array':lambda x:isinstance(x,(tuple,list)),'string':lambda x:isinstance(x,str),'integer':lambda x:type(x) is int,'number':lambda x:type(x) in (int,float) and math.isfinite(x),'boolean':lambda x:type(x) is bool,'null':lambda x:x is None}
        if types and not any(t in checks and checks[t](value) for t in types):
            raise ContractError(ErrorCode.INVALID_SCHEMA,f'expected {types}',path)
        if 'const' in s and (value!=s['const'] or type(value)!=type(s['const'])):
            raise ContractError(ErrorCode.INVALID_SCHEMA,'constant mismatch',path)
        if 'enum' in s and not any(value==x and type(value)==type(x) for x in s['enum']):
            raise ContractError(ErrorCode.INVALID_SCHEMA,'value outside enum',path)
        if isinstance(value,Mapping):
            missing=set(s.get('required',()))-set(value)
            if missing:raise ContractError(ErrorCode.INVALID_SCHEMA,f'missing fields {sorted(missing)}',path)
            props=s.get('properties',{})
            if s.get('additionalProperties') is False and set(value)-set(props):
                raise ContractError(ErrorCode.INVALID_SCHEMA,f'unknown fields {sorted(set(value)-set(props))}',path)
            for key,subschema in props.items():
                if key in value:self.validate(value[key],subschema,path+'.'+key)
        if isinstance(value,(list,tuple)):
            if len(value)<s.get('minItems',0) or len(value)>s.get('maxItems',float('inf')):
                raise ContractError(ErrorCode.INVALID_SCHEMA,'array cardinality',path)
            if s.get('uniqueItems') and len({json.dumps(x,sort_keys=True,allow_nan=False) for x in value})!=len(value):
                raise ContractError(ErrorCode.INVALID_SCHEMA,'duplicate array member',path)
            if 'items' in s:
                for i,item in enumerate(value):self.validate(item,s['items'],f'{path}[{i}]')
        if isinstance(value,str) and 'pattern' in s and not re.search(s['pattern'],value):
            raise ContractError(ErrorCode.INVALID_SCHEMA,'pattern mismatch',path)
        if type(value) in (int,float):
            if not math.isfinite(value) or value<s.get('minimum',-math.inf) or value>s.get('maximum',math.inf):
                raise ContractError(ErrorCode.INVALID_SCHEMA,'number outside finite range',path)
        for child in s.get('allOf',()):self.validate(value,child,path)
        if 'if' in s:
            try:self.validate(value,s['if'],path)
            except ContractError:matches=False
            else:matches=True
            if matches and 'then' in s:self.validate(value,s['then'],path)
            if not matches and 'else' in s:self.validate(value,s['else'],path)


def validate_finite_json_tree(value: object,path: str='$') -> None:
    if isinstance(value,Mapping):
        if any(not isinstance(k,str) for k in value):raise ContractError(ErrorCode.INVALID_SCHEMA,'wire object keys must be strings',path)
        for key,item in value.items():validate_finite_json_tree(item,path+'.'+key)
    elif isinstance(value,(list,tuple)):
        for i,item in enumerate(value):validate_finite_json_tree(item,f'{path}[{i}]')
    elif isinstance(value,float):
        if not math.isfinite(value):raise ContractError(ErrorCode.INVALID_SCHEMA,'nonfinite wire number',path)
    elif value is not None and not isinstance(value,(str,int,bool)):
        raise ContractError(ErrorCode.INVALID_SCHEMA,'wire payload is not finite JSON data',path)


def load_json(text: str) -> object:
    def pairs(items: list[tuple[str,object]]) -> dict:
        result={}
        for k,v in items:
            if k in result:raise ContractError(ErrorCode.INVALID_SCHEMA,'duplicate JSON key',k)
            result[k]=v
        return result
    def bad(value: str) -> None:
        raise ContractError(ErrorCode.INVALID_SCHEMA,'nonfinite JSON constant '+value)
    value=json.loads(text,object_pairs_hook=pairs,parse_constant=bad)
    validate_finite_json_tree(value)
    return value
