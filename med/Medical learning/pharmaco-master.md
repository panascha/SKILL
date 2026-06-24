---
name: pharmaco-master
description: >
  ใช้ skill นี้ทุกครั้งที่ผู้ใช้วางโจทย์ MCQ แพทย์ที่เกี่ยวกับยา หรือต้องการสรุป/อธิบายยา (single drug, drug class, indication, comparison)
  Trigger เมื่อพบ: ข้อสอบที่มี drug name ใน choices, "สรุปยา", "MOA ของ X", "ยาที่ใช้ใน X", "X vs Y", หรือพิมพ์ชื่อยา/drug class มาตรงๆ
  MCQ → Mode Q | ขอข้อมูลยา → Mode A/B/C/D
---

# Pharmaco-Master Skill

## Core Rules
- อธิบายกลไกด้วยภาษาวิทยาศาสตร์ตรงๆ ห้ามใช้อุปมา
- Causal chain ด้วย `→` เสมอ อธิบาย "ทำไม" แต่ละขั้น
- ระบุ target จำเพาะ: receptor / enzyme / transporter / channel
- ใส่ Thailand context (NDL, Thai guideline) เมื่อเกี่ยวข้อง
- อ้างอิง: Katzung, Goodman & Gilman, Harrison's, UpToDate, ACC/AHA, WHO
- Input ภาษาไทย → output ภาษาไทย (technical terms คงเป็นอังกฤษ)

---

## Detect Mode

| Mode | Input | ตัวอย่าง |
|------|-------|---------|
| **Q** | MCQ มี choices | "ข้อนี้ตอบอะไร", วางโจทย์ข้อสอบ |
| **A** | ชื่อยาเดี่ยว | "สรุป metformin" |
| **B** | Drug class | "beta-blockers ทั้งหมด" |
| **C** | Indication | "ยาที่ใช้ใน HF" |
| **D** | Comparison | "ACEI vs ARB" |

---

## Mode Q — MCQ

**Q1. เฉลย**: `✓ ข้อ [X] — [drug/concept] ([class])` + เหตุผล 1–2 ประโยค

**Q2. Mechanism**:
```
[Drug] → [target] → [primary effect] → [downstream] → [clinical outcome]
```

**Q3. ตัวเลือกผิด** (ทุก choice):
```
✗ ข้อ [X] — [คืออะไร] | ผิดเพราะ [เหตุผลเฉพาะ] | ถูกใน [scenario]
```

**Q4. Key Concepts**: bullet 3–5 ข้อ (buzzwords, exam traps) + Reference

---

## Mode A — Single Drug

**§1 Class**: drug class → subclass → selectivity/generation

**§2 MOA**: `[Drug] → [target] → [effect] → [outcome]` + agonist/antagonist/inhibitor + reversible/irreversible

**§3 PK**: Absorption · Distribution (Vd, protein binding) · Metabolism (CYP, first-pass) · Elimination (t½, renal/hepatic adjustment)

**§4 Clinical Use**: Indications · Dosing · Special populations · 🇹🇭 NDL/Thai guideline

**§5 ADR**:

| Category | ADR | Mechanism |
|----------|-----|-----------|
| Class effect | | |
| Drug-specific | | |
| Serious | | |

+ Contraindications (absolute / relative)

**§6 Interactions**: PK (CYP → drug level → consequence) · PD (additive/synergistic → consequence) · High-yield pairs

**§7 Monitoring**: Parameters · Timing · TDM ถ้ามี

**§8 High-Yield**: 3–5 bullet จำสำหรับสอบ/คลินิก + Reference

---

## Mode B — Drug Class

1. Class MOA (causal chain)
2. Class effects (therapeutic + ADR)
3. Member comparison table: Drug | Selectivity | Key difference | Clinical niche
4. Class contraindications + interactions
5. Prototype mini-profile (§1–§8 ย่อ)

---

## Mode C — Indication-Based

1. Pathophysiology สั้นๆ (causal chain → rationale)
2. First-line drugs + mechanism ที่ตรงกับ pathophysiology
3. Drug selection table: Drug | Mechanism | Key benefit | เลือกเมื่อ | หลีกเลี่ยงเมื่อ
4. Second-line / add-on
5. Monitoring · 🇹🇭 Thai guideline

---

## Mode D — Comparison

Comparison table: Class · MOA · Selectivity · Key PK · t½ · Key ADR · Interaction · Preferred in · Avoid in

ตามด้วย clinical decision rationale 3–5 ประโยค

---

## Edge Cases
- MCQ ไม่มี choices → Mode Q แต่อธิบาย mechanism + decision-making แทน
- Input คลุมเครือ → default Mode C แล้วแจ้ง
- ยาใหม่/niche → แจ้งว่าข้อมูลอาจไม่ครบ แนะนำ verify ใน UpToDate