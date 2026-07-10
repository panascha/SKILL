# MedSuite — Handoff

## Phase
**(e) — Manual-handoff chaining: CODE-COMPLETE + HEADLESS-VERIFIED (new surface).** Notes .md
→ Generate input. Only the end-to-end "→ quiz" tail is key-blocked (redundant: same code path
phase (b) already live-verified). Phases (a)–(d) DONE; (d) live-verify still pending.

### Phase (e) — DONE (all in `MedSuite/convert.py`)
File handoff, NOT a shared DB (advisor-confirmed). Scope = **Generate only** (Convert globs
`*.pdf` + extracts existing MCQs; a note has none). Scans the **filesystem**, not `notes_sessions`,
so a later session picks up an earlier Notes run.
- Backend (after `/api/notes/download`): `NOTES_HANDOFF_KINDS = {enrich: lecture-enrich.md,
  summary: lecture-summary.md}`. `GET /api/notes/outputs` scans `notes_output/batch_*/<lec>/`,
  lists a kind only if that exact file exists (stopped run w/ only markdown → omitted).
  `POST /api/notes/use-as-lecture {batch,lecture,kind}` → basename-strip + resolve-under-
  `NOTES_OUTPUT_BASE` traversal guard + basename whitelist → `shutil.copyfile` into
  `LECTURE_DIR/<lecture>_<kind>.md`. Re-pick OVERWRITES (snapshot semantics, intended).
  Existing `run_generation` reads it unchanged (`LECTURE_DIR / Path(filename).name`).
- Frontend (HTML_PAGE, inline): "📥 จาก Notes" picker in `#sectionGenerate` (reuses
  `file-scroll`/`lec-item` styling, no new CSS). JS `loadNotesOutputs` (called on first switch
  to Generate, next to `loadGeneratorFiles`) + `useNotesOutput` (mirrors `uploadFile`'s
  post-action: copy → refresh → auto-select).
- **VERIFY headless PASS** (`test_handoff.py`, Flask test_client, no key, 15 checks): listing
  200 + enrich/summary listed + stopped-lec omitted + size present; copy → `01_TestLec_enrich.md`
  in LECTURE_DIR, content verbatim, appears in `/api/generator-files`; re-pick overwrites (no dup);
  bad kind → 400; traversal batch → 404; missing lecture → 404. Boot smoke :8765 clean (no cp874),
  4 HTML markers render, `/api/notes/outputs` → `{outputs:[]}`. Fixture cleaned.
- Minor deferral (advisor-OK): two batches sharing a `folder_stem` collide on the copied name
  (`<lecture>_<kind>.md`) — plain overwrite, fine for verify; add a batch discriminator only if wanted.

## (d) — Saved keys + rotation
BACKEND + UI + HEADLESS TESTS ALL DONE. Only LIVE verify pending (needs real Gemini keys).
Phase (c) done+headless-verified; its LIVE run also pending.

### Phase (d) VERIFY — headless PASS (scratchpad, no key/network)
- `test_rotation.py` (Site 1 `run_conversion`, faked clients+process_pdf, 4 cases ALL PASS):
  CASE1 429→rotate KEY same model→done `[K0/M0,K1/M0]`; CASE2 503→NO rotate, model-fallback
  same key→done `[K0/M0,K0/M1]` (proves the don't-rotate-on-503 fix); CASE3 single-key 429→
  model-fallback; CASE4 all keys×all models 429→`partial`, full traversal, no hang.
- `test_keys_routes.py` (Flask test_client, 13 checks ALL PASS): GET/POST/DELETE, dedup 400,
  empty 400, disk-persist, mask `AIza…0001`, `build_key_list` order+dedup (typed first),
  guard accepts saved-key-only (empty typed → files-error not key-error), guard still 400 when
  truly no key, HTML renders panel markers (`savedKeysList`/`saveKeyBtn`/`loadSavedKeys`/
  `savedKeyCount`/`deleteSavedKey`).
- Real boot `PYTHONUTF8=1 python convert.py` :8765 → `/api/keys`=`{keys:[],ok:true}`, `/`=200,
  no cp874 crash. Server killed after.
- **Site 2 (`generate_content_with_fallback`) — separately tested** (advisor: its loop is different
  code from Site 1, not "the same primitive"). `test_generate_site2.py` (3 cases PASS): A 429→rotate
  key same model; B 503→NO rotate, model advance, idx stays 0; C 429 all keys→`pool.reset()`+model
  downgrade→ok. **Behavior change while here:** pre-(d) this helper NEVER downgraded model on 429
  (the model-advance `break` was 503-only) — it raised. Now 429-with-keys-exhausted downgrades the
  model + `pool.reset()` (last resort), matching Site 1 + the plan's "downgrade model only when all
  keys exhausted." 429 no longer does same-key backoff-retry (rotate/advance immediately, like
  Site 1); 503 keeps its backoff. Bounded by #keys×#models, no hang.
