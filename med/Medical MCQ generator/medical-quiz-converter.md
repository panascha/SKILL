---
name: medical-quiz-converter
description: >
  Convert medical exam questions (MCQs, clinical vignettes) into a specific JavaScript object structure
  for quiz applications. Use this skill whenever the user provides medical questions, USMLE-style vignettes,
  Thai medical board questions, or any MCQ content and wants it converted to JavaScript/JSON format,
  especially when they mention allquestionN, quiz array, quizdata, or a JS object with fields like
  problem/choices/answer/explain/category. Also trigger when the user provides a lecture topic list and
  asks to categorize or label questions by topic. Always trigger this skill when the user pastes or
  uploads a block of numbered medical questions and asks for code output — even if they don't say
  "skill" or "convert". Trigger when the user provides one or more PDF files of exam questions and
  asks for JSON or JS output.
---

# Medical Quiz Converter

Converts medical MCQ content (single file or multiple files) into a `var quizdata` JavaScript object
for MDKKU Manager Center / quiz apps. This skill is used alongside `convert.py` (Gemini-powered Flask
batch processor) — the output format must be compatible with that pipeline.

---

## Final Output Format

### Single-file run
One deliverable per source file:
1. **JSON file** — contains `meta` + converted question array for that file.

### Multi-file run (combining all files)
One additional deliverable:
2. **Combined `var quizdata` JS file** — merges all files under one object, keyed by **Default_CategoryID**
   (formatted as `SubjectCode_ExamGroup`, e.g. `CVS_51MCQ1`).

```js
var quizdata = {
    "CVS_51MCQ1": [
        {
            "problem": "1. What is the arterial supply of the descending colon?",
            "img": "",
            "choices": "Inferior mesenteric artery///Superior mesenteric artery///Celiac trunk///Internal iliac artery///Pudendal artery",
            "answer": "Inferior mesenteric artery",
            "select": "",
            "explain": "...",
            "category": ["CVS_51MCQ1", "CVS_ANA_Anatomy of Heart"],
            "state": false
        }
    ],
    "GI_51MCQ1": [
        { ... }
    ]
};
```

> **Key naming convention for `var quizdata` keys:**
> Always use **Default_CategoryID** format: `SubjectCode_ExamGroup`
> (e.g., `CVS_51MCQ1`, `GI_51FMT`, `HEMATO_51MCQ1`).
> This is extracted from the PDF/source filename via the parsing logic below.

---

## Question Object Schema

```js
{
    "problem": "1. Full question text here...",
    "img": "",
    "choices": "Choice A///Choice B///Choice C///Choice D///Choice E",
    "answer": "Choice A",
    "select": "",
    "explain": "อธิบายหลักการแพทย์และเหตุผลทางการแพทย์อย่างละเอียด (ภาษาไทยผสมคำศัพท์ทางการแพทย์ภาษาอังกฤษ)...",
    "category": ["Default_CategoryID", "Standardized_CategoryID"],
    "state": false
}
```

### `category` field — always a 2-element array

| Index | Name | Format | Example |
|---|---|---|---|
| 0 | Default_CategoryID | `SubjectCode_ExamGroup` | `"CVS_51MCQ1"` |
| 1 | Standardized_CategoryID | `SubjectCode_SubGroupSuffix_TopicLabel` | `"CVS_ANA_Anatomy of Heart"` |

**SubGroupSuffix** must be exactly one of:
`ANA`, `BIOCHEM`, `PHYSIO`, `MICRO`, `PARASITO`, `PATHO`, `PHARM`, `RADIO`, `CLINICAL`

Choose based on keywords in the topic:
- `ANA` — anatomy, histology, embryology, structure, กายวิภาค
- `BIOCHEM` — biochemistry, metabolism, molecular, gene, ชีวเคมี
- `PHYSIO` — physiology, function, mechanism, สรีรวิทยา
- `MICRO` — microbiology, virology, immunology, infection, จุลชีววิทยา
- `PARASITO` — parasitology, helminth, protozoa, worm, ปรสิต
- `PATHO` — pathology, lesion, biopsy, histopathology, พยาธิวิทยา
- `PHARM` — pharmacology, drug, medication, เภสัช
- `RADIO` — radiology, X-ray, imaging, CT, MRI, ultrasound, รังสี
- `CLINICAL` — clinical, medicine, surgery, diagnosis, case management, คลินิก (default if unclear)

### CategoryID extraction from filename

