import ast, importlib.abc, json, sys, unittest
from pathlib import Path
root=Path.cwd();number=int(sys.argv[1]);name=f'h{number:02}';module=root/'src/latent_comm/mechanisms'/f'{name}_legacy'
class DenyResearchNetwork(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'torch','transformers','numpy','jax','tensorflow','requests','httpx','socket','boto3','openai'} or fullname.startswith(('urllib.request','http.client')):raise RuntimeError('Forbidden research/network import during authoring: '+fullname)
sys.meta_path.insert(0,DenyResearchNetwork());sys.path.insert(0,str(root/'src'))
count=0
for file in module.glob('*.py'):
 tree=ast.parse(file.read_text());count+=1
 for node in ast.walk(tree):
  if isinstance(node,ast.Name) and node.id=='NotImplementedError':raise AssertionError(f'{file}: incomplete mechanism')
  if isinstance(node,ast.ClassDef) and all(isinstance(x,ast.Pass) for x in node.body):raise AssertionError(f'{file}: empty class')
 for item in tree.body:
  if isinstance(item,(ast.Import,ast.ImportFrom)):
   imports=[a.name.split('.')[0] for a in item.names] if isinstance(item,ast.Import) else [(item.module or '').split('.')[0]]
   assert not set(imports)&{'torch','transformers','numpy','jax','tensorflow'},file
print(f'M{number:02}: AST parsed {count} own Python source files; neural/array/network imports blocked; research NOT_RUN.',flush=True)
from latent_comm.core.budgets import aggregate_budget,StepBudget
class BoundedResult(unittest.TextTestResult):
 def startTest(self,test):
  self._scope=aggregate_budget(StepBudget());self._meter=self._scope.__enter__();super().startTest(test)
 def stopTest(self,test):
  self._scope.__exit__(None,None,None);super().stopTest(test)
suite=unittest.defaultTestLoader.discover('tests/contracts',pattern=f'test_{name}.py')
result=unittest.TextTestRunner(verbosity=2,resultclass=BoundedResult).run(suite)
assert not any(k.split('.')[0] in {'torch','transformers','numpy','jax','tensorflow'} for k in sys.modules)
print(f'M{number:02}: {result.testsRun} contract tests; failures={len(result.failures)} errors={len(result.errors)}; no tensor/model import or execution.',flush=True)
sys.exit(0 if result.wasSuccessful() else 1)
