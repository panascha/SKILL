---
name: med-teaching-summarizer
description: >
  สรุปเนื้อหาทางการแพทย์จากไฟล์ Markdown หรือ PDF เพื่อใช้สอนนักเรียนแพทย์
  ให้เข้าใจในรูปแบบที่เหมาะสมกับระดับการศึกษา ครอบคลุมการอ่านไฟล์ การจัดโครงสร้าง
  การอธิบายแนวคิด การยกตัวอย่างทางคลินิก และการสร้าง learning objectives
  ใช้ skill นี้เสมอเมื่อผู้ใช้ต้องการ: สรุปเนื้อหาแพทย์จากเอกสาร, อธิบายโรค/พยาธิวิทยา/
  เภสัชวิทยา/สรีรวิทยาให้นักเรียนแพทย์, สร้างสรุปบทเรียนแพทยศาสตร์, แปลง lecture notes
  หรือตำราแพทย์เป็นสื่อการสอน, หรือสร้าง study guide สำหรับนักศึกษาแพทย์
---

# Med Teaching Summarizer

Skill สำหรับสรุปและนำเสนอเนื้อหาทางการแพทย์ เพื่อใช้สอนนักเรียนแพทย์ให้เข้าใจได้ง่าย

---

## ขั้นตอนการทำงาน

### ขั้นที่ 1 — อ่านไฟล์ต้นฉบับ

ดูว่ามีไฟล์แนบมาหรือไม่ก่อนเริ่มต้น:

- **ไม่มีไฟล์**: ถามว่าต้องการสอนหัวข้ออะไร แล้ว list หัวข้อย่อยทั้งหมดที่เกี่ยวข้องให้ก่อน (ดู "โหมด List หัวข้อ" ด้านล่าง)
- **ไฟล์ .md**: อ่านโดยตรงด้วย bash `cat`
- **ไฟล์ .pdf**: อ่าน SKILL.md ของ `pdf-reading` skill ที่ `/mnt/skills/public/pdf-reading/SKILL.md` ก่อนเสมอ แล้วทำตามวิธีที่ระบุไว้

หากเป็นการใช้งานครั้งแรกในหัวข้อ (ผู้ใช้ไม่ได้ระบุ subtopic ที่ต้องการ) → ไปที่ "โหมด List หัวข้อ" ก่อน

---

### ขั้นที่ 2 — ระบุ context การสอน

ก่อนสรุป ต้องรู้ว่า:
1. **ระดับผู้เรียน** — นักศึกษาแพทย์ปี 1–2 (preclinical), ปี 3–4 (clinical), หรือแพทย์ใช้ทุน/แพทย์ประจำบ้าน
2. **จุดประสงค์** — สอนในห้องเรียน, ทำ study guide, สอบ, หรือ bedside teaching
3. **ความลึก** — overview/big picture, standard depth, หรือ deep dive

ถ้าผู้ใช้ไม่ได้ระบุ ให้ **สันนิษฐานว่าเป็น clinical year (ปี 3–4) ที่ต้องการ standard depth** และแจ้งสมมติฐานนี้ไว้ตอนต้นผลลัพธ์

---

### ขั้นที่ 3 — สรุปและจัดโครงสร้าง

ใช้ template ที่เหมาะสมตาม subject area (ดูด้านล่าง) หรือ `references/templates.md`

#### หลักการสรุปสำหรับนักเรียนแพทย์

**✅ ควรทำ:**
- เริ่มด้วย **"ทำไมต้องรู้เรื่องนี้"** — relevance ทางคลินิก
- ใช้ **memory aids** (mnemonics, rules of thumb) ที่ใช้งานได้จริง
- ยก **ตัวอย่าง case** ประกอบเสมอ (แม้เป็น case สั้นๆ)
- เน้น **red flags** และ **ข้อผิดพลาดที่พบบ่อย** ในการปฏิบัติ
- เชื่อมโยงกับ **basic science** (pathophysiology → clinical manifestation)
- ใช้ภาษาที่ **กระชับ อ่านง่าย** เหมาะกับการทบทวนเร็ว
- แยก **"must know"** ออกจาก **"nice to know"** อย่างชัดเจน