Parse the PDF filename (without extension) to extract:
- **SubjectCode**: Known codes first (`CVS`, `GI`, `HEMATO`, `MS`, `NS`, `EN`), else first meaningful uppercase token
- **ExamGroup**: Pattern like `51MCQ1`, `50FMT`, `52QUIZ2` — combine year + exam type + sequence number
- Default ExamGroup fallback: `51MCQ1`

Examples:

| Filename | SubjectCode | ExamGroup | Default_CategoryID |
|---|---|---|---|
| `GI_51MCQ1_Anatomy.pdf` | `GI` | `51MCQ1` | `GI_51MCQ1` |
| `CVS_50FMT.pdf` | `CVS` | `50FMT` | `CVS_50FMT` |
| `HEMATO_52MCQ2_Physiology.pdf` | `HEMATO` | `52MCQ2` | `HEMATO_52MCQ2` |

---

## Strict Conversion Rules

### 1. `problem` — Extraction + Completion

- Copy the **entire** question stem / clinical vignette **verbatim**.
- Preserve all: vitals, lab values, dates, medication names, dosages, timeline details.
- Do **NOT** summarize, paraphrase, shorten, or restructure.
- Only allowed change to original text: **correct spelling typos**.
- Prepend the question number: `"1. A 45-year-old man presents with..."`.

**Incomplete Question Handling:**
If the source question is missing key clinical elements, you **must**:
1. Complete the question with medically appropriate content.
2. Append tag at the end of the `problem` string:
   `" [⚠️ เพิ่มเติมเพื่อความสมบูรณ์: <รายละเอียดที่เพิ่ม>]"`
3. Never silently fill gaps — the tag is mandatory whenever any addition is made.

### 2. `select` and `state`

- Always `"select": ""` and `"state": false` (boolean, not string). Never change these.

### 3. `choices` — Formatting Rules

- Separator: exactly `///` — **no spaces before or after**.
  - ✅ `"Metformin///Insulin///Glipizide///Acarbose///Sitagliptin"`
  - ❌ `"Metformin /// Insulin /// Glipizide"`
- Exactly **5 choices** per question.
- If source has fewer than 5, add plausible medical distractors. Never duplicate the correct answer.

### 4. `answer` — Exact Match

- Must be a **string that exactly matches** one segment in `choices` (same spelling, same case, character-for-character).

### 5. `img` — Image Handling

- Default: `"img": ""`
- If the question references a visual (e.g., "See X-ray below", "ECG shows"): `"img": "require_img"`
- If an actual image URL is known: use the URL string.
- Multiple images: separate with `///`.

### 6. `explain` — Clinical Reasoning (Thai + Medical Terms)

Write a **single continuous paragraph** (no bullet lists, no line breaks inside the string):

1. **Key Concept** — Identify the diagnosis/core concept.
2. **Why Correct** — Explain the answer using specific clues from the question.
3. **Rule Out Each Distractor** — For every wrong choice, briefly explain why incorrect.
   Style: `"ส่วนข้อ B ผิดเพราะ... (because...)"`, `"ข้อ C มักใช้ใน... แต่ผู้ป่วยรายนี้..."`
4. **Clinical Pearl** (optional) — High-yield exam fact.

> **⚠️ Language Rule (Enforced by convert.py):**
> `explain` **MUST** be written in **ภาษาไทย prose mixed with English medical terminology**.
> Absolutely **NO pure English explanations** allowed.
> ห้ามใช้ภาษาอังกฤษล้วนในการอธิบายโดยเด็ดขาด

### 7. String Safety

- No unescaped double quotes, backslashes, or newline characters inside any string value.
- Single logical line strings only. Use `\'` for apostrophes if needed.
- All question object keys use double-quoted JSON style.

---

## Workflow

### Phase 0 — Read Context Inputs

Before starting, identify what the user has provided:

- **Source file(s)**: one or more PDF/text blocks of MCQ content (required).
  Record the filename of each source; derive Default_CategoryID from it.
- **Category/topic list**: optional. May be provided as table, plain list, or ID list.
- **Existing question IDs**: optional, for duplicate detection.

---

### Phase 1a — Duplicate Detection

If the user provides an **existing question ID list**:

1. Compare each incoming question against the existing set.
2. Flag as **duplicate** if `QuestionID` matches exactly OR `problem` text is ≥ 85% similar.
3. Output a **Duplicate Report** block before the code:

```
🔁 DUPLICATE REPORT:
- Q3 ("A 45-year-old woman with chest pain..."): ซ้ำกับ CVS_51MCQ1_7 (100%)
- Q7 ("A man presents with hemoptysis..."): คล้ายกับ RESP_MCQ2_3 (~90% — แนะนำตรวจสอบ)
ข้อที่ซ้ำจะถูก ข้าม ไม่รวมใน output array
```

