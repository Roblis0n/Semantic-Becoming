"""Compose Q02 after the final sanitized artifact scan; no external actions."""
from pathlib import Path
import ast,datetime,hashlib,json
import task_checkpoint as ck
W=ck.WORK
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def bound(name):return {'path':name,'sha256':sha(W/name)}
def main():
 for dependency in ck.dependencies_for('Q02'):ck.verify_receipt(dependency)
 scan=json.loads((W/'run_state/checks/Q02_release_secret_scan.json').read_text())
 if scan['findings']:raise ValueError('release permission scan has unresolved findings')
 incident=json.loads((W/'src/latent_comm/learning/joint/audit_incident.json').read_text())
 media_manifest=json.loads((W/'assets/audio/tts_ai/manifest.json').read_text())
 chunks=media_manifest['chunks'];ids=[row['id'] for row in chunks]
 if len(ids)!=len(set(ids)) or len(ids)>64:raise ValueError('media receipt identity/case budget invalid')
 media_receipts=[];media_pending=[];media_unsubmitted=[]
 for row in chunks:
  receipt_path=W/f"assets/audio/tts_ai/public_receipts/{row['id']}.json"
  if not receipt_path.exists():media_unsubmitted.append(row);continue
  receipt=json.loads(receipt_path.read_text())
  if receipt['response']['credits_used']!=0 or receipt['request_body']['text']!=row['text'] or receipt['request_url']!=media_manifest['endpoint']:raise ValueError('media authority/completion receipt mismatch')
  if receipt['status']=='downloaded':media_receipts.append(receipt)
  else:media_pending.append(receipt)
 media_usage={'provider':media_manifest['provider'],'planned_requests':len(chunks),'planned_characters':sum(len(row['text']) for row in chunks),'accepted_requests':len(media_receipts)+len(media_pending),'accepted_characters':sum(r['characters'] for r in media_receipts+media_pending),'prior_probe_characters':media_manifest['budget']['prior_probe_characters'],'total_recorded_credits_used':sum(row['response']['credits_used'] for row in media_receipts+media_pending),'downloaded':len(media_receipts),'accepted_remote_outcome_pending':len(media_pending),'unsubmitted_chunks':len(media_unsubmitted),'unsubmitted_characters':sum(len(r['text']) for r in media_unsubmitted),'full_narration_complete':not media_pending and not media_unsubmitted,'all_public_text_matches_manifest':True,'license':media_manifest['license'],'provenance_manifest':bound('assets/audio/tts_ai/manifest.json')}
 generation=json.loads((W/'assets/audio/tts_ai/generation_summary.json').read_text())
 media_usage.update(unique_source_accepted_requests=media_usage['accepted_requests'],unique_source_characters=media_usage['accepted_characters'],accepted_requests=generation['accepted_submission_count'],accepted_characters=generation['accepted_submission_characters'],historical_unknown_submissions=generation['outcome_unknown_prior_submissions'],replacement_history=generation['replacement_history'])
 policy=ast.parse((W/'src/latent_comm/safety/policy.py').read_text())
 gate=next(n for n in policy.body if isinstance(n,ast.FunctionDef) and n.name=='require_research_action')
 statements=[s for s in gate.body if not(isinstance(s,ast.Expr) and isinstance(s.value,ast.Constant) and isinstance(s.value.value,str))]
 if not statements or not isinstance(statements[0],ast.Raise):raise ValueError('research gate is not unconditional rejection')
 result={
 'schema_version':1,'task_id':'Q02','reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'research_state':'NOT_RUN',
 'assessment':'No unresolved credential/path finding in the declared release scan. The recorded destination/payload authorization denial and guard-test deviation are disclosed rather than converted into blanket authorization claims. Mandatory auditory media QA remains blocked by verified unsupported audio input.',
 'authority':{'source_policy':'unchanged authoritative specs/execution_policy.json in the supplied v3 plan','plan_policy_sha256':sha(ck.PLAN/'specs/execution_policy.json'),'task_scope':'current replacement package only; old afternoon package withdrawn','execution_window_utc':['2026-10-27T10:45:00Z','2026-10-27T15:00:00Z'],'window_note':'User explicitly requested immediate early start today;15UTC is targetfinish, not a claim of elapsed execution' ,'maximum_code_writers':3,'one_owner_per_file':True,'environment':'assistant cloud workspace, not user computer'},
 'actions_reviewed':[
  {'category':'local source/design authoring','status':'authorized','evidence':'task receipts, output hashes and file ownership registry'},
  {'category':'public read-only source/documentation discovery','status':'authorized','evidence':'D01 source ledger retains observed identities, read level and limitations; not full-paper proof certification'},
  {'category':'finite/static checks','status':'authorized selected checks','evidence':'current per-file logs, AST/name-resolution reports and bounded stdlib fixtures; no neural imports in these runs'},
  {'category':'local PPT/SVG/PDF/audio-video assembly','status':'authorized','evidence':'actual native/rendered files, stream metadata and visual QA; media synthesis is not research inference'},
  {'category':'free third-party Mandarin TTS','status':'zero-new-cost media route with a recorded destination/payload permission interruption; see permission event','provider':'freeTTS.ai anonymous MeloTTS/ZH','official_api':'https://tts.ai/api/','data_sent':'existing public/synthetic Mandarin narration text only, not packages, private data, credentials or research datasets','new_account':False,'api_key_used':False,'paid_fallback':False,'terms':'https://tts.ai/terms/','privacy':'https://tts.ai/privacy/','license':'generated audio and videos containing it are personal/noncommercial only; this service restriction is not automatically applied to independent code/PPT/SVG/silent visuals','evidence':'final sanitized assets/audio/tts_ai provenance, per-cue public receipts and measured files'},
  {'category':'durable Library checkpoints and final artifact upload','status':'authorized user-owned delivery storage','evidence':'versioned checkpoints and final Library artifact identity; not public publication'},
  {'category':'research model execution','status':'NOT_RUN','denied':['download','initialize','load','forward','generate','train','eval','benchmark','research cloud API','random neural fixtures']},
  {'category':'purchases/publication/external messaging/unrelated private access/system changes','status':'not performed in the reviewed project actions','notes':'Local LaTeX cache/format construction stayed inside WORK_ROOT. No public site or repository deployment is authorized.'}
 ],
 'historical_guard_calls':{'total_attempt_count_claimed':None,'reason':'Historical gate-contract tests intentionally exercised rejection paths. Logs are retained; do not interpret model computation count zero as entrypoint invocation count zero. No exhaustive tool-level attempt counter is fabricated.','specific_audit_deviation':incident,'three_accidental_legacy_calls_credit':'not credited as approved checks; each denied before tensor/model construction or neural imports'},
 'verified_media_usage':media_usage,
 'destination_disclosure_permission_event':json.loads((W/'run_state/permission_events/tts_destination_disclosure_denial.json').read_text()),
 'post_denial_authorization':{'status':'explicit scoped grants recorded; all current raw audio downloaded','records':[json.loads((W/p).read_text()) for p in ['release/authorization_updates/20261025T0234_TTS_APPROVAL.json','release/authorization_updates/20261026_TTS_APPROVAL.json','release/authorization_updates/20261027_TTS036_APPROVAL.json']]},
 'second_historical_denial':json.loads((W/'run_state/permission_events/tts_continuation_denial_20261025.json').read_text()),
 'prior_transmission_note':'Earlier production used then-assumed generic media authority. Subsequent enforcement explicitly rejected continuation as insufficient destination/payload consent. Destination-specific authorization for those prior disclosures is not established by this audit; it is not labelled as blanket compliant. This report does not invent retroactive approval or erase that interruption.',
 'destination_specific_confirmation_for_initial_transmission':'NOT_ESTABLISHED_IN_AVAILABLE_EVIDENCE; explicit refusal and pending user clarification retained',
 'current_checks':[bound('run_state/checks/Q02_release_secret_scan.json'),bound('run_state/checks/Q02_allowed_policy_contracts.txt'),bound('run_state/checks/Q02_policy_test_preflight.json'),bound('run_state/checks/Q01_source_contract_inventory.json'),bound('run_state/checks/Q01_receipt_portability.txt'),bound('run_state/checks/Q01_release_contracts.txt')],
 'current_policy_contract_result':{'reuse_note':'Prior accepted checks reused because researchpolicy source unchanged; not rerun during media-only update','allowed_tests_run':6,'failures':0,'errors':0,'excluded_legacy_entry_tests':4,'neural_modules_loaded':[],'research_entry_invocations_in_Q02_checks':0},
 'credential_scan':{'scanned_files':scan['scanned_files'],'text_files':scan['text_files_scanned'],'ooxml_parts':scan['ooxml_parts_scanned'],'findings':[],'bundled_font_files':scan['bundled_font_files'],'scope':scan['scan_scope'],'self_generated_outputs_excluded':scan['self_generated_audit_outputs_excluded_from_scan_and_hash'],'limitations':scan['limits']},
 'platform_isolation':{'hard_sandbox_guaranteed':False,'implemented':'repository policy guards, typed action classification, workspace path fences, exact versioned receipts and shared finite budgets','actual_environment':'managed cloud filesystem/network tooling; no claim of proving host containment','limitations':['Text policy alone is not OS isolation.','Local transaction simulation is not distributed consensus.','Future source paths require a separately authorized research session; editing config does not grant permission.']},
 'audio_perception_capability':{'current_evidence':bound('reports/audio_input_capability_20261027.json'),'tested_by_parent':True,'actual_result':'audio content omitted because you do not support audio input','listening_performed':False,'pronunciation_review_performed':False,'consequence':'USER_WAIVED_NOT_PERFORMED under release/authorization_updates/20261027_AUDITION_SCOPE_CHANGE.json; stream decoding, nonsilence, timing, loudness and matching text are not listening'},
 'new_spend':0,'public_publication':False,'external_person_messages':False,'unrelated_private_access':False,'human_approval_fabricated':False
 }
 (W/'reports/permission_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'task':'Q02','scan_findings':0,'known_audit_deviation_calls':len(incident['guard_only_invocations']),'research_state':'NOT_RUN','permission_review_sha256':sha(W/'reports/permission_review.json')},indent=2))
if __name__=='__main__':main()
