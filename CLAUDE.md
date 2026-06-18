# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

A personal skill/tool library for medical AI workflows, targeting KKU medical students. Three independent sub-projects live here alongside a markdown skill library:

| Path | What it is |
|---|---|
| `med/Medical MCQ convert/` | Flask app that converts MCQ PDFs → JSON/JS via Gemini |
| `med/Medical MCQ generator/` | Extended version that also *generates* new MCQs from lecture slides |
| `med/Medical note/lecture-pipeline/` | Flask app that runs a 5-step note-enrichment pipeline on lecture slides |
| `kku/` | KKU IntelSphere API skill (OpenAI-compatible LLM platform) |
| `index.html` | Single-page markdown viewer (static, no build step) |
| `engineering/`, `med/*.md`, `medical technologist/` | Prompt skill library (markdown only, no code) |

Each sub-project has its own `CLAUDE.md` with full detail. This file covers cross-cutting concerns.

---

## Running the apps

### MCQ Converter (`med/Medical MCQ convert/`)

```bash
pip install flask google-genai pymupdf pypdfium2 Pillow
python convert.py          # http://localhost:8765
```

Place input PDFs in `input_pdfs/`. Outputs land in `output/<stem>/`.

### MCQ Generator (`med/Medical MCQ generator/`)

```bash
pip install google-genai flask pymupdf Pillow
python convert.py          # http://localhost:8765
```

Place lecture slides in `input_lectures/`, old exam references in `input_old_exams/`, exam PDFs in `input_pdfs/`.

### Lecture Pipeline (`med/Medical note/lecture-pipeline/`)

```bash
pip install -r requirements.txt    # flask>=3.0.0, google-generativeai>=0.8.0
python app.py                      # http://localhost:5000
```

All 5 prompt `.md` files must exist in `prompts/` before running.

> **Windows note:** use `python`, not `python3`.

---

## Architecture: MCQ Converter / Generator

Both apps follow the same single-file pattern:

- `convert.py` — everything: Flask routes, background job runner, image extraction, JSON parsing, and the full embedded HTML page (`HTML_PAGE` string, ~1200 lines CSS+JS).
- `medical-quiz-converter.md` / `medical-ai-generator.md` — live-reloaded on every run; edit without restarting the server. Falls back to `DEFAULT_SYSTEM_PROMPT` in `convert.py` if the file is missing.
- **Job model**: each browser session gets a `job_id`; a `daemon=True` thread runs the conversion; the frontend polls `/api/status/<job_id>`.
- **Cumulative output**: `output/quizdata.js` is read at batch start and *merged* (not overwritten) — deduplication by exact `problem` text match.
- **PDF delivery**: files ≤ 20 MB are sent inline to Gemini; larger files use the Files API (upload → convert → delete).
- **Model fallback**: on quota exhaustion (429 / RESOURCE_EXHAUSTED), automatically advances `gemini-3.5-flash` → `gemini-3.0-flash` → `gemini-2.5-flash`.

### Flask API routes (MCQ Converter)

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the embedded HTML page |
| `/api/files` | GET | Lists PDFs in `input_pdfs/` |
| `/api/outputs` | GET | Lists existing output dirs with question counts |
| `/api/run` | POST | Starts a conversion job; returns `job_id` |
| `/api/status/<job_id>` | GET | Returns job state, logs (last 300), and progress |
| `/api/download/<job_id>` | GET | Streams the timestamped ZIP file |
| `/api/courses` | GET | Lists course definition files from `courses/` |
| `/api/courses/<course_id>` | GET | Returns full course JSON |

`/api/run` body fields: `api_key`, `model`, `files`, `job_id`, `subject_title`, `additional_prompt`.

### Image extraction

`extract_images()` tries PyMuPDF (`fitz`) first — extracts embedded images (skips blobs < 2 KB). Falls back to `pypdfium2` to render each page at 1.5× scale as `page_NNN_render.png`. Images land in `output/<stem>/images/`.

### Self-healing / retry logic

- `execute_with_retry()` retries on HTTP 429 / 503 with progressive backoff: delay = `20 + 12 × attempt` seconds, up to 5 attempts; 12 s proactive cooldown between files.
- `parse_json_response()` strips markdown fences, tries multiple extraction strategies, and falls back to `extract_valid_questions_from_broken_json` — a brace-matching scanner that recovers from truncated payloads.
- Max output tokens: 65,536 for Pro/3.5 models; 8,192 for Flash-lite.

### MCQ Generator output structure (differs from Converter)