4. Exclude confirmed duplicates. Near-duplicates included but flagged in POST-CONVERSION NOTES.

---

### Phase 1b — Category Assignment

**Always assign `category` as a 2-element array** — no exceptions.

1. Parse filename → extract SubjectCode + ExamGroup → build `Default_CategoryID = SubjectCode_ExamGroup`
2. Analyze question content to infer SubGroupSuffix (from the fixed list above).
3. Derive TopicLabel from the most specific lecture topic matching the content.
4. Build `Standardized_CategoryID = SubjectCode_SubGroupSuffix_TopicLabel`
5. Result: `category: ["CVS_51MCQ1", "CVS_ANA_Anatomy of Heart"]`

**If a category list IS provided by the user:**
- Use exact CategoryID values from the list for `Standardized_CategoryID`.
- For questions that don't match any topic: `category: ["SubjectCode_ExamGroup", "SubjectCode_CLINICAL_Uncategorized"]`
- Flag unmatched questions in POST-CONVERSION NOTES.

**Output a Category Summary after the code:**

```
📂 CATEGORY SUMMARY:
- CVS_ANA_Anatomy of Heart: Q1, Q4, Q6
- CVS_PHYSIO_Cardiac cycle: Q2, Q5
- CVS_PATHO_Heart failure: Q3, Q7, Q8
- CVS_CLINICAL_Uncategorized: Q9
```

---

### Phase 2 — Content Validation

Perform a **medical accuracy check** before converting:

1. **Answer–Distractor Consistency**: Verify the correct answer is medically defensible. Flag if another choice is arguably more correct.
2. **Clinical Coherence**: Confirm lab values, vitals, and drug names are internally consistent.
3. **Guideline Alignment**: Note if a question reflects outdated practice.

Output before the code only if issues found:
```
⚠️ VALIDATION WARNINGS:
- Q2: คำตอบที่ให้มาคือ X แต่ตาม current guidelines (AHA 2023)...
- Q5: ค่า lab ที่ระบุ (Na 180 mEq/L) สูงผิดปกติมาก — แนะนำตรวจสอบ
```

---

### Phase 3 — Conversion

For each non-duplicate question:
1. Extract `problem` verbatim (typo-fix only); complete + tag if incomplete.
2. Parse or infer 5 choices; add distractors if needed.
3. Confirm `answer` exactly matches one `choices` segment.
4. Set `img` value.
5. Assign `category` array per Phase 1b rules.
6. Write `explain` paragraph in Thai + English medical terms.

---

### Phase 4 — Self-Review

After drafting all objects, silently verify each question:

- [ ] `answer` matches exactly one `choices` segment (character-for-character).
- [ ] `choices` uses `///` with no surrounding spaces; exactly 5 segments.
- [ ] `problem` preserves all clinical details; completion tag present if applicable.
- [ ] `explain` covers correct rationale + all 4 distractors ruled out.
- [ ] `explain` is Thai prose mixed with English medical terms — NOT pure English.
- [ ] No line breaks or unescaped quotes inside any string.
- [ ] `category[0]` = `SubjectCode_ExamGroup` (e.g., `CVS_51MCQ1`).
- [ ] `category[1]` = `SubjectCode_SubGroupSuffix_TopicLabel` with valid SubGroupSuffix.
- [ ] `state` is `false` (boolean, not string).

Silently fix any errors found. If a **substantive clinical uncertainty** remains, note it in POST-CONVERSION NOTES.

---

### Phase 5 — Final Output

#### Per-file output:

**JSON file** (`<filename_stem>.json`):

```json
{
    "meta": {
        "source": "CVS_51MCQ1_Anatomy.pdf",
        "categoryID": "CVS_51MCQ1_Anatomy",
        "converted": 10,
        "skipped_duplicates": 0,
        "completions_added": 1,
        "validation_warnings": 0,
        "categories_found": ["CVS_ANA_Anatomy of Heart", "CVS_PHYSIO_Cardiac cycle"],
        "converted_at": "2026-05-30T12:00:00.000000"
    },
    "questions": [
        { ...question object... }
    ]
}
```

Note: `meta.categoryID` = raw filename stem (e.g., `CVS_51MCQ1_Anatomy`), while `var quizdata` key uses Default_CategoryID (`CVS_51MCQ1`).

#### Multi-file combined output (when 2+ source files):

**`quizdata.js`** — keyed by Default_CategoryID (`SubjectCode_ExamGroup`):

