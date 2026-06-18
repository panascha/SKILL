# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

A Flask web app (`convert.py`) that converts medical MCQ PDFs into structured JSON/JavaScript data using the Google Gemini API. The output feeds the **MDKKU Manager Center** quiz system.

Run the server:

```bash
pip install flask google-genai pymupdf pypdfium2 Pillow
python convert.py
# Open http://localhost:8765
```

Place input PDFs in `input_pdfs/`. Outputs land in `output/<filename_stem>/`.

## Architecture

**Single-file app** — `convert.py` contains everything: Flask routes, background job runner, image extraction, JSON parsing, category logic, and the embedded HTML page (`HTML_PAGE` string, ~1200 lines of CSS+JS).

**Prompt is external and live-reloaded** — `medical-quiz-converter.md` is read fresh on every conversion run. If the file is missing or unreadable, `DEFAULT_SYSTEM_PROMPT` (defined inline in `convert.py`) is used as fallback. Edit `medical-quiz-converter.md` without restarting the server.

**Job model** — each browser session gets a `job_id`. Jobs run in a `daemon=True` thread; the frontend polls `/api/status/<job_id>` for progress and logs.

**PDF delivery** — files ≤ 20 MB are sent inline to Gemini; larger files use the Files API (upload → convert → delete).

## Flask API routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the embedded HTML page |
| `/api/files` | GET | Lists PDFs in `input_pdfs/` |
| `/api/outputs` | GET | Lists existing output directories with question counts |
| `/api/run` | POST | Starts a conversion job; returns `job_id` |
| `/api/status/<job_id>` | GET | Returns job state, logs (last 300), and progress |
| `/api/download/<job_id>` | GET | Streams the timestamped ZIP file |
| `/api/courses` | GET | Lists course definition files from `courses/` |
| `/api/courses/<course_id>` | GET | Returns full course JSON (name, subject_code, subgroup, topics) |

`/api/run` JSON body fields: `api_key`, `model` (default `gemini-3.5-flash`), `files` (list of PDF filenames), `job_id`, `subject_title` (overrides SubjectCode in category), `additional_prompt` (appended to the per-file user query).

## Courses directory

`courses/*.json` files define lecture topic lists for a subject. Schema:

```json
{
  "name": "EMBRYO Y1 — Embryology & Human Development",
  "subject_code": "EMBRYO",
  "subgroup": "LEC",
  "topics": ["Introduction to human development", "Fertilization and Advance Technique in Embryology", "..."]
}
```

The UI reads these via `/api/courses` to populate a topic-list dropdown, letting users attach structured topic metadata to a conversion run via `subject_title`.

## Key data flows

1. User POSTs to `/api/run` → spawns background thread calling `run_conversion()`
2. `run_conversion()` calls `process_pdf()` for each file sequentially (12 s cooldown between files to respect RPM limits)
3. `process_pdf()` loads the prompt from `medical-quiz-converter.md`, sends PDF + query to Gemini, parses the JSON response, sanitizes categories, writes `output/<stem>/<stem>.json`
4. After all files: accumulates results into `output/quizdata.js` (keyed by `Default_CategoryID`), packages a timestamped ZIP

## Output format — critical invariants

Every question object must match this schema exactly for MDKKU compatibility:

```js
{
  "problem": "1. Full stem...",
  "img": "",                        // or "require_img" or URL
  "choices": "A///B///C///D///E",   // exactly 5, separator "///" no spaces
  "answer": "A",                    // must match one choices segment verbatim
  "select": "",                     // always empty string
  "explain": "Thai prose + English medical terms...",  // NO pure English
  "category": ["SubjectCode_ExamGroup", "SubjectCode_SubGroupSuffix_TopicLabel"],
  "state": false                    // boolean, not string
}
```

`quizdata.js` keys are `Default_CategoryID` (`SubjectCode_ExamGroup`, e.g. `CVS_51MCQ1`).

## Category system

`sanitize_category()` derives the two-element category array from the PDF filename stem:

- **SubjectCode**: known block codes first (`CVS`, `GI`, `HEMATO`, `MS`, `NS`, `EN`), else first meaningful uppercase token
- **ExamGroup**: pattern like `51MCQ1`, `50FMT` — year + exam type + sequence
- **SubGroupSuffix**: classified from topic keywords; valid values: `ANA`, `BIOCHEM`, `PHYSIO`, `MICRO`, `PARASITO`, `PATHO`, `PHARM`, `RADIO`, `CLINICAL`

Words `BY`, `AI`, `BY_AI` are always stripped from category IDs.

## Image extraction

`extract_images()` tries PyMuPDF (`fitz`) first — extracts embedded images (skips blobs < 2 KB). If no images are found via PyMuPDF (or PyMuPDF is not installed), it falls back to `pypdfium2` to render each page at 1.5× scale as `page_NNN_render.png`. Images land in `output/<stem>/images/`.

## Self-healing / retry logic

- `execute_with_retry()` retries on HTTP 429 / 503 with progressive backoff (up to 5 attempts)
- `parse_json_response()` strips markdown fences, tries multiple extraction strategies, and falls back to a brace-matching scanner (`extract_valid_questions_from_broken_json`) that recovers from truncated payloads
- Max output tokens: 65,536 for Pro/3.5 models; 8,192 for others (Flash-lite, etc.)
- **Model fallback chain**: on quota exhaustion (429 / RESOURCE_EXHAUSTED), `run_conversion()` automatically advances through `gemini-3.5-flash` → `gemini-3.0-flash` → `gemini-2.5-flash` for all remaining files in the batch

## Cumulative output

`quizdata.js` is read at the start of each batch run and **merged** (not overwritten) — new questions are appended to existing category arrays. Deduplication is by `problem` text exact match.
