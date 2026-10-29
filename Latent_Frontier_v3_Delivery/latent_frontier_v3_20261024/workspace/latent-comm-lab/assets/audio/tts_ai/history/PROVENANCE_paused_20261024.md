# Current production status

External production is paused pending explicit user permission to disclose the remaining 493 narration characters to api.tts.ai. There are 43 accepted records and 42 downloaded cue WAVs, all with credits_used 0. One previously accepted 16-character cue remains outcome-unknown; it is not being polled. The 90-second narrated edition is created and objectively checked. The six-minute narrated edition is not complete. No replacement silence is presented as missing narration.

Private recovery state is preserved outside the deliverable. Project receipts and logs are sanitized and contain no returned download URLs or job capability identifiers. Resume requires an explicit private recovery directory; missing pending state never triggers resubmission. No network action may resume until appropriate user permission is established.

# Mandarin narration provenance and restrictions

Provider: TTS.ai. Official API: https://tts.ai/api/ . Anonymous endpoint: https://api.tts.ai/v1/tts/ . Model: melotts. Voice: ZH. Language: zh. Provider speed: 1.0. Output: mono PCM WAV. No account, authentication token, payment, premium fallback, voice clone, or speech-recognition service is used.

License restriction: PERSONAL AND NONCOMMERCIAL USE ONLY. This applies to the generated speech and videos containing it. Do not use these editions for monetized channels, advertising, client work, sale, or business purposes under this free-tier license. Source: https://tts.ai/terms/ , section 7(a), effective 2026-09-14, checked 2026-10-24. This production did not purchase or obtain a commercial license.

The planned source contains 1,754 public/synthetic narration characters in 58 caption-sized requests across 17 scenes. At the pause, 1,261 characters have been submitted in 43 requests, 42 WAVs have been downloaded, and the remaining 493 characters have not been sent. Further disclosure requires explicit user authorization. Available request receipts preserve exact submitted text, response status, credits_used and actual downloaded-audio hashes. The prior successful 47-character capability probe is not repeated. Official free-tier limits are 500 characters/request, 5,000/day/IP and 10 requests/minute; this script permits only one in-flight job and at least 8 seconds between API requests. It stops instead of buying credits, creating an account, or blindly retrying an uncertain submission.

Completed short-edition audio timing is measured from generated PCM frame counts; long-edition assembly is incomplete. Local signal processing trims only leading/trailing near-silence, applies a recorded bounded tempo factor of 0.80–1.10, and inserts documented pauses to retain the 90/360-second scene budgets. Subtitles cover exactly one generated chunk at a time with small nonoverlapping display margins. This is not word-level forced alignment and uses no ASR.

Loudness, clipping, silence intervals and stream validity are measured locally. Actual auditory review is not available in this worker. The narration has not been listened to and pronunciation is not certified. Narrated editions remain explicitly marked as synthesized and unauditioned until that check is completed.

TTS is media production, not execution of this research project. Further external narration disclosure is currently blocked pending explicit user authorization. All research models, neural adapters, training, evaluation and benchmark paths remain NOT_RUN. Silent visual editions and draft timing sources are preserved separately as history.
