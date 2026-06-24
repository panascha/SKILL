---
name: meq-question-generator
description: Generates Modified Essay Question (MEQ) clinical exam scenarios for medical education, in the progressive multi-scenario style used by Thai medical schools (e.g. MD KKU). Use whenever the user asks to write, draft, create, or "ออกข้อสอบ" / "สร้างคำถาม" / "แต่งโจทย์" MEQ, OSCE-style written exam, or a clinical case-based exam question for a named disease, system, or topic — even if they just give a disease name and say "ทำ MEQ ให้หน่อย" or "generate an MEQ for X". Also use when asked to extend an existing MEQ scenario with a follow-up scene/scenario.
---

# MEQ Question Generator

Writes Modified Essay Question (MEQ) exam items: a clinical vignette that unfolds across 2–3 escalating "scenarios" (scenes), each followed by a short numbered set of sub-questions that test a different layer of clinical reasoning (history → exam → investigations → diagnosis → mechanism → management → long-term care).

This format is used in Thai medical curricula (referenced here as "MD KKU"-style) but the structure generalizes to any case-based written clinical exam.

## Why this structure works

MEQs are not just "ask a question about disease X." Their power comes from **forcing the examinee to commit to an answer before more data is revealed** — exactly like real clinical reasoning. Each new scenario should plausibly follow from (and sometimes correct or complicate) the answer to the previous one. Don't reveal the diagnosis early; let it emerge from clues the student has to interpret.

## Input needed

At minimum you need a disease/topic (e.g. "tuberculous arthritis", "acute ischemic stroke", "Graves' disease", "mitral stenosis with AF and heart failure"). If the user doesn't specify, infer or ask for:
- **Target learner level** (default: medical student, final years / clinical clerkship)
- **Number of scenarios** (default: 3 — see structure below)
- **System/subject framing** (e.g. file this under "Endocrine System MEQ Key" the way the reference examples do), if they're building a set
- **Language** — default to the same mix the reference examples use: Thai for narrative/questions framed in Thai instruction verbs ("จงบอก", "จงอธิบาย"), English for exam-style sub-questions ("What is the provisional diagnosis?") and all medical/technical terms. If the user asks for a fully English or fully Thai version, follow that instead.

If genuinely ambiguous (e.g. "make an MEQ" with no topic at all), ask one clarifying question. Otherwise pick a sensible, common clinical presentation for the disease and proceed — don't stall on clarifying questions for something this generative.

## Overall shape

```
[Title] MEQ — <Disease/System> Key
[Optional: section marker if part of a set, e.g. "MEQ I"]

SCENARIO 1
<Vignette: demographics, chief complaint, history of present illness,
 relevant past history/risk factors, physical exam findings>

1.1) <question>
1.2) <question>
1.3) <question>
...

SCENARIO 2
<New info: investigation results, labs, imaging — revealed only after
 scenario-1 questions would have been answered>

2.1) <question>
2.2) <question>
...

SCENARIO 3
<Treatment response / follow-up / complication / discharge>

3.1) <question>
3.2) <question>
...
```

Two or three scenarios is typical. A short topic can do 2; a rich topic (e.g. burns, stroke) can do 3-5 scenarios with 2-4 sub-questions each. Don't pad — every sub-question should test something a clinician actually needs to know, not trivia.

## What goes in each scenario

**Scenario 1 — Presentation.** Demographics + chief complaint + a *duration* ("for 2 weeks", "3 months ago"). History of present illness should read like a real history, with a clear timeline ("2 weeks ago... 2 days ago..."). Weave in 1-2 risk factors or red herrings that are *medically real* (e.g. a patient who self-medicates with NSAIDs, or stopped their metformin 2 years ago) — these aren't tricks, they're the kind of detail a real history would surface and that later questions can exploit (e.g. "why did the doctor ask about X"). Past history should include anything causally relevant (e.g. childhood rheumatic fever history before revealing valvular disease). Physical exam findings should be *specific and measurable* (e.g. "SLRT positive at 40°", "BP 90/48, HR 118", "Dix-Hallpike: upbeat torsional nystagmus toward the right ear") rather than vague ("patient looks sick"). Include enough exam findings to localize the lesion/diagnosis but not so many that the diagnosis is obvious without reasoning — let some findings be genuinely diagnostic and others be supportive/distractor (e.g. normal findings worth noting, like "no weakness," "bowel/bladder normal").

Typical Scenario-1 question set:
- Positive/negative finding interpretation ("What are positive findings, interpreted as medical terms?")
- Anatomic/lesion localization ("Where is the lesion and why?")
- Additional history or exam to ask for (a great way to test what a thorough clinician would check)
- Pain/symptom mechanism if relevant
- Differential or provisional diagnosis

