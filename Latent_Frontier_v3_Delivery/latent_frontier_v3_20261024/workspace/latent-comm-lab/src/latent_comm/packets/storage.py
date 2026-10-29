"""Atomic finite JSON storage under an explicitly chosen workspace root."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from .schema import load_json
from latent_comm.core import ContractError, ErrorCode

def resolve_workspace_path(root: Path,relative: str) -> Path:
    if not relative or '\\' in relative or '\x00' in relative:
        raise ContractError(ErrorCode.SCOPE_VIOLATION,'invalid relative path')
    rel=Path(relative)
    if rel.is_absolute() or any(x in {'..','.'} for x in relative.split('/')):
        raise ContractError(ErrorCode.SCOPE_VIOLATION,'path escapes workspace')
    root=root.resolve();p=root/rel;cursor=root
    for part in rel.parts:
        cursor=cursor/part
        if cursor.is_symlink():raise ContractError(ErrorCode.SCOPE_VIOLATION,'symlink is not an authorized object path')
    if not p.resolve().is_relative_to(root):raise ContractError(ErrorCode.SCOPE_VIOLATION,'path outside workspace')
    return p

def save_finite_json(root: Path,relative: str,value: object) -> str:
    path=resolve_workspace_path(root,relative);path.parent.mkdir(parents=True,exist_ok=True)
    content=(json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n').encode()
    fd,temp=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    return hashlib.sha256(content).hexdigest()

def load_finite_json(root: Path,relative: str,expected_digest: str) -> object:
    path=resolve_workspace_path(root,relative);raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected_digest:raise ContractError(ErrorCode.CONFLICT,'stored content digest mismatch')
    return load_json(raw.decode())