- **Site 3 (Notes) — FIXED then tested** (advisor caught a real hole). Notes uploads the slide via
  Files API then passes the key-bound handle to `generate()`, so `_call`-level rotation was WRONG
  (rotate → key0's file handle on key1 → file-not-found) AND upload never rotated (429 on upload
  before generate). Fix: **removed `func_factory` from `generate()`/`_call`**; added
  `GoogleProvider.rotate_key()` + `current_masked`; rotation now happens at the **LECTURE level** in
  `run_notes_batch` — on 429 rotate key + re-run the whole lecture (upload+generate on one key);
  model-fallback only once all keys exhausted. `test_notes_rotation.py` (2 cases PASS): CASE1 429→
  rotate→rerun on key1→done (`seen=[0,1]`, rotate+lecture_done emitted); CASE2 both keys 429→rotate
  exhausts→model-fallback→lecture_error, no hang (`seen=[0,1,1]`).
- **Chat-chain gap still stands** (enrich→crystal): a 429 mid-chat won't switch key (chat bound to
  old client); degrades to model-fallback. Narrow, documented, deferred.
- **Generate large-PDF (>20MB Files-API) path:** upload/delete stay on captured `client` (=key0),
  paired per file; generate rotates. Same key-bound-handle class as notes but not lecture-wrapped —
  large decks on an exhausted key0 fail the upload. Inline <20MB path (the common case) rotates
  fine. Documented limitation, not fixed (out of (d) verify scope).

### Phase (d) LIVE verify — TODO (needs user Gemini key(s))
Save 2 keys via the panel (or type one + save). Exhaust key1 (free-tier 20 req/day) → confirm the
log line `🔑 คีย์ชนโควตา (429) → สลับไปคีย์ถัดไป AIza…xxxx` and the run completes on key2. Also the
still-pending phase (c) LIVE: Notes tab, 1 slide → 5-stage + zip; Stop mid-run → partial+stopped.
While on the Notes run, eyeball that a 429 renders a `rotate` node in the progress tree (verified by
inspection — `notesEnsureStep` creates a node for any step id, same as the existing `fallback` node —
just confirm visually).

### UI wiring (phase d, all inline in HTML_PAGE)
Panel added after the shared `#apiKey` field: `#savedKeysList` (masked rows + ✕ delete) +
`#saveKeyBtn` (saves the typed key). CSS `.sk-list/.sk-row/.sk-del/.sk-add` (scoped, dark-theme
vars). JS: `renderSavedKeys` (sets global `savedKeyCount`), `loadSavedKeys` (on page load),
`addSavedKey`, `deleteSavedKey`. All 4 client-side `!apiKey` guards relaxed to
`!apiKey && !savedKeyCount` (else the alert blocks saved-key-only runs before POST).

---
### (archived) Phase (d) backend detail

### Phase (d) — IN PROGRESS (backend complete, all on disk in `MedSuite/convert.py`)
Design was advisor-reviewed. Rotation rule: **429/RESOURCE_EXHAUSTED → rotate KEY (same model);
only when all keys exhausted → downgrade model + `pool.reset()`. 503/timeout → model-fallback,
NO rotation, pool.idx untouched.** (Advisor's load-bearing fix: don't rotate on 503.)

DONE:
- `SAVED_KEYS_FILE = BASE_DIR/"saved_keys.json"` + `.gitignore` (new, in MedSuite) ignores it.
- Helpers (after NOTES paths): `_sanitize_key`, `load_saved_keys`, `save_saved_keys`, `mask_key`,
  `build_key_list(typed_key)` (typed key FIRST, then saved, dedup), and **`KeyPool`** class
  (lazy per-key client cache, `current_client`/`current_masked`/`rotate()→bool`/`reset()`).
