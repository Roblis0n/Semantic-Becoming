import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h40_instruction_set.types import *
from latent_comm.mechanisms.h40_instruction_set.reference import *
from latent_comm.mechanisms.h40_instruction_set.serialization import *
import latent_comm.mechanisms.h40_instruction_set.adapter as adapter

class H40Contracts(unittest.TestCase):
    def body(self):return Expr('multiply',(Expr('add',(Expr('var',name='x'),Expr('const',value=1))),Expr('const',value=2)))
    def test_lowering_and_old_reader(self):
        isa=ISARevision('2',(MacroDefinition('mu',('x',),self.body(),('scalar',)),));lowered=migrate_for_reader(Expr('call',(Expr('const',value=0),),name='mu'),isa,'base:1')
        self.assertEqual(execute_base(lowered,{}),2.);self.assertNotEqual(execute_base(lowered,{}),1.)
    def test_capture_avoidance(self):
        body=Expr('let',(Expr('const',value=1),Expr('add',(Expr('var',name='a'),Expr('var',name='x')))),name='x')
        isa=ISARevision('1',(MacroDefinition('m',('a',),body,('scalar',)),));expr=Expr('call',(Expr('var',name='x'),),name='m')
        self.assertEqual(execute_base(lower(expr,isa),{'x':10}),11.)
    def test_recursion_rejected(self):
        isa=ISARevision('1',(MacroDefinition('r',('x',),Expr('call',(Expr('var',name='x'),),name='r'),('scalar',)),))
        with self.assertRaises(ContractError):lower(Expr('call',(Expr('const',value=1),),name='r'),isa)
    def test_real_description_gain(self):
        p=propose_macro((self.body(),)*4,'m');self.assertGreater(p.saved_bytes,0);self.assertEqual(p.occurrences,4)
    def test_immutable_base_and_fixture_limit(self):
        with self.assertRaises(ContractError):MacroDefinition('add',(),Expr('const'),())
        with self.assertRaises(ContractError):lower(self.body(),ISARevision('1',()),StepBudget(max_steps=1))
        self.assertEqual(ISARevision('1',()).future_expansion_budget,256)
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_base_execute(None,{})
    def test_neural_source_is_lazy_and_gated(self):
        tree=ast.parse(Path(adapter.__file__).read_text())
        self.assertFalse(any(isinstance(x,(ast.Import,ast.ImportFrom)) and any(a.name.startswith(('torch','transformers')) for a in x.names) for x in tree.body))
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                imports=[x for x in ast.walk(node) if isinstance(x,ast.Import) and any(a.name=='torch' for a in x.names)]
                if imports:
                    gates=[x for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require_research_action']
                    self.assertTrue(gates)
                    self.assertLess(min(x.lineno for x in gates),min(x.lineno for x in imports))

if __name__=='__main__':unittest.main()
