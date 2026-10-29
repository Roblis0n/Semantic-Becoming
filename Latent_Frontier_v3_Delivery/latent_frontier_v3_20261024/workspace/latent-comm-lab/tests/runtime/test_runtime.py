"""Local finite state/control fixtures. No neural models or external effects."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from latent_comm.core import ContractError, Scope, VersionSet, StepBudget
from latent_comm.runtime import *
from latent_comm.runtime.loops import FixtureOperation, execute_fixture_ir, execute_research_ir

SCOPE=Scope('local',frozenset({'worker'}),frozenset({'Z','O','K','E'}))
V=VersionSet(state='1',ontology='1')
def begin(store,**kw):return store.begin(scope=SCOPE,actor='worker',**kw)
def write(tx,key,value,**kw):tx.write(key,value,type_name=kw.pop('type_name','Scalar'),component='Z',versions=kw.pop('versions',V),**kw)
def seed(store):
    tx=begin(store);write(tx,'state:x',1);write(tx,'state:y',2);tx.commit();return store

def increment(ctx,event):
    x=ctx.read('state:x')
    return EventResult((Write('state:x',x+1,'Scalar','Z',V),),phase='advanced')

class Transactions(unittest.TestCase):
    def test_snapshot_isolation_and_atomic_commit(self):
        s=seed(VersionedStore());a=begin(s);b=begin(s);write(a,'state:x',4);write(a,'state:y',5)
        self.assertEqual(b.read('state:x'),1);a.prepare();a.commit();self.assertEqual(b.read('state:y'),2)
        self.assertEqual(s.snapshot().cells['state:y'].value(),5)
    def test_delete_reads_pending_writes(self):
        s=VersionedStore();tx=begin(s);write(tx,'state:new',1);tx.delete('state:new')
        self.assertFalse(tx.exists('state:new'))
        with self.assertRaises(ContractError):tx.delete('state:new')
        tx.commit();self.assertNotIn('state:new',s.snapshot().cells)
    def test_durable_workspace_unsupported_platform_is_explicit(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root, patch('latent_comm.runtime.files.fcntl',None):
            path=Path(root)/'state'
            with self.assertRaises(ContractError) as ctx:AtomicWorkspace(path)
            self.assertEqual(ctx.exception.failure.code,'UnsupportedPlatform');self.assertFalse(path.exists())
    def test_read_conflict_even_disjoint_writes(self):
        s=seed(VersionedStore());a=begin(s);b=begin(s);a.read('state:x');b.read('state:x');write(a,'state:x',3);write(b,'state:y',4);a.commit()
        with self.assertRaises(ContractError):b.commit()
        self.assertEqual(s.snapshot().cells['state:y'].value(),2)
    def test_blind_writes_track_versions(self):
        s=seed(VersionedStore());a=begin(s);b=begin(s);write(a,'state:x',3);write(b,'state:x',4);a.commit()
        with self.assertRaises(ContractError):b.commit()
    def test_absence_reads_conflict(self):
        s=VersionedStore();a=begin(s);self.assertFalse(a.exists('state:x'));b=begin(s);write(b,'state:x',4);b.commit()
        with self.assertRaises(ContractError):a.commit()
    def test_delete_recreate_aba_rejected(self):
        s=seed(VersionedStore());a=begin(s);a.read('state:x');b=begin(s);b.delete('state:x');b.commit();c=begin(s);write(c,'state:x',1);c.commit()
        self.assertEqual(s.snapshot().cells['state:x'].version,3)
        with self.assertRaises(ContractError):a.commit()
    def test_returned_values_cannot_mutate_store(self):
        s=VersionedStore();a=begin(s);write(a,'state:list',[1,2]);a.commit();b=begin(s);x=b.read('state:list');x.append(3)
        self.assertEqual(b.read('state:list'),[1,2])
    def test_abort_discards_draft(self):
        s=seed(VersionedStore());a=begin(s);write(a,'state:x',9);a.abort();self.assertEqual(s.snapshot().cells['state:x'].value(),1)
        with self.assertRaises(ContractError):a.commit()
    def test_schema_migration_explicit(self):
        s=seed(VersionedStore());a=begin(s)
        with self.assertRaises(ContractError):write(a,'state:x',1,versions=VersionSet(state='2',ontology='1'))
        write(a,'state:x',1,versions=VersionSet(state='2',ontology='1'),migration='state-v2');a.commit()
    def test_reject_external_effects(self):
        tx=begin(VersionedStore())
        for kind in ['send_email','payment','publish']:
            with self.assertRaises(ContractError):tx.external_effect(kind)
    def test_scope_and_expiry(self):
        scope=Scope('s',frozenset({'worker'}),frozenset('Z'),expires_step=1)
        with self.assertRaises(ContractError):VersionedStore().begin(scope=scope,actor='worker',step=2)
        tx=begin(VersionedStore())
        with self.assertRaises(ContractError):tx.write('state:x',1,type_name='X',component='host',versions=V)
    def test_sensitive_payload_rejected(self):
        tx=begin(VersionedStore())
        for field in ['label','hidden_solution','password','api_key']:
            with self.assertRaises(ContractError):write(tx,'state:x',{'nested':{field:'x'}})
    def test_duplicate_commit_identity(self):
        s=VersionedStore();a=begin(s,transaction_id='same');write(a,'state:x',1);a.commit();b=begin(s,transaction_id='same');write(b,'state:x',2)
        with self.assertRaises(ContractError):b.commit()

class FilesAndRecovery(unittest.TestCase):
    def test_multifile_generation_visibility(self):
        with tempfile.TemporaryDirectory() as root,AtomicWorkspace(root) as w:
            first=w.commit({'a':'old-a','b':'old-b'},expected_generation=None)
            w.commit({'a':'new-a','b':'new-b'},expected_generation=first)
            self.assertEqual((w.read('a'),w.read('b')),(b'new-a',b'new-b'))
    def test_stale_file_version(self):
        with tempfile.TemporaryDirectory() as root,AtomicWorkspace(root) as w:
            w.commit({'a':'1'},expected_generation=None)
            with self.assertRaises(ContractError):w.commit({'a':'2'},expected_generation=None)
    def test_crash_before_commit_aborts(self):
        with tempfile.TemporaryDirectory() as root:
            with AtomicWorkspace(root) as w:
                w.commit({'a':'old','b':'old'},expected_generation=None)
                with self.assertRaises(SimulatedCrash):w.commit({'a':'new','b':'new'},expected_generation=w.generation,crash_at='after_prepare')
                with self.assertRaises(ContractError):w.read('a')
            with AtomicWorkspace(root) as w:self.assertEqual((w.read('a'),w.read('b')),(b'old',b'old'))
    def test_crash_after_commit_replays_all(self):
        for point in ['after_commit','after_publish']:
            with tempfile.TemporaryDirectory() as root:
                with AtomicWorkspace(root) as w:
                    w.commit({'a':'old','b':'old'},expected_generation=None)
                    with self.assertRaises(SimulatedCrash):w.commit({'a':'new','b':'new'},expected_generation=w.generation,crash_at=point)
                with AtomicWorkspace(root) as w:self.assertEqual((w.read('a'),w.read('b')),(b'new',b'new'))
    def test_store_recovery_committed_state(self):
        with tempfile.TemporaryDirectory() as root:
            with AtomicWorkspace(root) as w:
                s=seed(VersionedStore(w));a=begin(s);write(a,'state:x',7);write(a,'state:y',8)
                with self.assertRaises(SimulatedCrash):a.commit(crash_at='after_commit')
                s.recover();self.assertEqual((s.snapshot().cells['state:x'].value(),s.snapshot().cells['state:y'].value()),(7,8))
            with AtomicWorkspace(root) as w:self.assertEqual(VersionedStore(w).snapshot().cells['state:x'].value(),7)
    def test_torn_tail_only_is_repairable(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'journal';j=Journal(p);j.append('audit','t',{'count':1})
            with p.open('ab') as f:f.write(b'{"partial":')
            self.assertTrue(j.scan().torn_tail);self.assertTrue(j.repair_torn_tail());self.assertEqual(len(j.scan().records),1)
    def test_complete_line_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'journal';j=Journal(p);j.append('audit','t',{'count':1});p.write_bytes(p.read_bytes().replace(b'"count":1',b'"count":2'))
            with self.assertRaises(ContractError):j.scan()
    def test_manifest_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with AtomicWorkspace(root) as w:head=w.commit({'a':'1'},expected_generation=None)
            p=Path(root)/'generations'/head;p.write_text('{}')
            with self.assertRaises(ContractError):AtomicWorkspace(root)
    def test_single_coordinator(self):
        with tempfile.TemporaryDirectory() as root,AtomicWorkspace(root) as w:
            with self.assertRaises(ContractError):AtomicWorkspace(root)
    def test_path_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as root,AtomicWorkspace(root) as w:
            for name in ['../escape','/tmp/escape','a/../escape','a\\b']:
                with self.assertRaises(ContractError):w.commit({name:'bad'},expected_generation=w.generation)
    def test_journal_limit_is_finite(self):
        with tempfile.TemporaryDirectory() as root:
            j=Journal(Path(root)/'j',max_records=2);j.append('a','1',{});j.append('a','2',{})
            with self.assertRaises(ContractError):j.append('a','3',{})

class Branches(unittest.TestCase):
    def test_private_branch_commit(self):
        s=seed(VersionedStore());m=BranchManager(s,scope=SCOPE,actor='worker');a=m.fork('a');write(a.transaction,'state:x',5)
        self.assertEqual(s.snapshot().cells['state:x'].value(),1);m.merge('a');self.assertEqual(s.snapshot().cells['state:x'].value(),5)
    def test_competing_branches_conflict(self):
        s=seed(VersionedStore());m=BranchManager(s,scope=SCOPE,actor='worker');a=m.fork('a');b=m.fork('b');write(a.transaction,'state:x',5);write(b.transaction,'state:x',6);m.merge('a')
        with self.assertRaises(ContractError):m.merge('b')
    def test_nested_merge_and_ancestry(self):
        s=seed(VersionedStore());m=BranchManager(s,scope=SCOPE,actor='worker');a=m.fork('a');write(a.transaction,'state:x',5);b=m.fork('b',parent='a');self.assertEqual(b.transaction.read('state:x'),5);write(b.transaction,'state:y',6)
        self.assertEqual(m.ancestry('b'),('a','b'));m.merge('b');m.merge('a');self.assertEqual(s.snapshot().cells['state:y'].value(),6)
    def test_child_can_delete_parent_pending_creation(self):
        s=VersionedStore();manager=BranchManager(s,scope=SCOPE,actor='worker')
        parent=manager.fork('parent');write(parent.transaction,'state:new',1)
        child=manager.fork('child',parent='parent');child.transaction.delete('state:new')
        manager.merge('child');manager.merge('parent')
        self.assertNotIn('state:new',s.snapshot().cells)
    def test_nested_conflict_does_not_average(self):
        s=seed(VersionedStore());m=BranchManager(s,scope=SCOPE,actor='worker');a=m.fork('a');b=m.fork('b',parent='a');b.transaction.read('state:x');write(a.transaction,'state:x',6)
        with self.assertRaises(ContractError):m.merge('b')
    def test_branch_budget_and_discard(self):
        s=seed(VersionedStore());m=BranchManager(s,scope=SCOPE,actor='worker',budget=StepBudget(max_branches=1));a=m.fork('a');write(a.transaction,'state:x',99);m.discard('a')
        with self.assertRaises(ContractError):m.fork('b')
        self.assertEqual(s.snapshot().cells['state:x'].value(),1)

class Scheduling(unittest.TestCase):
    def scheduler(self,**kw):return FiniteScheduler(seed(VersionedStore()),scope=SCOPE,actor='worker',input_digest='input-v1',**kw)
    def test_event_execution_and_clock(self):
        s=self.scheduler();s.enqueue(Event('a','increment',due_time=9,causal_time=12));r=s.run({'increment':RegisteredHandler(increment)})
        self.assertEqual(r.status,'complete');self.assertEqual(r.clock.scheduler_step,1);self.assertEqual(r.clock.causal_time,13);self.assertEqual(r.clock.cognitive_phase,'advanced')
    def test_finite_queue(self):
        s=self.scheduler(max_queue=1);s.enqueue(Event('a','increment'))
        with self.assertRaises(ContractError):s.enqueue(Event('b','increment'))
    def test_duplicate_event_not_replayed(self):
        s=self.scheduler();e=Event('a','increment');s.enqueue(e);s.run({'increment':RegisteredHandler(increment)})
        with self.assertRaises(ContractError):s.enqueue(e)
    def test_stale_event_fails(self):
        s=self.scheduler();s.enqueue(Event('a','increment',expected_versions=(('state:x',0),)));r=s.run({'increment':RegisteredHandler(increment)})
        self.assertEqual(r.failed,('a',));self.assertEqual(s.store.snapshot().cells['state:x'].value(),1)
    def test_retry_bound(self):
        def fail(ctx,event):raise ContractError('Transient','fixed fixture error',recoverable=True)
        s=self.scheduler();s.enqueue(Event('a','f'));r=s.run({'f':RegisteredHandler(fail)})
        self.assertEqual(r.processed,3);self.assertEqual(r.failed,('a',));self.assertEqual([a['status'] for a in s.audit],['retry','retry','failed'])
    def test_budget_exhaustion_keeps_queue(self):
        s=self.scheduler(budget=StepBudget(max_steps=1));s.enqueue(Event('a','increment'));s.enqueue(Event('b','increment'));r=s.run({'increment':RegisteredHandler(increment)})
        self.assertEqual(r.status,'budget_exhausted');self.assertEqual(r.queued,1)
    def test_expired_scope_records_terminal_failure(self):
        scope=Scope('expired',frozenset({'worker'}),frozenset('Z'),expires_step=0)
        s=FiniteScheduler(seed(VersionedStore()),scope=scope,actor='worker',input_digest='v1');s.enqueue(Event('a','increment'))
        self.assertEqual(s.run({'increment':RegisteredHandler(increment)}).failed,('a',))
    def test_missing_handler_fails(self):
        s=self.scheduler();s.enqueue(Event('a','missing'));self.assertEqual(s.run({}).failed,('a',))
    def test_policy_gate_before_callback(self):
        called=[];s=self.scheduler();s.enqueue(Event('a','research'));r=s.run({'research':RegisteredHandler(lambda c,e:called.append(1),'model_forward')})
        self.assertEqual(called,[]);self.assertEqual(r.failed,('a',));self.assertEqual(s.audit[0]['code'],'ResearchForbidden')
    def test_emission_validation_before_commit(self):
        def duplicate(ctx,event):return EventResult((Write('state:x',99,'Scalar','Z',V),),(Event('a','f'),))
        s=self.scheduler();s.enqueue(Event('a','f'));s.run({'f':RegisteredHandler(duplicate)});self.assertEqual(s.store.snapshot().cells['state:x'].value(),1)
    def test_resume_safe_boundary(self):
        s=self.scheduler();s.enqueue(Event('a','increment'));s.enqueue(Event('b','increment'));s.run({'increment':RegisteredHandler(increment)},max_events=1)
        with tempfile.TemporaryDirectory() as root,AtomicWorkspace(root) as w:
            s.checkpoint(w);r=FiniteScheduler.resume(w,s.store,scope=SCOPE,actor='worker',input_digest='input-v1');r.run({'increment':RegisteredHandler(increment)})
            self.assertEqual(r.store.snapshot().cells['state:x'].value(),3);self.assertEqual(r.meter.steps,2)
    def test_resume_rejects_changed_inputs_or_state(self):
        s=self.scheduler()
        with tempfile.TemporaryDirectory() as root,AtomicWorkspace(root) as w:
            s.checkpoint(w)
            with self.assertRaises(ContractError):FiniteScheduler.resume(w,s.store,scope=SCOPE,actor='worker',input_digest='changed')
            a=begin(s.store);write(a,'state:x',4);a.commit()
            with self.assertRaises(ContractError):FiniteScheduler.resume(w,s.store,scope=SCOPE,actor='worker',input_digest='input-v1')

class Invalidation(unittest.TestCase):
    def setup_index(self,root):
        i=DependencyIndex(root);i.add('a',[],'input-a');i.add('b',['a'],'input-b');i.add('c',['b'],'input-c');return i
    def finish(self,i,root,key):
        (Path(root)/(key+'.txt')).write_text(key);(Path(root)/(key+'.check')).write_text('finite check passed')
        i.start(key);i.finish(key,[key+'.txt'],[key+'.check'],expected_input_digest='input-'+key)
    def test_dependency_ready_and_done_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            i=self.setup_index(root);self.assertEqual(i.ready(),('a',));self.finish(i,root,'a');self.assertEqual(i.ready(),('b',))
    def test_input_change_invalidates_descendants(self):
        with tempfile.TemporaryDirectory() as root:
            i=self.setup_index(root)
            for key in ['a','b','c']:self.finish(i,root,key)
            self.assertEqual(i.invalidate({'a':'new'}),('a','b','c'));self.assertEqual(i.ready(),('a',))
    def test_hash_change_invalidates_on_resume(self):
        with tempfile.TemporaryDirectory() as root:
            i=self.setup_index(root);self.finish(i,root,'a');self.finish(i,root,'b');i.save('checkpoint.json');(Path(root)/'a.txt').write_text('changed')
            j=DependencyIndex.resume(root,'checkpoint.json');self.assertEqual(j.records['a'].status,'pending');self.assertEqual(j.records['b'].status,'pending')
    def test_interrupted_running_becomes_pending(self):
        with tempfile.TemporaryDirectory() as root:
            i=self.setup_index(root);i.start('a');i.save('checkpoint.json');j=DependencyIndex.resume(root,'checkpoint.json');self.assertEqual(j.ready(),('a',))
    def test_cannot_claim_missing_checks(self):
        with tempfile.TemporaryDirectory() as root:
            i=self.setup_index(root);i.start('a')
            with self.assertRaises(ContractError):i.finish('a',[],[],expected_input_digest='input-a')
    def test_blocker_requires_specific_reason(self):
        with tempfile.TemporaryDirectory() as root:
            i=self.setup_index(root)
            with self.assertRaises(ContractError):i.terminal('a','blocked','')
            i.terminal('a','blocked','dependency permission absent');self.assertEqual(i.ready(),())

class IRLoops(unittest.TestCase):
    def make_ir(self):
        from latent_comm.compiler import Compiler
        from latent_comm.compiler.types import NodeCapability
        cap=NodeCapability('Increment','Increment',(('in0','Scalar'),),(('out0','Scalar'),),frozenset('Z'),frozenset('Z'),'exact','deterministic_given_inputs',('fixture',),('schema',),'fixture:increment','test')
        r={'schema_version':3,'id':'loop','objects':{'a':{'type':'Scalar'},'b':{'type':'Scalar'}},'nodes':[{'id':'inc','operation':'Increment','inputs':{'in0':'a'},'outputs':{'out0':'b'}}],'bounded_loops':[{'id':'three','body':['inc'],'max_iterations':3,'carried':[['b','a']]}]}
        return Compiler({'Increment':cap}).compile(r)
    def test_carry_loop_executes_exact_three_steps(self):
        r=execute_fixture_ir(self.make_ir(),{'a':0},{'inc':FixtureOperation(lambda d:{'out0':d['in0']+1})});self.assertEqual(r.objects['a'],3);self.assertEqual(r.steps,3)
    def test_fixture_budget_never_lifted_by_ir(self):
        with self.assertRaises(ContractError):execute_fixture_ir(self.make_ir(),{'a':0},{},budget=StepBudget(max_steps=2))
    def test_fixture_dimension_cannot_exceed_budget(self):
        with self.assertRaises(ContractError):execute_fixture_ir(self.make_ir(),{'a':[1,2,3]},{},budget=StepBudget(max_dimension=2))
    def test_research_dispatch_never_runs(self):
        with self.assertRaises(ContractError):execute_research_ir(self.make_ir())
    def test_no_model_imports(self):
        subprocess.run([sys.executable,'-c',"import sys; import latent_comm.runtime; assert not any(x in sys.modules for x in ['torch','transformers'])"],check=True)

if __name__=='__main__':unittest.main()
