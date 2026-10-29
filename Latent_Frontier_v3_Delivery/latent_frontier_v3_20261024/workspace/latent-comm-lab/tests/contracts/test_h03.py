import ast, json, math, unittest
from pathlib import Path
from latent_comm.core import ContractError, StepBudget, VersionSet
from latent_comm.mechanisms.h03_legacy.types import *
from latent_comm.mechanisms.h03_legacy.reference import *
from latent_comm.mechanisms.h03_legacy.migration import migrate_legacy, validate_wire
V=VersionSet(schema='3',state='s1',frame='f1',ontology='o1',isa='i1',world='w1',task='t1',evidence='e1')
ROOT=Path(__file__).resolve().parents[2]/'src/latent_comm/mechanisms/h03_legacy'

class BeliefTests(unittest.TestCase):
    def packet(self):return BeliefPacket((BeliefBranch('a',(1.,),0.,'d',frozenset(),'o1'),BeliefBranch('b',(2.,),0.,'d',frozenset(),'o1')),'sequence_mixture',V)
    def test_sequence_not_token_average(self):
        p=self.packet();nll=sequence_mixture_nll(p,((math.log(.9),math.log(.9)),(math.log(.1),math.log(.1))))
        self.assertAlmostEqual(math.exp(-nll),.41);self.assertNotAlmostEqual(math.exp(-nll),.25)
        updated=prefix_posterior_update(p,(math.log(.9),math.log(.1)))
        self.assertAlmostEqual(math.exp(normalized_logs(updated)[0]),.9)
    def test_unknown_and_deduplicated_evidence(self):
        p=update_evidence(self.packet(),'source:1',(1.,0.));self.assertEqual(p,update_evidence(p,'source:1',(1.,0.)))
        q=prune(p,{'a'});self.assertTrue(q.branches[-1].unknown)
        self.assertAlmostEqual(logsumexp(b.log_weight for b in p.branches),logsumexp(b.log_weight for b in q.branches))
    def test_set_matching_and_domain(self):
        p=self.packet();self.assertEqual(match_branches(p.branches,tuple(reversed(p.branches)))[0],0.)
        from dataclasses import replace
        with self.assertRaises(ContractError):match_branches(p.branches,tuple(replace(b,ontology_version='other') for b in p.branches))
        with self.assertRaises(ContractError):prefix_posterior_update(p,(-math.inf,-math.inf))

    def test_source_gate_and_schema(self):
        schema=json.loads((ROOT/'schema.json').read_text())
        self.assertFalse(schema['additionalProperties'])
        for name in ('adapter.py','losses.py'):
            tree=ast.parse((ROOT/name).read_text())
            for node in tree.body:
                self.assertFalse(isinstance(node,(ast.Import,ast.ImportFrom)) and any(a.name.split('.')[0] in {'torch','transformers'} for a in node.names))
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    calls=[x for x in ast.walk(node) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require_research_action']
                    self.assertTrue(calls,node.name)
                    imports=[x for x in ast.walk(node) if isinstance(x,ast.Import) and any(a.name=='torch' for a in x.names)]
                    for imp in imports:self.assertLess(min(x.lineno for x in calls),imp.lineno)
        with self.assertRaises(ContractError):migrate_legacy({'schema_version':2},bindings={},versions=V)


    def test_wire_roundtrip_explicit_migration_and_bad_types(self):
        from copy import deepcopy
        from latent_comm.mechanisms.h03_legacy.migration import encode_wire,decode_wire
        example=json.loads((ROOT/'wire_example.json').read_text())
        self.assertEqual(decode_wire(encode_wire(example)),example)
        legacy={k:v for k,v in example.items() if k not in ('schema_version','versions')};legacy['schema_version']=2
        migrated=migrate_legacy(legacy,bindings={},versions=V);self.assertEqual(migrated,example)
        malformed=deepcopy(example);malformed['versions']['state']=float('inf')
        with self.assertRaises(ContractError):validate_wire(malformed)
        malformed=deepcopy(example);malformed['unexpected']=True
        with self.assertRaises(ContractError):validate_wire(malformed)
        key=next(k for k in example if k not in ('schema_version','versions'));malformed=deepcopy(example);malformed[key]=object()
        with self.assertRaises(ContractError):validate_wire(malformed)
        with self.assertRaises(ContractError):decode_wire(b'{"schema_version":3,"schema_version":3}')

    def test_static_loss_ledger_and_empty_mask_contract(self):
        allowed={'EXACT','SECOND_ORDER','FIRST_ORDER','POLICY_GRADIENT','STRAIGHT_THROUGH','ENUMERATION','NONDIFFERENTIABLE'}
        tree=ast.parse((ROOT/'losses.py').read_text())
        aliases={'masked_tensor_mean'}
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom):
                aliases.update(alias.asname or alias.name for alias in node.names if alias.name=='masked_tensor_mean')
            if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='GradientEstimator':self.assertIn(node.attr,allowed)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in aliases:
                self.assertTrue(any(k.arg=='zero_valid_policy' and isinstance(k.value,ast.Constant) and k.value.value=='differentiable_zero' for k in node.keywords))

    def test_conflict_counterexample_query_and_provenance_bindings(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h03_legacy import integration as bind
        from latent_comm.mechanisms.h26_sheaf.types import SheafPacket,LocalDomain,AffineRestriction
        from latent_comm.mechanisms.h36_disagreement.types import Counterexample
        from latent_comm.mechanisms.h48_evidence_genealogy.types import EvidenceAtom
        b=BeliefBranch('a',(1.,0.),0.,'domain',frozenset({'e'}),'o1');unknown=BeliefBranch('unknown',None,0.,'domain',frozenset({'e'}),'o1',True)
        packet=BeliefPacket((b,unknown),'sequence_mixture',V)
        sheaf=SheafPacket((LocalDomain('a',1),LocalDomain('b',1)),(AffineRestriction('edge','a','b',((1.,),),((1.,),),(0.,),('e',)),),(),'s1')
        result=bind.branch_overlap_residuals(packet,sheaf);self.assertEqual(result[0][1][0][1],(1.,));self.assertIsNone(result[1][1])
        with self.assertRaises(ContractError):bind.branch_overlap_residuals(packet,replace(sheaf,version='wrong'))
        witness=Counterexample('claim',2,False,True,'is_even','verified_counterexample');updated=bind.update_from_counterexample(packet,witness,{'a':'claim'});self.assertEqual(updated.branches[0].log_weight,-math.inf)
        with self.assertRaises(ContractError):bind.update_from_counterexample(packet,replace(witness,status='unresolved_disagreement'),{'a':'claim'})
        state=bind.as_identification_state(packet,(),version='q1');self.assertTrue(state.unknown_hypothesis_possible)
        graph=bind.branch_provenance(b,(EvidenceAtom('e','source','observed',None),),version='e1');self.assertEqual(graph.root,'support:a')
        with self.assertRaises(ContractError):bind.branch_provenance(b,(),version='e1')

    def test_typed_zero_mass_wire(self):
        from dataclasses import replace
        from latent_comm.mechanisms.h03_legacy.migration import encode_belief,decode_belief
        p=self.packet();p=replace(p,branches=(p.branches[0],replace(p.branches[1],log_weight=-math.inf)))
        payload=encode_belief(p);self.assertNotIn(b'Infinity',payload);self.assertEqual(decode_belief(payload),p)
        from latent_comm.mechanisms.h03_legacy.integration import as_identification_state
        self.assertTrue(as_identification_state(p,(),version='id').unknown_hypothesis_possible)

    def test_recipe_api_loss_names_and_owner_edges(self):
        api=json.loads((ROOT/'training_api.json').read_text())
        adapter=ast.parse((ROOT/'adapter.py').read_text());loss_tree=ast.parse((ROOT/'losses.py').read_text())
        functions={f.name:f for f in adapter.body if isinstance(f,ast.FunctionDef) and not f.name.startswith('_')}
        self.assertEqual(set(api['forward_entries']),set(functions))
        for name,f in functions.items():
            self.assertEqual(api['forward_entries'][name]['arguments'],[a.arg for a in f.args.posonlyargs+f.args.args+f.args.kwonlyargs])
        loss_fn=next(f for f in loss_tree.body if isinstance(f,ast.FunctionDef) and f.name=='tensor_losses')
        args={a.arg for a in loss_fn.args.posonlyargs+loss_fn.args.args+loss_fn.args.kwonlyargs}
        self.assertEqual(set(api['loss_input_bindings']),args)
        returned={k.value for node in ast.walk(loss_fn) if isinstance(node,ast.Return) and isinstance(node.value,ast.Dict) for k in node.value.keys if isinstance(k,ast.Constant) and isinstance(k.value,str)}
        ledger=next(n.value for n in loss_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LEDGER' for t in n.targets))
        names={ast.literal_eval(call.args[0]) for call in ledger.elts}
        self.assertEqual(names,{row['name'] for row in api['loss_specs']});self.assertTrue(names<=returned)
        for row in api['loss_specs']:
            self.assertTrue(set(row['requires_grad_inputs'])<=args)
            self.assertTrue({edge[0] for edge in row['stop_gradient_edges']}<=args)
            self.assertTrue(set(row['parameter_owners'])<=set(api['parameter_bindings']))
            self.assertEqual(row['zero_valid_policy'],'differentiable_zero')
        config=json.loads((ROOT.parents[3]/'configs/mechanisms'/('H'+ROOT.name[1:3]+'.json')).read_text())
        self.assertEqual(config['training_integration']['forward_entry'],api['forward_entry'])
        self.assertEqual(config['training_integration']['loss_input_bindings'],api['loss_input_bindings'])
        self.assertFalse(config['research_execution_authorized'])