**❌ หลีกเลี่ยง:**
- คัดลอกเนื้อหาจากตำราทั้งหมดโดยไม่กลั่นกรอง
- ใช้ศัพท์เทคนิคโดยไม่อธิบาย (หรืออธิบายสั้นๆ เอาไว้)
- สรุปยาวเกินกว่าที่คนจะอ่านจบใน 15–20 นาที
- ลืม clinical application

---

## โหมด List หัวข้อ (First-time / No specific subtopic)

เมื่อผู้ใช้ระบุหัวข้อกว้างๆ หรือไม่ได้บอกว่าต้องการสรุปส่วนไหน ให้ทำดังนี้:

1. **แสดง Learning Objectives Map** — แตกหัวข้อใหญ่เป็น subtopics ทั้งหมดที่นักเรียนแพทย์ควรรู้
2. **จัดกลุ่ม** เป็นหมวดหมู่ตามตรรกะการเรียนรู้ (เช่น Basic science → Diagnosis → Management)
3. **ระบุ priority** ของแต่ละ subtopic (⭐ must know / 📘 good to know / 📖 reference)
4. **ถามว่าต้องการเริ่มสรุปหัวข้อใด** หรือจะให้สรุปทั้งหมด

ตัวอย่าง format:

```
## หัวข้อ: Pneumonia

### 🗺️ สิ่งที่นักเรียนแพทย์ควรรู้ทั้งหมด

**กลุ่มที่ 1: พื้นฐาน (Basic Science)**
⭐ Pathophysiology ของการติดเชื้อในปอด
⭐ เชื้อก่อโรคที่พบบ่อย (Community vs Hospital-acquired)
📘 Host defense mechanisms

**กลุ่มที่ 2: การวินิจฉัย (Diagnosis)**
⭐ Symptoms & Signs ที่สำคัญ
⭐ Chest X-ray interpretation
⭐ Laboratory workup
📘 CURB-65 / PSI scoring
📖 Advanced imaging (CT chest)

**กลุ่มที่ 3: การรักษา (Management)**
⭐ Empirical antibiotic regimens (CAP / HAP / VAP)
⭐ Criteria for admission vs outpatient
📘 Supportive care
📘 Complications และวิธีจัดการ

**กลุ่มที่ 4: พิเศษ (Special Situations)**
📘 Immunocompromised host
📖 Atypical pneumonia
📖 Aspiration pneumonia

ต้องการให้เริ่มสรุปหัวข้อใดก่อน หรือจะสรุปทั้งหมดในครั้งเดียว?
```

---

## Templates ตาม Subject Area

อ่าน `references/templates.md` สำหรับ template ละเอียดของแต่ละ subject area

| Subject Area | Template |
|---|---|
| โรคและสภาวะทางคลินิก (Disease / Condition) | Disease Template |
| ยาและเภสัชวิทยา (Pharmacology) | Drug Template |
| สรีรวิทยา / ชีวเคมี (Physiology / Biochemistry) | Mechanism Template |
| การตรวจวินิจฉัย (Diagnostics / Procedures) | Diagnostic Template |
| กายวิภาคศาสตร์ (Anatomy) | Anatomy Template |

---

## รูปแบบ output

### โครงสร้างหลักของการสรุป

```markdown
# [ชื่อหัวข้อ]
> 📋 สำหรับ: [ระดับผู้เรียน] | 🎯 จุดประสงค์: [สอน/ทบทวน/สอบ] | ⏱️ อ่าน: ~[X] นาที

## 🎯 Learning Objectives
(3–5 ข้อที่วัดได้จริง)

## 🔑 Key Concepts (Big Picture)
(อธิบายแบบ "ทำไมถึงเป็นอย่างนี้" ก่อนลงรายละเอียด)

## 📚 เนื้อหาหลัก
(ตาม template ของ subject area)

## ⚠️ Red Flags & Common Mistakes
(สิ่งที่นักเรียนมักพลาดหรือเข้าใจผิด)

## 🏥 Clinical Pearl
(case สั้น 3–5 บรรทัด + คำถาม + เฉลย)

## 🧠 Memory Aids
(mnemonics หรือ visual patterns ที่ช่วยจำ)

## ❓ Self-Check Questions
(3–5 คำถาม MCQ-style หรือ short answer)
```

