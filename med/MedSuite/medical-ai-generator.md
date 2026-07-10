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

If sample exam is missing, default to USMLE Step 1/2 clinical vignette style — but kept short per
the length rules in 2.1 below.

---

### Phase 1 — Question Blueprint (Internal Planning)

Before generating, read the **question count** from the input (default 35 if not specified).
Then silently plan a **content distribution** proportional to that count:

| Category | Target Share | Question Types |
|---|---|---|
| Basic Science (ANA, PHYSIO, BIOCHEM, PHARM, MICRO, PATHO) | ~70% | Mechanism-based, "Why does...", direct knowledge recall and understanding |
| Clinical Application (short-vignette Dx/Management) | ~30% | Brief clinical scenario requiring applied reasoning |

This is a deliberate shift toward foundational science: most questions should test whether the
student understands the underlying mechanism, structure, or pathway directly — not wrapped in a
long clinical story. Only ~30% of questions should be clinical-application style, and even those
stay brief (see 2.1).

Also plan which CategoryID (topic key) each question belongs to — distribute across multiple topics when possible.

Ensure no two questions test the identical learning point.

---

### Phase 2 — Question Generation Rules

#### 2.1 Question Design

**Length rule (applies to ALL questions, non-negotiable):**
Keep `problem` short enough to read in one glance — target **2-4 sentences max**, roughly
under ~60 words. Long blocks of vitals/labs/timeline make the question "อ่านแล้วตาลาย" (eye-straining
wall of text) — avoid that. Cut anything not essential to answering the question. If a clinical
detail doesn't change the answer, leave it out.

**Basic Science Format (~70% of questions):**
- Ask directly about a fact, mechanism, structure, pathway, or principle
- Can be a plain knowledge/understanding question — no vignette required
- When a mini-scenario helps (e.g., "A drug that blocks X would most affect..."), keep it to
  one short sentence of setup, then the question
- Focus on "Why/How" or straightforward "What is/does..." — mechanisms, pathways, consequences,
  structures, classic associations
- Example length: *"Which receptor mediates the vasoconstrictor effect of norepinephrine on
  vascular smooth muscle?"* — one sentence, no padding

**Clinical Application Format (~30% of questions):**
- Short vignette: 1-2 sentences max of clinical setup (age/sex + 1 key finding or short
  history is usually enough — do NOT stack vitals + labs + PE + imaging unless absolutely
  necessary to discriminate between answer choices)
- End with a specific stem: "Which of the following is the MOST LIKELY diagnosis?", "What is the
  NEXT BEST STEP in management?", "Which mechanism BEST explains...?"
- Still requires reasoning, just compressed — trim every detail that isn't load-bearing for the answer

**Question Stems to Vary (never repeat the same stem twice in a row):**
- "Which of the following is MOST LIKELY to..."
- "What is the NEXT BEST STEP in management?"
- "Which mechanism BEST explains...?"
- "Which of the following BEST describes the function/structure of...?"
- "Which drug is MOST APPROPRIATE for...?"
- "Which of the following lab findings is MOST consistent with...?"
- "Which of the following BEST describes the pathophysiology of...?"

#### 2.2 Choices Formatting

- Exactly **5 choices** per question
- Separator: `///` — **absolutely no spaces before or after**
  - ✅ `"Metformin///Insulin///Glipizide///Acarbose///Sitagliptin"`
  - ❌ `"Metformin /// Insulin"` or `"Metformin ///Insulin"`
- **Plausible distractors**: choices must be homogeneous in grammatical structure and approximate length
- **No obvious wrong answers**: every choice should require clinical/scientific reasoning to rule out
- **Distractor strategy**: include related structures/mechanisms/drugs that partially fit, common
  misconceptions, or adjacent-but-wrong concepts
- Keep choices short and parallel — single words, short phrases, or short clauses; avoid long
  choice sentences that add to visual clutter

#### 2.3 Answer Matching

- `answer` must be a **character-for-character exact match** to one segment in `choices`
- Verify: Split `choices` by `///` → confirm `answer` === one of the 5 segments exactly

#### 2.4 Numbering

