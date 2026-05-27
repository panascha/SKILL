---
name: medical-report-export
description: >
  Export Medical Report / Admission Record ที่เขียนและ review แล้ว ให้เป็นไฟล์ Markdown (.md) ทางการ
  พร้อมส่ง ตาม heading มาตรฐานคณะแพทยศาสตร์ โรงพยาบาลมหาสารคาม ในรูปแบบไทย-อังกฤษผสม
  ใช้ skill นี้ทุกครั้งที่ผู้ใช้พูดถึง: export report, บันทึกรายงาน, สร้างไฟล์รายงาน, ดาวน์โหลดรายงาน,
  final report, finalize, สรุปรายงานเป็นไฟล์, หรือหลังจาก review report เสร็จแล้วและต้องการไฟล์สุดท้าย
  ใช้ด้วยเมื่อผู้ใช้พิมพ์: /export, /บันทึก, /final, /ส่งรายงาน, /สร้างไฟล์
---

# Medical Report Export Skill

รับ Medical Report ที่ผ่านการ review แล้ว และสร้างไฟล์ `.md` ทางการพร้อมส่ง

---

## จุดประสงค์

Skill นี้คือ **ขั้นตอนสุดท้าย** ใน workflow:
```
เขียน report (medical-report skill)
    ↓
ตรวจ / review (medical-report-review skill)
    ↓
Export เป็นไฟล์ (skill นี้) ← คุณอยู่ที่นี่
```

---

## กฎก่อน Export — ห้ามข้าม

### 1. ตรวจสอบ source ของ report
ก่อน export ให้ถามผู้ใช้ว่า:
- Report ผ่านการ review แล้วหรือยัง?
- มีการแก้ไขตาม feedback ครบหรือยัง?

ถ้ายังไม่ได้ review → แจ้งผู้ใช้และแนะนำให้ใช้ `medical-report-review` ก่อน  
แต่ถ้าผู้ใช้ยืนยันว่าพร้อม export → ดำเนินการต่อได้

### 2. ดึงข้อมูลสำหรับ Header ไฟล์
ก่อน export ต้องมีข้อมูลต่อไปนี้ครบ (ถามถ้าไม่มี):
- ชื่อนักศึกษาแพทย์ + รหัสนักศึกษา + ชั้นปี + Block
- ชื่อผู้ป่วย (ใช้เฉพาะตัวย่อ เช่น นาง ท. น. เพื่อความเป็นส่วนตัว)
- ชื่ออาจารย์ที่ปรึกษา
- Ward / แผนก
- วันที่ Admit และวันที่ส่งรายงาน

---

## โครงสร้างไฟล์ Output มาตรฐาน

สร้างไฟล์ชื่อ: `medical_report_[HN_หรือชื่อย่อ]_[วันที่].md`  
เช่น: `medical_report_น.ท.น_2569-05-17.md`