---

## การจัดการ output ที่ยาวมาก

ถ้าเนื้อหาต้นฉบับยาวมาก (>5 หน้า หรือ >3000 คำ):
- **แบ่งเป็นส่วน** และถามว่าต้องการส่วนใดก่อน
- หรือสร้าง **2 ระดับ**: Quick Reference (1 หน้า) + Full Summary (ฉบับเต็ม)
- แจ้งผู้ใช้ว่ากำลังสรุปในระดับไหน

---

## หมายเหตุสำคัญ

- ห้ามแต่งข้อมูลทางการแพทย์ที่ไม่มีในเอกสารต้นฉบับ — ระบุว่า "ไม่มีในเอกสาร" แทน
- ถ้าข้อมูลในไฟล์ดูเก่าหรืออาจไม่ up-to-date ให้แจ้งเตือนผู้ใช้
- ยาและขนาดยา ต้องระบุแหล่งที่มาหรือเตือนให้ตรวจสอบ guidelines ล่าสุดเสมอ
- ใช้ภาษาไทยเป็นหลัก เว้นแต่ผู้ใช้ขอเป็นภาษาอื่น หรือศัพท์เทคนิคที่ควรใช้ภาษาอังกฤษ

# Templates สำหรับ Subject Areas ต่างๆ

---

## 1. Disease Template — โรค / สภาวะทางคลินิก

ใช้กับ: โรคต่างๆ เช่น Diabetes, Pneumonia, Heart Failure, Stroke ฯลฯ

```markdown
## Pathophysiology (พยาธิสรีรวิทยา)
- กลไกหลักที่ทำให้เกิดโรค (อธิบายแบบ flow)
- ทำไมจึงเกิด symptoms ที่เห็น

## Etiology & Risk Factors
- สาเหตุหลัก / ปัจจัยเสี่ยง
- แบ่งเป็น modifiable vs non-modifiable ถ้าเหมาะสม

## Clinical Features
| Symptom/Sign | กลไก | Frequency |
|---|---|---|
| ... | ... | Common/Uncommon |

## Diagnosis
- **Criteria หรือ Approach** (ถ้ามี scoring system ให้ใส่)
- ตรวจอะไรก่อน → ตรวจอะไรเพิ่ม
- Lab / Imaging ที่ essential

## Management
### Acute/Initial
- ลำดับการรักษาในห้องฉุกเฉินหรือ admit แรก

### Long-term / Definitive
- ยา / หัตถการ / การติดตาม

### เป้าหมายการรักษา (Treatment Goals)
- ตัวเลข / endpoints ที่ต้องการ

## Complications
- ภาวะแทรกซ้อนที่สำคัญ (เรียงตาม urgency)

## Prognosis
- ปัจจัยที่กำหนด prognosis
- ตัวเลขสั้นๆ (ถ้ามีในเอกสาร)
```

---

## 2. Drug Template — ยาและเภสัชวิทยา

ใช้กับ: ยาตัวใดตัวหนึ่ง หรือกลุ่มยา เช่น Beta-blockers, ACE inhibitors ฯลฯ