- **Site 1 `run_conversion`:** single client → `pool = KeyPool(keys, http_options=...)`. Model loop
  now has an inner while: on `is_rate_limit` `pool.rotate()` → retry SAME model next key; else break.
  Model-fallback branch splits `is_rate_limit` vs `is_unavailable`; `pool.reset()` ONLY on rate_limit.
- **Site 2 `generate_content_with_fallback(job, pool, ...)`:** sig changed client→pool; on 429
  `pool.rotate()`+continue before backoff. `run_generation` builds pool; passes `pool` at call
  (L~1340). Files API upload/delete still on captured `client` (=key0) — paired, one key per file
  (large-deck upload rotation NOT covered; inline <20MB path is the common case → fine).
- **Site 3 `GoogleProvider`:** `__init__(...,keys=None)` builds `self._pool`; added `_rotate_key`;
  `_call(...,func_factory=None)` rotates on 429 + re-binds func; `generate()` passes
  `func_factory=lambda:self.client.models.generate_content`; `with_model` shares `self._pool`.
  `run_notes_batch` builds provider with `keys=build_key_list(api_key)`.
  **Chat-chain gap (advisor-OK deferral):** a 429 mid enrich→crystal chat won't switch key (chat
  bound to old client) — degrades to model-fallback, not worse. Documented, not fixed.
- **Guards relaxed (all THREE routes):** `/api/run`, `/api/retry`, `/api/notes/run` now accept an
  empty typed key when saved keys exist (`if not build_key_list(api_key): 400`).
- **New routes:** `GET /api/keys` (masked list), `POST /api/keys` (add, dedup), `DELETE
  /api/keys/<int:idx>`. Persist to gitignored file under `_keys_lock`.

TODO (next session, in order):
1. **Headless test BOTH directions** (advisor-mandated, monkeypatch — no key needed): key0 429 →
   rotates to key1 → success (plan verify); AND key0 503 → does NOT rotate, `pool.idx` stays 0,
   falls to model-fallback. Second test is what proves the don't-rotate-on-503 fix. Test all 3
   sites if practical; Site 1 `run_conversion` is the priority (most surgery).
