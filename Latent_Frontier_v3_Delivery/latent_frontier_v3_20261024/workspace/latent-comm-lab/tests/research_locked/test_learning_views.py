import ast
import json
from pathlib import Path
import unittest
from latent_comm.learning.views.train import describe
from latent_comm.learning.views import checked_symbol_packet
from latent_comm.core import ContractError,RoleView,VersionSet,Visibility
ROOT=Path(__file__).resolve().parents[2]
class ContractChecks(unittest.TestCase):
    def test_metadata(self):
        self.assertEqual(describe()['research_state'],'NOT_RUN')
        self.assertFalse(describe()['execution_authorized'])
    def test_stage_syntax_and_gates(self):
        for path in (ROOT/'src/latent_comm/learning/views').glob('*.py'):
            tree=ast.parse(path.read_text())
            for node in tree.body:
                if isinstance(node,ast.Import):self.assertFalse(any(a.name.split('.')[0] in {'torch','transformers','numpy'} for a in node.names))
                if isinstance(node,ast.ImportFrom):self.assertNotIn((node.module or '').split('.')[0],{'torch','transformers','numpy'})
            for node in ast.walk(tree):
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    direct_neural=any(isinstance(n,ast.Import) and any(a.name=='torch' for a in n.names) for n in node.body)
                    if direct_neural or node.name in {'build_stage','forward_roles','losses','run'}:
                        body=node.body[1:] if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) else node.body
                        self.assertTrue(any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id','')=='require_research_action' for n in body[:2]),(path.name,node.name))
                    if node.name=='forward_roles':self.assertEqual([a.arg for a in node.args.args],['self','sender','receiver'])
    def test_recipe_is_unbound(self):
        cfg=json.loads((ROOT/'configs/learning/views.json').read_text())
        self.assertEqual(cfg['model_manifest_digest'],'UNBOUND');self.assertEqual(cfg['data_manifest'],'UNBOUND')
        self.assertEqual(cfg['stage'],'L01')
    def test_engine_delegation_and_resume_command(self):
        source=(ROOT/'src/latent_comm/learning/views/train.py').read_text()
        self.assertIn('from latent_comm.learning.engine import train',source)
        self.assertIn('resume=resume',source);self.assertIn('--resume-sha256',source)
    def source_views(self,*,source_value='1.20',source_visibility='receiver'):
        versions=VersionSet(state='s1',ontology='o1',task='t1',evidence='e1');v=versions.as_dict()
        scope={'scope_id':'learning:symbols','readers':['learning_receiver'],'writable_components':[]}
        symbol={'name':'amount','kind':'decimal','value':'1.20','unit':'m','source':'source:amount','origin_role':'sender'}
        packet={'symbols':[symbol],'latent_handle':'latent:one','versions':v}
        source={k:symbol[k] for k in ('name','kind','value','unit','origin_role')};source.update(value=source_value,versions=v,scope=scope,visibility=source_visibility)
        s=RoleView(Visibility.SENDER,{}, {'symbol_packet':packet},versions)
        r=RoleView(Visibility.RECEIVER,{}, {'verified_symbol_sources':{'source:amount':source},'latent_handle':'latent:one','latent_slots':((0.,1.),),'latent_scope':scope},versions)
        return s,r
    def test_auxiliary_loss_live_owners(self):
        from latent_comm.learning.views import DUAL_LOSS_SPECS
        from latent_comm.learning.contracts import Phase,validate_phase
        for loss in ('symbol_structure','conflict'):
            for owner in ('mechanism_writer','mechanism_reader'):
                validate_phase(Phase('auxiliary',(owner,),((loss,1.),),1,.01),{owner:{'p':object()}},DUAL_LOSS_SPECS)
    def test_exact_symbol_preserved(self):
        packet=checked_symbol_packet(*self.source_views());self.assertEqual(packet.symbols[0].value,'1.20')
    def test_symbol_source_conflict_and_role_leak_rejected(self):
        for kwargs in ({'source_value':'1.21'},{'source_visibility':'supervision'}):
            with self.assertRaises(ContractError):checked_symbol_packet(*self.source_views(**kwargs))
    def test_no_total_double_count(self):
        c=json.loads((ROOT/'configs/learning/views.json').read_text())
        self.assertTrue(all('total' not in phase['loss_weights'] for phases in c['phases'].values() for phase in phases))
    def test_receiver_backend_keeps_live_input_path(self):
        source=(ROOT/'src/latent_comm/learning/views/__init__.py').read_text()
        self.assertIn('apply_to_receiver(',source);self.assertIn("capabilities.require('input_gradients')",source);self.assertNotIn('no_grad()',source)

if __name__=='__main__':unittest.main()
