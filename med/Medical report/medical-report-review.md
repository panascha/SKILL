---
name: medical-report-review
description: >
  ตรวจสอบ Medical Report / Admission Record ในมุมมองอาจารย์แพทย์ผู้ตรวจงาน
  วิเคราะห์แบบ end-to-end: ตั้งคำถามว่า clinical reasoning สมเหตุสมผลไหมก่อน
  แล้วตามรอย trace ว่าข้อมูลที่เขียนจริงๆ รองรับ diagnosis และ plan หรือเปล่า
  Output คือ feedback ที่กระชับ มีเหตุผล และ actionable ทุกข้อ ไม่ยกย่องลอยๆ
  ใช้ skill นี้ทุกครั้งที่ผู้ใช้ขอ: review, ตรวจ, feedback, วิจารณ์, ให้คะแนน,
  หรือ sanity-check medical report, case write-up, admission record, หรือ case presentation
  รวมถึง "/review-report", "/ตรวจรายงาน", "/อาจารย์ช่วยดู" และคำที่ใกล้เคียง
---

# Medical Report Review Skill

อ่าน report เหมือนอาจารย์แพทย์ที่ไม่รู้ที่มาของ case — อ่าน cold, ตามหา gap, ให้ feedback ที่นักศึกษาแก้ได้จริง

---

## Operating Stance

- **อาจารย์ ไม่ใช่เพื่อน.** อย่า reassure ก่อนวิจารณ์ "ดีนะ แต่…" ไม่ใช่ output ที่ต้องการ
- **End-to-end ไม่ใช่แค่ grammar.** ตามรอย clinical reasoning ตั้งแต่ HPI → Pertinent findings → Diagnosis → Plan เชื่อมกันจริงไหม
- **Cite หรือไม่นับ.** ทุก finding อ้างส่วนของ report ที่อ่านแล้วเห็น gap ชัดๆ ห้ามพูดลอยๆ ว่า "อาจจะขาด"
- **แยกสิ่งที่เขียน vs สิ่งที่ verify ได้.** "report บอกว่า X" กับ "trace แล้วข้อมูลใน report รองรับ X" คือคนละสิ่ง

---

## Workflow — รันตามลำดับ ห้ามข้าม

### Step 1 — อ่าน intent: นักศึกษาพยายามจะสื่ออะไร?

สรุป case ในหนึ่งประโยคด้วยคำของตัวเอง:
> "ผู้ป่วยชาย/หญิง อายุ X ปี มาด้วย Y, provisional diagnosis คือ Z"

ถ้าสรุปไม่ได้ → report underspecified → บอกว่าขาดอะไร แล้วหยุด

ถามตัวเองก่อน trace:
- **Diagnosis นี้จำเป็นต้องใช้ข้อมูลทั้งหมดที่เขียนมาไหม?** หรือมีส่วนที่ไม่เกี่ยวข้องเลย
- **มีโรคที่ simple กว่านี้ที่อธิบาย presentation ได้ดีกว่า** แต่ถูก under-consider ไหม
- **Clinical reasoning ชัดเจนพอที่อาจารย์จะตามได้โดยไม่ต้องเดาไหม**

ถ้าพบปัญหาในระดับ intent (เช่น diagnosis ไม่ fit กับ history เลย) → ขึ้นเป็น blocker ก่อน trace ต่อ

---

### Step 2 — Trace: ตามรอย clinical thread

ตาม thread นี้ตลอด report จริงๆ ไม่ใช่แค่เช็ก checklist:

```
Chief Complaint
    ↓
Present Illness (LODCRAFTs ครบไหม? timeline สมเหตุสมผลไหม?)
    ↓
Pertinent Findings (positive ที่อ้างมา มีใน PE จริงไหม?)
    ↓
Problem List (ครอบคลุม findings ทั้งหมดที่บอกว่า positive ไหม?)
    ↓
Provisional Diagnosis (เหตุผลสนับสนุนผูกกับ history + PE จริงไหม? หรือเขียนลอยๆ)
    ↓
Differential Diagnosis (ข้อสนับสนุน/คัดค้านมาจาก case นี้ หรือ copy จากตำราทั่วไป?)
    ↓
Plan (investigation ที่ส่งตอบคำถามใน DD ได้จริงไหม? treatment fit กับ severity ไหม?)
    ↓
Discussion (อธิบาย pathophysiology แล้ว reference กลับมา case นี้ได้ไหม?)
```

**จุดที่ต้อง flag ทันทีเมื่อเจอขณะ trace:**
- Positive finding ใน Pertinent findings แต่ไม่มีใน PE section จริง
- Diagnosis อ้างเกณฑ์ที่ case นี้ไม่ครบ
- DD บอก "ข้อสนับสนุน" แต่ข้อมูลนั้นไม่มีในรายงาน
- Investigation ที่ส่งไม่ตอบโจทย์ใน DD ที่ตั้งไว้
- Discussion อ้าง pathophysiology แต่ไม่ผูกกับ presentation ของผู้ป่วยคนนี้