- Start `problem` text with question number: `"1. A 45-year-old..."`, `"2. Which of..."`
- Number sequentially from 1 to 35 across ALL topics (do not restart per topic)

---

### Phase 3 — Explanation Writing (Critical Quality Gate)

Each `explain` must be a **single continuous paragraph** — no `\n`, no bullet points inside the string.
The explanation can still be thorough even though the question stem is short — depth belongs in
`explain`, not in `problem`.

**Required structure (flowing prose, NOT labeled sections):**

1. **Key Concept** — Open by identifying the core mechanism/diagnosis/concept being tested
2. **Why Correct** — Explain the correct answer using specific reasoning or evidence from the question stem
3. **Rule Out Each Distractor** — For EACH of the 4 wrong choices, explain why incorrect
   - Style: `"ส่วนข้อ B ผิดเพราะ... (because...)"`, `"ข้อ C มักใช้ในกรณี... แต่..."`
   - Be specific — reference the actual concept being tested, not generic statements
4. **Clinical/High-Yield Pearl** (optional) — One high-yield fact for NL/board exams

**Language Rule (Non-negotiable):**
- `explain` MUST be Thai prose mixed with English medical terminology
- ❌ Pure English forbidden: `"The correct answer is ACE inhibitor because..."` — NEVER
- ✅ Mixed Thai/English: `"ผู้ป่วยรายนี้มีภาวะ heart failure with reduced ejection fraction (HFrEF) ซึ่ง first-line treatment คือ ACE inhibitor เพราะ..."`
- Never start with `"คำตอบที่ถูกต้องคือ"` — go straight to the reasoning

**Tone:** Professional yet accessible. Write as if explaining to a medical student, not writing a textbook.

---

### Phase 4 — Self-Review Checklist

Before outputting, silently verify EVERY question:

- [ ] `answer` exactly matches one segment in `choices` (split by `///`, exact string comparison)
- [ ] `choices` uses `///` with no surrounding spaces; exactly 5 segments
- [ ] `problem` starts with question number; is short (2-4 sentences, ~60 words max) — no wall-of-text vitals/labs dump
- [ ] `explain` covers correct answer + ALL 4 distractors ruled out
- [ ] `explain` is Thai prose + English medical terms (NOT pure English)
- [ ] No `\n`, unescaped `"`, or backslashes inside any string value
- [ ] `img: ""`, `select: ""`, `state: false` (boolean) on every object
- [ ] `category` is a single string equal to the verbatim CategoryID of the topic
- [ ] No two questions test the identical point
- [ ] Roughly 70% basic science (direct/mechanism-based) vs 30% short clinical-application questions overall

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
- **Clinical application** over pure memorization — but this skill weights toward basic science
  (~70%) per current configuration, with clinical application as a smaller (~30%) but still
  important slice
- **"Next best step"** management questions (most common clinical-style type)
- **Mechanism-based** basic science (especially pharmacology, pathophysiology) — this is now the
  primary focus
- **High-yield associations**: structure/mechanism → function, or classic presentation → diagnosis
- Questions test **understanding**, not just recall — even short basic-science stems should
  require knowing *why*, not just *what*

When in doubt about difficulty, err toward **moderate** — testing real understanding while staying
quick to read.

---

## Integration with medical-quiz-converter

This skill generates questions directly in `var quizdata` format with `category` string fields.
If the user later wants to re-convert, re-categorize, or batch-process with convert.py,
route to the **medical-quiz-converter** skill.

---

## Example Output (3 questions — 2 basic science, 1 short clinical — across 2 topics)

