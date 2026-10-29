import unittest, ast, json
from pathlib import Path
from latent_comm.core import ContractError, StepBudget
from latent_comm.mechanisms.h34_boundary_value.types import *
from latent_comm.mechanisms.h34_boundary_value.reference import *
from latent_comm.mechanisms.h34_boundary_value.serialization import *
import latent_comm.mechanisms.h34_boundary_value.adapter as adapter

class H34Contracts(unittest.TestCase):
    def graph(self,goal='3'):
        edges=tuple((str(i),str(j)) for i in range(4) for j in (i,i+1) if j<4)
        return TrajectoryFactorGraph(('0','1','2','3'),(edges,)*3,('0',),PublicTerminalConstraint((goal,),'public_goal','1'),'1')
    def test_public_goal_prunes_waits(self):
        r=solve_boundary(self.graph());self.assertEqual(r.paths,(('0','1','2','3'),));self.assertEqual(r.status,'UniquePath')
    def test_infeasible_and_multiple(self):
        g=replace(self.graph(),transitions=(self.graph().transitions[0],));self.assertEqual(solve_boundary(g).status,'BoundaryInfeasible')
        self.assertGreater(len(solve_boundary(self.graph('2')).paths),1)
    def test_limit_retains_pending(self):
        r=solve_boundary(self.graph('2'),path_limit=1);self.assertEqual(r.status,'SolverLimit');self.assertTrue(r.unexplored_prefixes)
    def test_future_label_leak(self):
        with self.assertRaises(ContractError):PublicTerminalConstraint(('3',),'hidden_solution','1')
        from latent_comm.core.views import project_role
        from latent_comm.core.refs import Visibility
        with self.assertRaises(ContractError):project_role({'hidden_solution':'3'},role=Visibility.SENDER,feature_fields=('hidden_solution',),public_fields=(),versions=VersionSet(task='1'))
    def test_migration_and_gate(self):
        g=migrate_states(self.graph(),'2',{str(i):f's{i}' for i in range(4)});self.assertEqual(solve_boundary(g).paths[0][-1],'s3')
        with self.assertRaises(Exception):adapter.tensor_forward_backward(None,None,None,terminal_source='public_goal')
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