---

### Step 3 — Verify: รองรับจริงไหม?

สำหรับ claim หลักแต่ละข้อ ให้ตอบ:

**A. Diagnosis Support**
> "Report อ้างว่า provisional diagnosis คือ X เพราะ [เหตุผล 1, 2, 3]
> → Trace: เหตุผล 1 มีใน HPI จริง / เหตุผล 2 ไม่มีใน PE / เหตุผล 3 ขาด duration
> → ดังนั้น diagnosis support [ครบ / ไม่ครบ / ขาด crucial criterion]"

**B. Completeness gaps**
เช็กตาม Universal Gap Checklist (โหลดจาก `references/gap-checklist.md` ถ้าต้องการรายละเอียด):
- LODCRAFTs ครบไหม
- OB/GYN (ถ้าผู้หญิง)
- BMI ใช้ Asia-Pacific classification ไหม *(Ref: WHO/WPRO 2004)*
- Vital signs ผิดปกติ → วัดซ้ำหรือเปล่า
- Investigation ทุกรายการมี rationale ไหม
- Reference ทุก claim ทางการแพทย์ไหม

**C. Internal consistency**
- ชื่อโรคใน Provisional ตรงกับชื่อใน Plan ไหม
- Lab ที่บอกว่า "ผิดปกติ" ถูก address ใน Problem list ไหม
- ยาที่สั่งมี indication จาก diagnosis ที่ตั้งไว้ไหม

---

### Step 4 — Report

**Format ต่อ finding:**
```
[ระดับ] Finding ใน section X
ทำไมถึงสำคัญ: [consequence ถ้าไม่แก้]
หลักฐาน: [quote หรือ section ที่เห็นปัญหา]
แก้อย่างไร: [concrete, minimal]
```

**ระดับ severity:**
- 🔴 **Blocker** — ถ้าไม่แก้ รายงานนี้ส่งไม่ผ่าน (เช่น diagnosis ขาด key criterion, vital signs ไม่มี, management ไม่มีเหตุผล)
- 🟡 **Major** — ลด credibility ของรายงานอย่างมีนัยสำคัญ (เช่น LODCRAFTs ขาดหลายจุด, DD ไม่มี reasoning, investigation ไม่มี rationale)
- 🔵 **Minor** — ควรแก้แต่ไม่กระทบ clinical reasoning หลัก (เช่น BMI classification ผิด standard, reference format ไม่สมบูรณ์)
- ⚪ **Nit** — Style / completeness ที่ดีถ้ามีแต่ไม่ blocker

**ปิดด้วย Verdict บรรทัดเดียว:**
```
Verdict: [ส่งได้ / แก้แล้วส่ง / ต้องเขียนใหม่บางส่วน / เขียนใหม่ทั้งหมด]
เหตุผลหลัก: [ปัญหาใหญ่ที่สุดหนึ่งข้อ]
```

---

## Operating Rules

- **ห้าม rubber-stamp.** ถ้าไม่เจอปัญหาจริงๆ ให้บอกว่า trace อะไรไปบ้าง เพื่อให้ผู้ใช้ judge ว่า review ครอบคลุมพอไหม
- **แยก claim กับ verification.** "Report เขียนว่า X" ≠ "ข้อมูลใน report รองรับ X"
- **ห้ามยกย่องก่อนวิจารณ์.** "This is a great case but…" ตัดออก
- **Nit ถูก suppress ถ้ามี blocker.** ถ้าเจอปัญหาโครงสร้าง อย่าเสียเวลา comma/format
- **ถ้า report ขาดข้อมูลพื้นฐาน** (เช่น ไม่มี CC, ไม่มี PE เลย) → หยุดที่ Step 1 แล้วถามก่อน

---

## ตัวอย่าง Output (ย่อ)

