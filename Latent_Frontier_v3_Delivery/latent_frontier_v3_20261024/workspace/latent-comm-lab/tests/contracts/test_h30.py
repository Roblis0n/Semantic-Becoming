import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h30_analogy.types import *
from latent_comm.mechanisms.h30_analogy.reference import *
from latent_comm.mechanisms.h30_analogy.serialization import *
import latent_comm.mechanisms.h30_analogy.adapter as adapter

class H30Contracts(unittest.TestCase):
    def graph(self,prefix,step):
        objects=tuple(TypedObject(prefix+str(i),'number') for i in range(4))
        return TypedOperationGraph(objects,(FiniteOperation('advance','number','number',tuple((prefix+str(i),prefix+str(i+step)) for i in range(4-step))),),'1')
    def test_commuting_and_program(self):
        a=self.graph('x',1);b=self.graph('y',1);m=AnalogyMorphism(tuple((f'x{i}',f'y{i}') for i in range(4)),(('advance','advance'),),(('number','number'),),tuple(f'x{i}' for i in range(4)))
        c=check_morphism(a,b,m);self.assertFalse(c.broken_squares);self.assertEqual(compile_program(a,b,c,('advance','advance'),'x0')[1],('y0','y1','y2'))
        bad=check_morphism(a,self.graph('y',2),m);self.assertTrue(bad.broken_squares)
    def test_symmetry_returns_multiple(self):
        a=TypedOperationGraph((TypedObject('a','t'),TypedObject('b','t')),(),'1');b=TypedOperationGraph((TypedObject('c','t'),TypedObject('d','t')),(),'1')
        self.assertEqual(len(candidate_matches(a,b,(('t','t'),),())),2)
    def test_unmapped_step_rejected(self):
        a=self.graph('x',1);b=self.graph('y',1);m=AnalogyMorphism((('x0','y0'),),(),(('number','number'),),('x0',));c=check_morphism(a,b,m)
        self.assertTrue(c.uncovered_edges)
        with self.assertRaises(ContractError):compile_program(a,b,c,('advance',),'x0')
    def test_typed_schema_and_migration(self):
        a=self.graph('x',1);new=migrate_graph(a,'2',{f'x{i}':f'z{i}' for i in range(4)});self.assertEqual(new.operations[0].table[0],('z0','z1'))
        with self.assertRaises(ContractError):TypedOperationGraph(a.objects,(FiniteOperation('bad','wrong','number',(('x0','x1'),)),),'1')
    def test_gate(self):
        with self.assertRaises(Exception):adapter.soft_matching(None,None)
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