```js
var quizdata = {
    "EN_by AI_PHYSIO_Physiology of adrenal hormone": [
        {
            problem: "1. Which zone of the adrenal cortex is primarily responsible for cortisol synthesis?",
            img: "",
            choices: "Zona fasciculata///Zona glomerulosa///Zona reticularis///Adrenal medulla///Zona pellucida",
            answer: "Zona fasciculata",
            select: "",
            explain: "Zona fasciculata เป็นชั้นกลางของ adrenal cortex และเป็นแหล่งสร้าง cortisol หลักภายใต้การควบคุมของ ACTH จาก anterior pituitary ส่วนข้อ B (zona glomerulosa) ผิดเพราะชั้นนอกสุดนี้สร้าง aldosterone เป็นหลัก ควบคุมโดย renin-angiotensin system ไม่ใช่ ACTH ข้อ C (zona reticularis) ผิดเพราะชั้นในสุดสร้าง androgens (DHEA) เป็นหลัก ข้อ D (adrenal medulla) ผิดเพราะเป็นคนละส่วนกับ cortex สร้าง catecholamines ไม่ใช่ steroid hormone ข้อ E (zona pellucida) ผิดเพราะเป็นโครงสร้างของ oocyte ไม่เกี่ยวกับต่อมหมวกไต Clinical Pearl: จำลำดับชั้นจากนอกสุดเข้าใน ด้วย mnemonic 'GFR' (Glomerulosa-Fasciculata-Reticularis) คู่กับ 'salt-sugar-sex'",
            category: "EN_by AI_PHYSIO_Physiology of adrenal hormone",
            state: false
        },
        {
            problem: "2. A drug that blocks 11-beta-hydroxylase would most directly impair synthesis of which hormone?",
            img: "",
            choices: "Cortisol///Aldosterone only///DHEA///Estrogen///Testosterone",
            answer: "Cortisol",
            select: "",
            explain: "11-beta-hydroxylase เป็น enzyme สำคัญในขั้นตอนสุดท้ายของการสร้าง cortisol (เปลี่ยน 11-deoxycortisol เป็น cortisol) ในชั้น zona fasciculata การยับยั้ง enzyme นี้จึงลด cortisol production โดยตรง ส่วนข้อ B ผิดเพราะแม้ enzyme นี้มีบทบาทบางส่วนใน aldosterone pathway แต่ผลกระทบหลักและเด่นชัดที่สุดคือต่อ cortisol ไม่ใช่ aldosterone อย่างเดียว ข้อ C ผิดเพราะ DHEA synthesis ไม่ต้องพึ่ง 11-beta-hydroxylase ข้อ D และ E ผิดเพราะ sex steroid pathway ใช้ enzyme คนละชุด (เช่น 17,20-lyase) Clinical Pearl: 11-beta-hydroxylase deficiency เป็นสาเหตุของ congenital adrenal hyperplasia ที่ทำให้เกิด hypertension จาก mineralocorticoid precursor สะสม",
            category: "EN_by AI_PHYSIO_Physiology of adrenal hormone",
            state: false
        }
    ],
    "EN_by AI_PATHO_Pathology of adrenal gland": [
        {
            problem: "3. A 50-year-old man has an incidental 2.5 cm adrenal mass with normal hormone workup. What is the MOST appropriate next step?",
            img: "",
            choices: "Surveillance imaging in 6-12 months///Immediate adrenalectomy///Fine-needle aspiration biopsy///Start spironolactone empirically///131-I MIBG scintigraphy",
            answer: "Surveillance imaging in 6-12 months",
            select: "",
            explain: "Adrenal incidentaloma ขนาด < 4 cm ที่ biochemically silent (hormone workup ปกติทั้งหมด) และ imaging ไม่น่ากังวล → guideline แนะนำ surveillance imaging ที่ 6-12 เดือนแทนการผ่าตัดทันที ส่วนข้อ B ผิดเพราะ adrenalectomy สงวนไว้สำหรับ mass > 4 cm, โตเร็ว, หรือ functional tumor ข้อ C ผิดเพราะ FNA ไม่ช่วยแยก adrenocortical carcinoma ได้ดีและมี risk ของ tumor seeding ข้อ D ผิดเพราะ spironolactone ใช้เมื่อมี primary aldosteronism ซึ่งผู้ป่วยนี้ workup ปกติ ข้อ E ผิดเพราะ MIBG ใช้ตรวจ pheochromocytoma ซึ่งไม่มีข้อบ่งชี้ในรายนี้",
            category: "EN_by AI_PATHO_Pathology of adrenal gland",
            state: false
        }
    ]
};
```