```
output/
├── generated_<timestamp>/
│   ├── quizdata.js       ← generation result
│   └── quizdata.json
└── quizdata.js           ← global cumulative file (also updated)
```

### Output schema — MDKKU compatibility invariants

Every question object must be exactly:

```js
{
  "problem": "1. Full stem...",
  "img": "",                        // "" | "require_img" | URL
  "choices": "A///B///C///D///E",   // exactly 5, separator "///" no spaces
  "answer": "A",                    // must match one choices segment verbatim
  "select": "",
  "explain": "Thai prose + English medical terms",  // NO pure English
  "category": ["SubjectCode_ExamGroup", "SubjectCode_SubGroup_TopicLabel"],
  "state": false
}
```

`quizdata.js` top-level keys are `Default_CategoryID` (e.g. `CVS_51MCQ1`).

### Category system

`sanitize_category()` derives the two-element category from the PDF filename stem:
- **SubjectCode**: known block codes first (`CVS`, `GI`, `HEMATO`, `MS`, `NS`, `EN`), else first uppercase token
- **ExamGroup**: pattern `51MCQ1`, `50FMT` — year + exam type + sequence
- **SubGroupSuffix**: classified from topic keywords (`ANA`, `BIOCHEM`, `PHYSIO`, `MICRO`, `PARASITO`, `PATHO`, `PHARM`, `RADIO`, `CLINICAL`)
- Words `BY`, `AI`, `BY_AI` are always stripped

Name PDFs as `<SubjectCode>_<YearExamType>[Num]_<Topic>.pdf` for auto-detection.

---

## Architecture: Lecture Pipeline

`app.py` is a single-file Flask app. The 5-stage pipeline (all driven by Gemini):

1. `slide-to-markdown-gemini.md` → `lecture-markdown.md`
2. *(optional)* `lecture-synthesizer.md` + transcript → `lecture-transcribe.md`
3. `slide-enrich.md` → `lecture-enrich.md`
4. `lecture-crystallizer.md` → `lecture-summary.md`
5. *(optional)* `curriculum-tracker.md` + Curriculum Map → `Curriculum_Map_updated.md`

Prompt files in `prompts/` are live-reloaded. Output goes to `output/<slide_name>_<timestamp>/` with a ZIP available for download.

---

## Courses presets (MCQ Converter)

`courses/*.json` files define topic lists per subject. Schema:

```json
{
  "name": "EMBRYO Y1 — Embryology & Human Development",
  "subject_code": "EMBRYO",
  "subgroup": "LEC",
  "topics": ["Introduction to human development", "..."]
}
```

Loaded via `/api/courses` to populate the topic dropdown in the UI. Currently 4 presets: `CVS_Y3`, `EMBRYO_Y1`, `GEN1_Y1`, `PSYCHIATRY_Y1`.

---

## KKU IntelSphere API (`kku/`)

KKU IntelSphere is KKU's AI API platform — OpenAI-compatible, so the standard `openai` SDK works directly:

```python
from openai import OpenAI
client = OpenAI(
    api_key=os.environ.get("KKU_API_KEY"),
    base_url="https://gen.ai.kku.ac.th/api/v1"
)
```

**Recommended defaults:** `gemini-2.5-flash` (balanced), `deepseek-v3.2` (1M tokens/day quota — best for high-volume batch), `claude-sonnet-4.6` (Thai text + instruction following).

Daily quotas: Deepseek 1M, Gemini 350K, Meta/Nova/xAI/Qwen 200K, Claude/OpenAI/Mistral 150K tokens/day.

Store the key as `KKU_API_KEY` environment variable. Full boilerplate in `kku/kku-intelsphere-implement-apikey.md`.

---

## Skill commands (MCQ Converter)

Skills live in `med/Medical MCQ convert/.claude/skills/`:

- **`/convert-medical`** — guided end-to-end conversion: checks server, builds `additional_prompt` from course preset, fires `/api/run`, monitors progress, verifies categories.
- **`/create-course`** — parses a KKU Moodle page (Ctrl+A paste) to extract lecture topics and writes a `courses/*.json` preset.

---

## Known issues (MCQ Generator `convert.py`)

- Generate Mode always uses Files API even for PDFs < 20 MB (should use inline path).
- `job["done"]` is never incremented in `run_generation()`, so the UI shows "0 files processed".
- `file_stem` is passed directly into regex without `re.escape()`.
- `_jobs` dict has no threading lock around all critical sections.
- `subject_title` field was removed from the HTML UI but still expected by the Python backend.
