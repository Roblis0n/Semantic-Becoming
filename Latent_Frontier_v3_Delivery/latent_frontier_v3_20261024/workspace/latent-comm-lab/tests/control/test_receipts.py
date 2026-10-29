"""Pure filesystem/identity contracts for portable authoring receipts."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import task_checkpoint as ck

class ReceiptContracts(unittest.TestCase):
    def test_relative_identity_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);old=root/'old';new=root/'delivery';work=new/'workspace/latent-comm-lab';work.mkdir(parents=True)
            for plan in (old,new):(plan/'specs').mkdir(parents=True)
            raw=b'{"tasks": []}';binding={'PLAN_ROOT':str(old),'task_graph_sha256':hashlib.sha256(raw).hexdigest()}
            for plan in (old,new):(plan/'specs/task_graph.json').write_bytes(raw)
            self.assertEqual(ck.locate_plan(work,binding),new)
            (new/'specs/task_graph.json').write_text('{}')
            with self.assertRaises(ValueError):ck.locate_plan(work,binding)
            (new/'specs/task_graph.json').unlink();self.assertEqual(ck.locate_plan(work,binding),old)
            (old/'specs/task_graph.json').unlink()
            with self.assertRaises(ValueError):ck.locate_plan(work,binding)
    def test_directory_add_remove_and_mutation_invalidate(self):
        saved=(ck.WORK,ck.TASKS,ck.input_digest)
        with tempfile.TemporaryDirectory() as td:
            try:
                ck.WORK=Path(td);ck.TASKS={'T':{'outputs':['artifacts/'],'receipt':'receipt.json'}};ck.input_digest=lambda *a,**k:'input'
                directory=ck.WORK/'artifacts';directory.mkdir();source=directory/'source.txt';source.write_text('original')
                receipt={'status':'done','input_digest':'input','outputs':ck.output_files('T'),'checks':[]};(ck.WORK/'receipt.json').write_text(json.dumps(receipt))
                self.assertEqual(ck.verify_receipt('T')['status'],'done')
                extra=directory/'unrecorded.txt';extra.write_text('extra')
                with self.assertRaises(ValueError):ck.verify_receipt('T')
                extra.unlink();source.write_text('mutated')
                with self.assertRaises(ValueError):ck.verify_receipt('T')
                source.unlink()
                with self.assertRaises(ValueError):ck.verify_receipt('T')
            finally:ck.WORK,ck.TASKS,ck.input_digest=saved

    def test_sync_missing_receipt_resets_stale_terminal_ledger(self):
        saved = (ck.WORK, ck.TASKS, ck.RUNTIME_DEPENDENCIES)
        with tempfile.TemporaryDirectory() as td:
            try:
                ck.WORK = Path(td)
                ck.TASKS = {'T': {'dependencies': [], 'receipt': 'receipts/T.json'}}
                ck.RUNTIME_DEPENDENCIES = {}
                (ck.WORK / 'run_state').mkdir()
                ledger = {'tasks': {'T': {'status': 'done'}}, 'completed_tasks': ['T']}
                (ck.WORK / 'run_state/ledger.json').write_text(json.dumps(ledger), encoding='utf-8')
                result = ck.sync()
                self.assertEqual(result['done'], [])
                self.assertEqual(result['ready'], ['T'])
                current = json.loads((ck.WORK / 'run_state/ledger.json').read_text(encoding='utf-8'))
                self.assertEqual(current['tasks']['T']['status'], 'pending')
            finally:
                ck.WORK, ck.TASKS, ck.RUNTIME_DEPENDENCIES = saved

if __name__=='__main__':unittest.main()
