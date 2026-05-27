---
name: medical-report
description: >
  สร้าง template และช่วยเขียน Medical Report (Admission Record) สำหรับนักศึกษาแพทย์ ตาม heading มาตรฐาน
  โรงพยาบาล/คลินิก ในรูปแบบ Markdown ผสมไทย-อังกฤษ พร้อม emoji เตือนทุก heading ให้ตรวจสอบก่อนส่ง
  และทุกข้อมูลทางการแพทย์ต้องมี reference ที่น่าเชื่อถือกำกับไว้เสมอ
  ใช้ skill นี้ทุกครั้งที่ผู้ใช้พูดถึง: medical report, admission record, case write-up, รายงานผู้ป่วย,
  เขียน case, เขียนรายงาน OPD/IPD, หรือขอ template รายงานทางการแพทย์
---

# Medical Report Skill

## วัตถุประสงค์
ช่วยนักศึกษาแพทย์เขียน **Admission Record / Medical Report** ให้ถูกต้องตาม heading มาตรฐาน
โดยยึดหลัก: **คิดก่อนเขียน — ถามถ้าไม่ชัด — อ้างอิงทุกข้อมูลทางการแพทย์**

---

## Heading มาตรฐาน (จากไฟล์ตัวอย่าง คณะแพทยศาสตร์ โรงพยาบาลมหาสารคาม)

### ส่วนที่ 1 — Admission Record (ซักประวัติ)
1. Patient identification and status
2. Chief complaint
3. Present illness
4. Systemic review
5. Social and personal history
6. Past history (Medical, surgical, general health, OB/GYN ถ้าเป็นผู้หญิง)
7. Family history
8. Current medication

### ส่วนที่ 2 — Physical Examination
1. General inspection
2. BP, PR, RR, BT, BW, Height, BMI
3. Physical findings (HEENT, CVS, RS, Abdomen, Per rectal exam, Extremities, Skin, MSK, NS)
4. Pertinent findings (Positive / Negative / Incidental)

### ส่วนที่ 3 — Clinical Reasoning
1. Problem list
2. Provisional Diagnosis
3. Differential Diagnosis
4. Plan of investigation and management
5. Discussion

---

## กฎสำคัญ — ห้ามข้าม

### 1. ถามก่อนเขียนทุกครั้ง
ก่อนเริ่มเขียนหรือ generate template ให้ถาม **อย่างน้อย** ข้อมูลต่อไปนี้ถ้ายังไม่มี:
- ข้อมูลผู้ป่วย: อายุ เพศ chief complaint ระยะเวลา
- แผนก / ward
- โรคหรือ provisional diagnosis ที่สงสัย (ถ้ามี)
- มีผล lab / imaging แล้วหรือยัง

> ⚠️ **ห้ามเดาหรือแต่งข้อมูลผู้ป่วยขึ้นมาเอง** ถ้าไม่มีข้อมูล ให้ใส่ `[ระบุ: ...]` แทน

### 2. อ้างอิงทุกข้อมูลทางการแพทย์
ทุกข้อความที่เป็น:
- ค่าปกติ / ค่าผิดปกติ (เช่น normal range ของ lab, vital signs thresholds)
- เกณฑ์วินิจฉัย (เช่น diagnostic criteria ของโรคที่ provisional/DD)
- การรักษา / ยา / dose / แนวทางการผ่าตัด
- Pathophysiology ที่อธิบายในส่วน Discussion

**ต้องระบุ reference** ในรูปแบบ: `*(Ref: ชื่อตำรา/แนวทาง ฉบับ/ปี)*`

แหล่ง reference ที่ยอมรับ (เลือกตามความเกี่ยวข้องกับ case):
- **ตำราแพทย์ทั่วไป:** Harrison's Principles of Internal Medicine, Schwartz's Principles of Surgery, Williams Obstetrics, Nelson Textbook of Pediatrics, Robbins Pathology
- **ตำราไทย:** ตำราศัลยศาสตร์จุฬา, อาการวิทยาทางอายุรศาสตร์ มข., ตำราสูติศาสตร์ไทย
- **แนวทางเวชปฏิบัติสากล:** WHO guidelines, AHA/ACC, ACOG, IDSA, NICE guidelines, ESC, UpToDate (ระบุ accessed date)
- **แนวทางเวชปฏิบัติไทย:** ราชวิทยาลัยแพทย์ไทย, สมาคมแพทย์เฉพาะทางที่เกี่ยวข้อง, กรมการแพทย์ กระทรวงสาธารณสุข

