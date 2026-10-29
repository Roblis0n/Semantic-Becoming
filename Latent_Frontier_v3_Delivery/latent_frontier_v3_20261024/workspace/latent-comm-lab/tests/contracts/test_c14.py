import unittest,json
from dataclasses import replace
from latent_comm.core import VersionSet,ContractError
from latent_comm.compositions.c14 import *
from latent_comm.mechanisms.h22_legacy.types import StateCell
from latent_comm.mechanisms.h27_ontology.types import Predicate

def fixture():
 v=VersionSet(state='s1',ontology='o1',isa='i1',frame='f1',task='t1',evidence='e1')
 branch=BranchState('main',(),(('phase',(.2,)),),(),frozenset(),(),'ordered',frozenset({'e1'}),'o1','q1','snapshot1',v)
 cell=StateCell('c','scalar',(.2,),'f1',frozenset({'a','b'}),frozenset({'a','b'}),'ab',0)
 partition=PartitionState((('ab',frozenset({'a','b'})),),(cell,),frozenset({'cache-old'}),'s1',v)
 action=PartitionAction('isolate',('ab',),'a-only',frozenset({'a'}),frozenset({'c'}),'s1','s2')
 old=ConceptDefinition('old',Predicate('eq','seen',True),(),('e1',),('seen',));new=ConceptDefinition('new',Predicate('eq','usable',True),('old',),('e1',),('usable',))
 return StructureTransitionInput(branch,partition,OntologySnapshot('o1',(old,),(('reader','old'),)),(-1.,1.),action,(new,),('old',),(('reader','new'),),'o2','evidence1',None,None,False,v)
class C14Tests(unittest.TestCase):
 def test_atomic_ontology_and_partition(self):
  q=fixture();r=run_reference(q);cells={c.key:json.loads(c.payload_json) for c in r.value.visible_cells}
  self.assertEqual(r.value.status,'Committed');self.assertEqual(cells['ontology:active']['version'],'o2');self.assertEqual(cells['state:partition']['versions']['ontology'],'o2');self.assertEqual(q.ontology.version,'o1');self.assertEqual(q.partition.version,'s1');self.assertEqual(len(r.audit),6);self.assertEqual(r.value.proposed.invalidated_cache_refs,frozenset({'cache-old'}))
 def test_read_only_conflict_blocks_both_writes(self):
  r=run_reference(replace(fixture(),concurrent_key='evidence:read_only')).value
  self.assertEqual(r.status,'ConflictPreserved');self.assertEqual(r.conflicts,('evidence:read_only',));self.assertTrue(all(c.version==0 for c in r.visible_cells if c.key!='evidence:read_only'))
 def test_prepare_crash_aborts(self):
  r=run_reference(replace(fixture(),crash_at='after_prepare')).value;self.assertEqual(r.status,'RecoveredAborted');self.assertTrue(all(c.version==0 for c in r.visible_cells))
 def test_publish_crash_recovers_atomic_side(self):
  r=run_reference(replace(fixture(),crash_at='after_publish')).value;self.assertEqual(r.status,'RecoveredCommitted');self.assertEqual(dict((c.key,c.version) for c in r.visible_cells)['ontology:active'],1)
 def test_rollback_monotonic_versions(self):
  r=run_reference(replace(fixture(),rollback_after_commit=True)).value;self.assertEqual(r.status,'RolledBackWithNewCellVersions');c=next(c for c in r.visible_cells if c.key=='ontology:active');self.assertEqual(c.version,2);self.assertEqual(json.loads(c.payload_json)['version'],'o1')
 def test_no_new_access(self):
  q=fixture()
  with self.assertRaises(ContractError):run_reference(replace(q,partition_action=replace(q.partition_action,members=frozenset({'intruder'}))))
 def test_retired_reader_requires_migration(self):
  with self.assertRaises(ContractError):run_reference(replace(fixture(),reader_targets=()))
if __name__=='__main__':unittest.main()
