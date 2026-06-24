---
name: med-keyword-recall
description: >
  สร้าง active recall cards แบบ Notion toggle (keyword → คำอธิบาย) จากเนื้อหาการเรียนแพทย์
  รับเนื้อหาหลากหลายรูปแบบ: สรุปเนื้อหา, ข้อสอบเก่า (MCQ), note ที่ทำเอง, สไลด์
  ครอบคลุมทุก subject: Anatomy, Physiology, Biochemistry, Microbiology, Parasitology,
  Pathology, Pharmacology, Radiology, Clinical — และ subject อื่นๆ นอกเหนือจากนี้
  Trigger ทุกครั้งที่ user พูดถึง: "active recall", "toggle", "keyword recall", "card",
  "จำ/สรุปแบบถาม-ตอบ", "ทำ flashcard", "ทำ recall", "ทำ toggle", "notion toggle"
  หรือแปะเนื้อหาพร้อมสัญญาณว่าต้องการ format สำหรับท่อง/ทบทวน
---

# Med Keyword Recall Skill

สกัดเนื้อหา → Notion-style toggle สำหรับ active recall: เห็น keyword → ลองนึก → เปิดดูคำตอบ

---

## Output format: Notion toggle (markdown indent)

ส่งผล **inline ใน chat** เป็น markdown ที่ copy ไป Notion แล้วใช้ได้เลย — ไม่สร้าง HTML artifact

### โครงสร้างพื้นฐาน

```
## 🔬 Physiology

- **[Keyword / คำถาม / trigger]**
    - [คำตอบ 1 บรรทัด — กลไก + buzzword + ตัวเลขสำคัญ]

- **[Keyword 2]**
    - [คำตอบ]
```

### ตัวอย่าง output จริง

```markdown
## 📻 Radiology

- **TOF → CXR รูปร่าง?**
    - Boot 🥾 (Coeur en sabot) — ปอดน้อย (decreased flow) + RVH apex ยก

- **TGA → CXR รูปร่าง?**
    - Egg on a string 🥚 — mediastinum แคบ (parallel vessels) + increased flow

- **HyperK → ECG progression?**
    - Peaked T → Wide QRS → PR↑ → Flat P → Sine wave

- **Digoxin + Atorvastatin → effect?**
    - Digoxin toxicity ↑ — Atorvastatin ยับยั้ง P-gp → ลดการขับ digoxin
```

---

## Subject Groups และ emoji header

| Code (ใน input) | Display Header |
|----------------|---------------|
| ANA / Anatomy | `## 🦴 Anatomy` |
| PHYSIO / Physiology | `## 🔬 Physiology` |
| BIOCHEM / Biochemistry | `## ⚗️ Biochemistry` |
| MICRO / Microbiology | `## 🦠 Microbiology` |
| PARASITO / Parasitology | `## 🪱 Parasitology` |
| PATHO / Pathology | `## 🔴 Pathology` |
| PHARM / Pharmacology | `## 💊 Pharmacology` |
| RADIO / Radiology | `## 📻 Radiology` |
| CLINIC / Clinical | `## 🏥 Clinical` |
| subject อื่น | ตั้ง header ใหม่ให้เหมาะสม + emoji |

ถ้า input ไม่มี subject tag ชัดเจน ให้ **detect จากเนื้อหา** แล้วจัดกลุ่มเอง

---

## ขั้นตอนการสกัดเนื้อหา

### 1. วิเคราะห์ input
- input เป็นอะไร? (MCQ, note สรุป, keyword list, สไลด์)
- detect subject groups ที่มีอยู่
- ระบุ "จุดที่ต้องจำ" = concept + ค่า specific + จุดสับสนบ่อย

### 2. เลือก card front ตามประเภทเนื้อหา

| เนื้อหา | Card Front | Card Back |
|--------|-----------|-----------|
| Shape / sign | `[โรค/ภาวะ] → [modality] sign?` | ชื่อ sign + กลไกสั้น |
| ECG / Lab | `[ภาวะ] → ECG / Lab?` | ลำดับ progression |
| Drug MOA | `[ยา] → MOA?` | กลไกหลัก + buzzword |
| Drug interaction | `[ยา A] + [ยา B] → ?` | ผล + เหตุผลสั้น |
| Antidote | `[ยา/พิษ] → Antidote?` | ชื่อยา + MOA สั้น |
| Diagnosis | `[อาการ/triad/scenario] → Dx?` | diagnosis + key differentiator |
| Cutoff / ค่าตัวเลข | `[Parameter] cutoff?` | ตัวเลข + หน่วย + clinical significance |
| Mechanism | `[ภาวะ] เกิดจาก?` | กลไกสั้น 1 บรรทัด |
| Management | `[ภาวะ] → first line Rx?` | ยา/หัตถการ + เหตุผลสั้น |

### 3. กฎการเขียน

**Card front (bold text):**
- ≤ 10 คำ เน้น trigger จำ
- ปิดด้วย `?` เสมอ ยกเว้น comparison (`A vs B → จุดต่าง?`)
- อย่าใส่คำตอบใน front

**Card back (indented):**
- ≤ 1-2 บรรทัด — ถ้ายาวกว่าตัดทิ้ง
- ตัวเลขสำคัญต้องใส่เสมอ (PCWP >25, QT ≥0.12s ฯลฯ)
- จุดสับสนบ่อยให้ขึ้น `❌` นำหน้าสิ่งที่ผิด
- Emoji ใส่ได้ถ้าช่วยจำ ไม่บังคับ

---

## กฎ output สุดท้าย

1. **ส่งเป็น markdown inline** — ไม่สร้าง HTML artifact ไม่สร้างไฟล์
2. **จัดกลุ่มด้วย `##` header** ตาม subject — ถ้า input มีหลาย subject ให้แยก section
3. **ถ้า input มี subject เดียว** ไม่ต้องมี header — ส่ง cards ตรงๆ
4. **อย่าเพิ่ม intro/outro** — ขึ้นด้วย header หรือ card แรกเลย
5. **บอกจำนวน card** หลัง output สั้นๆ เช่น `> 12 cards · 3 subjects`