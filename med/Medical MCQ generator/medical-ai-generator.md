---
name: medical-ai-generator
description: >
  Generate high-quality medical exam questions (35 items) from lecture slides, learning objectives,
  and sample exam references using AI. Use this skill whenever the user provides medical lecture content
  (slides, LOs, or PDFs) and wants to generate new exam questions, practice questions, or mock exams
  for NL (National License), USMLE-style, or Thai medical board preparation. Trigger when the user says
  "generate questions", "สร้างข้อสอบ", "ออกข้อสอบ", "generate MCQ from slides", or uploads a topic/syllabus
  and asks for exam questions. Always trigger when the user provides learning objectives and asks for
  a var quizdata quiz output. Also trigger when the user asks for AI-generated questions that mimic
  a sample exam style. This skill pairs with medical-quiz-converter: use this skill to generate NEW
  questions, use medical-quiz-converter to convert EXISTING questions.
---

# Medical AI Question Generator

Generates medical exam questions from Learning Objectives, Slide Content, and Sample Exam references.
Default count is 35 per batch; overridden per lecture when the user specifies a number in the input.
Output is a valid JavaScript `var quizdata` object compatible with the MDKKU quiz system.

---

## Output Format

```js
var quizdata = {
    "EN_by AI_ANA_Anatomy of adrenal gland": [
        {
            problem: "1. A 45-year-old male presents with...",
            img: "",
            choices: "Choice1///Choice2///Choice3///Choice4///Choice5",
            answer: "Correct Answer",
            select: "",
            explain: "อธิบาย...(Thai + English medical terms)...",
            category: "EN_by AI_ANA_Anatomy of adrenal gland",
            state: false
        }
    ],
    "EN_by AI_PHYSIO_Physiology of adrenal hormone": [
        { ... }
    ]
};
```

> **Note:** The `var quizdata` keys are verbatim CategoryID strings from the MDKKU topic list.
> Questions are grouped under the topic key they belong to.
> `category` is a **single string** — the verbatim CategoryID of the topic this question belongs to.

---

## CategoryID System

CategoryID is the **verbatim topic key string** from the MDKKU topic list. It serves as both the
`var quizdata` object key and the `category` string value inside each question object.

### Two CategoryID Patterns

**System subjects** (EN, GI, CVS, NS, HEMATO, MS, etc.) — include SubGroupSuffix:
```
SubjectCode_by AI_SubGroupSuffix_TopicName
```
Examples:
- `EN_by AI_ANA_Anatomy of adrenal gland`
- `GI_by AI_PHYSIO_Bile secretion`
- `NS_by AI_PATHO_Pathology of nervous system`

**General principle / Biochemistry subjects** (GEN2, GEN3, GEN4, GEN5, MBN2, COMMED) — no SubGroupSuffix:
```
SubjectCode_by AI_TopicName
```
Examples:
- `GEN3_by AI_Bacteria`
- `GEN2_by AI_Cell Adaptations`
- `MBN2_by AI_Lipid metabolism`
- `GEN5_by AI_Pharmacodynamic`

**SubGroupSuffix options** (system subjects only):
`ANA`, `BIOCHEM`, `PHYSIO`, `MICRO`, `PARASITO`, `PATHO`, `PHARM`, `RADIO`, `CLINICAL`

### CategoryID Assignment Priority

1. **User provides MDKKU topic list** → use exact verbatim string from the list
2. **Derive from content/filename** → assemble using correct pattern for that SubjectCode
3. **Fallback** → `SubjectCode_by AI_CLINICAL_Uncategorized` (system) or `SubjectCode_by AI_Uncategorized` (general)

---

## Question Object Schema

```js
{
    problem: "N. Full question text (English)",     // Unquoted keys (JS object literal)
    img: "",
    choices: "A///B///C///D///E",                   // Exactly 5, NO spaces around ///
    answer: "A",                                     // Exact match to one choices segment
    select: "",
    explain: "Thai prose + English medical terms",   // Single line, no \n
    category: "CategoryID",                          // Single string — verbatim CategoryID
    state: false                                     // Boolean, not string
}
```