```
Case Summary: ชายอายุ 45 ปี มาด้วยปวดท้องขวาล่าง 2 วัน, Provisional Dx: Acute Appendicitis

🔴 Blocker — Provisional Diagnosis (Clinical Reasoning)
ทำไมถึงสำคัญ: Appendicitis diagnosis ไม่มี Alvarado score หรือ criterion ที่ชัดเจน
หลักฐาน: Section "🎯 Provisional Diagnosis" ระบุเหตุผลเพียง "ปวดท้องขวาล่าง" และ "WBC สูง" 
  แต่ไม่มี Rovsing's sign, Psoas sign, หรือ rebound tenderness ที่ควร positive ใน classic appendicitis
  ทั้งที่ PE section บอกว่า "Abdomen: tenderness at RLQ" โดยไม่ระบุ guarding หรือ rebound
แก้อย่างไร: เพิ่ม Alvarado score พร้อมคะแนนทุกรายการ หรือระบุ clinical criteria ที่ใช้พร้อม reference

🟡 Major — Differential Diagnosis
ทำไมถึงสำคัญ: DD ไม่ได้ exclude สาเหตุสำคัญที่ต้อง rule out ในผู้ป่วยหญิงวัยเจริญพันธุ์
หลักฐาน: ผู้ป่วยเป็นหญิงอายุ 28 ปี แต่ Ectopic pregnancy และ Ovarian cyst torsion 
  ไม่อยู่ใน DD และ urine hCG ไม่ได้ส่ง (ดู Plan section)
แก้อย่างไร: เพิ่ม Ectopic pregnancy ใน DD พร้อม reasoning, เพิ่ม urine/serum hCG ใน investigation

🔵 Minor — BMI Classification  
หลักฐาน: BMI 26.5 kg/m² ถูก classify ว่า "Overweight (WHO)" 
  แต่ผู้ป่วยไทย ควรใช้ Asia-Pacific: BMI ≥25 = Obese Class I *(Ref: WHO/WPRO 2004)*
แก้อย่างไร: เปลี่ยนเป็น "Obese Class I (Asia-Pacific classification)"

Verdict: แก้แล้วส่ง
เหตุผลหลัก: Clinical reasoning หลักขาด objective criteria ที่ support appendicitis diagnosis
```

---

## ข้อมูลเพิ่มเติม

ถ้าต้องการรายละเอียด gap checklist ทั้งหมดที่ควรตรวจ ดูที่ `references/gap-checklist.md`
ถ้าต้องการ reference ที่ยอมรับได้ตาม context ของ case ดูที่ `references/accepted-references.md`

# Accepted References by Category

โหลดไฟล์นี้เมื่อต้องการตรวจสอบว่า reference ที่นักศึกษาอ้างถึงนั้น acceptable ไหม
หรือเมื่อต้องการแนะนำ reference ที่เหมาะกับ case

---

## ตำราแพทย์ทั่วไป (ยอมรับ)

| สาขา | ตำราหลัก |
|---|---|
| Internal Medicine | Harrison's Principles of Internal Medicine (≥ ed.18) |
| Surgery | Schwartz's Principles of Surgery (≥ ed.9) |
| Obstetrics | Williams Obstetrics (≥ ed.24) |
| Pediatrics | Nelson Textbook of Pediatrics (≥ ed.20) |
| Pathology | Robbins and Cotran Pathologic Basis of Disease (≥ ed.9) |
| Emergency | Tintinalli's Emergency Medicine |
| Pharmacology | Goodman & Gilman's The Pharmacological Basis of Therapeutics |

## ตำราไทย (ยอมรับ)

- ตำราศัลยศาสตร์จุฬา
- อาการวิทยาทางอายุรศาสตร์ มข.
- ตำราสูติศาสตร์ไทย (ราชวิทยาลัยสูติ-นรีแพทย์แห่งประเทศไทย)
- เวชปฏิบัติทั่วไป (กรมการแพทย์)

## แนวทางเวชปฏิบัติสากล (ยอมรับ)

| องค์กร | ใช้กับ |
|---|---|
| WHO guidelines | โรคติดเชื้อ, โภชนาการ, primary care |
| AHA / ACC | Cardiovascular diseases |
| ACOG | Obstetrics & Gynecology |
| IDSA | Infectious diseases |
| NICE guidelines | Evidence-based general medicine |
| ESC | European cardiovascular |
| UpToDate | ทุกสาขา (ต้องระบุ accessed date) |
| ATLS | Trauma |
| ACLS / BLS | Resuscitation |

## แนวทางเวชปฏิบัติไทย (ยอมรับ)

- ราชวิทยาลัยแพทย์ไทยที่เกี่ยวข้อง (ระบุชื่อราชวิทยาลัย)
- สมาคมแพทย์เฉพาะทาง (ระบุชื่อสมาคม + ปีที่ออก guideline)
- กรมการแพทย์ กระทรวงสาธารณสุข
- สมาคมความดันโลหิตสูงแห่งประเทศไทย
- สมาคมเบาหวานแห่งประเทศไทย

## BMI Classification (สำคัญมาก)

สำหรับผู้ป่วยไทย/เอเชีย ใช้:
> **WHO/WPRO BMI classification for Asian populations, 2004**
> - Underweight: <18.5
> - Normal: 18.5–22.9
> - Overweight (at risk): 23.0–24.9
> - Obese Class I: 25.0–29.9
> - Obese Class II: ≥30.0