### 3. Emoji เตือนทุก heading
ใส่ emoji ไว้หน้า heading ทุกหัวข้อ **เพื่อเตือนให้ผู้เขียนตรวจสอบข้อมูลก่อนส่ง** ตามตารางนี้:

| Heading | Emoji | ความหมาย |
|---|---|---|
| Patient identification | 🪪 | ตรวจสอบชื่อ-สกุล HN AN วันที่ |
| Chief complaint | 🗣️ | ตรวจสอบว่าตรงกับที่ผู้ป่วยบอก |
| Present illness | 📋 | ตรวจสอบ timeline และ LODCRAFTs |
| Systemic review | 🔍 | ตรวจสอบครบทุก system |
| Social & personal history | 🏠 | ตรวจสอบ alcohol, smoking, drug use |
| Past history | 📁 | ตรวจสอบ OB/GYN, surgery, allergy |
| Family history | 👨‍👩‍👧 | ตรวจสอบโรคทางพันธุกรรม |
| Current medication | 💊 | ตรวจสอบยาและขนาดยา |
| Physical examination | 🩺 | ตรวจสอบ vital signs และผลตรวจ |
| Pertinent findings | ⭐ | ตรวจสอบ positive/negative ครบ |
| Problem list | 📌 | ตรวจสอบปัญหาหลักครบ |
| Provisional Diagnosis | 🎯 | ตรวจสอบเหตุผลสนับสนุน |
| Differential Diagnosis | 🔀 | ตรวจสอบข้อสนับสนุนและคัดค้าน |
| Plan of investigation | 🧪 | ตรวจสอบเหตุผลของทุก investigation |
| Discussion | 📚 | ตรวจสอบ reference ทุกข้อ |

---

## วิธีใช้ — 3 โหมด

### โหมด A: สร้าง Template เปล่า
ผู้ใช้ขอ template เปล่าสำหรับกรอกเอง → generate template ตาม heading ทั้งหมด
ใส่ `[ระบุ: ...]` ทุกจุดที่ต้องกรอก พร้อม hint ว่าควรเขียนอะไร

### โหมด B: ช่วยเขียนจาก case ที่มี
ผู้ใช้ให้ข้อมูล case → เขียน report ตาม heading โดย:
1. ใช้เฉพาะข้อมูลที่ได้รับ ห้ามแต่ง
2. ถ้าข้อมูลไหนขาด ให้ถามก่อน ไม่เดา
3. ระบุ `[❓ ข้อมูลที่ควรหาเพิ่มเติม: ...]` ทุกจุดที่ข้อมูลไม่ครบ
4. ใส่ reference ทุก claim ทางการแพทย์

### โหมด C: Review / ให้ feedback รายงานที่เขียนแล้ว
ผู้ใช้แนบ draft → วิเคราะห์ตาม checklist ใน `## Checklist ก่อนส่งรายงาน` ด้านล่าง

---

## โครงสร้าง Output มาตรฐาน

