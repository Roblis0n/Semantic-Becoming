"""Q02 release-scope credential/path scan and truthful authority evidence.

Heuristic scanning is not a proof that arbitrary secrets cannot exist. It does
not read unrelated user locations or credential stores, and invokes no research
entry point. Run after media provenance sanitization for a final clean scan.
"""
from pathlib import Path
import ast,datetime,hashlib,json,re,zipfile
import build_release as release
W=release.W
PATTERNS={
 'private_key_material':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
 'openai_style_secret':re.compile(r'\bsk-[A-Za-z0-9_-]{24,}\b'),
 'aws_access_identifier':re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
 'github_secret':re.compile(r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{24,}\b'),
 'capability_url':re.compile(r'https?://[^\s"<>]+(?:[?&](?:X-Amz-Signature|sig|token|api_key|access_token)=)[^\s"<>]+',re.I),
}
TEXT_SUFFIXES={'.py','.md','.json','.jsonl','.txt','.csv','.tsv','.tex','.bib','.lua','.sh','.html','.css','.js','.svg','.srt','.vtt','.xml','.ssml','.toml','.yaml','.yml','.log','.sha256'}
SELF_OUTPUTS={'run_state/checks/Q02_release_secret_scan.json','reports/permission_review.json'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def examine(name,text,findings):
 for category,pattern in PATTERNS.items():
  for match in pattern.finditer(text):findings.append({'path':name,'category':category,'line':text.count('\n',0,match.start())+1,'matched_value_disclosed':False})
 if name.startswith('assets/audio/tts_ai/') and not name.endswith('.py'):
  for match in re.finditer(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',text,re.I):
   findings.append({'path':name,'category':'transient_provider_capability_identifier','line':text.count('\n',0,match.start())+1,'matched_value_disclosed':False})

def scan():
 findings=[];text_files=0;xml_parts=0;paths=[];font_files=[]
 for path in release.work_files():
  name=path.relative_to(W).as_posix();paths.append({'path':name,'sha256':sha(path),'bytes':path.stat().st_size})
  if name in SELF_OUTPUTS:
   paths.pop();continue
  if path.suffix.lower() in {'.ttf','.otf','.woff','.woff2'}:font_files.append(name)
  if path.suffix.lower() in TEXT_SUFFIXES:
   try:text=path.read_text(encoding='utf-8')
   except UnicodeError:continue
   examine(name,text,findings);text_files+=1
  elif path.suffix.lower() in {'.pptx','.docx'}:
   with zipfile.ZipFile(path) as archive:
    for info in archive.infolist():
     if info.filename.endswith(('.xml','.rels')):
      examine(name+'!'+info.filename,archive.read(info).decode('utf-8','replace'),findings);xml_parts+=1
  if path.is_symlink() or not path.resolve().is_relative_to(W):findings.append({'path':name,'category':'path_escape'})
 if font_files:findings.extend({'path':p,'category':'bundled_font_forbidden'} for p in font_files)
 result={'scan_scope':'generated release-included workspace files and OOXML XML parts only; no unrelated private access','scanned_files':len(paths),'text_files_scanned':text_files,'ooxml_parts_scanned':xml_parts,'file_hashes':paths,'findings':findings,'bundled_font_files':font_files,'limits':['Heuristic credential patterns cannot prove absence of every possible secret.','Historical absolute workspace paths are provenance, not credentials or operational authority.','Synthetic URL placeholders in policy tests are not real authentication credentials.','Current audio capability limitation is actual unsupported audio input; signal analysis is not listening.'],'research_state':'NOT_RUN'}
 result['self_generated_audit_outputs_excluded_from_scan_and_hash']=sorted(SELF_OUTPUTS)
 out=W/'run_state/checks/Q02_release_secret_scan.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k!='file_hashes'},ensure_ascii=False,indent=2));return result

if __name__=='__main__':
 result=scan();raise SystemExit(bool(result['findings']))
