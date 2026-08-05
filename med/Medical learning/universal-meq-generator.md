---
name: universal-meq-generator
description: >
  Generate Thai medical-style MEQ (Modified Essay Question) exams — progressive, multi-part
  clinical case questions used in Thai medical school board exams — from any learning source
  (notes, textbook chapters, slides, a topic name). Produces two files every time: a blank
  MEQ exam (staged clinical vignette, scored sub-questions, answer space) and a matching
  answer key (tiered real-world-breadth answers plus pathophysiology explanations). Use this
  whenever the user wants study material turned into practice exam questions, an "ข้อสอบ
  MEQ", a clinical case exam, or an exam+key pair for board exam prep — even without saying
  "MEQ" (e.g. "make a case exam from this chapter", "quiz me MEQ style on thalassemia",
  "แปลงเนื้อหานี้เป็นข้อสอบผู้ป่วยจำลอง"). Route staged/continuing clinical-case questions
  here instead of a flat MCQ or short-answer quiz.
---

# Universal MEQ Generator

## What an MEQ is (so the output feels authentic)

An MEQ (Modified Essay Question) is not a flat list of questions — it's **one clinical case that unfolds in stages**. Each stage (ตอนที่ 1, ตอนที่ 2, ... / Scenario I, II, III...) reveals a little more information — first the presenting complaint, then history/exam findings, then labs or imaging — and asks the student to reason from only what's been revealed so far. This mirrors real clinical reasoning: you can't order every test at once, you build a differential and narrow it down as data arrives.

That progressive reveal is the entire point of the format. Don't flatten it into a single wall of questions about a fully-described patient — the pedagogical value is in forcing the student to commit to an answer with incomplete information before the next stage is unlocked.

## Critical rule: the case should make the student diagnose — never the question itself

This is the most common way this format breaks, so read it closely before drafting.

**The single biggest failure mode is naming the diagnosis inside the question stem or the revealed-data text.** If a question says "why doesn't a normal exam rule out Asthma" or "what test confirms Reflux-induced Cough," the student has already been told the answer — they're just asked to cite support for a fact they were handed, not to reason their way to it. That's the opposite of what an MEQ is for. Similarly, if the "results revealed" text describes an endoscopy as "consistent with Reflux Esophagitis Grade A" instead of describing the raw mucosal findings, the diagnosis has leaked before the question was even asked.

