"""Read-only AST check: direct imported project function-call signatures.
No target code is executed or imported. Dynamic tensor/member APIs are outside scope.
"""
import ast, json, inspect, pathlib, sys
ROOT=pathlib.Path(sys.argv[1]); SRC=ROOT/'src'
STAGES=('views','objects','concept_questions','causal_analogy','dynamics_scales','transport','meta_rules','isa_search','worlds','uncertainty','evidence','joint')
cache={};checked=[];errors=[]
def module_defs(module):
 if module in cache:return cache[module]
 path=SRC.joinpath(*module.split('.')).with_suffix('.py')
 if not path.is_file():path=SRC.joinpath(*module.split('.'))/'__init__.py'
 if not path.is_file():cache[module]={};return {}
 tree=ast.parse(path.read_text());cache[module]={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};return cache[module]
def local_nodes(node):
 yield node
 for child in ast.iter_child_nodes(node):
  if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Lambda)):
   continue
  yield from local_nodes(child)
def signature(node):
 a=node.args;params=[];pos=a.posonlyargs+a.args;defaults=[inspect.Parameter.empty]*(len(pos)-len(a.defaults))+[None]*len(a.defaults)
 for i,(arg,default) in enumerate(zip(pos,defaults)):params.append(inspect.Parameter(arg.arg,inspect.Parameter.POSITIONAL_ONLY if i<len(a.posonlyargs) else inspect.Parameter.POSITIONAL_OR_KEYWORD,default=default))
 if a.vararg:params.append(inspect.Parameter(a.vararg.arg,inspect.Parameter.VAR_POSITIONAL))
 for arg,default in zip(a.kwonlyargs,a.kw_defaults):params.append(inspect.Parameter(arg.arg,inspect.Parameter.KEYWORD_ONLY,default=inspect.Parameter.empty if default is None else None))
 if a.kwarg:params.append(inspect.Parameter(a.kwarg.arg,inspect.Parameter.VAR_KEYWORD))
 return inspect.Signature(params)
def scope(node,inherited,path):
 bindings=dict(inherited)
 nodes=list(local_nodes(node))
 for n in nodes:
  if isinstance(n,ast.ImportFrom) and n.level==0 and (n.module or '').startswith('latent_comm.'):
   for alias in n.names:
    if alias.name in module_defs(n.module):bindings[alias.asname or alias.name]=(n.module,alias.name,module_defs(n.module)[alias.name])
 # Function arguments and assignments may shadow imported names.
 if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
  for arg in node.args.posonlyargs+node.args.args+node.args.kwonlyargs:bindings.pop(arg.arg,None)
 for n in nodes:
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in bindings:
   if any(isinstance(a,ast.Starred) for a in n.args) or any(k.arg is None for k in n.keywords):continue
   module,name,target=bindings[n.func.id];item={'path':str(path.relative_to(ROOT)),'line':n.lineno,'target':module+'.'+name}
   try:signature(target).bind(*[None]*len(n.args),**{k.arg:None for k in n.keywords})
   except TypeError as e:item['error']=str(e);errors.append(item)
   checked.append(item)
 for n in ast.iter_child_nodes(node):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):scope(n,bindings,path)
  else:
   for child in local_nodes(n):
    for inner in ast.iter_child_nodes(child):
     if isinstance(inner,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):scope(inner,bindings,path)
for name in STAGES:
 for path in (SRC/'latent_comm/learning'/name).glob('*.py'):scope(ast.parse(path.read_text()),{},path)
print(json.dumps({'checked_calls':len(checked),'errors':errors,'method':'AST-only signature binding for resolvable direct imported project functions'},indent=2))
assert not errors