---

## Workflow

### Phase 0 — Parse Inputs

Identify what the user has provided:

1. **Learning Objectives (LOs)** — list of topics/concepts students must know
2. **Slide Content** — lecture notes, tables, diagrams described in text
3. **Sample Exam** — example questions for style/difficulty calibration
4. **Topic key list** — optional MDKKU topic list for CategoryID matching
5. **Subject code** — e.g., EN, GI, NS (infer from content if not given)
6. **Question count** — number of questions per lecture (if specified in input); default = 35

If sample exam is missing, default to USMLE Step 1/2 clinical vignette style.

---

### Phase 1 — Question Blueprint (Internal Planning)

Before generating, read the **question count** from the input (default 35 if not specified).
Then silently plan a **content distribution** proportional to that count:

| Category | Target Share | Question Types |
|---|---|---|
| Basic Science (ANA, PHYSIO, BIOCHEM, PHARM, MICRO, PATHO) | ~30% | Mechanism-based, "Why does..." |
| Clinical Diagnosis (Dx, DDx) | ~35% | Clinical vignette with labs/vitals |
| Management (Tx, next best step) | ~35% | "What is the next best step..." |

Also plan which CategoryID (topic key) each question belongs to — distribute across multiple topics when possible.

Ensure no two questions test the identical learning point.

---

### Phase 2 — Question Generation Rules

#### 2.1 Question Design

**Clinical Vignette Format (for Dx and Management questions):**
- Include: Age, Gender, Chief Complaint, HPI timeline
- Include as appropriate: Vital Signs (BP, HR, RR, Temp, O2 sat), Physical Exam findings, Labs, Imaging
- End with a specific stem: "Which of the following is the MOST LIKELY diagnosis?", "What is the NEXT BEST STEP in management?", "Which mechanism BEST explains...?"
- Complexity: Moderate to Hard. Avoid simple recall — require reasoning.

**Basic Science Format:**
- Start from a physiological/pathological principle
- Require analytical thinking before arriving at the answer
- Can use mini-vignettes: "A medical student notes that..."
- Focus on "Why/How" — mechanisms, pathways, consequences

**Question Stems to Vary (never repeat the same stem twice in a row):**
- "Which of the following is MOST LIKELY to..."
- "What is the NEXT BEST STEP in management?"
- "Which mechanism BEST explains...?"
- "A biopsy of the lesion would MOST LIKELY show..."
- "Which drug is MOST APPROPRIATE for...?"
- "Which of the following lab findings is MOST consistent with...?"
- "Which of the following BEST describes the pathophysiology of...?"

#### 2.2 Choices Formatting

- Exactly **5 choices** per question
- Separator: `///` — **absolutely no spaces before or after**
  - ✅ `"Metformin///Insulin///Glipizide///Acarbose///Sitagliptin"`
  - ❌ `"Metformin /// Insulin"` or `"Metformin ///Insulin"`
- **Plausible distractors**: choices must be homogeneous in grammatical structure and approximate length
- **No obvious wrong answers**: every choice should require clinical reasoning to rule out
- **Distractor strategy**: include common misdiagnoses, related-but-wrong drugs, mechanisms that partially fit

#### 2.3 Answer Matching

- `answer` must be a **character-for-character exact match** to one segment in `choices`
- Verify: Split `choices` by `///` → confirm `answer` === one of the 5 segments exactly

#### 2.4 Numbering

- Start `problem` text with question number: `"1. A 45-year-old..."`, `"2. Which of..."`
- Number sequentially from 1 to 35 across ALL topics (do not restart per topic)

---

### Phase 3 — Explanation Writing (Critical Quality Gate)

Each `explain` must be a **single continuous paragraph** — no `\n`, no bullet points inside the string.

**Required structure (flowing prose, NOT labeled sections):**

