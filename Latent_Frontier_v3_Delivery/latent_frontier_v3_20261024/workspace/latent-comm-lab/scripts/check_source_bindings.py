"""Static local imports/enum resolution plus opt-in guarded loss-module imports.

The default mode does not import any mechanism. The guarded mode accepts only
preflighted metadata-only loss modules, installs a deny finder for all tensor,
model and network libraries, then checks current lazy import contracts. It never
initializes a model, neural fixture or optimizer.
"""
from pathlib import Path
import ast
import argparse
import importlib
import importlib.abc
import json
import sys

ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'src';PACKAGE=SRC/'latent_comm'
ENUMS={}
for file in (PACKAGE/'core').glob('*.py'):
    tree=ast.parse(file.read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node,ast.ClassDef) and any(isinstance(b,ast.Name) and b.id=='Enum' for b in node.bases):
            ENUMS[node.name]={target.id for statement in node.body if isinstance(statement,ast.Assign) for target in statement.targets if isinstance(target,ast.Name)}

def module_file(name):
    base=SRC.joinpath(*name.split('.'))
    return base.with_suffix('.py') if base.with_suffix('.py').exists() else base/'__init__.py' if (base/'__init__.py').exists() else None

def module_name(path):
    parts=path.relative_to(SRC).with_suffix('').parts
    return '.'.join(parts[:-1] if parts[-1]=='__init__' else parts)

def import_target(path,node):
    if not node.level:return node.module or ''
    package=module_name(path).split('.')
    if path.name!='__init__.py':package.pop()
    if node.level>1:package=package[:-(node.level-1)]
    return '.'.join(package+([node.module] if node.module else []))

_SYMBOLS={}
def symbols(path,seen=frozenset()):
    if path in _SYMBOLS:return _SYMBOLS[path]
    if path in seen:return set(),True
    names=set();dynamic=False
    for n in ast.parse(path.read_text(encoding='utf-8')).body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            names.add(n.name);dynamic|=n.name=='__getattr__'
        elif isinstance(n,(ast.Assign,ast.AnnAssign)):
            for target in n.targets if isinstance(n,ast.Assign) else [n.target]:
                names.update(x.id for x in ast.walk(target) if isinstance(x,ast.Name))
        elif isinstance(n,ast.Import):names.update(a.asname or a.name.split('.')[0] for a in n.names)
        elif isinstance(n,ast.ImportFrom):
            for a in n.names:
                if a.name!='*':names.add(a.asname or a.name)
                else:
                    target=module_file(import_target(path,n))
                    if target:
                        ns,dyn=symbols(target,seen|{path});names|=ns;dynamic|=dyn
    _SYMBOLS[path]=(names,dynamic);return names,dynamic


def static_check(paths):
    errors=[];checked=0;dynamic=[]
    for path in paths:
        tree=ast.parse(path.read_text(encoding='utf-8'));aliases={}
        for n in ast.walk(tree):
            if isinstance(n,ast.ImportFrom):
                for a in n.names:
                    if a.name in ENUMS:aliases[a.asname or a.name]=a.name
                target_name=import_target(path,n)
                if not target_name.startswith('latent_comm'):continue
                target=module_file(target_name)
                if target is None:errors.append({'file':str(path.relative_to(ROOT)),'line':n.lineno,'missing_module':target_name});continue
                available,may_dynamic=symbols(target)
                for a in n.names:
                    if a.name=='*' or a.name in available or module_file(target_name+'.'+a.name):continue
                    row={'file':str(path.relative_to(ROOT)),'line':n.lineno,'import':target_name+'.'+a.name}
                    if may_dynamic:dynamic.append(row)
                    else:errors.append(row)
            elif isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id in aliases:
                enum=aliases[n.value.id]
                if n.attr not in ENUMS[enum]:errors.append({'file':str(path.relative_to(ROOT)),'line':n.lineno,'invalid_enum':enum+'.'+n.attr})
        checked+=1
    return {'files_checked':checked,'errors':errors,'dynamic_aliases_not_statically_resolved':dynamic}

class DenyResearchImports(importlib.abc.MetaPathFinder):
    blocked={'torch','tensorflow','jax','flax','transformers','safetensors','openai','anthropic','requests','httpx','urllib3','socket','subprocess'}
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in self.blocked:raise ImportError('source audit denies research/network import: '+fullname)


def safe_loss_imports(paths):
    permitted_calls={'LossSpec','GradientEstimator','tuple','list','dict','set','frozenset','len','range','enumerate','zip','str','float','int'}
    def live_nodes(node):
        # Function bodies are not executed at import, but their defaults/decorators are.
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for item in node.decorator_list+node.args.defaults+[d for d in node.args.kw_defaults if d is not None]:yield from ast.walk(item)
            return
        if isinstance(node,ast.ClassDef):raise ValueError('loss preflight requires metadata/functions only, not executable class definitions')
        yield from ast.walk(node)
    modules=[]
    for path in paths:
        for statement in ast.parse(path.read_text(encoding='utf-8')).body:
            for n in live_nodes(statement):
                if isinstance(n,ast.Call) and (not isinstance(n.func,ast.Name) or n.func.id not in permitted_calls):raise ValueError(f'loss import requires manual preflight: {path}:{n.lineno}')
        modules.append(module_name(path))
    guard=DenyResearchImports();sys.meta_path.insert(0,guard);sys.path.insert(0,str(SRC))
    try:
        for name in modules:importlib.import_module(name)
        leaked=sorted(n for n in sys.modules if n.split('.')[0] in {'torch','tensorflow','jax','transformers','safetensors'})
        if leaked:raise RuntimeError('forbidden neural module loaded: '+str(leaked))
    finally:sys.meta_path.remove(guard)
    return {'metadata_loss_modules_imported':modules,'neural_modules_loaded':[]}


def main():
    p=argparse.ArgumentParser();p.add_argument('--guarded-loss-imports',action='store_true');p.add_argument('--output');args=p.parse_args()
    paths=sorted(PACKAGE.rglob('*.py'));report=static_check(paths)
    if args.guarded_loss_imports and not report['errors']:report.update(safe_loss_imports(sorted((PACKAGE/'mechanisms').glob('*/losses.py'))))
    report['research_state']='NOT_RUN'
    text=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.output:(ROOT/args.output).write_text(text, encoding='utf-8')
    print(text)
    return bool(report['errors'])
if __name__=='__main__':raise SystemExit(main())
