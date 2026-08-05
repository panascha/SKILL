# MedSuite — Handoff

## Phase
**(e2) — Notes flat per-PDF output: CODE-COMPLETE + HEADLESS-VERIFIED + BOOT-SMOKED.** (unchanged from prior)

## Current status (as of this session)
**Python transforms updated (Convert + Generate) + prompt instructions aligned.**

- Convert mode (`medical-quiz-converter.md` + `DEFAULT_SYSTEM_PROMPT`) now enforces a **single-string** `category` field (per the mandate).
- Generate mode (`medical-ai-generator.md`) consistently emits single-string `category` values with the `by_AI` pattern and underscores.
- `sanitize_category()` regularly returns a single CategoryID string; `quizdata.js` merge keys on that string.

**Category-doubling defect FIXED (this session).** `sanitize_category()` used to re-prefix a category
the model had already returned complete, producing doubled ids
(`CONCEPT_by_AI_RADIO_RS_by_AI_RADIO_Topic`). Now: if the model's value already contains `_by_AI_`,
it is honoured as-is (subject from the model, or `subject_code_override` when set; a leading `LEC_`
on the tail is dropped to keep the LEC contract `<subject>_by_AI_<Topic>`). Shared normalizer
extracted as `normalize_category()`.

**CategoryID format LOCKED to the upload target (user-confirmed golden):**
`<SubjectCode>_by AI_<SubGroup>_<Topic Label>` — separator is `_by AI_` (space, not underscore),
and the topic label keeps its spaces. Example: `RS_by AI_RADIO_Imaging RS`.
Reference copy: `scratchpad/quizdata.GOLDEN-FORMAT.js`.
- `CATEGORY_SEP` constant in convert.py; `normalize_category()` no longer converts spaces to `_`.
- `sanitize_category()` accepts BOTH `_by_AI_` (legacy model output) and `_by AI_`, always emits `_by AI_`;
  underscores inside the topic label become spaces (SubGroup token preserved, LEC still gets none).
- Prompts updated: `medical-ai-generator.md` (19), `medical-quiz-converter.md` (5),
  and the 3 UI prompt-builder templates in convert.py.
- Topic-label *wording* (short `Imaging RS` vs long lecture title) is content, not format — it comes
  from `topic_title`/the model; no shortening rule was encoded.

**Existing output repaired** — all 10 `output/generated_*` dirs + `output/quizdata.js`: 265 questions
re-keyed to `RS_by_AI_<SubGroup>_<Topic>`, plus 30 questions in `generated_L44-45 Symptomatology...`
that had `"setting": None` instead of `"select": ""` (model one-off; the prompts never mention
`setting`). Backup of pre-repair `output/` is in this session's scratchpad only.
`output/generated_quiz_20260801_213919.zip` was NOT repaired — it is pre-fix and stale.

**New: `validate_format.py`** — schema validator for Convert + Generate output.
`PYTHONUTF8=1 python validate_format.py [name-filter] [--self-test]`; exit 1 on ERROR.
Currently reports 0 errors / 0 warnings over 265 questions in 11 files.

**Stale, NOT fixed:** `validate_categories.py` still treats `category` as an array (`q["category"][1]`,
lines 101-103) — broken since the single-string migration, unrelated to this session.
`DEFAULT_SYSTEM_PROMPT` (convert.py ~line 361) shows a third format `SubjectCode_YearGroup_TopicLabel`;
only reachable if `medical-quiz-converter.md` goes missing.
`output/generated_quiz_20260801_213919.zip` is two generations behind (pre-category-fix AND pre-format-change).

**Note:** both `CLAUDE.md` files still document `category` as a 2-element array and `quizdata.js` keys
as `CVS_51MCQ1`. Code and data are single-string `<Subject>_by_AI_<SubGroup>_<Topic>`. Docs stale.

**End-to-end integration test is still pending** (waiting for a real Gemini key run over mixed Convert + Generate to confirm the category schema alignment in the cumulative file).

## Next steps (unchanged from prior)
- Phase (d) live-verify (needs Gemini key(s)) → Notes 1 slide → 5-stage, key rotation on 429 at lecture level.
- Phase (e) head-to-tail live smoke: Notes → pick "จาก Notes" → Generate run using the handoff lecture.
- Phase (f) gated (destructive archive of originals).

Remainder of prior handoff material (phase e1, d, a–c, gotchas) preserved below.

--- (archived detail preserved from prior handoff) ---
[Prior content retained as-is for continuity]