1. **Key Concept** — Open by identifying the core diagnosis or concept based on the clinical findings
2. **Why Correct** — Explain the correct answer using specific evidence from the question stem
3. **Rule Out Each Distractor** — For EACH of the 4 wrong choices, explain why incorrect
   - Style: `"ส่วนข้อ B ผิดเพราะ... (because...)"`, `"ข้อ C มักใช้ในกรณี... แต่ผู้ป่วยรายนี้..."`
   - Be specific — reference clinical details from the question, not generic statements
4. **Clinical Pearl** (optional) — One high-yield fact for NL/board exams

**Language Rule (Non-negotiable):**
- `explain` MUST be Thai prose mixed with English medical terminology
- ❌ Pure English forbidden: `"The correct answer is ACE inhibitor because..."` — NEVER
- ✅ Mixed Thai/English: `"ผู้ป่วยรายนี้มีภาวะ heart failure with reduced ejection fraction (HFrEF) ซึ่ง first-line treatment คือ ACE inhibitor เพราะ..."`
- Never start with `"คำตอบที่ถูกต้องคือ"` — go straight to clinical reasoning

**Tone:** Professional yet accessible. Write as if explaining to a medical student, not writing a textbook.

---

### Phase 4 — Self-Review Checklist

Before outputting, silently verify EVERY question:

- [ ] `answer` exactly matches one segment in `choices` (split by `///`, exact string comparison)
- [ ] `choices` uses `///` with no surrounding spaces; exactly 5 segments
- [ ] `problem` starts with question number; includes sufficient clinical context
- [ ] `explain` covers correct answer + ALL 4 distractors ruled out
- [ ] `explain` is Thai prose + English medical terms (NOT pure English)
- [ ] No `\n`, unescaped `"`, or backslashes inside any string value
- [ ] `img: ""`, `select: ""`, `state: false` (boolean) on every object
- [ ] `category` is a single string equal to the verbatim CategoryID of the topic
- [ ] No two questions test the identical clinical point
- [ ] Questions span Basic Science, Diagnosis, and Management

Silently fix any errors before outputting.

---

### Phase 5 — Final Output

Output ONLY the JavaScript code. No markdown fences, no conversational text before or after.

```js
var quizdata = {
    "CategoryID_Topic1": [
        { problem: "1. ...", img: "", choices: "...", answer: "...", select: "", explain: "...", category: "CategoryID_Topic1", state: false },
        { problem: "2. ...", img: "", choices: "...", answer: "...", select: "", explain: "...", category: "CategoryID_Topic1", state: false }
    ],
    "CategoryID_Topic2": [
        { problem: "3. ...", img: "", choices: "...", answer: "...", select: "", explain: "...", category: "CategoryID_Topic2", state: false }
    ]
};
```

**String Safety Rules:**
- All strings on a single logical line — no line breaks inside string values
- Escape any `"` inside strings as `\"`
- No trailing commas after the last object in the array or last key in the object
- Keys use unquoted JS style: `problem:` not `"problem":`

---

## NL Exam Alignment Notes

The Thai National License (NL) exam emphasizes:
- **Clinical application** over pure memorization
- **"Next best step"** management questions (most common type)
- **Mechanism-based** basic science (especially pharmacology, pathophysiology)
- **High-yield associations**: classic presentation → diagnosis → management
- Questions test whether students can **apply knowledge** in real clinical scenarios

When in doubt about difficulty, err toward **moderate-hard** — the NL exam rewards reasoning, not recall.

---

## Integration with medical-quiz-converter

This skill generates questions directly in `var quizdata` format with `category` string fields.
If the user later wants to re-convert, re-categorize, or batch-process with convert.py,
route to the **medical-quiz-converter** skill.

---

## Example Output (2 questions across 2 topics)

