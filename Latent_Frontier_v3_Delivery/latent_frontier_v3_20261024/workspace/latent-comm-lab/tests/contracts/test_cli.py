import ast,contextlib,io,json,sys,tempfile,unittest
from pathlib import Path
from latent_comm.cli.main import main
class CliTests(unittest.TestCase):
 def capture(self,args):
  output=io.StringIO()
  with contextlib.redirect_stdout(output):code=main(args)
  return code,json.loads(output.getvalue())
 def test_inventory_is_complete(self):
  code,data=self.capture(['design']);self.assertEqual(code,0);self.assertEqual(len(data['design']['mechanisms']),48);self.assertEqual(len(data['design']['compositions']),20);self.assertEqual(len(data['design']['horizons']),12)
 def test_specific_design_no_execution(self):
  for args in (['--mechanism','H38'],['--composition','C20'],['--horizon','X12']):
   code,data=self.capture(['design']+args);self.assertEqual(code,0);self.assertFalse(data['execution_authorized']);self.assertEqual(data['research_state'],'NOT_RUN')
 def test_future_research_description_only(self):
  code,data=self.capture(['research','train','--describe']);self.assertEqual(code,0);self.assertFalse(data['executable_in_current_task'])
 def test_inspect_strict_finite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'object.json';p.write_text('{"versions":{"task":"t1"}}');code,data=self.capture(['inspect',str(p)]);self.assertEqual(code,0);self.assertFalse(data['execution_performed'])
   p.write_text('{"nested":{"value":1e1000}}')
   with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(main(['inspect',str(p)]),2)
 def test_research_gate_source_precedes_dispatch(self):
  source=Path(__file__).resolve().parents[2]/'src/latent_comm/cli/research.py';tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');self.assertTrue(any(isinstance(n,ast.Call) and getattr(n.func,'id','')=='require_research_action' for n in ast.walk(fn)))
 def test_no_neural_imports(self):self.assertFalse(set(sys.modules)&{'torch','transformers','tensorflow','jax'})
if __name__=='__main__':unittest.main()
