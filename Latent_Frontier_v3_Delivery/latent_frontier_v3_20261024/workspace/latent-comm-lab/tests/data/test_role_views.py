import unittest
from dataclasses import replace
from latent_comm.core import *
from latent_comm.data import *

V=VersionSet(state='s1',ontology='o1',isa='i1',frame='f1',world='w1',task='t1',evidence='e1')
P=ProjectionContract(('task',),('clues',),('query',),(('task','public problem definition without answer'),))
def fixture():
    return WorldFactory(StructureSignature('family','v1','add(x,y)'),P).fixture({'task':'add','clues':(1.,2.),'query':(3.,),'hidden_solution':6}, {'sum':6},versions=V)

class RoleDataTests(unittest.TestCase):
    def test_world_role_supervision_separation(self):
        r=fixture();self.assertEqual(r.supervision.targets['sum'],6);self.assertNotIn('sum',r.sender_view.features)
        self.assertNotIn('record_id',RoleBatch(Visibility.SENDER,(r.sender_view,)).model_records()[0])
    def test_projection_unknown_fields_not_forwarded(self):
        s,r=P.project({'task':'add','clues':(1.,),'query':(2.,),'unapproved':'private'},V)
        self.assertEqual(tuple(s.features),('clues',));self.assertEqual(tuple(r.features),('query',))
    def test_projection_reason_required(self):
        with self.assertRaises(ContractError):ProjectionContract(('task',),(),(),())
    def test_model_collator_rejects_full_record_and_mixed_roles(self):
        r=fixture()
        with self.assertRaises(ContractError):RoleBatch(Visibility.SENDER,(r,))
        with self.assertRaises(ContractError):RoleBatch(Visibility.SENDER,(r.sender_view,r.receiver_view))
    def test_padded_mask_distinguishes_real_zero(self):
        a=RoleView(Visibility.SENDER,{'task':'t'},{'clues':(0.,2.)},V);b=RoleView(Visibility.SENDER,{'task':'t'},{'clues':(0.,)},V)
        x=collate_finite_numeric(RoleBatch(Visibility.SENDER,(a,b)),'clues')
        self.assertEqual(x.values,((0.,2.),(0.,0.)));self.assertEqual(x.valid_mask,((True,True),(True,False)))
    def test_seed_not_part_of_structure_signature(self):
        s=StructureSignature('f','v1','same-program');m=partition_templates((s,),salt='fixed')
        self.assertEqual(m.for_template(s),m.for_template(s));self.assertNotIn('seed',s.canonical())
    def test_partition_before_sampling_and_no_duplicate_template(self):
        s=StructureSignature('f','v1','a');m=partition_templates((s,),salt='x')
        with self.assertRaises(ContractError):m.for_template(StructureSignature('f','v1','b'))
        with self.assertRaises(ContractError):partition_templates((s,s),salt='x')
    def test_novel_composition_reserved(self):
        s=StructureSignature('f','v1','a+b',concept_combination=('a','b'));m=partition_templates((s,),salt='x',novel_compositions=frozenset({('a','b')}))
        self.assertEqual(m.for_template(s).split,'novel_composition')
    def test_derivation_preserves_partition_and_structure(self):
        p=SplitProvenance('test','s','m');self.assertEqual(derived_provenance((p,),('parent',),'s').split,'test')
        with self.assertRaises(ContractError):derived_provenance((p,replace(p,split='train')),('p','q'),'s')
        with self.assertRaises(ContractError):derived_provenance((p,),('p',),'new_structure')
    def test_bulk_generator_locked_before_callback(self):
        s=StructureSignature('f','v1','p');m=partition_templates((s,),salt='x');calls=[]
        g=generate_dataset(m,lambda *args:calls.append(args),instances_per_template=2,seed=1)
        with self.assertRaises(ContractError):next(g)
        self.assertEqual(calls,[])
    def test_fixture_cannot_be_relabelled_as_training(self):
        r=fixture()
        with self.assertRaises(ContractError):replace(r,split_provenance=replace(r.split_provenance,split='train'))
    def test_encoded_roles_preserve_live_identity_without_model_execution(self):
        from latent_comm.packets import LiveTensor
        class ShapeDescriptor:
            shape=(2,1)
        r=fixture();origin=RoleBatch(Visibility.SENDER,(r.sender_view,));value=ShapeDescriptor()
        live=LiveTensor(value,TensorSpec(('item','channel'),(2,1),'float32','sender_feature','adapter'))
        encoded=EncodedRoleBatch(origin,'clues',(live,));self.assertIs(encoded.tensors[0].value,value)
        with self.assertRaises(ContractError):EncodedRoleBatch(origin,'clues',(LiveTensor(value,replace(live.spec,semantic_role='supervision')),))
    def test_tensor_collation_is_locked(self):
        r=fixture()
        with self.assertRaises(ContractError):collate_tensor(RoleBatch(Visibility.SENDER,(r.sender_view,)),'clues',device='cpu',dtype_name='float32')
    def test_nested_leak_rejected_before_factory(self):
        with self.assertRaises(ContractError):P.project({'task':'t','clues':{'nested':{'world_seed':2}},'query':(1.,)},V)

if __name__=='__main__':unittest.main()