```js
// Auto-generated Combined MCQ Quiz Data
var quizdata = {
    "CVS_51MCQ1": [
        {
            "problem": "1. ...",
            "img": "",
            "choices": "A///B///C///D///E",
            "answer": "A",
            "select": "",
            "explain": "...",
            "category": ["CVS_51MCQ1", "CVS_ANA_Anatomy of Heart"],
            "state": false
        }
    ],
    "GI_51MCQ1": [
        { ... }
    ]
};
```

#### Full output structure:

```
[⚠️ VALIDATION WARNINGS — if any]
[🔁 DUPLICATE REPORT — if applicable]

--- FILE: CVS_51MCQ1_Anatomy ---
[JSON file]

--- FILE: GI_51MCQ1_Physiology ---
[JSON file]

[Combined quizdata.js — if multi-file]

[📂 CATEGORY SUMMARY — per file]
[📋 POST-CONVERSION NOTES — if any]
[✅ BATCH SUMMARY]
```

**Batch Summary** (always present):
```
✅ BATCH SUMMARY: แปลงสำเร็จ 8 ข้อ | ข้าม 2 ข้อ (ซ้ำ) | ⚠️ เติมเนื้อหา 1 ข้อ | 🔍 Validation warning 1 ข้อ | 📂 Category: 3 หัวข้อ | 📁 ไฟล์: 2 ไฟล์
```

---

## MDKKU Manager Center Integration Notes

- `var quizdata` keys = Default_CategoryID = `SubjectCode_ExamGroup` (e.g., `CVS_51MCQ1`)
- `category[0]` = Default_CategoryID for top-level filtering
- `category[1]` = Standardized_CategoryID for sub-topic filtering and display label
- The system auto-generates `QuestionID` as `{Default_CategoryID}_{n}` (e.g., `CVS_51MCQ1_1`)
- `img` supports multiple images separated by `///`
- `meta.categoryID` = raw filename stem (may differ from `var quizdata` key)
- `meta.converted_at` = ISO 8601 timestamp, added by convert.py post-processing

---

## Example Output

```js
// Auto-generated Combined MCQ Quiz Data
var quizdata = {
    "GI_51MCQ1": [
        {
            "problem": "1. A surgical resident is asked to identify the ligament of Treitz during an exploratory laparotomy. Which of the following best describes its anatomical significance?",
            "img": "",
            "choices": "It marks the junction between the duodenum and jejunum///It suspends the transverse colon///It forms the hepatoduodenal ligament///It anchors the descending colon to the posterior abdominal wall///It connects the stomach to the spleen",
            "answer": "It marks the junction between the duodenum and jejunum",
            "select": "",
            "explain": "Ligament of Treitz (suspensory muscle of the duodenum) เป็น landmark สำคัญที่ใช้กำหนด duodenojejunal flexure ซึ่งเป็นจุดเริ่มต้นของ jejunum ใน clinical surgery ใช้บ่งชี้ upper vs lower GI bleeding (proximal to ligament = upper GI) ส่วนข้อ B ผิดเพราะ transverse colon ถูก suspend โดย transverse mesocolon ข้อ C ผิดเพราะ hepatoduodenal ligament ประกอบด้วย portal triad (portal vein, hepatic artery, bile duct) ข้อ D ผิดเพราะ descending colon ยึดกับ posterior abdominal wall โดย peritoneal attachment โดยตรง ข้อ E ผิดเพราะ gastrosplenic ligament เป็นโครงสร้างที่เชื่อมกระเพาะกับม้าม",
            "category": ["GI_51MCQ1", "GI_ANA_Anatomy of lower GI (Small & Large intestine)"],
            "state": false
        }
    ]
};
```

```json
{
    "meta": {
        "source": "GI_51MCQ1_Anatomy.pdf",
        "categoryID": "GI_51MCQ1_Anatomy",
        "converted": 1,
        "skipped_duplicates": 0,
        "completions_added": 0,
        "validation_warnings": 0,
        "categories_found": ["GI_ANA_Anatomy of lower GI (Small & Large intestine)"],
        "converted_at": "2026-05-30T12:00:00.000000"
    },
    "questions": [
        {
            "problem": "1. A surgical resident...",
            "img": "",
            "choices": "It marks the junction between the duodenum and jejunum///...",
            "answer": "It marks the junction between the duodenum and jejunum",
            "select": "",
            "explain": "...",
            "category": ["GI_51MCQ1", "GI_ANA_Anatomy of lower GI (Small & Large intestine)"],
            "state": false
        }
    ]
}
```

✅ BATCH SUMMARY: แปลงสำเร็จ 1 ข้อ | ไม่มีซ้ำ | ไม่มีการเติมเนื้อหา | 📂 Category: 1 หัวข้อ | 📁 ไฟล์: 1 ไฟล์