```markdown
# 📋 Medical Report — Admission Record

**สถาบัน:** [ชื่อโรงพยาบาล]  
**แผนก/Ward:** [ระบุ]  
**นักศึกษาแพทย์:** [ชื่อ] รหัส [xxx] ชั้นปีที่ [x]  
**อาจารย์ที่ปรึกษา:** [ระบุ]  
**วันที่ Admit:** [วัน/เดือน/ปี]  
**วันที่ส่งรายงาน:** [วัน/เดือน/ปี]  

> ⚠️ **หมายเหตุ:** ตรวจสอบข้อมูลทุกหัวข้อให้ถูกต้องก่อนส่ง emoji ⚠️ หมายถึงจุดที่ต้องระวังเป็นพิเศษ

---

## 🪪 Patient Identification and Status
[ระบุ: เพศ อายุ อาชีพ ภูมิลำเนา สิทธิการรักษา ความน่าเชื่อถือของข้อมูล]

## 🗣️ Chief Complaint
[ระบุ: อาการหลัก + ระยะเวลา]

## 📋 Present Illness
[ระบุ: เรียงตามลำดับเวลา ใช้ LODCRAFTs เป็นแนวทาง]

> ❓ **ข้อมูลที่ควรหาเพิ่มเติม (ถ้ายังไม่มี):**
> - Radiation ของอาการปวด
> - Alleviating / Aggravating factors

## 🔍 Systemic Review
[ระบุ: ทบทวนทุก system — General, HEENT, CVS, RS, GI, GU, Skin, MSK, NS, Endocrine, Hemato]

## 🏠 Social and Personal History
[ระบุ: อาชีพ สถานะครอบครัว alcohol/smoking/drug use อาหาร ยาสมุนไพร]

## 📁 Past History
[ระบุ: โรคประจำตัว การผ่าตัด การแพ้ยา/อาหาร]
**OB/GYN (สำหรับผู้หญิง):** [ระบุ: G_P_ LMP การคุมกำเนิด]

## 👨‍👩‍👧 Family History
[ระบุ: โรคทางพันธุกรรม มะเร็ง CVD DM HT]

## 💊 Current Medication
[ระบุ: ยาทุกชนิดพร้อมขนาด หรือ No current medication]

---

## 🩺 Physical Examination

### Vital Signs
| Parameter | ค่าที่ได้ | ค่าปกติ | สถานะ |
|---|---|---|---|
| BP | [x/x mmHg] | <120/80 mmHg | [ปกติ/ผิดปกติ] |
| PR | [x bpm] | 60–100 bpm | |
| RR | [x tpm] | 12–20 tpm | |
| BT | [x °C] | 36.1–37.2 °C | |
| O2Sat | [x %] | ≥95% | |
| BW/Height | [x kg / x cm] | — | |
| BMI | [x kg/m²] | 18.5–22.9 (Asian) | |

*(Ref: WHO/WPRO BMI classification for Asian populations, 2004)*

### General Appearance
[ระบุ]

### HEENT
[ระบุ]

### CVS
[ระบุ]

### RS
[ระบุ]

### Abdomen
[ระบุ — รวม bowel sound, tenderness, guarding, rebound tenderness, organomegaly, palpable mass, special signs ที่เกี่ยวข้องกับ case (เช่น Murphy's sign, McBurney's point, Rovsing's sign, Psoas sign ฯลฯ)]

### Per Rectal Examination
[ระบุ หรือ Not performed — ระบุเหตุผลถ้าไม่ได้ทำ]

### Extremities / Skin / MSK / NS
[ระบุ]

---

## ⭐ Pertinent Findings

**Positive findings:**
- [ระบุ]

**Negative findings:**
- [ระบุ]

**Incidental findings:**
- [ระบุ หรือ None]

---

## 📌 Problem List
1. [ปัญหาหลัก]
2. [ปัญหารอง]

---

## 🎯 Provisional Diagnosis
**[ชื่อโรค]**

เหตุผลสนับสนุน:
1. [อาการ/อาการแสดงที่เข้าได้]
2. [ผล lab/imaging ที่สนับสนุน]
3. [เกณฑ์การวินิจฉัยที่ใช้]

*(Ref: [ระบุ แนวทาง/ตำรา ฉบับ/ปี])*

---

## 🔀 Differential Diagnosis

### 1. [โรค DD อันดับ 1]
- **ข้อสนับสนุน:** [ระบุ]
- **ข้อคัดค้าน:** [ระบุ]

### 2. [โรค DD อันดับ 2]
- **ข้อสนับสนุน:** [ระบุ]
- **ข้อคัดค้าน:** [ระบุ]

---

## 🧪 Plan of Investigation and Management

### Initial Assessment & Stabilization
[ระบุ: Vital signs monitoring, IV access, NPO ถ้าจำเป็น พร้อมเหตุผล]

### Laboratory Investigation
| รายการ | เหตุผลที่ส่ง | ผลที่ได้ | แปลผล |
|---|---|---|---|
| CBC | [ระบุ] | [ระบุ] | [ระบุ] |
| [รายการอื่น] | | | |

### Imaging
[ระบุ: ชนิด imaging เหตุผล และผลที่ได้]

### การรักษา
[ระบุ: ยา/หัตถการ พร้อมเหตุผลและ dose]

*(Ref: [ระบุ])*

---

## 📚 Discussion

[สรุป case และอธิบายโรค pathophysiology การวินิจฉัย และแผนการรักษา
**ทุก claim ต้องมี reference กำกับ**]

*(Ref: [ระบุทุก reference ที่ใช้])*

---

## 📖 References
1. [ชื่อตำรา ฉบับ ปี]
2. [แนวทางเวชปฏิบัติ ปี]
3. [อื่นๆ]
```