2. **UI manage-keys panel** — small masked list + add/remove near the shared `#apiKey` box in
   `HTML_PAGE`. Wire to `/api/keys` GET/POST/DELETE. Keep JS inline (`n-`-style scoping not needed;
   it's shared chrome). Typed key still works as ad-hoc key[0].
3. Run `PYTHONUTF8=1 python convert.py` :8765, boot smoke.
4. LIVE verify (needs user Gemini key(s)): save 2 keys → exhaust key1 (429) → confirm auto-rotate
   to key2 in logs (look for `🔑 คีย์ชนโควตา (429) → สลับไปคีย์ถัดไป`). Also still-pending phase (c)
   LIVE: Notes tab 1 slide → 5-stage + zip; Stop mid-run → partial + stopped.

Next real phase after (d): **(e) manual-handoff chaining** (Notes `.md` → Generate input).

## State
**Phase (c) COMPLETE (headless).** Notes tab grafted into `MedSuite/convert.py`. Phase (a)(b)
done+verified (below). Phase (e–f) untouched. Phase (f) destructive + gated.

### Phase (c) — Notes tab graft (all in `MedSuite/convert.py`)
Decision (advisor-reviewed): kept Notes on its OWN transport — **SSE + `notes_sessions` +
`GoogleProvider`** — NOT ported to MedSuite's polling/`_jobs` model, because the per-lecture×
per-step progress TREE needs structured events polling can't reconstruct. Verbatim graft also
eases phase (f) "reproduces each tool's output".

**Backend (before the routes block):**
- Paths: `NOTES_PROMPTS_DIR = BASE_DIR/"prompts"` (6 .md copied from lecture-pipeline; only 5
  wired — `gemini-transcribe.md` unused, transcript step uses `lecture-synthesizer.md`).
  `NOTES_OUTPUT_BASE = BASE_DIR/"notes_output"` — kept OUTSIDE `output/` so `api_outputs` /
  `organize_output.py` never scan it. Added `import queue, random`. Bumped
  `MAX_CONTENT_LENGTH` 200→500 MB (large slide decks).
- Grafted verbatim: `GoogleProvider` (own pacing 13s/5RPM + 503/429 retry + frontier→2.5
  fallback), `_safe_stem`, `run_single_lecture` (5 steps, chat-chains enrich→crystal, resume-
  from-stage via `uploaded_*_path`), `run_notes_batch` (was `run_batch_pipeline`).
- **CANCEL THREADED IN NOW** (advisor: no later phase adds it). `notes_sessions[sid]["cancel"]`,
  checked at every step boundary via `cancel_check`→`NotesCancelled`; batch loop also checks
  before each lecture. On cancel: break → package partial → `state="stopped"`,
  `done` event carries `cancelled=True`. `state` in {idle,running,stopped,done,error}.
- Routes: `/api/notes/run` (POST multipart, 1–20 lectures), `/api/notes/progress/<sid>` (SSE),
  `/api/notes/cancel/<sid>` (POST, 404/400 guarded), `/api/notes/download/<sid>`.

**Frontend (HTML_PAGE, all inline):**
- 3rd mode button `📝 สรุปเลกเชอร์` → `setMode('notes')`. setMode now toggles `.cg-only` config
  sections (Course Preset + Extra Prompt hidden in notes), swaps footers (shared `.run-wrap` ⇄
  `#notesRunWrap`) and right panels (`#cgRightPanel` ⇄ `#notesRightPanel`).
- `#sectionNotes`: cooldown field + lecture cards (per-card: label, slide/transcript/curriculum
  drop-zones, transcript textarea, resume `.md` inputs, per-step checkbox selector). Reuses the
  SHARED `#apiKey` + `#modelSelect`.
- `#notesRightPanel`: per-lecture×per-step SSE progress tree + package card + download banner.
- All Notes CSS/JS **`n-`-prefixed + `#sectionNotes`/`#notesRightPanel`-scoped** → ZERO collision
  with Convert/Generate. Dropped the source's global `*{}`/`body{}` reset (advisor landmine #1).
  Reuses shared `escHtml`/`escJs`. JS fns: `notesAddLecture/…/notesStart/notesStop/notesHandleEvent`.

### Phase (c) VERIFY — headless PASS (scratchpad `test_notes.py`, monkeypatched provider, no key)
- CASE 1 normal (2 lectures, steps slide_md+enrich+crystal): 2× lecture_done, `state=done`,
  `cancelled=False`, all 3 output .md per lecture written, zip ok.
- CASE 2 cancel (trip during lecture 0): `state=stopped`, `done.cancelled=True`, lecture 2 never
  started, partial markdown saved, partial zip ok.
- Boot smoke (real server :8765): `/` renders all notes markers; `/api/notes/progress|cancel/nope`
  →404; `/api/notes/run` no-key →400; Convert `/api/files` →200 (regression intact). Py syntax OK.

### ⚠️ Deferred to phase (d) — DO NOT MISS (advisor-flagged)
1. **Two Gemini call sites now.** Key rotation must wire into BOTH `generate_content_with_fallback`
   (convert/generate) AND `GoogleProvider._call` (notes). The parallel subsystem means notes is a
   SECOND rotation site.
2. **Plan Target says "shared job+poll engine"** — Notes deliberately does NOT share it (SSE).
   Conscious deviation, recorded here. Notes Stop works (cancel threaded); it just uses its own
   transport. Retry-remaining for notes is NOT built (resume-from-stage exists in the pipeline via
   `uploaded_*_path`, but no UI wires it) — no scheduled phase covers it; revisit if wanted.

### Phase (c) LIVE verify — TODO (needs user Gemini key)
Run `PYTHONUTF8=1 python convert.py`, Notes tab → upload 1 slide PDF → 5-stage output + zip;
Stop mid-run → partial saved + `stopped`.

---

<details><summary>Phase (a)(b) archived detail</summary>

**Phase (b) COMPLETE.** Backend + HTML graft + live end-to-end all verified. Phase (a) done
+ verified (below).

### Phase (b) HTML graft — DONE (all inline in `MedSuite/convert.py` HTML_PAGE)
- Mode switcher (`.mode-switch`, `setMode()`): Convert ⇄ Generate; hides Subject-Code field in
  Generate; swaps run-button label; lazy-loads generator files on first switch.
- `#sectionGenerate`: old-exam `<select>` + upload, lecture list `#lectureList` (per-row
  num_questions + topic_title inputs via `lectureMeta` map), lecture/old-exam upload buttons.
- One `run()` dispatcher → `startConversion()` / `startGeneration()`. Generate POST sends
  `mode:generate, lecture_files:[{filename,num_questions,topic_title}], old_exam_file, additional_prompt`.
- **Morphing action button** `#actionBtn`: **Stop** while running (`POST /api/cancel`, first UI
  trigger for the phase-a cancel route) → **Retry** when ended with pending (`POST /api/retry/<id>`,
  api_key+model only). Shown when `state in (stopped,partial)` && pending.length.
- Advisor-flagged fixes applied: `startRetry` REUSES `currentJobId` (server holds pending); both
  start paths reset `lastLogCount=0` via `beginJobUI()` (runners wipe job logs on entry); idle
  run-label branches on `currentMode`; lecture list NOT rebuilt in the poll loop (status via logs).
- New JS helpers: `loadGeneratorFiles`, `renderLectures`, `toggleLecture`, `setLectureMeta`,
  `uploadFile`, `escJs`.

### Phase (b) LIVE VERIFY — ALL PASS (real Gemini, both user keys)
- Generate from `test_lec.md` slide → 2 Qs, merged into shared `output/quizdata.js`.
- Batch [real, missing `ghost.md`] → `state=partial`, `pending=[ghost.md]` (scoped correctly),
  `done=2/2`, real Qs still merged.
- Retry (key1) → re-ran ONLY ghost (`total=1`); key1 hit free-tier daily quota (20 req/day) → 429,
  stayed partial (key exhaustion, not a bug — motivates phase-d rotation).
- Retry (key2) → ghost `success` (2 Q), `state=done`, `pending=[]` cleared, merged.
- Shared `quizdata.js`: convert (`MD_*`) + generate categories coexisted, `unique==count` (no dup).
- Test artifacts cleaned (slides, `generated_*` dirs, test categories stripped from quizdata.js).
- **Note:** Gemini derived its own category (`LEC_51TEST1`, `GHOST_51MCQ1`) instead of the literal
  `topic_title` — that's prompt/`sanitize_category` behavior, out of HTML-graft scope; flag if the
  CATEGORY MANDATE is supposed to be verbatim.

### (archived) Phase (b) BACKEND DONE + headless-verified

### DONE (backend, all in `MedSuite/convert.py`)
- Consts `LECTURE_DIR`/`OLD_EXAMS_DIR`/`GENERATOR_PROMPT_FILE` (+ dirs); `medical-ai-generator.md` copied in.
- Helpers grafted: `generate_content_with_fallback`, `extract_sample_questions`, and NEW
  `merge_into_global_quizdata(job, job_new_data)` (locked read-merge-write). `run_conversion`
  refactored to call the helper (was inline L877–912).
- `run_generation` grafted + fixed: phase-a cancel/state wiring; `done`+result at EVERY unit
  boundary via inner `_fail()` (fixes lost-done on the 4 continues); inline PDF <20MB else
  Files API; `.md/.txt` as text; sanitize via MedSuite canonical `sanitize_category(q, stem)`
  (NO 3rd arg — MedSuite's 3rd param is subject_code_override, NOT the generator's override_topic;
  prompt's CATEGORY MANDATE carries topic_title); shared locked merge; per-lecture
  `output/generated_<stem>/generated_<stem>.json`; ZIP; `pending_units` for retry.
- Retry: runners store `mode`+`static_params`+`pending_units` on job (NOT api_key). New
  `POST /api/retry/<job_id>` reads key from body, re-invokes same runner with only pending.
  State: pending→`stopped`(cancelled)/`partial`(failed); none→`done`.
- Routes: `/api/generator-files`, `/api/upload/<file_type>`, `/api/run` mode-dispatch
  (`mode=generate`→run_generation), `/api/retry`. Added `_jobs_lock` around check-and-mark
  in run+retry. `new_job()` seeds mode/pending_units/static_params.
- **5 bugs:** #1 done-counting FIXED; #2 inline<20MB FIXED; #3 re.escape ABSENT in this version
  (documented); #4 _jobs lock FIXED; #5 subject_title defaults "" (no crash) — decide UI in HTML step.

### Verified headless (scratchpad, no key) — ALL PASS
- `test_generate.py` (13 checks): fail file 2/3 → done==3, state==partial, pending==[file2],
  quizdata.js has CVS+NS not GI; retry pending → done, all 3 cats, no dup (CVS still 1 Q);
  cancel after file1 → stopped, done==1, only file1 saved.
- `test_routes.py`: all new routes registered; retry 404/400, run 400 validation; Convert-mode
  regression (merge helper) → done + quizdata.js written + pending empty.

### REMAINING for phase (b)
1. **HTML graft** into `MedSuite/convert.py` `HTML_PAGE` (Convert-only today). Source =
   `Medical MCQ generator/convert.py` HTML (L1433+). Lift: Mode Switcher (L2399–2403,
   `setMode()`), Generate section `#sectionGenerateMode` (L2419–2442: lecture upload+list,
   old-exam upload+list, num_questions/topic inputs), and JS state+funcs (L2550+: `setMode`,
   `uploadFile`, `loadGeneratorFiles`, lecture/old-exam selection, `lectureQCounts`,
   `lectureTopicTitles`). WIRE (inline, don't blind-carve): POST `/api/run` must send
   `mode`, `lecture_files:[{filename,num_questions,topic_title}]`, `old_exam_file` in generate
   mode. Add a **Retry** button shown when `state in (stopped,partial)` && `pending_units.length`
   → POST `/api/retry/<job_id>` with api_key+model. Keep Convert UI + Thai UI intact. Decide
   subject_title: drop from payload or restore field (backend tolerates absent).
   Markup/CSS bulk may go to a subagent (advisor: keep JS wiring inline); user hasn't OK'd a
   spawn — do inline unless they ask.
2. **Live verify (needs user Gemini key):** generate a quiz from 1 slide → output + merged
   quizdata.js; fail one file → Retry redoes only it; Convert+Generate share one quizdata.js.
   Run server `PYTHONUTF8=1 python convert.py` :8765.

### Phase (b) plan (advisor-reviewed)
Backend first, headless-tested, THEN HTML (carve markup to subagent, keep JS wiring inline).
1. Assets: copy `medical-ai-generator.md` into MedSuite; add `input_lectures/`,
   `input_old_exams/` dirs + `LECTURE_DIR`/`OLD_EXAMS_DIR`/`GENERATOR_PROMPT_FILE` consts.
2. Helpers: bring `generate_content_with_fallback` + `extract_sample_questions` from generator.
   Extract run_conversion's locked merge (L877–912) into `merge_into_global_quizdata(job, data)`
   under `_quizdata_lock`; call from BOTH runners (advisor item 1 — do NOT copy generator's
   unlocked merge; that reintroduces the race on the shared file).
3. `run_generation` graft + fixes: cancel/state wiring (phase-a pattern); `done`+result at
   EVERY unit boundary incl. the 4 `continue`s (advisor item 2); inline <20MB path (bug #2);
   shared locked merge; track succeeded → `pending_units` for retry.
4. Retry: runners store `mode` + `static_params` + `pending_units` on job (NOT api_key —
   advisor item 5). `POST /api/retry/<job_id>` reads key from body, re-invokes the same runner
   with only `pending_units`. Retryable state: pending non-empty → `stopped`(cancelled) or
   `partial`(failed/exhausted); all done → `done` (fixes phase-a quota→"done" TODO).
5. Routes: `/api/generator-files`, `/api/upload/<file_type>`, extend `/api/run` (mode=generate),
   `/api/retry`. (`api_outputs` already lists `generated_*` dirs — no change.)
6. HTML: mode switcher + Generate panel + upload + Retry button (markup→subagent, wiring inline).
7. Headless tests (monkeypatch Gemini, like phase-a `test_cancel.py`): done-counting, cancel,
   retry-pending (fail file 2/3 → pending==[file2], retry runs only it, quizdata.js has all 3).

### Bug notes
- `re.escape`: L198 is `re.escape(kw)` (keyword, already escaped). `file_stem` only ever a
  regex *subject* (L71–91), needs no escaping. **Bug absent in this version** — confirm no
  `stem`-as-pattern site during graft; do NOT cite the `kw` line as the fix.
- `subject_title`: defaults `""` in api_run → no crash; dead feature only. Decide restore-vs-drop
  when doing the Convert UI.
- `_jobs` lock: pre-mark `running=True` before thread start already covers most TOCTOU; add a
  small lock around check-and-mark in api_run + retry only. Don't over-build.

## Phase (a) — DONE + fully verified

- **DONE — build.** `med/MedSuite/` created by copying `Medical MCQ convert/`
  (convert.py, medical-quiz-converter.md, courses/, .claude/, organize_output.py,
  validate_categories.py, CLAUDE.md, README.md, input_pdfs/ [6 PDFs], empty output/).
- **DONE — cancel/state wiring** in `MedSuite/convert.py` (5 surgical edits, additive only):
  1. `new_job()` +`cancel:False` +`state:"idle"`.
  2. `run_conversion` start: reset `cancel`, `state="running"`.
  3. client-fail early return: `state="error"`.
  4. per-file loop top: `if job.get("cancel"): cancelled=True; break` (unit boundary).
  5. tail guard: if cancelled → `state="stopped"` (skip progress=100 + success log); else
     `state="done"`. `running=False` always.
  6. new route `POST /api/cancel/<job_id>` → sets `job["cancel"]`, 404 if unknown, 400 if not running.

## Verify — last results
- ✅ **Code-diff** original vs MedSuite `convert.py`: every changed line is cancel/state
  wiring, nothing else (deterministic proof Convert path is unchanged; Gemini output is
  non-deterministic so a literal output diff is meaningless — this is the real proof).
- ✅ **Boot**: `python convert.py` serves Thai UI on :8765, `/api/files` lists 6 PDFs,
  `/api/cancel/nope` → 404.
- ✅ **Cancel mechanics** (deterministic, no key — scratchpad `test_cancel.py`,
  monkeypatched `process_pdf`): 4-file batch, cancel after file 1 → file 2 never started,
  partial `quizdata.js` saved, `state="stopped"`, `running=False`, `done=1/4`. PASS.
- ✅ **`/api/cancel` route** (Flask test_client, no key — scratchpad `test_route.py`):
  unknown job → 404; running job → 200 + `cancel` flag set; not-running job → 400, flag
  untouched. PASS.
- ✅ **Live end-to-end schema smoke** (real Gemini key, `gemini-3.5-flash`, 3 BIOCHEM PDFs):
  all 3 converted from the fresh copy → `output/<stem>/<stem>.json` + merged `quizdata.js`.
  `MD47_BIOCHEM_MCQ3.json` = 37 Q, all 8 MDKKU keys, exactly 5 choices, answer verbatim in
  choices, 2-element category. Proves the copied folder runs end-to-end (Gemini round-trip +
  parse + write to new `output/`), not just source-identical.
- ✅ **Live mid-batch cancel** (real Gemini, 3-file batch, cancel the instant file 1
  finished): `done=1/3`, `running=false`, `state="stopped"`; files 2-3 never started,
  partial saved. Confirms the real-timing composition, not just the stubbed/route tests.

**➡️ PHASE (a) FULLY VERIFIED — ready for phase (b).**

Note: the doubled `BIOCHEM_BIOCHEM` in one category is a PRE-EXISTING `sanitize_category`
quirk from the filename — identical in the original tool (code-diff proves it), out of
phase-(a) scope.

## Next steps
1. Phase (a) is closed. Phase (b): graft Generate mode (`run_generation` @ generator L827)
   + upload endpoints (generator L1306–1360) + fix the 5 known bugs + wire retry-remaining
   (re-run only failed/unreached units) onto the shared cancel/state engine built in (a).
2. Reuse the `cancel`/`state`/`cancelled` pattern from (a) for Generate's per-file boundary.

## Keys
User supplied 2 Gemini keys during (a). Used the FIRST for the live smoke only; **not
persisted to any file** (passed via POST body / inline env). Proper storage = phase (d):
gitignored key file + rotation (429 → next key; downgrade model only when all keys exhausted).

## Gotchas
- **Windows console cp874 crashes `print()` on emoji** (⏳/⏹️ in push_log). Run any CLI/test
  with `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`. Pre-existing in original code — do NOT strip
  the emojis (Thai UI preserved). Real server run needs UTF-8 console.
- In-flight file when cancel fires **finishes** and lands in partial output; only the *next*
  file is skipped (per plan — can't kill mid-Gemini-call). Do NOT check cancel inside `process_pdf`.
- Both SDKs already on `google-genai`; note app's requirements.txt is stale.
- Generate reads `.md`/`.txt` as lecture text input (enables phase-e chaining).
- **Phase (f) is destructive + GATED** — move 3 originals to `med/_archive/` only after user
  confirms MedSuite reproduces each tool's output on real input. Not on our say-so.
- `BASE_DIR = Path(__file__).parent` → copying the folder relocates all paths automatically.
- **Phase (b) TODO (state semantics):** on quota-exhaustion the loop breaks with
  `cancelled=False` → tail sets `state="done"`, so a quota-killed run currently reports
  "done". Fine for phase (a) (only stopped-vs-done matters), but phase (b) retry-remaining
  must distinguish *exhausted/failed* from *cleanly complete* — add a distinct state there.

</details>
