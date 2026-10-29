"""Run explicitly selected finite/static contracts, excluding research entry calls.

No model-entry invocation is used as a gate test. This runner is not a general
sandbox: it combines an AST exclusion preflight, denied imports and explicit
finite budgets. C/X tests may contain multiple independent invocations, each
already bounded end-to-end by their runtime; pass --individual-fixture-scopes.
"""
from pathlib import Path
import argparse,ast,importlib.abc,inspect,json,sys,textwrap,unittest
W=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('test_file');parser.add_argument('--individual-fixture-scopes',action='store_true');parser.add_argument('--list-only',action='store_true');args=parser.parse_args()
path=(W/args.test_file).resolve()
if not path.is_relative_to(W/'tests') or path.suffix!='.py':raise ValueError('one local test source is required')
if args.individual_fixture_scopes and not(path.name.startswith('test_c') or path.name=='test_horizons.py'):raise ValueError('only C/X tests have separately aggregate-bounded fixture calls')
class DenyImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'torch','transformers','tensorflow','jax','flax','numpy','safetensors','anthropic','openai','requests','httpx','socket','boto3'} or fullname.startswith(('urllib.request','http.client')):raise RuntimeError('finite/static runner denies '+fullname)
sys.meta_path.insert(0,DenyImports());sys.path.insert(0,str(W/'src'))
guarded=set()
for file in (W/'src').rglob('*.py'):
    for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and any(isinstance(s,ast.Expr) and isinstance(s.value,ast.Call) and isinstance(s.value.func,ast.Name) and s.value.func.id=='require_research_action' for s in node.body):guarded.add(node.name)
# Resolve renamed imports from each inspected test source as well as call attrs.
test_tree=ast.parse(path.read_text(encoding='utf-8'));aliases={a.asname:a.name for n in ast.walk(test_tree) if isinstance(n,ast.ImportFrom) for a in n.names if a.asname}
def called_names(tree):
    raw=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id if isinstance(n.func,ast.Name) else '' for n in ast.walk(tree) if isinstance(n,ast.Call)]
    return set(raw)|{aliases.get(x,x) for x in raw}
blocked_methods={}
for node in ast.walk(test_tree):
    if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):
        referenced={n.id for n in ast.walk(node) if isinstance(n,ast.Name)}
        blocked=(called_names(node)|referenced)&guarded
        if any(word in node.name.lower() for word in ('gate','locked','denied','denial','research_action')):
            blocked.add('conservative legacy gate-test exclusion')
        if blocked:blocked_methods[node.name]=sorted(blocked)
suite=unittest.defaultTestLoader.discover(str(path.parent),pattern=path.name)
def flat(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from flat(item)
        else:yield item
selected=[];excluded=[]
for test in flat(suite):
    method=getattr(test,'_testMethodName','')
    if method in blocked_methods:excluded.append({'test':test.id(),'guarded_calls':blocked_methods[method]})
    else:selected.append(test)
summary={'selected':len(selected),'excluded_research_entry_tests':excluded,'test_file':str(path.relative_to(W)),'research_state':'NOT_RUN','budget_scope':'per independent C/X fixture invocation' if args.individual_fixture_scopes else 'per test aggregate'}
if args.list_only:print(json.dumps(summary,indent=2));raise SystemExit(0)
from latent_comm.core.budgets import aggregate_budget,StepBudget
class BoundedResult(unittest.TextTestResult):
    def startTest(self,test):
        if not args.individual_fixture_scopes:self._scope=aggregate_budget(StepBudget());self._meter=self._scope.__enter__()
        super().startTest(test)
    def stopTest(self,test):
        if not args.individual_fixture_scopes:self._scope.__exit__(None,None,None)
        super().stopTest(test)
result=unittest.TextTestRunner(verbosity=2,resultclass=BoundedResult).run(unittest.TestSuite(selected))
summary.update(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),neural_modules_loaded=[m for m in sys.modules if m.split('.')[0] in {'torch','transformers','tensorflow','jax','flax','numpy','safetensors'}])
print(json.dumps(summary,indent=2));raise SystemExit(not result.wasSuccessful() or bool(summary['neural_modules_loaded']))
