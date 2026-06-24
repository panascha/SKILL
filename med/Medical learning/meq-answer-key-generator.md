---
name: meq-answer-key-generator
description: Generates short, bullet-point "keyword style" model answers (answer keys) for MEQ (Modified Essay Question) clinical exam questions, matching the terse model-answer format used in Thai medical school exam keys (e.g. MD KKU). Use whenever the user asks for a "เฉลย", an "answer key", "model answer", "keyword answer" for MEQ/clinical exam questions, or asks to grade/score what a correct short answer should contain — even if they only paste the questions and a disease name without explicitly saying "answer key." Pairs naturally with the meq-question-generator skill: use this right after generating or receiving a set of MEQ questions.
---

# MEQ Answer Key Generator

Produces the terse, bullet-point model answers that go with MEQ exam questions — the kind a grader checks a handwritten exam answer against, not a textbook paragraph.

## The core constraint: these are keyword answers, not essays

Real MEQ answer keys are written for **speed of grading**, not completeness of explanation. A grader scans a hand-written answer sheet looking for whether the examinee wrote the right *terms*. So each bullet should be:

- A short noun phrase or named entity (a diagnosis, a drug + route, an anatomical structure, a lab value with its abnormality label) — **not** a full sentence restating the question.
- Ordered the way a clinician would generate it (most-likely-first for differentials/organisms; chronological for management steps; by severity for red flags).
- Numbered/lettered to match the question, and counted to match any number the question asked for ("name 3 organisms" → exactly 3 bullets, ranked).

Compare:
- ❌ "The patient most likely has a Pseudomonas aeruginosa infection because the abscess is green-blue in color, which is a classic pathognomonic sign of this organism in burn wounds."
- ✅ "*Pseudomonas aeruginosa* (most likely — green-blue abscess = pathognomonic)"

The parenthetical is fine and often expected (it's how the reference keys work — a 3-8 word reason in parentheses or after a colon), but it should stay a fragment, not a paragraph.

## Output structure

For each question number, produce:

```
**N.M) <restate the question briefly, or just the number>**
- <bullet 1>
- <bullet 2>
- <bullet 3>
```

Group by scenario the same way the questions are grouped, so the answer key is easy to grade scenario-by-scenario against a student's written response.

After the bullet answers for a question, you may add a clearly separated, *short* explanation block if the underlying mechanism is genuinely worth spelling out (1-3 sentences max) — but keep this visually distinct from the bullets themselves (e.g. an indented "เหตุผล:" / "Rationale:" line, or a separate "Mechanism" subsection at the end as the reference keys do). Don't let mechanism explanations bleed into the keyword bullets — graders need to find the bullets fast.

## Calibrating bullet content by question type

- **"What are positive findings, interpreted as medical terms?"** → one bullet per finding, format: `<raw finding> → <medical term>` (e.g. "Right lower facial drooping → Central (UMN) facial palsy").
- **"Name N causes/organisms/structures/drugs"** → exactly N bullets, ranked by likelihood, each a name only (plus a short parenthetical reason if it disambiguates, e.g. why this organism and not another).
- **"What is the provisional/definite diagnosis?"** → 1 bullet, the diagnosis stated the way it would appear in a chart (e.g. "Acute ischemic stroke, left MCA territory" not just "stroke").
- **Drug questions** → bullet per drug, format: `Drug name (route) — one-line mechanism`. Always give a real route (PO/IV/topical) and a real mechanism, not a placeholder.
- **"Explain the mechanism/pathogenesis in N steps"** → a short numbered chain (`A → B → C → D`), each link 2-6 words, not prose. This is the one place where the bullets *are* the mechanism, so keep each step a single causal hop.
- **Lab/value interpretation with reasons** → bullet per abnormal value: `<value/finding> (<abnormal-direction label>) — <1-line reason>`. If asked for "3 abnormal results," don't pick three that are all explained by the same single mechanism (e.g. all just "dehydration") unless the question is specifically testing that they recognize the shared cause — reference keys explicitly warn against this redundancy.
- **Counseling/advice/lifestyle questions** → exactly N short imperative bullets a patient could actually follow ("avoid heavy lifting," "lifelong antiplatelet therapy"), not abstract goals.

## Accuracy is non-negotiable — check against current evidence, don't just pattern-match the question

Bullet answers are short, which makes a wrong drug or mechanism look just as authoritative as a right one. Before finalizing:
- Verify drug/mechanism pairings against current standard-of-care (e.g. neuropathic pain after burns is gabapentinoids/TCAs, not opioids; routine high-flow O2 isn't recommended in normoxic ischemic stroke). If you're aware the "obvious" textbook-sounding answer is actually outdated or contested, give the evidence-based answer and add a one-line flag noting the discrepancy rather than silently propagating it.
- Make any numbers you cite actually consistent (a WBC differential must sum to 100%; an osmolality you assert as abnormal should be calculated correctly: 2×Na⁺ + glucose(mg/dL)/18 [+ BUN/2.8 if total, not effective, osmolality is intended] ).
- If a question's premise is itself ambiguous or under-specified given the scenario as written, it's fine to note that briefly rather than inventing false precision.

## Worked example (style reference)

From a burns MEQ, question "2.2) จงบอกเชื้อที่คนไข้มีโอกาสติด จากความเป็นไปได้มากสุดไปน้อยสุด (3 ข้อ)" given a green-blue abscess:

```
**2.2) Likely organisms (most → least likely)**
- *Pseudomonas aeruginosa* — green-blue pus is pathognomonic (pyocyanin/pyoverdine pigment)
- *Staphylococcus aureus* — common burn-wound colonizer
- *Klebsiella pneumoniae* — gram-negative burn pathogen

Rationale: Eschar is avascular, so systemic antibiotics alone won't reach it — topical silver sulfadiazine is added for local control alongside systemic coverage.
```

Note the structure: ranked bullets with terse reasons, then one short rationale line set apart — not folded into the bullets.

## Input handling

- If given a full MEQ (scenario text + numbered questions), answer every sub-question in order, scenario by scenario.
- If given only a disease/topic with no explicit questions, ask whether the user wants you to generate matching questions first (point them at `meq-question-generator`) or just produce a standalone keyword summary of the disease's classic MEQ-style answers (history clues, exam findings, key labs, diagnosis, management, complications) — pick the latter by default if they seem to just want quick study bullets rather than a graded key.
- Match the language mix of the source questions (Thai instruction + English medical terminology is the norm in the reference materials) unless told otherwise.