```js
var quizdata = {
    "EN_by AI_PHYSIO_Physiology of adrenal hormone": [
        {
            problem: "1. A 35-year-old woman presents with hypertension, central obesity, purple striae on her abdomen, and proximal muscle weakness for 6 months. Labs show fasting glucose 145 mg/dL and serum cortisol 55 mcg/dL (normal: 5-25). A 24-hour urine free cortisol is markedly elevated. Which of the following is the MOST LIKELY source of excess cortisol production?",
            img: "",
            choices: "ACTH-secreting pituitary adenoma///Primary adrenal adenoma///Ectopic ACTH from small cell lung carcinoma///Exogenous glucocorticoid use///Primary adrenal hyperplasia",
            answer: "ACTH-secreting pituitary adenoma",
            select: "",
            explain: "ผู้ป่วยรายนี้มีอาการของ Cushing syndrome ได้แก่ central obesity, purple striae, proximal myopathy, hypertension และ hyperglycemia สาเหตุที่พบบ่อยที่สุด (~70%) คือ Cushing disease ซึ่งเกิดจาก ACTH-secreting pituitary adenoma ทำให้ ACTH สูงและกระตุ้น adrenal cortex ทั้งสองข้างให้ผลิต cortisol มากเกิน ส่วนข้อ B ผิดเพราะ primary adrenal adenoma จะทำให้ cortisol สูงแต่ ACTH ต่ำ (negative feedback) และมักพบ unilateral adrenal mass ข้อ C เป็น ACTH-dependent เช่นกันแต่มักพบในผู้สูงอายุ มี hypokalemia รุนแรง และ ACTH สูงมากผิดปกติ ข้อ D ผิดเพราะ exogenous glucocorticoid จะทำให้ทั้ง cortisol และ ACTH ต่ำ (suppression) ข้อ E ผิดเพราะ primary adrenal hyperplasia พบน้อยมากและต้องการ genetic workup Clinical Pearl: Dexamethasone suppression test ช่วยแยก pituitary vs ectopic ACTH — high-dose suppress ได้เฉพาะ pituitary source",
            category: "EN_by AI_PHYSIO_Physiology of adrenal hormone",
            state: false
        }
    ],
    "EN_by AI_PATHO_Pathology of adrenal gland": [
        {
            problem: "2. A 50-year-old man is found to have an incidental 2.5 cm right adrenal mass on CT scan performed for kidney stones. He denies weight gain, hypertension, or muscle weakness. Biochemical workup shows normal 24-hour urine metanephrines, normal aldosterone-renin ratio, and a 1 mg overnight dexamethasone suppression test cortisol of 0.8 mcg/dL. Which of the following is the MOST APPROPRIATE next step?",
            img: "",
            choices: "Surveillance imaging in 6-12 months///Immediate adrenalectomy///Fine-needle aspiration biopsy of the mass///Start spironolactone empirically///Refer for 131-I MIBG scintigraphy",
            answer: "Surveillance imaging in 6-12 months",
            select: "",
            explain: "ผู้ป่วยรายนี้มี adrenal incidentaloma ขนาด 2.5 cm ซึ่งไม่มี biochemical evidence ของ hypercortisolism (dexamethasone suppression cortisol < 1.8 mcg/dL = suppressed ปกติ), ไม่มี pheochromocytoma (metanephrines ปกติ) และไม่มี primary aldosteronism (ARR ปกติ) ขนาด < 4 cm และ imaging ที่ไม่น่ากังวล → guideline แนะนำ surveillance imaging ที่ 6-12 เดือน ส่วนข้อ B ผิดเพราะ immediate adrenalectomy สงวนไว้สำหรับ mass > 4 cm, rapid growth, หรือ functional tumor ข้อ C ผิดเพราะ FNA ของ adrenal mass ไม่ช่วย diagnose adrenocortical carcinoma ได้ดีและมี risk ของ seeding ข้อ D ผิดเพราะ spironolactone ใช้ใน primary aldosteronism ซึ่งผู้ป่วยนี้ไม่มี ข้อ E ผิดเพราะ MIBG scintigraphy ใช้สำหรับ suspected pheochromocytoma ซึ่ง metanephrines ปกติแล้ว ไม่มีข้อบ่งชี้",
            category: "EN_by AI_PATHO_Pathology of adrenal gland",
            state: false
        }
    ]
};
```