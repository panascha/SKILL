---
name: slide-enrich
description: |
  เพิ่มคุณค่าทางการแพทย์ให้กับ Markdown notes ที่แปลงมาจาก slide แล้ว โดยเพิ่ม:
  กลไกทางการแพทย์ (pathophysiology/mechanism), สิ่งที่ต้องรู้ (ภาษาไทย), และตรวจสอบข้อมูลกับแหล่งอ้างอิง
  ให้ trigger skill นี้ทุกครั้งที่ user:
  - ส่งไฟล์ notes-raw.md หรือ Markdown จาก slide มาแล้วบอกว่า "เพิ่มกลไก", "enrich", "ตรวจสอบ", "เพิ่มเนื้อหา"
  - พูดถึง "slide-enrich" โดยตรง
  - บอกว่าต้องการ "สิ่งที่ต้องรู้", "กลไก", "mechanism", "pathophysiology" จาก notes ที่มีอยู่แล้ว
  - ต้องการตรวจสอบความถูกต้องของ notes กับ guidelines หรือแหล่งอ้างอิงทางการแพทย์
  ห้าม undertrigger: ถ้า user มี notes จาก slide และต้องการเพิ่ม clinical context ให้ใช้ skill นี้เสมอ
  รับ input เป็นไฟล์ notes-raw.md หรือ Markdown text, output เป็น notes-enriched.md
---

# Slide-Enrich

เพิ่มคุณค่าทางการแพทย์ให้กับ notes ที่แปลงมาจาก slide แล้ว
รับ `notes-raw.md` เป็น input → output เป็น `notes-enriched.md`

**scope ของ skill นี้:** เพิ่ม 3 sections ต่อทุก topic:
1. `🧠 กลไกและเหตุผลทางการแพทย์`
2. `📌 สิ่งที่ต้องรู้ (ภาษาไทย)`
3. `‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์` (ต้องใช้ web search)

ไม่แตะต้องเนื้อหาเดิมจาก `notes-raw.md` — เพิ่มเติมเท่านั้น ห้ามแก้ไขหรือตัดทอน

---

## หลักการสำคัญ

1. **ทำทีละ section** — อ่าน section จาก notes-raw.md ทีละอัน เพิ่ม 3 subsections แล้วค่อยไป section ถัดไป เพื่อไม่ให้ context window ล้น
2. **Web search ทุก topic** — ต้องค้นหาข้อมูลเพื่อตรวจสอบและเสริมความรู้ก่อนเขียนทุก section
3. **กลไกต้องอธิบาย "ทำไม"** — ไม่ใช่แค่ list ข้อเท็จจริง ต้องอธิบาย pathophysiology, mechanism, หรือ clinical application
4. **สิ่งที่ต้องรู้เป็นภาษาไทยเสมอ** — ห้ามเขียนเป็นภาษาอื่น
5. **แหล่งอ้างอิงต้องเป็นความรู้ทางการแพทย์** — ห้ามอ้างสำนักพิมพ์ (ดูรายการที่ยอมรับได้ด้านล่าง)

---

## โครงสร้าง 3 Sections ที่ต้องเพิ่ม

เพิ่มต่อท้าย `### เนื้อหาจากสไลด์` ของทุก section:

```markdown
### 🧠 กลไกและเหตุผลทางการแพทย์
[อธิบาย "ทำไม" ของเนื้อหาในสไลด์:
- กลไกการเกิด (pathophysiology/mechanism)
- การนำไปใช้ทางคลินิก (clinical application)
ห้ามแค่ list ข้อมูลโดยไม่มี context]

### 📌 สิ่งที่ต้องรู้ (ภาษาไทย)
- bullet points ภาษาไทย ครอบคลุม key concepts, clinical pearls, และ red flags
- เขียนให้ผู้เรียนจำและเข้าใจได้จริง ไม่ใช่แค่ copy จากสไลด์

### ‼️ ข้อมูลที่อาจไม่ตรงกับสไลด์
[ถ้าไม่พบความขัดแย้ง:]
✅ ข้อมูลสอดคล้องกับแหล่งอ้างอิง

[ถ้าพบความขัดแย้ง:]
‼️ [ระบุประเด็นที่แตกต่าง]
- **ในสไลด์:** ...
- **ตามแหล่งอ้างอิง:** ...
- **แหล่งอ้างอิง:** [ชื่อแหล่ง + URL หรือ DOI]
```