```markdown
# 📋 Medical Report — Admission Record
**คณะแพทยศาสตร์ โรงพยาบาลมหาสารคาม**

| รายการ | ข้อมูล |
|---|---|
| **นักศึกษาแพทย์** | [ชื่อ-สกุล] รหัส [xxxxxxxx-x] ชั้นปีที่ [x] Block [x] |
| **อาจารย์ที่ปรึกษา** | [ชื่ออาจารย์] |
| **ผู้ป่วย** | [ชื่อย่อ] |
| **Ward** | [ชื่อ Ward] |
| **วันที่ Admit** | [วัน เดือน ปี พ.ศ.] |
| **วันที่ส่งรายงาน** | [วัน เดือน ปี พ.ศ.] |

> ⚠️ **หมายเหตุ:** ข้อมูลผู้ป่วยในรายงานนี้เป็นความลับทางการแพทย์  
> ตรวจสอบความถูกต้องทุกหัวข้อก่อนส่ง

---

## 🪪 Patient Identification and Status
[เนื้อหา]

---

## 🗣️ Chief Complaint
[เนื้อหา]

---

## 📋 Present Illness
[เนื้อหา]

### Relevant History
[เนื้อหา — ถ้ามี]

---

## 🔍 Systemic Review
[เนื้อหา แยกตาม system: General, HEENT, CVS, RS, GI, Skin, MSK, NS, KUB, Hemato, Endocrine]

---

## 🏠 Social and Personal History
[เนื้อหา]

---

## 📁 Past History
[เนื้อหา รวม OB/GYN ถ้าเป็นผู้หญิง]

---

## 👨‍👩‍👧 Family History
[เนื้อหา]

---

## 💊 Current Medication
[เนื้อหา หรือ "No current medication"]

---

## 🩺 Physical Examination

### General Appearance
[เนื้อหา]

### Vital Signs

| Parameter | ค่าที่วัดได้ | Reference Range | สถานะ |
|---|---|---|---|
| BP | [x/x mmHg] | <120/80 mmHg | [ปกติ / สูง / ต่ำ] |
| PR | [x bpm] | 60–100 bpm | |
| RR | [x tpm] | 12–20 tpm | |
| BT | [x °C] | 36.1–37.2 °C | |
| O₂Sat | [x%] | ≥95% | |
| BW / Height | [x kg / x cm] | — | |
| BMI | [x kg/m²] | 18.5–22.9 (Asia-Pacific) | [classification] |

*(Ref: WHO/WPRO BMI classification for Asian populations, 2004)*

### HEENT
[เนื้อหา]

### CVS
[เนื้อหา]

### RS
[เนื้อหา]

### Abdomen
[เนื้อหา — รวม special signs พร้อมความหมาย]

### Per Rectal Examination
[เนื้อหา หรือ "Not performed — [เหตุผล]"]

### Extremities
[เนื้อหา]

### Skin
[เนื้อหา]

### MSK
[เนื้อหา]

### Neurological System
[เนื้อหา]

---

## ⭐ Pertinent Findings

**Positive findings:**
- [รายการ]

**Negative findings:**
- [รายการ]

**Incidental findings:**
- [รายการ หรือ "None"]

---

## 📌 Problem List
1. [ปัญหาหลัก]
2. [ปัญหารอง]

---

## 🎯 Provisional Diagnosis

**[ชื่อโรค — ภาษาอังกฤษ (ภาษาไทย)]**

เหตุผลสนับสนุน:
1. [อาการ/อาการแสดง]
2. [ผล lab/imaging]
3. [เกณฑ์วินิจฉัย]

*(Ref: [ตำรา/แนวทาง ฉบับ/ปี])*

---

## 🔀 Differential Diagnosis

### 1. [โรค DD อันดับ 1]
- **ข้อสนับสนุน:** [ระบุจาก case นี้]
- **ข้อคัดค้าน:** [ระบุจาก case นี้]

### 2. [โรค DD อันดับ 2]
- **ข้อสนับสนุน:** [ระบุ]
- **ข้อคัดค้าน:** [ระบุ]

---

## 🧪 Plan of Investigation and Management

### Initial Assessment & Stabilization
[เนื้อหา]

### Laboratory Investigation

| รายการ | เหตุผลที่ส่ง | ผลที่ได้ | แปลผล |
|---|---|---|---|
| [Lab] | [เหตุผล] | [ผล (reference range)] | [ปกติ/ผิดปกติ — ความหมาย] |

### Imaging
[ชนิด imaging — เหตุผล — ผลที่ได้พร้อมแปลผล]

### การรักษา
[ยา/หัตถการ พร้อมขนาดและเหตุผล]

*(Ref: [ตำรา/แนวทาง ปี])*

---

## 📚 Discussion

[เนื้อหา — สรุป case, pathophysiology, เหตุผลการวินิจฉัย, แผนการรักษา  
**ทุก claim ต้องมี reference กำกับ**]

*(Ref: [ระบุทุก reference ที่ใช้])*

---

## 📖 References

1. [ชื่อตำรา Edition ปี]
2. [แนวทางเวชปฏิบัติ ปี]
3. [อื่นๆ]

---

*รายงานนี้จัดทำโดยนักศึกษาแพทย์ชั้นปีที่ [x] คณะแพทยศาสตร์ โรงพยาบาลมหาสารคาม*  
*เพื่อวัตถุประสงค์ทางการศึกษาเท่านั้น*
```