Concrete rules:
- **Never write a specific disease name inside a question stem**, unless an earlier sub-question in the same case already required the student to state that diagnosis themselves. Even then, refer back to it as "โรคที่ท่านวินิจฉัย" (the diagnosis you gave) rather than restating the name — students who got it wrong shouldn't get a free hint from a later question.
- **Revealed data must stay descriptive, never pre-diagnosed.** Labs, imaging, and exam findings go in as raw observations a clinician would actually read off a report — values, morphology, visual appearance — never labeled with the diagnostic conclusion. "Endoscopy shows shallow mucosal breaks in the distal esophagus" is fine; "endoscopy consistent with Reflux Esophagitis" is not — that's the answer, not a finding.
- **DDx question stems must stay data-driven, not pre-filtered.** Don't write "differential diagnosis for a cough that's positional and worse after meals" — that phrase alone already points straight at reflux. Ask plainly — "จากข้อมูลทั้งหมด จงระบุการวินิจฉัยแยกโรคที่เป็นไปได้มากที่สุด 3 อันดับ" — and let the vignette's own details carry the signal, not the question's wording.
- **Ask the way a clinician actually thinks, not the way a textbook summarizes a case.** Prefer "จากข้อมูลนี้ ท่านคิดว่าผู้ป่วยเป็นโรคใดมากที่สุด และจะส่งตรวจใดเพื่อยืนยัน" (what's your leading diagnosis, and what would confirm it) over "why does finding X support diagnosis Y" — the first makes the student commit and defend a position; the second hands them the conclusion and asks for a citation.
- When you catch yourself writing a question that only makes sense if the reader already knows the diagnosis, that's the signal to rewrite it, not a sign the case is "advanced."

## Workflow

### Step 1: Get the learning source and topic

The user provides a learning source — pasted notes, an uploaded file, or just a topic name. Read/skim it for the disease(s), key diagnostic reasoning steps, and any teaching points that lend themselves to a "what would you do next" structure (a workup sequence, a set of red flags, a management decision point). If a file is mentioned but not yet in context, read it first (check `/mnt/user-data/uploads`).

### Step 2: Propose the case structure, then confirm

Before writing anything, decide how many parts (ตอนที่) the case should have and tell the user your reasoning, then let them confirm or override — don't just pick silently and don't generate without checking in first.

Rough guide for the suggestion (adjust based on judgment, not just word count of the source):
- **2 parts**: a narrow, single-decision-point topic (e.g., recognize a classic presentation → interpret one confirmatory test)
- **3 parts**: the standard shape — matches most real MEQs — (1) history/exam reasoning, (2) differential + workup, (3) result interpretation + management. Use this as your default unless the source clearly calls for something else.
- **4+ parts**: a topic with a genuine multi-stage clinical course (e.g., acute presentation → stabilization → complication → long-term management) or several distinct sub-conditions worth separating out.

If a tool for asking the user a quick choice is available, use it; otherwise just ask directly in text. Proceed once they've confirmed a count (or explicitly said "you decide").

### Step 3: Design the case before drafting text

Sketch, even just mentally:
- Patient: age, sex, presenting complaint — chosen so the natural workup **is** the teaching content of the source
- What gets revealed at each part, in the order a real clinician would obtain it (Hx → PE → basic labs → special tests/imaging → results after treatment)
- Which parts (if any) hinge on visual data (blood smear, X-ray, CT, ECG, gross/microscopic pathology, skin lesion). If the source's teaching point is visual, include one — see the image convention below.
- For each part, the specific sub-questions and, for each, how many discrete items the answer needs (this drives both blank-line count in the exam and answer-bullet count in the key)
- **Where the "state your diagnosis" question sits, and what every other question is allowed to say as a result.** Place it deliberately — usually once the data is sufficient to reasonably commit — and make sure no earlier or later question stem, or any revealed-data text, names that diagnosis before or instead of the student (see the rule above).

Invent an original vignette — don't lift patient descriptions or exact wording from any copyrighted source material even if the underlying medical facts come from it.

### Step 4: Write the exam file

Follow this structure exactly (see Format Reference below for the literal template). Key rules:

- Each part starts with `### ตอนที่ N (X คะแนน, Y นาที)` — assign points/time proportional to how much reasoning the part demands (a "list 10 history questions" part is worth more and takes longer than "interpret one lab value")
- Every part after the first opens with a continuity line: `> _ต่อเนื่องจากผู้ป่วยตอนที่ [previous part(s)]_`
- Present only the information appropriate to that stage — never leak later-stage findings early, and never phrase revealed data or a question stem in a way that states the diagnosis for the student (see the Critical Rule above — this is the most important thing to get right)
- Each sub-question is bold, numbered, and states its point value and, if it wants a specific count of items, that count too: `**1. Differential diagnosis 3 ข้อ (10 คะแนน)**`
- Answer space is a blockquote of dotted lines (`> ......`). Line count logic:
  - If the question asks for a specific number of items ("3 ข้อ", "4 อย่าง", "2 คำตอบ"), use exactly that many lines
  - If it's an open essay-style prompt with no explicit count (e.g., "จงบอกการซักประวัติที่ช่วยวินิจฉัย"), use a line count close to the point value, capped around 12–15 lines so the exam doesn't look absurd for high-point questions
- If a part includes a visual finding, add it right after the revealed data, before the questions: `> 🖼️ **ภาพประกอบ:** [neutral description of what's visually present — describe findings, don't name the diagnosis]`
- Separate parts with `---`

### Step 5: Write the key file

Same skeleton as the exam (headers, continuity lines, revealed data, image notes) but every blank is replaced with the answer, and every answer reflects the real breadth a practicing clinician would accept — not a checklist padded to a round number:

- **Don't just pad "3 ข้อ" up to "3 + 2 bonus."** Real practice rarely has one correct list — differentials, confirmatory tests, and especially treatment choices vary by guideline, resource setting, and patient factors. Structure the answer in tiers instead of a flat count:
  - **Core answer(s)** — the most important, most guideline-supported points; these carry most of the credit
  - **Also acceptable** — other answers a competent clinician might reasonably give, presented as genuinely valid, not as an afterthought
  - Use the `(+/-)` marker only for answers that are genuinely secondary or edge-case — not as a container for mainstream alternatives that just didn't make the top of the list
- **Include one line, once, near the top of the key file**, making the grading philosophy explicit: the listed answers are model answers, not an exhaustive list, and any answer with sound clinical reasoning should receive credit even if it isn't written out below. This matters most for open questions (workup choices, management plans) where the "right" answer is really a right *category* of answers.
- **Explain, don't just assert.** For every answer — not only the ones that explicitly say "อธิบาย" or "explain" — add a short line tying it back to physiology or clinical reasoning: *why* this is the answer, not just what it is. For lab/imaging interpretation questions especially, walk through the mechanism (e.g., why a hormone is low given a feedback loop, why a cell morphology implies a mechanism of anemia). This is the part that makes the key useful for actual studying, not just grading.
- Keep single-best-answer questions tight (`**Ans:** ...`) but still follow with 1–2 sentences of reasoning.
- Use numbered sub-lists when the question itself is numbered/lettered (e.g., "1.2", "1.3"), matching the exam's numbering exactly so a student can line the two files up side by side.

### Step 6: Language

Write the case narrative, question stems, and explanations in **Thai**, keeping medical/technical vocabulary — drug names, lab abbreviations, disease names, imaging modalities — in **English**, exactly the way Thai clinical exams and case discussions actually read (e.g., "มี tophi ที่ข้อเท้า", "Low-dose dexamethasone suppression test"). If the learning source itself is in English throughout, mirror that instead — the goal is to match the register of the input, defaulting to Thai-primary when the source doesn't make it obvious.

### Step 7: Save and present

Save both files as markdown, named from the case topic:
- `/mnt/user-data/outputs/<topic-slug>_exam.md`
- `/mnt/user-data/outputs/<topic-slug>_key.md`

Then present both files to the user. Don't paste the full content into the chat as well — the files are the deliverable.

---

## Format Reference

### Good vs. bad question stem (worked example)

> ❌ **Bad — names the diagnosis, asks for a citation:**
> "เหตุใดผลตรวจร่างกายและ CXR ที่ปกติจึงไม่สามารถตัดภาวะ **Asthma** ออกได้ (6 คะแนน)"
>
> ✅ **Good — same teaching point, student still has to commit:**
> "ผลตรวจร่างกายระบบหายใจและ CXR ของผู้ป่วยรายนี้ปกติ จงอธิบายว่าเหตุใดผลปกตินี้จึงไม่สามารถใช้ตัดโรคที่ท่านสงสัยมากที่สุดออกจากการวินิจฉัยแยกโรคได้ (6 คะแนน)"

> ❌ **Bad — the qualifier itself gives away the category:**
> "จงระบุการวินิจฉัยแยกโรคสำหรับอาการไอเรื้อรังที่สัมพันธ์กับท่าทางและมื้ออาหาร (6 คะแนน)"
>
> ✅ **Good — lets the vignette's details do the work instead of the question wording:**
> "จากข้อมูลทั้งหมดที่ได้ จงระบุการวินิจฉัยแยกโรคที่เป็นไปได้มากที่สุด 3 อันดับ (6 คะแนน)"

> ❌ **Bad — revealed data pre-diagnoses the finding:**
> "Upper GI Endoscopy พบรอยโรคเข้าได้กับ **Reflux Esophagitis (LA Grade A)**"
>
> ✅ **Good — same finding, described raw:**
> "Upper GI Endoscopy พบ mucosal breaks สั้นๆ บริเวณ distal esophagus ยาวไม่เกิน 5 มม."

### Exam file skeleton

```markdown
# MEQ: [Topic Name in Thai/English]

## ตอนที่ 1 ([X] คะแนน, [Y] นาที)

[Patient demographics + presenting complaint, 1-2 sentences]

**1. [Question stem] ([X] คะแนน)**

> .................................................................................................................
> ................................................................................................................. 
[... one line per required item or per point, per the rule above]

---

## ตอนที่ 2 ([X] คะแนน, [Y] นาที)
> _ต่อเนื่องจากผู้ป่วยตอนที่ 1_

**ผลการซักประวัติ/ตรวจร่างกาย:** [new info revealed as raw findings only — values, appearance, morphology — never a pre-labeled diagnostic conclusion]

**1. [Question stem] [N] ข้อ ([X] คะแนน)**

> .................................................................................................................
[N lines]

---

## ตอนที่ 3 ([X] คะแนน, [Y] นาที)
> _ต่อเนื่องจากผู้ป่วยตอนที่ 1 และ 2_

**ผลตรวจทางห้องปฏิบัติการ:** [labs/imaging]

> 🖼️ **ภาพประกอบ:** [only if relevant — neutral visual description]

**1. [Question stem] ([X] คะแนน)**

> .................................................................................................................
[lines]
```

### Key file skeleton

Mirrors the exam 1:1, structurally — same headers, same continuity notes, same revealed data — but every question is followed by its answer instead of blank lines:

```markdown
# MEQ Answer Key: [Topic Name]

> หมายเหตุ: คำตอบด้านล่างเป็นตัวอย่างคำตอบหลักที่ควรได้คะแนนเต็มหรือใกล้เคียง ไม่ใช่รายการคำตอบทั้งหมด
> คำตอบอื่นที่มีเหตุผลทางคลินิกรองรับสามารถให้คะแนนได้ตามดุลยพินิจผู้ตรวจ

## ตอนที่ 1 ([X] คะแนน, [Y] นาที)

[same vignette as exam — raw findings, no diagnostic labels]

**1. [Question stem] ([X] คะแนน)**
- [Core answer 1] — [why: brief mechanism/reasoning]
- [Core answer 2] — [why]
- [Core answer 3] — [why]
- **คำตอบอื่นที่ยอมรับได้:** [Also-acceptable answer(s)] — [why]
- (+/-) [Genuinely secondary/edge-case point]
```

For single-answer questions:

```markdown
**1. [Question stem, 1 คำตอบ]**
- **Ans:** [Diagnosis/answer]
- [1-2 sentences explaining why the findings point here and not to close differentials]
```

---

## Quick self-check before saving

- **Read every question stem and every "revealed data" block and ask: could someone answer this, or recognize the diagnosis, just from the wording — without reasoning through the clinical data?** If yes, rewrite it (this is the single most important check — re-read the Critical Rule section above if anything fails it).
- Does any question stem name a diagnosis before the student was asked to state it themselves? Does any lab/imaging finding come pre-labeled with a diagnostic conclusion instead of described raw?
- Does each later part avoid repeating info the student should already have written down (no re-stating findings from part 1 unless it's the recap line), and avoid leaking anything from a later part?
- Does every "N ข้อ" style question have exactly N blank lines in the exam?
- Does the key present tiered, illustrative answers (core + also-acceptable) with the credit-for-sound-reasoning note, rather than a rigid list padded to a round number?
- Does every key answer have a reason attached, not just a bare list?
- Thai/English mix consistent with the source's register?
- Two separate files saved, both delivered?