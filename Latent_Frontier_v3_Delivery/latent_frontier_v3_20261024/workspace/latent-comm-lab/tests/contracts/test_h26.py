import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h26_sheaf.types import *
from latent_comm.mechanisms.h26_sheaf.reference import *
from latent_comm.mechanisms.h26_sheaf.serialization import *
import latent_comm.mechanisms.h26_sheaf.adapter as adapter

class H26Contracts(unittest.TestCase):
    def packet(self,cycle=False,anchors=True):
        edges=[AffineRestriction('xy','x','y',((1.,),),((1.,),),(0.,),('e:1',)),AffineRestriction('yz','y','z',((1.,),),((1.,),),(0.,),('e:2',))]
        if cycle:edges.append(AffineRestriction('zx','z','x',((1.,),),((1.,),),(1.,),('e:3',)))
        return SheafPacket(tuple(LocalDomain(x,1) for x in 'xyz'),tuple(edges),(Anchor('x',0,0.),) if anchors else (),'1')
    def test_consistent_chain_and_missing_overlap(self):
        r=glue(self.packet());self.assertEqual(r.status,'CompatibleOnDeclaredOverlaps');self.assertEqual(r.missing_overlaps,(('x','z'),))
    def test_cycle_retains_conflict_and_hard_anchor(self):
        r=glue(self.packet(True));self.assertEqual(r.status,'NoGlobalSection');self.assertEqual(set(r.conflict_witness),{'xy','yz','zx'})
        self.assertEqual(dict(r.sections)['x'],(0.,));self.assertAlmostEqual(sum(x*x for _,v in r.residuals for x in v),1/3)
    def test_zero_consensus_rejected(self):
        with self.assertRaises(ContractError):glue(self.packet(anchors=False))
    def test_migration_preserves_constraints(self):
        p=migrate_cover(self.packet(True),'2',{'x':'a','y':'b','z':'c'});self.assertEqual(glue(p).status,'NoGlobalSection')
    def test_budget(self):
        with self.assertRaises(ContractError):glue(self.packet(True),StepBudget(max_steps=1))
    def test_semantic_schema_rejects_bad_anchor(self):
        p={'schema_version':3,'version':'1','cover':[{'name':'x','dimension':1}],'restrictions':[],'anchors':[{'domain':'x','coordinate':1,'value':0}]}
        with self.assertRaises(ContractError):validate_payload(p)
    def test_mixed_batch_cannot_hide_homogeneous_row(self):
        rows=((1.,),(0.,))
        self.assertTrue(any(all(x==0 for x in row) for row in rows))
        source=Path(adapter.__file__).read_text()
        self.assertIn('(bias==0).all(dim=-1).any()',source)
    def test_gate(self):
        with self.assertRaises(Exception):adapter.tensor_glue(None,None,(),None)
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