---

## กฎการ Format ไฟล์

### ภาษา
- **Heading หลัก:** ภาษาอังกฤษ (ตาม PDF ต้นแบบ) + emoji ตาม skill `medical-report`
- **เนื้อหา:** ภาษาไทยเป็นหลัก, ศัพท์ทางการแพทย์ใช้ภาษาอังกฤษ
- **ตาราง Lab/Vitals:** ภาษาอังกฤษสำหรับชื่อรายการ, ภาษาไทยสำหรับการแปลผล

### ตาราง Lab
ทุกรายการ Lab ต้องแสดงใน format:  
`ค่าที่ได้ (reference range)` และระบุว่า High/Low/Normal พร้อมความหมายทางคลินิก

ตัวอย่าง:
```
| WBC Count | 14,040 Cell/mm³ (5,000–10,000) **High** | Leukocytosis — บ่งบอก systemic inflammation |
```

### Reference ใน Text
ทุก claim ทางการแพทย์ให้ใส่ inline reference:
```
*(Ref: Schwartz's Principles of Surgery, 11th ed.)*
*(Ref: Tokyo Guidelines 2018)*
*(Ref: สมาคมความดันโลหิตสูงแห่งประเทศไทย)*
```

### ข้อมูลผู้ป่วย
- ใช้ชื่อย่อเสมอ (เช่น นาง ท. น.) ไม่ใช้ชื่อเต็ม
- ไม่ใส่ HN/AN ในชื่อไฟล์ — ใช้ชื่อย่อและวันที่แทน

---

## ขั้นตอน Export

1. **รับ report** จาก conversation (ที่ผ่าน review แล้ว)
2. **ตรวจสอบ header info** — ถามถ้าข้อมูลไม่ครบ
3. **Render ไฟล์** ตาม template ด้านบน โดย:
   - ใส่เนื้อหาจาก report ทั้งหมด — ห้ามตัดทอนหรือแต่งเพิ่ม
   - Format ตาราง Vitals และ Lab ให้ครบ
   - ตรวจสอบว่า reference ทุกข้อมีครบ
   - ถ้ามีข้อมูลที่ขาดหายใน report เดิม → ใส่ `[❓ ข้อมูลขาด: ระบุ]` อย่าแต่งขึ้นมาเอง
4. **บันทึกไฟล์** ไปที่ `/mnt/user-data/outputs/[ชื่อไฟล์].md`
5. **เรียก `present_files`** เพื่อให้ผู้ใช้ดาวน์โหลดได้

---

## สิ่งที่ห้ามทำระหว่าง Export

- ❌ ห้ามแก้ไขเนื้อหาทางการแพทย์ที่ review ผ่านแล้ว
- ❌ ห้ามเพิ่มข้อมูลที่ไม่มีใน report ต้นฉบับ
- ❌ ห้ามเปลี่ยน diagnosis หรือ plan โดยไม่ได้รับอนุญาต
- ❌ ห้ามใช้ชื่อเต็มของผู้ป่วยในไฟล์
- ✅ แก้ได้: การ format, spacing, emoji, ตาราง

---

## ตัวอย่าง Trigger

ผู้ใช้พูดว่า → ควรใช้ skill นี้:
- "export รายงานเป็นไฟล์ได้เลย" ✅
- "/final" ✅
- "ขอไฟล์ .md สำหรับส่งอาจารย์" ✅
- "บันทึกรายงานที่ review แล้ว" ✅
- "สร้างไฟล์ final report" ✅
- "ดาวน์โหลด report" ✅