---

## Checklist ก่อนส่งรายงาน

ใช้รายการนี้ตรวจสอบก่อนส่งทุกครั้ง:

**Admission Record**
- [ ] 🪪 ข้อมูลผู้ป่วยครบ: ชื่อ HN AN วันที่ สิทธิ
- [ ] 🗣️ Chief complaint ระบุอาการหลักและระยะเวลาชัดเจน
- [ ] 📋 Present illness ครอบคลุม LODCRAFTs ครบ
- [ ] 🔍 Systemic review ครบทุก system ไม่ข้ามระบบ
- [ ] 🏠 Social history ระบุ alcohol, smoking, drug use ชัดเจน
- [ ] 📁 Past history ระบุ allergy และ OB/GYN (ถ้าเป็นหญิง)
- [ ] 👨‍👩‍👧 Family history ระบุโรคทางพันธุกรรมที่เกี่ยวข้อง
- [ ] 💊 Current medication ระบุครบหรือ "No current medication"

**Physical Examination**
- [ ] 🩺 Vital signs ครบทุกตัว รวม BMI และ classification
- [ ] 🩺 Physical findings ครอบคลุมทุก system
- [ ] ⭐ Pertinent findings แยก Positive / Negative / Incidental ชัดเจน

**Clinical Reasoning**
- [ ] 📌 Problem list ครอบคลุมปัญหาทั้งหมดของผู้ป่วย
- [ ] 🎯 Provisional diagnosis มีเหตุผลสนับสนุนครบ + reference
- [ ] 🔀 Differential diagnosis ระบุข้อสนับสนุนและคัดค้านทุกโรค
- [ ] 🧪 Investigation ทุกรายการมีเหตุผลกำกับ + แปลผลครบ
- [ ] 📚 Discussion มี reference ทุก claim ทางการแพทย์
- [ ] 📖 Reference list ครบ เป็นแหล่งที่น่าเชื่อถือ

---

## จุดที่ต้องระวังเป็นพิเศษ (⚠️ Universal Common Mistakes)

ข้อผิดพลาดเหล่านี้พบได้ในทุก case ไม่ว่าจะเป็นโรคอะไร:

**ประวัติและการซักถาม**
1. **LODCRAFTs ไม่ครบ** — Present illness ต้องครอบคลุม Location, Onset, Duration, Character, Radiation, Associated symptoms, Factors, Time course *(Ref: ตำราการซักประวัติและตรวจร่างกาย)*
2. **OB/GYN history ขาด** — ต้องระบุในผู้ป่วยหญิงทุกราย: G_P_, LMP, การคุมกำเนิด ไม่ว่าจะมาด้วยโรคอะไร
3. **Relevant history ขาด** — ต้องสรุปประเด็นสำคัญที่เชื่อมโยงกับ chief complaint แยกออกจาก full history
4. **ยา OTC และสมุนไพร** — ผู้ป่วยมักไม่นับว่าเป็น "ยา" ต้องถามเพิ่มเติมเสมอ

