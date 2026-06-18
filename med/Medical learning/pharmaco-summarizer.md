---
name: pharmaco-summarizer
description: |
  สรุป pharmacology จากไฟล์ markdown สำหรับนักศึกษาแพทย์ โดยเรียบเรียงเนื้อหาใหม่ตามวิธีที่แพทย์จริงๆ คิดในคลินิก ไม่ใช่เรียงตามตำรา ครอบคลุม: ทำความเข้าใจโรคและกลไกก่อน → เชื่อมกลุ่มยากับพยาธิสรีรวิทยา → ข้อมูลยาที่มีใช้จริงในประเทศไทย → สรุปตาม clinical guidelines

  ใช้ skill นี้เมื่อ:
  - ผู้ใช้แนบ/วางเนื้อหา markdown ของ pharmacology และขอให้สรุป/เรียบเรียง
  - ขอสรุปยา หรือ drug class สำหรับโรคใดโรคหนึ่ง ในบริบทนักศึกษาแพทย์หรือแพทย์
  - พูดถึงการเรียน pharmaco, drug treatment, clinical pharmacology, ยากลุ่มไหน ใช้ตอนไหน
  - ขอ clinical approach ของการรักษาโรค เชื่อมกับยา
  - มีคำว่า "สรุปยา", "เรียบเรียงยา", "ยาที่ใช้ในไทย", "drug of choice", "first-line", "guideline"
---

# Pharmaco Summarizer — Clinical-First Approach

## เป้าหมาย

สรุปเนื้อหา pharmacology จาก markdown ให้ออกมาในรูปแบบที่ **แพทย์คิดจริงๆ ในคลินิก** ไม่ใช่เรียงตามตำรา เป็น workflow ที่โยง disease → pathophysiology → drug target → drug class → ยาที่มีจริงในไทย → guideline

---

## Workflow หลัก (ทำตามลำดับนี้)

### Phase 1 — Parse input

อ่าน markdown ที่ผู้ใช้ให้มา แยกเป็น:
- ชื่อโรค / กลุ่มโรค
- หัวข้อยาหรือ drug class ที่มีอยู่
- บริบทว่าเป็นระดับไหน (preclinical, clerkship, นักศึกษาแพทย์ปีเท่าไร ถ้าระบุ)

ถ้า markdown ไม่ชัด ให้ถามผู้ใช้ 1 ข้อก่อนดำเนินการต่อ

---

### Phase 2 — Disease + Drug Classes (รวมโรคและกลุ่มยาไว้ด้วยกัน)

**เริ่มจากทำความเข้าใจโรค แล้วเชื่อมต่อไปยังกลุ่มยาทันที** — ไม่แยกเป็นสองส่วน

**ส่วนแรก: เข้าใจโรคก่อน**

เขียนให้ครอบคลุมในลักษณะ prose ต่อเนื่อง:
1. **นิยามและภาพรวมคลินิก** — โรคนี้คืออะไร แพทย์เจอในคลินิกอย่างไร
2. **พยาธิกำเนิด (Pathogenesis)** — กลไกการเกิดโรคในระดับที่นำไปสู่ drug target ได้
3. **Pathophysiology → Clinical Features** — จาก mechanism อธิบาย symptom/sign สำคัญ
4. **Drug Targets ที่เป็นไปได้** — สรุปจุดที่ยาเข้าไปแทรกแซงได้ นำเข้าสู่ส่วนถัดไปทันที

ใช้ภาษาที่กระชับ เน้น "เพราะ X จึงรักษาด้วย Y"

**ส่วนที่สอง: กลุ่มยา (ต่อเนื่องทันทีหลังอธิบายโรค)**

**ไม่เรียงตามตำรา** — เรียงตามลำดับที่แพทย์คลินิกเลือกใช้จริง:
1. First-line / cornerstone therapy ก่อน
2. Add-on / combination therapy
3. Alternative ถ้า contraindication หรือ intolerance
4. Special situations / niche indications

สำหรับแต่ละ drug class เขียน prose เชื่อมกลไกกับโรคที่อธิบายไปแล้ว:

```
## [Drug Class / กลุ่มยา]

[อธิบายว่า drug class นี้เข้าแทรกแซงที่จุดไหนของ pathophysiology ที่อธิบายไว้ข้างบน
ผลทางคลินิกที่เกิดขึ้นคืออะไร และอยู่ตำแหน่งไหนใน treatment ladder]
```

---

### Phase 3 — Drugs Available in Thailand (prose ไม่ใช้ตาราง)

**สำคัญมาก: ระบุเฉพาะยาที่มีใช้จริงในประเทศไทย**

สำหรับแต่ละยาใน drug class เขียนเป็น prose ต่อเนื่อง รูปแบบนี้:

```
**[Generic name]** (ชื่อการค้า: [ชื่อ] — หรือระบุว่า "ตรวจสอบกับ NLEM/TMHF" ถ้าไม่แน่ใจ)

ขนาดยาที่ใช้จริงในผู้ใหญ่คือ [dose] โดย [route/frequency] อธิบายว่าทำไมขนาดนี้ถึงเหมาะสมถ้ามีนัยสำคัญ

ผลข้างเคียงที่ต้องรู้และต้องแจ้งผู้ป่วยได้แก่ [อธิบาย SE หลักพร้อมกลไกสั้นๆ ว่าเกิดขึ้นได้อย่างไร]

ห้ามใช้ในกรณี [contraindication หลัก พร้อมเหตุผลสั้นๆ]

การติดตาม: [สิ่งที่ต้อง monitor และความถี่ถ้ามีนัย]

หมายเหตุสำคัญ: [การปรับขนาดใน CKD/hepatic impairment, drug interaction สำคัญ, หรือ clinical pearl ที่แพทย์ควรรู้]
```

ถ้ายาบางตัวไม่มีในไทยหรือไม่แน่ใจ → บอกตรงๆ ว่า "อาจไม่มีในไทย / ตรวจสอบเพิ่มเติม"

---

### Phase 4 — Clinical Decision Summary

**สรุปการเลือกยาตาม Guidelines** (ใช้ข้อมูลจาก input หรือ knowledge ที่มี)

รูปแบบ:
```
### แนวทางการรักษา (Treatment Algorithm)

[Condition/Severity] → [First-line] → [ถ้าไม่ตอบสนอง/Intolerance] → [Alternative]

**ตัวอย่างการเลือกยาตามสถานการณ์:**
- ผู้ป่วยทั่วไปไม่มี comorbidity → ...
- มี CKD → ...
- มี ประวัติ ... → ...
- ผู้สูงอายุ → ...
- หญิงตั้งครรภ์ → ...
```

ระบุ guideline ที่อ้างอิง เช่น Thai guideline, ACC/AHA, WHO, ESC (ถ้าอ้างอิงได้จาก input หรือ knowledge ที่มี)

---

### Phase 5 — Rapid Review Box

ปิดท้ายด้วย "กล่องทบทวนเร็ว" สำหรับอ่านก่อนสอบหรือก่อนขึ้น ward:

```
┌─────────────────────────────────────┐
│  RAPID REVIEW — [ชื่อโรค]           │
├─────────────────────────────────────┤
│ 🔑 Key Mechanism:                   │
│ 💊 Drug of Choice:                  │
│ ⚠️  Must-Know SE:                    │
│ 🚫 Avoid in:                        │
│ 📋 Monitor:                         │
└─────────────────────────────────────┘
```

---

## กฎสำคัญ

1. **ภาษา**: ใช้ภาษาไทยเป็นหลัก ยกเว้น terminology ทางการแพทย์/ยาที่ควรเป็นภาษาอังกฤษ (MOA, drug names, กลุ่มยา)
2. **ความถูกต้อง**: ถ้าไม่แน่ใจข้อมูลยา โดยเฉพาะ dose และ availability ในไทย — บอกตรงๆ และแนะนำให้ตรวจสอบจาก NLEM, TMHF, หรือ package insert
3. **ไม่ประดิษฐ์ข้อมูล**: ห้ามแต่งยา dose หรือ guideline ขึ้นมาเอง ถ้า markdown input ไม่มีข้อมูลพอ ให้บอกว่าต้องการข้อมูลเพิ่มเติม
4. **เน้น clinical pearls**: ทุกส่วนควรมี take-home message สั้นๆ ที่แพทย์จำได้และใช้ได้จริง
5. **ปรับตามระดับ**: ถ้าผู้ใช้บอกว่าเป็นนักศึกษาปีต้น ลดความละเอียดของ MOA ลง เพิ่มภาพรวม; ถ้าเป็น clerkship เพิ่มส่วน clinical scenario
6. **ทุกสิ่งที่เกิดขึ้นต้องมีเหตุผลหรือกลไกรองรับเสมอ**: ห้ามระบุผลลัพธ์หรืออาการลอยๆ โดยไม่อธิบายว่าเกิดขึ้นได้อย่างไร ใช้ลูกศรหรือสัญลักษณ์แสดงสายเหตุและผล เช่น `ACE inhibitor → ↓ angiotensin II → ↓ aldosterone → ↓ Na⁺ retention → ↓ preload` แทนการเขียนว่า "ลด preload"

---

## ตัวอย่าง Output Structure

```
# สรุป Pharmacology: [ชื่อโรค]

## 1. โรคและกลุ่มยา
### นิยามและภาพรวมคลินิก
### กลไกการเกิดโรค (Pathogenesis)
### จาก Mechanism ถึง Symptom
### Drug Targets
### [Drug Class 1 — First-line] + กลไกเชื่อมโรค
### [Drug Class 2 — Add-on] + กลไกเชื่อมโรค
### [Drug Class 3 — Alternative] + กลไกเชื่อมโรค

## 2. ยาที่มีในประเทศไทย
[prose รายยาต่อ drug class ไม่ใช้ตาราง]

## 3. การเลือกใช้ยาตาม Guideline
[Treatment algorithm]

## 4. Rapid Review
[กล่องทบทวน]
```