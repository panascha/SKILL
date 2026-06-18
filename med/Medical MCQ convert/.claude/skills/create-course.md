---
name: create-course
description: >
  Parse a Ctrl+A dump from a KKU e-Learning (Moodle) course page and create
  a course preset JSON in courses/. Trigger when user pastes e-learning page
  text and asks to create a course, build a preset, or says "create course from
  this" / "make course config". Also trigger on /create-course.
---

# Create Course Preset from E-Learning Page

When invoked, follow these steps.

## Step 1 — Get the e-learning text

If the user already pasted e-learning content in this message, use it directly.
Otherwise ask: "กรุณา Ctrl+A แล้ว paste เนื้อหาจากหน้า e-learning ได้เลยครับ"

## Step 2 — Extract course identity

From the pasted text, find:
- **Course code**: pattern `MD\s*\d+\s*\d+\s*\d+` (e.g. "MD 533 117" → "MD533117")
- **Course name**: text after `::` on the same line (e.g. "Cardiovascular system")
- **Year level**: from the code — `MD5XX` = year 3, `MD4XX` = year 2, `MD3XX` = year 1 (KKU convention: first digit after MD5 = year)

## Step 3 — Extract lecture topics

Scan for lines matching these patterns (in order of priority):
1. `LEC\s*[\d\.\-]+\s*[-:]\s*(.+)` → capture the topic name after the colon/dash
2. `TBL\s*\d+\s*[-:]\s*(.+)` → include TBL sessions as topics
3. Lines under `Topic \d+` headings that look like lecture titles (not "Not available", not lab/URL lines)

**Cleaning rules:**
- Strip prefix: `LEC 1-2.5:`, `LEC 10:`, `LEC 37-38:`, etc.
- Strip trailing whitespace, file size info (e.g. "File 3.8MB PDF"), URLs
- Deduplicate (same topic may appear in multiple Topic sections)
- Exclude: LAB sessions, ปฏิบัติการ headings, Clinical Correlation (CC), Wrap-up (optional)

## Step 4 — Ask for config decisions

Ask the user:

1. **Subject code** — e.g. `CVS`, `GI`, `HEMATO`, `MS`, `NS`. Suggest based on course name.
2. **Subgroup format**:
   - `LEC` — all questions mapped to lecture topics by name (recommended for year 1–2 integrated blocks)
   - Array of disciplines e.g. `["ANA", "BIOCHEM", "PHYSIO", "MICRO", "PARASITO", "PATHO", "PHARM", "RADIO", "CLINICAL"]` — system auto-classifies each question by keyword; no topic list needed (recommended when block spans many disciplines)
   - Single discipline string e.g. `"PATHO"` — auto-classify, scoped to one discipline
3. **File name** — suggest `<SUBJECT_CODE>_Y<N>.json` (e.g. `CVS_Y3.json`). Confirm with user.

## Step 5 — Build and write the JSON

```json
{
  "name": "<Course Name> (<CourseCode>)",
  "subject_code": "<CODE>",
  "subgroup": "<see below>",
  "topics": ["<topic 1>", "<topic 2>", "..."]
}
```

`subgroup` values:
- `"LEC"` → keep full `topics` array
- `["ANA", "BIOCHEM", "PHYSIO", "MICRO", "PARASITO", "PATHO", "PHARM", "RADIO", "CLINICAL"]` → omit or empty `topics`
- `"PATHO"` (single discipline) → omit or empty `topics`

Write to: `C:\Users\LENOVO\Desktop\SKILL\med\Medical MCQ convert\courses\<filename>.json`

## Step 6 — Confirm and offer next step

Show the user the extracted topic list for review:
```
✅ สร้าง courses/<filename>.json สำเร็จ — <N> topics
Subject: <CODE> | Format: <LEC/discipline>

Topics extracted:
1. <topic1>
2. <topic2>
...

มีข้อผิดพลาดหรืออยากแก้ไข topic ใดไหมครับ? (ถ้าโอเค พร้อมแปลง PDF ได้เลย)
```

If user confirms OK → ask: "วาง PDF ชื่ออะไรใน input_pdfs/ แล้วต้องการแปลงเลยไหมครับ?"
If yes → invoke `/convert-medical` skill with the new course preset already loaded.

## Parsing tips

KKU Moodle page structure (Ctrl+A output) typically contains:
- `Topic N` headings followed by `LEC N: Title` lines
- Each LEC line has the topic name, then instructor info, then file links
- The first meaningful text after `LEC N[-N]:` or `LEC N:` (before a newline with `โดย` or a file name) is the topic name
- TBL sessions appear as `TBL1: Title`, `TBL2: Title`

Example extraction from "LEC 1-2.5: Gross Anatomy of Mediastinum\n\nโดย อ.ดร.นพ.ตุลยณัฐ":
→ topic = "Gross Anatomy of Mediastinum"

Example from "LEC 24: Pathology of blood vessels\nLEC 25: Atherosclerosis\nLEC 26: Ischemic Heart Disease":
→ 3 separate topics