---

## การตรวจสอบความถูกต้อง

ทุก topic ให้ web search เพื่อตรวจสอบ โดยเฉพาะ:
- ตัวเลขทางคลินิก (ค่า cutoff, dosage, reference range)
- คำแนะนำการรักษา (guidelines)
- กลไกที่อธิบายไว้
- การจำแนกประเภท/classification

**ตัวอย่างเมื่อพบความขัดแย้ง:**
```
‼️ เกณฑ์การวินิจฉัยในสไลด์อาจล้าสมัย
- **ในสไลด์:** HbA1c ≥ 6.5% ใช้ได้เฉพาะวิธี NGSP
- **ตามแหล่งอ้างอิง:** ADA 2024 ยอมรับทั้ง NGSP และ IFCC โดยต้องระบุหน่วยด้วย
- **แหล่งอ้างอิง:** American Diabetes Association Standards of Care 2024 — https://diabetesjournals.org/care
```

---

## แหล่งข้อมูลที่ยอมรับได้

**ห้ามอ้างสำนักพิมพ์** (ห้ามอ้าง "Elsevier", "Wiley", "Lippincott" ฯลฯ)

| ประเภท | ตัวอย่าง |
|--------|----------|
| Clinical guidelines | ADA, AHA, ACC, WHO, NICE, ACOG, IDSA |
| Evidence databases | UpToDate, PubMed/MEDLINE, Cochrane Library |
| Reference tools | StatPearls (NCBI Bookshelf), Medscape |
| Pharmacology | FDA Drug Label, BNF, Micromedex |
| Pathology/Lab | CLSI, CAP, RCPA |
| Thai guidelines | แนวทางเวชปฏิบัติของราชวิทยาลัยแพทย์ไทย, กรมการแพทย์ |

**รูปแบบที่ถูกต้อง:**
- `WHO Guidelines on Malaria Treatment (2023) — https://www.who.int/...`
- `AHA/ACC 2023 Hypertension Guidelines — doi:10.1161/...`
- `StatPearls: Acute Pancreatitis — NCBI Bookshelf`

**ห้ามอ้างอิงในลักษณะนี้:**
- ❌ "Robbins & Cotran (Elsevier)"
- ❌ "Harrison's Principles (McGraw-Hill)"

---

## ขั้นตอนการทำงาน

1. **รับ input** — อ่านไฟล์ notes-raw.md หรือ Markdown ที่ user ส่งมา
2. **นับ sections** — ระบุจำนวน section ทั้งหมดที่ต้องทำให้ user ทราบ
3. **ทำทีละ section** — สำหรับแต่ละ section:
   - อ่าน `### เนื้อหาจากสไลด์`
   - web search เพื่อตรวจสอบและหาข้อมูลกลไก
   - เขียน `🧠 กลไก` → `📌 สิ่งที่ต้องรู้` → `‼️ ตรวจสอบ`
4. **รักษาโครงสร้างเดิม** — copy เนื้อหาจาก notes-raw.md ครบถ้วน ไม่ตัดไม่แก้
5. **อัปเดต Checklist** — ถ้า notes-raw.md มี checklist ให้ update สถานะเป็น ✅ เมื่อ enrich แล้ว
6. **ส่งไฟล์** ด้วย present_files โดยตั้งชื่อว่า `notes-enriched.md`

---

## ข้อห้าม

- ❌ ห้ามแก้ไข ตัด หรือย่อเนื้อหาเดิมจาก notes-raw.md
- ❌ ห้ามเขียน `📌 สิ่งที่ต้องรู้` เป็นภาษาอื่นนอกจากภาษาไทย
- ❌ ห้ามอ้างอิงสำนักพิมพ์เป็นแหล่งข้อมูล
- ❌ ห้ามเขียน `🧠 กลไก` แบบ list ข้อเท็จจริงโดยไม่มีบริบท
- ❌ ห้ามข้าม section ใดโดยไม่เพิ่ม 3 subsections ครบ
- ❌ ห้าม skip web search — ทุก topic ต้องตรวจสอบ