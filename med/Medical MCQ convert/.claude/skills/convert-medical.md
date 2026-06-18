---
name: convert-medical
description: >
  Run the Medical MCQ PDF → JSON conversion pipeline. Ask for course info,
  check input files, fire the Flask API, and monitor until done.
  Trigger when user says /convert-medical or asks to convert MCQ PDFs.
---

# Medical MCQ Conversion Skill

When invoked, follow these steps exactly.

## Step 1 — Gather required info (always ask, even if partially known)

Ask the user for:
1. **API key** — Gemini API key (or confirm if same as last session)
2. **Course preset** — check if a matching file exists in `courses/` directory first:
   - Run: `Get-ChildItem "courses/*.json" | Select-Object Name`
   - If a matching course exists, offer to load it (saves step 3–5 below)
3. **Subject code** — e.g. `EMBRYO`, `CVS`, `GI`, `HEMATO`, `MS`, `NS`
4. **Subgroup format** — `LEC` (year 1–2 lecture-based) or discipline (`ANA`/`PHYSIO`/`PATHO`/`PHARM`/`MICRO`/`CLINICAL`)
5. **Lecture topic list** — exact topic names (required only if subgroup = `LEC`)
6. **Which PDFs** — list files in `input_pdfs/` and ask which to convert

## Step 2 — Check server

Verify the Flask server is running on port 8765:
```powershell
Invoke-RestMethod -Uri "http://localhost:8765/" -TimeoutSec 3 | Out-Null
```
If not running, start it:
```powershell
Start-Process python -ArgumentList "convert.py" -WorkingDirectory "<project_dir>" -WindowStyle Hidden
Start-Sleep -Seconds 3
```

## Step 3 — Build additional_prompt

**MAPPED** (course preset has `"subgroup": "MAPPED"` and `topics` = array of `{subgroup, topic}` objects):
```
รายชื่อหัวข้อบรรยายพร้อมกลุ่มวิชา (Lecture Topics with Subgroup mapping):
1. [ANA] Gross Anatomy of Mediastinum
2. [PHYSIO] Electrical activity of the heart
...

คำสั่งพิเศษ:
- SubjectCode = <SUBJECT_CODE>
- category[0] = <SUBJECT_CODE>_<ExamGroup>
- category[1] = <SUBJECT_CODE>_<SubGroupSuffix>_<TopicLabel>
  โดย <SubGroupSuffix> ต้องตรงกับกลุ่มวิชาในวงเล็บ [...] ของ topic นั้น
  และ <TopicLabel> ต้องตรงกับชื่อ lecture ทุกตัวอักษร
- ถ้าข้อสอบไม่ตรงกับ lecture ใดเลย ให้ใช้ topic ที่ใกล้เคียงที่สุดจากรายการ
```

**LEC** (`"subgroup": "LEC"`, flat topic list):
```
รายชื่อหัวข้อบรรยาย (Lecture Topics) สำหรับการ assign category[1]:
1. <topic1>
2. <topic2>
...

คำสั่งพิเศษ:
- SubjectCode = <SUBJECT_CODE>
- SubGroupSuffix = LEC
- category[0] = <SUBJECT_CODE>_<ExamGroup>
- category[1] = <SUBJECT_CODE>_LEC_<TopicLabel> (ต้องตรงกับรายชื่อ lecture ทุกตัวอักษร)
- ถ้าข้อสอบไม่ตรงกับ lecture ใดเลย ให้ใช้ topic ที่ใกล้เคียงที่สุดจากรายการ
```

**Discipline** (`"subgroup"` = string or array, no MAPPED): leave additional_prompt empty; system derives subgroup from keywords automatically.

## Step 4 — Fire conversion job

```powershell
$body = @{
    api_key        = "<API_KEY>"
    model          = "gemini-3.5-flash"
    job_id         = "med_<timestamp>"
    subject_title  = "<SUBJECT_CODE>"
    additional_prompt = "<built_in_step3>"
    files          = @("<file1.pdf>", "<file2.pdf>", ...)
} | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:8765/api/run" -Method Post -Body $body -ContentType "application/json; charset=utf-8"
```

## Step 5 — Monitor

Poll every 30s. Show: done/total, current file, last 3 log lines.
On `🔑 โควตาหมดทุกโมเดลแล้ว` log → stop and ask user for new API key.
On `running=False` → report final results (file: status | questions).

## Step 6 — Verify output

Check `categories_found` in each output JSON:
- If subgroup=LEC: all entries must be `<SUBJECTCODE>_LEC_*`
- If discipline: all entries must use correct subgroup (`ANA`/`PHYSIO`/etc.)

Report any mismatches.

## Step 7 — Save course config (if new course)

If the user ran a new course not already in `courses/`, ask:
> "Save this as a course preset for next time?"

If yes, write `courses/<SUBJECT_CODE>_<YEAR_OR_TAG>.json`:
```json
{
  "name": "<descriptive name>",
  "subject_code": "<CODE>",
  "subgroup": "<LEC or discipline>",
  "topics": ["<topic1>", "..."]
}
```

## Notes

- Model fallback chain: `gemini-3.5-flash` → `gemini-3.0-flash` → `gemini-2.5-flash` (built into server)
- Free tier limit: 20 RPD per model. Large PDFs (>1 MB) take 2–5 min per file.
- Output: `output/<stem>/<stem>.json` + `output/quizdata.js` (cumulative merge)
- Always ask for subject code + topic list before running — never assume from previous sessions