```markdown
## กลไกการออกฤทธิ์ (Mechanism of Action)
- ออกฤทธิ์ที่จุดไหน → ผลที่เกิด
- Receptor / Enzyme / Channel ที่เกี่ยวข้อง

## Pharmacokinetics (ADME)
| พารามิเตอร์ | ข้อมูล |
|---|---|
| Absorption | |
| Distribution (Vd) | |
| Metabolism | |
| Excretion / Half-life | |

## Indications
- ⭐ Approved indications หลัก
- 📘 Off-label uses ที่พบบ่อย

## Dosing (ตามแนวทาง — ให้ตรวจสอบ guideline ล่าสุดเสมอ)
- ขนาดมาตรฐาน / การปรับใน renal/hepatic impairment

## Adverse Effects
| ผลข้างเคียง | กลไก | วิธีจัดการ |
|---|---|---|
| ... | ... | ... |

## Contraindications & Precautions
- Absolute CI
- Relative CI / ใช้ด้วยความระวัง

## Drug Interactions ที่สำคัญ
- คู่ยาที่ห้ามใช้ร่วม / ต้องระวัง

## Clinical Pearls
- เคล็ดลับการใช้ยาจริงในคลินิก
```

---

## 3. Mechanism Template — สรีรวิทยา / ชีวเคมี / Physiology

ใช้กับ: กระบวนการทางสรีรวิทยา เช่น Cardiac cycle, Renin-angiotensin system, Coagulation cascade ฯลฯ

```markdown
## Big Picture (ทำไมร่างกายต้องมีกระบวนการนี้)
- จุดประสงค์ของกลไก
- เชื่อมกับ homeostasis อย่างไร

## Components (ส่วนประกอบสำคัญ)
- อวัยวะ / เซลล์ / โมเลกูลที่เกี่ยวข้อง

## Flow / Sequence (ลำดับเหตุการณ์)
ใช้ Arrow diagram หรือ numbered steps:
1. → 2. → 3. → ผลลัพธ์

## Regulation (การควบคุม)
- อะไรกระตุ้น (stimulate) กระบวนการนี้
- อะไรยับยั้ง (inhibit)
- Feedback loops

## Clinical Relevance
- โรคที่เกิดเมื่อกลไกนี้ผิดปกติ
- ยาที่ออกฤทธิ์โดยใช้กลไกนี้

## Comparison Table (ถ้ามีหลายกลไกที่คล้ายกัน)
| Feature | กลไก A | กลไก B |
|---|---|---|
```

---

## 4. Diagnostic Template — การตรวจ / หัตถการ

ใช้กับ: การตรวจ Lab, Imaging, Procedures เช่น ECG interpretation, Lumbar puncture, Spirometry ฯลฯ

```markdown
## วัตถุประสงค์ของการตรวจ
- ตรวจเพื่ออะไร — บอก diagnosis / monitor / screen

## หลักการ (Principle)
- ทำงานอย่างไร (อธิบายสั้น)

## วิธีทำ / การอ่านผล
- ขั้นตอนสำคัญ
- Pattern ที่ต้องรู้จัก

## การแปลผล (Interpretation)
| ผลการตรวจ | ความหมาย | ข้อควรระวัง |
|---|---|---|

## Sensitivity / Specificity (ถ้าเหมาะสม)
- ตัวเลขสั้นๆ + ความหมายในทางปฏิบัติ

## Indications & Contraindications
## Complications (ถ้าเป็น invasive procedure)
```

---

## 5. Anatomy Template — กายวิภาคศาสตร์

ใช้กับ: โครงสร้างทางกายวิภาค เชื่อมกับ clinical application

```markdown
## โครงสร้างและตำแหน่ง
- บอก landmarks สำคัญ
- ความสัมพันธ์กับโครงสร้างข้างเคียง

## Variations ที่พบบ่อย (Anatomical variants)

## Blood Supply / Nerve Supply / Lymphatics

## Clinical Significance
- โรค/บาดเจ็บที่เกิดกับโครงสร้างนี้
- Procedures ที่ต้องรู้ anatomy นี้

## Surgical / Procedural Landmarks
- จุดสังเกตสำหรับการทำหัตถการ
```

---

## หมายเหตุสำหรับ Claude

- เลือก template ที่เหมาะสมที่สุดกับเนื้อหา ไม่จำเป็นต้องใช้ทุก section ถ้าข้อมูลไม่มีในต้นฉบับ
- สามารถผสม template ได้ถ้าเนื้อหาครอบคลุมหลาย category
- ถ้าหัวข้อเป็น clinical vignette-style ให้เพิ่ม "Approach to the Patient" section