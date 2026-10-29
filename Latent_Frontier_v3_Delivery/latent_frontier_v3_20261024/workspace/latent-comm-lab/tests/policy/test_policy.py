"""Finite non-neural safety contracts; no real model callback is used."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from latent_comm.core import ContractError,ResearchBudget
from latent_comm.safety import *
from latent_comm.safety.policy import RESEARCH_ACTIONS,EXTERNAL_DENIALS
from latent_comm.safety.model_access import load_hf_model,load_hf_tokenizer,initialize_from_config,invoke_research_api
from latent_comm.cli.research import main

class PolicyTests(unittest.TestCase):
    def test_all_research_and_unknown_actions_deny(self):
        policy=CurrentTaskPolicy()
        for action in sorted(RESEARCH_ACTIONS|EXTERNAL_DENIALS|{'unknown_side_effect'}):
            self.assertFalse(policy.decide(action).allowed)
    def test_gate_never_calls_callback(self):
        called=[]
        @locked_research('model_forward')
        def operation():called.append(True)
        with self.assertRaises(ContractError):operation()
        self.assertEqual(called,[])
    def test_loader_gate_precedes_imports(self):
        for f,args,kw in [(load_hf_model,('not-a-real-model',),{'revision':'none','device':'cpu','dtype_name':'float32'}),(load_hf_tokenizer,('not-a-real-model',),{'revision':'none'}),(initialize_from_config,(object(),),{}),(invoke_research_api,(object(),{}),{})]:
            with self.assertRaises(ContractError):f(*args,**kw)
        self.assertNotIn('torch',sys.modules);self.assertNotIn('transformers',sys.modules)
    def test_config_cannot_grant_models_or_external_actions(self):
        for obj in [{'models':{'forward':True}},{'allowed_actions':['publish']}]:
            with self.assertRaises(ContractError):CurrentTaskPolicy.from_mapping(obj)
        self.assertFalse(CurrentTaskPolicy.from_mapping({'allowed_actions':['static_check']}).decide('workspace_write').allowed)
    def test_media_requires_both_conditions(self):
        p=CurrentTaskPolicy()
        self.assertFalse(p.decide('authorized_zero_new_cost_media',media_authorized=True).allowed)
        self.assertTrue(p.decide('authorized_zero_new_cost_media',media_authorized=True,zero_new_cost=True).allowed)
    def test_fixture_requires_bounded_non_neural_declaration(self):
        with tempfile.TemporaryDirectory() as d:
            b=ActionBroker(Path(d));valid=FixtureDeclaration('math_fixture',False,False,2,3,1)
            self.assertEqual(b.execute_local(ActionRequest('stdlib_math_fixture','finite_sum',valid),lambda:1+2),3)
            for f in [None,FixtureDeclaration('math_fixture',True,False,2,3,1),FixtureDeclaration('math_fixture',False,True,2,3,1),FixtureDeclaration('math_fixture',False,False,65,3,1)]:
                with self.assertRaises(ContractError):b.authorize(ActionRequest('stdlib_math_fixture','x',f))
    def test_path_and_symlink_fences(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);b=ActionBroker(root)
            for path in ['../secret','/etc/passwd','safe/../../outside']:
                with self.assertRaises(ContractError):b.authorize(ActionRequest('workspace_read',path))
            (root/'link').symlink_to('/tmp')
            with self.assertRaises(ContractError):b.authorize(ActionRequest('workspace_write','link/file'))
    def test_future_metadata_not_execution_authority(self):
        future=FutureResearchAuthorization('r','m','d','b','a','train');self.assertIn('not_authorized_in_current_task',future.validate_description())
        with self.assertRaises(ContractError):ResearchBudget(256,128,128,128).meter()
    def test_cli_describe_safe_execute_denied(self):
        for operation in ['train','eval','benchmark','forward','generate','initialize','download']:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([operation,'--describe']),0);self.assertEqual(main([operation]),2)
    def test_public_read_url_constraints(self):
        with tempfile.TemporaryDirectory() as d:
            b=ActionBroker(Path(d))
            for url in ['file:///etc/passwd','https://user:secret@example.com/','http://example.com/']:
                with self.assertRaises(ContractError):b.authorize(ActionRequest('public_read',url))
            self.assertTrue(b.authorize(ActionRequest('public_read','https://arxiv.org/abs/1902.04615')).allowed)

if __name__=='__main__':unittest.main()
