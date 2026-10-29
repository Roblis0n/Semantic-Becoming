"""Regression checks for structural holdouts and batch version identity.

These fixtures use only finite metadata and never invoke a research entry point.
"""
import unittest
import copy
import json
from latent_comm.core import ContractError, RoleView, VersionSet, Visibility
from latent_comm.data.collate import RoleBatch, SupervisionBatch
from latent_comm.data.records import SupervisionView
from latent_comm.data.splits import StructureSignature, TemplateAssignment, SplitManifest, partition_templates
from latent_comm.learning.contracts import TrainingBatch, validate_batch_versions
from latent_comm.learning.source import validate_dataset_manifest, validate_training_record


class SplitAndBatchInvariants(unittest.TestCase):
    def test_generator_revision_cannot_move_a_structure_to_another_split(self):
        first=StructureSignature('family','v1','same-program',concept_combination=('a','b'))
        second=StructureSignature('family','v2','same-program',concept_combination=('b','a'))
        self.assertNotEqual(first.digest,second.digest)
        self.assertEqual(first.partition_digest,second.partition_digest)
        manifest=partition_templates((first,second),salt='2')
        self.assertEqual(manifest.policy_version,'structural-v2')
        self.assertEqual(manifest.for_template(first).split,manifest.for_template(second).split)
        with self.assertRaises(ContractError):
            SplitManifest((TemplateAssignment(first,'train'),TemplateAssignment(second,'test')),'manual','2')

    def test_reordered_novel_combination_is_always_held_out(self):
        template=StructureSignature('family','v1','program',concept_combination=('a','b'))
        manifest=partition_templates((template,),salt='fixed',novel_compositions=frozenset({('b','a')}))
        self.assertEqual(manifest.for_template(template).split,'novel_composition')

    def test_shards_must_follow_a_digest_bound_partition(self):
        train=StructureSignature('family','v1','train-template')
        heldout=StructureSignature('family','v1','heldout-template')
        partition=SplitManifest((TemplateAssignment(train,'train'),TemplateAssignment(heldout,'test')),'structural-v2','x')
        shards=[{'path':'train.jsonl','sha256':'a'*64,'split':'train','structure_signatures':[train.digest]},
                {'path':'test.jsonl','sha256':'b'*64,'split':'test','structure_signatures':[heldout.digest]}]
        manifest=json.loads(json.dumps(partition.dataset_manifest(shards)))
        self.assertEqual(validate_dataset_manifest(manifest).digest,partition.digest)
        bad=copy.deepcopy(manifest)
        bad['shards'][0]['structure_signatures'].append(heldout.digest)
        with self.assertRaises(ContractError):validate_dataset_manifest(bad)
        bad=copy.deepcopy(manifest);bad['split_manifest_digest']='0'*64
        with self.assertRaises(ContractError):validate_dataset_manifest(bad)
        bad=copy.deepcopy(manifest);del bad['split_manifest']
        with self.assertRaises(ContractError):validate_dataset_manifest(bad)

    def test_training_record_provenance_must_match_partition_and_structure(self):
        record={'purpose':'research_data','not_research_data':False,'structure_signature':'sig',
                'split_provenance':{'split':'train','template_signature':'sig','manifest_digest':'partition'}}
        validate_training_record(record,('sig',),'train','partition')
        for key,value in (('template_signature','other'),('manifest_digest','other'),('split','test')):
            bad=copy.deepcopy(record);bad['split_provenance'][key]=value
            with self.subTest(key=key), self.assertRaises(ContractError):
                validate_training_record(bad,('sig',),'train','partition')
        bad=copy.deepcopy(record);bad['not_research_data']=True
        with self.assertRaises(ContractError):validate_training_record(bad,('sig',),'train','partition')

    def test_explicit_axes_still_require_matching_schema_and_task(self):
        def batch(version):
            sender=RoleBatch(Visibility.SENDER,(RoleView(Visibility.SENDER,{}, {},version),))
            receiver=RoleBatch(Visibility.RECEIVER,(RoleView(Visibility.RECEIVER,{}, {},version),))
            supervision=SupervisionBatch((SupervisionView({}, {},'analytic'),))
            return TrainingBatch(sender,receiver,supervision,{})
        expected=VersionSet(schema='3',task='task-1',frame='frame-1')
        validate_batch_versions(batch(expected),expected,('frame',))
        for actual in (VersionSet(schema='4',task='task-1',frame='frame-1'),
                       VersionSet(schema='3',task='task-2',frame='frame-1')):
            with self.subTest(actual=actual), self.assertRaises(ContractError):
                validate_batch_versions(batch(actual),expected,('frame',))


if __name__=='__main__':
    unittest.main()