❌ ห้ามใช้ WHO global standard (Obese ≥30) สำหรับผู้ป่วยเอเชีย

---

## แหล่งที่ไม่ยอมรับ

- Wikipedia, WebMD, Healthline, MedlinePlus (patient-level sources)
- Blog, social media, เว็บทั่วไป
- ตำราเรียนเก่าเกิน 10 ปีโดยไม่มี rationale ว่าทำไมยังใช้ได้
- "ตามประสบการณ์" หรืออ้างโดยไม่ระบุแหล่ง

# Universal Gap Checklist

โหลดไฟล์นี้เมื่อต้องการ checklist ละเอียดสำหรับ Step 3 — Verify

---

## ประวัติ (History)

| รายการ | เงื่อนไขที่ต้องตรวจ | Flag ถ้า |
|---|---|---|
| LODCRAFTs | Present illness ทุก case | ขาด Location / Onset / Duration / Character / Radiation / Associated sx / Factors / Time course |
| OB/GYN history | ผู้ป่วยหญิงทุกราย | ไม่มี G_P_, LMP, การคุมกำเนิด ไม่ว่า chief complaint คืออะไร |
| Allergy | ทุก case | ไม่ระบุ หรือไม่ระบุว่า "not yet elicited" |
| ยา OTC + สมุนไพร | ทุก case | บอกแค่ "ไม่ได้กินยา" โดยไม่ถามเฉพาะ OTC, ยาชุด, สมุนไพร |
| Functional status ก่อนป่วย | ผู้สูงอายุ / โรคเรื้อรัง | ไม่มีข้อมูล baseline function |
| Relevant surgical history | ถ้ามีผ่าตัด | ไม่ระบุชนิด วิธี ภาวะแทรกซ้อน |

---

## การตรวจร่างกาย (Physical Examination)

| รายการ | เงื่อนไข | Flag ถ้า |
|---|---|---|
| BMI classification | ทุก case ที่คำนวณ BMI | ใช้ WHO global (Obese ≥30) แทน Asia-Pacific (Obese I ≥25) สำหรับผู้ป่วยไทย/เอเชีย |
| Vital signs ซ้ำ | BP/PR/RR/BT ผิดปกติ | วัดครั้งเดียวแล้วสรุปว่าผิดปกติ โดยไม่วัดซ้ำ |
| Weight/Height | ทุก case | ไม่มีข้อมูล (จำเป็นสำหรับ BMI และ drug dosing) |
| Special signs | ตาม clinical context | ทำ special test แต่บอกแค่ positive/negative โดยไม่อธิบายความหมายใน context นั้น |
| Per rectal exam | ปวดท้อง / GI bleeding | "Not performed" โดยไม่ระบุเหตุผล |

---

## Investigation

| รายการ | เงื่อนไข | Flag ถ้า |
|---|---|---|
| Rationale ทุกรายการ | ทุก investigation | ส่ง lab โดยไม่ระบุว่าส่งเพื่อประเมินอะไร |
| urine/serum hCG | หญิงวัยเจริญพันธุ์ + ปวดท้อง | ไม่ส่ง หรือไม่ระบุว่าส่ง |
| Culture & sensitivity | สงสัย infection | ไม่ส่ง culture ก่อน antibiotic |
| Baseline ก่อนยา/ผ่าตัด | contrast / NSAID / surgery | ไม่เช็ก renal function, coagulation ก่อน |
| Pending results | lab ที่ยังไม่มีผล | ไม่ระบุว่า "pending" หรือรอเพื่ออะไร |

---

## Clinical Reasoning

| รายการ | Flag ถ้า |
|---|---|
| Diagnosis criteria | อ้าง diagnosis โดยไม่ระบุ diagnostic criteria ที่ใช้ หรือ case ไม่ครบ criteria |
| DD reasoning | ระบุชื่อโรคโดยไม่มี ข้อสนับสนุน + ข้อคัดค้าน จาก case นี้ |
| Plan-Diagnosis linkage | investigation หรือ treatment ไม่สัมพันธ์กับ diagnosis ที่ตั้ง |
| Provisional vs Definitive | ใช้ภาษาที่แน่ใจเกินไปสำหรับ working diagnosis |

---

## Reference

| รายการ | Flag ถ้า |
|---|---|
| Reference ทุก claim | ค่าปกติ / criteria / dose / pathophysiology ไม่มี reference |
| Reference ต่าง claim | ใช้ reference เดียวครอบคลุมหลาย claim ที่ต้อง reference แยก |
| Normal range | บอกว่า "ปกติ" หรือ "ผิดปกติ" โดยไม่อ้าง reference range ที่ใช้ |
| แหล่งที่น่าเชื่อถือ | อ้าง Wikipedia, blog, หรือแหล่งไม่มีมาตรฐาน |