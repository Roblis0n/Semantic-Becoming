"""Archive-path and self-reference boundary checks; no models or publication."""
from pathlib import Path
import hashlib,json,stat,sys,tempfile,unittest,zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
import build_release as release
class ReleaseContracts(unittest.TestCase):
    def info(self,name,mode=stat.S_IFREG|0o644):
        info=zipfile.ZipInfo(name);info.external_attr=mode<<16;return info
    def test_paths_duplicates_and_symlinks_reject(self):
        self.assertEqual(release.validate_archive_members([self.info('root/a.txt'),self.info('root/中文.md')]),2)
        for path in ('/absolute','../outside','root/../outside','C:/outside','root\\outside',''):
            with self.assertRaises((ValueError,IndexError)):release.validate_archive_members([self.info(path)])
        with self.assertRaises(ValueError):release.validate_archive_members([self.info('root/a'),self.info('root/a')])
        with self.assertRaises(ValueError):release.validate_archive_members([self.info('root/link',stat.S_IFLNK|0o777)])
    def test_portable_zip_aliases_cannot_overwrite_members(self):
        for path in ('root/./a.txt','root//a.txt','root/C:/file','root/a.','root/a '):
            with self.subTest(path=path), self.assertRaises(ValueError):
                release.validate_archive_members([self.info(path)])
        with self.assertRaises(ValueError):
            release.validate_archive_members([self.info('root/A.txt'),self.info('root/a.txt')])
    def test_seal_detects_byte_and_file_set_changes(self):
        old=release.W
        with tempfile.TemporaryDirectory() as td:
            try:
                release.W=Path(td);p=release.W/'source.py';raw=b'answer = 42\n';p.write_bytes(raw)
                manifest={'files':[{'path':'source.py','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}]};(release.W/'manifest.json').write_text(json.dumps(manifest))
                self.assertEqual(len(release.verify_seal()['files']),1)
                (release.W/'extra.py').write_text('extra = True')
                with self.assertRaises(ValueError):release.verify_seal()
                (release.W/'extra.py').unlink();p.write_text('changed')
                with self.assertRaises(ValueError):release.verify_seal()
            finally:release.W=old
    def test_postbuild_evidence_is_not_self_hashed(self):
        self.assertIn('run_state/receipts/Z02.json',release.POSTBUILD)
        self.assertIn('reports/release_integrity.json',release.POSTBUILD)
        self.assertIn('run_state/receipts/Z01.json',release.SEAL_EXCLUSIONS)
        self.assertIn('manifest.json',release.SEAL_EXCLUSIONS)
if __name__=='__main__':unittest.main()