**Scenario 2 — Workup.** Reveal investigation results consistent with (but not 100%-overlapping with) the working diagnosis — include some numbers that need interpreting (e.g. an osmolality the student must calculate or recognize as abnormal, an INR that changes management, a culture result). Real labs have noise: include 1-2 *normal* results among the abnormal ones (this rewards students who know what's relevant). If you want a values-based reasoning question, give the actual raw numbers (Na+, glucose, BUN/Cr, WBC differential, etc.) rather than already-interpreted labels, so the sub-question can ask the student to interpret them.

Typical Scenario-2 question set:
- Interpret abnormal labs and explain mechanism (ask for a fixed number — "3 abnormal results, with reasons")
- Definite/confirmed diagnosis
- Immediate management (ask for drug names + route, not just drug classes)
- Pathogenesis / "how do the risk factors lead to this" chain-of-mechanism question

**Final scenario(s) — Course & disposition.** Show a response to treatment (improvement, a complication, or a need to change therapy — e.g. switching IV to subcutaneous insulin, escalating to surgery, discharge). This scenario is the natural home for:
- Long-term complications (ask for a specific count, e.g. "name 2/4")
- Patient education / lifestyle advice (ask for a specific count, e.g. "give 5 pieces of advice")
- Reasoning about a management *change* ("why switch from X to Y")
- Secondary prevention / follow-up planning

## Question-writing rules

1. **Number sub-questions** `N.M)` and **ask for a count** when the answer is a list ("name 3 organisms", "give 4 pieces of advice") — this is what makes MEQ answers gradeable.
2. **Mix question types** across the whole MEQ: pure recall (drug names, normal values), interpretation (lab/exam finding → meaning), mechanism ("explain the pathophysiology in N steps"), and management/communication (patient counseling, informed consent, discharge advice). Don't make every question "what is the diagnosis."
3. **Make numbers internally consistent.** If you give a TBSA calculation, an osmolality, or a differential count, the numbers must actually compute correctly (effective osmolality = 2×Na + glucose/18; WBC differential must sum to 100%). This is the single most common error in past Thai exam materials reviewed — double-check arithmetic before finalizing.
4. **Don't give away the diagnosis in scenario 1.** Findings should be specific enough to localize/narrow but should require the synthesis step the question is actually testing.
5. **Use real drug names, real routes, real mechanisms.** If the gold-standard treatment differs from what a quick guess would produce (e.g. neuropathic pain → gabapentinoids, not opioids), make sure your own model answer matches current evidence — don't propagate a plausible-sounding but outdated answer.
6. **Vary phrasing of instruction verbs** so the exam doesn't feel templated: "จงบอก/บรรยาย/อธิบาย" (Thai: state/describe/explain), "What is/are...", "Explain the mechanism of...", "How would you manage...", "Provide N reasons why...".

## Worked reference patterns

These come from real MEQ keys across Skin, Musculoskeletal, Nervous, Endocrine, and Cardiovascular systems — use them as a feel-for-style reference, not a template to copy verbatim:

- **Burns** — Scenario 1 gives two different burn appearances on different body regions (one full-thickness, one superficial) and a TBSA calculation; later scenarios add infection (organism inferred from pus color), then wound-healing divergence between the two regions, then long-term rehab.
- **Low back pain** — Scenario 1: mechanism-of-injury history + SLRT + dermatomal numbness + myotomal weakness, explicitly noting *normal* bowel/bladder (ruling out cauda equina) → red flags, structure ID, pain pathway. Scenario 2: nerve root localization + provisional diagnosis + confirmatory imaging choice. Scenario 3: explains *why not* to operate, first-line drugs with mechanism, lifestyle advice.
- **Stroke** — Scenario 1: lateralizing signs (aphasia type, facial palsy pattern, gaze deviation) → lesion localization reasoning. Scenario 2: CT + coag results that change management (e.g. abnormal INR rules out thrombolysis) → pathogenesis chain. Scenario 3: secondary prevention counseling.
- **HHS (hyperosmolar hyperglycemic state)** — raw electrolyte/glucose/osmolality panel the student must interpret and even calculate; diagnostic-criteria question explicitly asking "why is this HHS and not DKA"; a treatment-transition question (IV → subcutaneous insulin) testing clinical judgement about *timing*, not just drug choice.
- **Graves' disease** — unintentional weight loss + increased appetite as the hook (forces "hypermetabolism" reasoning over simple anorexia-driven weight loss); TFT + TRAb interpretation tied explicitly to pathophysiology; drug MOA + serious-but-rare adverse effect (agranulocytosis) + monitoring plan.
- **Valvular heart failure (CVS)** — childhood sore-throat/migratory-polyarthritis history buried in "past history" (rheumatic fever) that only becomes relevant once the murmur is described; vital signs include an irregular pulse the student must recognize as AF from the exam alone, confirmed later by ECG; echo findings given as structured numeric findings (valve area, EF) for the student to classify severity; final scenario tests medication reconciliation reasoning (why atenolol + warfarin + furosemide).

## Output format

Write the MEQ as clean Markdown matching the "Overall shape" above. If the user is building a set across multiple systems/diseases (like the reference documents), match their existing section-header and table-checklist conventions if you can see them; otherwise just produce the scenario/question structure.

Do **not** include the answer key in this output — that's a separate step (see the companion `meq-answer-key-generator` skill, which takes the questions you just wrote and produces the short bullet-point model answers). If the user wants both at once, generate the questions first, then explicitly switch to using that skill for the answers — keep the two outputs visually separate so the exam (without answers) can be used as a standalone document.