**การตรวจร่างกาย**
5. **BMI classification** — ใช้ Asia-Pacific classification สำหรับผู้ป่วยไทย/เอเชีย (Obese I: ≥25 kg/m²) ไม่ใช่ WHO global standard (Obese: ≥30 kg/m²) *(Ref: WHO/WPRO BMI classification for Asian populations, 2004)*
6. **Vital signs ครั้งเดียวไม่เพียงพอสำหรับวินิจฉัย** — BP สูงครั้งเดียว ≠ วินิจฉัย hypertension, ต้องวัดซ้ำ *(Ref: สมาคมความดันโลหิตสูงแห่งประเทศไทย)*
7. **Physical sign ต้องระบุเหตุผล** — การทำ special test ใดๆ (เช่น Murphy's sign, Psoas sign, Rovsing's sign) ต้องระบุว่า positive/negative หมายความว่าอะไรใน context ของ case นั้น ไม่ใช่บันทึกแค่ผล

**Clinical Reasoning**
8. **Provisional diagnosis ≠ Definitive diagnosis** — ต้องชัดเจนว่าเป็นเพียง working diagnosis และต้องมีเหตุผลสนับสนุนตาม clinical criteria ที่มีอยู่
9. **DD ต้องมีทั้งข้อสนับสนุนและข้อคัดค้าน** — การระบุแค่ชื่อโรคโดยไม่มี reasoning ถือว่าไม่สมบูรณ์
10. **Investigation ทุกรายการต้องมีเหตุผล** — ระบุว่าส่งเพื่อประเมินอะไร ไม่ใช่สั่งเพราะเป็น routine

**Reference**
11. **แต่ละ claim ต้องมี reference ของตัวเอง** — ห้ามใช้ reference เดียวครอบคลุมทุกข้อใน Discussion
12. **Normal range ของ lab ต้องอ้างอิง** — ค่าที่ระบุว่า "ปกติ" หรือ "ผิดปกติ" ต้องอ้างอิง laboratory reference range ที่ใช้

---

## ข้อมูลที่ควรหาเพิ่มเติม (Universal Gap Checklist)

ถ้า case ขาดข้อมูลเหล่านี้ ให้ระบุ `[❓ ควรหาเพิ่ม: ...]` ไว้ใน report ทุกครั้ง:

**ประวัติ**
- ประวัติ OB/GYN ถ้าเป็นผู้ป่วยหญิง (G_P_, LMP, การคุมกำเนิด)
- รายละเอียดการผ่าตัดหรือหัตถการครั้งก่อน (ชนิด วิธี ภาวะแทรกซ้อน)
- ประวัติยาทุกชนิดก่อนมาโรงพยาบาล รวม OTC, ยาสมุนไพร, ยาชุด
- Allergy — ถ้ายังไม่ได้ถามให้ระบุ "not yet elicited"
- Functional status ก่อนป่วย — โดยเฉพาะผู้สูงอายุหรือผู้ที่มีโรคเรื้อรัง

**การตรวจร่างกาย**
- Vital signs ซ้ำถ้ามีค่าผิดปกติ (เช่น BP สูง ควรวัดซ้ำก่อนสรุป)
- Weight/Height ถ้ายังไม่ได้วัด (จำเป็นสำหรับคำนวณ BMI และ drug dosing)

**Investigation**
- ผล lab หรือ imaging ที่ยังรอผล — ระบุว่า "pending" พร้อมระบุว่ารอเพื่ออะไร
- Culture and sensitivity ถ้าสงสัย infection
- Pregnancy test (urine/serum hCG) ในผู้ป่วยหญิงวัยเจริญพันธุ์ที่มาด้วยปวดท้อง/อาการบางอย่าง
- Baseline investigation ที่จำเป็นก่อนให้ยาหรือผ่าตัด (เช่น renal function ก่อนให้ contrast/NSAID, coagulation ก่อนผ่าตัด)

**เฉพาะตาม context ของ case**
- ถ้ามีไข้ — ควรมี blood culture และ source of infection ที่ชัดเจน
- ถ้าดื่มสุราหรือใช้สารเสพติด — ควร screen withdrawal risk
- ถ้าสงสัย malignancy — ควรมี weight loss, appetite, constitutional symptoms ครบ