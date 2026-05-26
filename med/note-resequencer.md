---
name: note-resequencer
description: >
  ใช้ skill นี้เมื่อต้องการเรียบเรียงลำดับเนื้อหาใน notes-enriched.md ใหม่
  ตามหลักการเรียนรู้แบบแพทย์ (Medical Learning Sequence) โดยจัด cluster เนื้อหา
  จากที่กระจัดกระจายในสไลด์ให้เป็นสายโซ่ความรู้ที่ต้องเรียนทีละขั้น ก่อนเชื่อมโยงต่อไปเรื่อยๆ
  เหมาะใช้หลังผ่านขั้นที่ 3 (slide-enrich) แล้ว ก่อนส่งต่อ curriculum-tracker
  Trigger เมื่อผู้ใช้พูดถึง: "จัดลำดับเนื้อหา", "เรียงโน้ตใหม่", "resequence",
  "เรียนแบบ step-by-step", "จัด sequence", "เรียงตามหลักการแพทย์"
---

# Note Resequencer — Medical Learning Sequence

## จุดประสงค์

รับ `notes-enriched.md` ที่เนื้อหาเรียงตามลำดับสไลด์ของอาจารย์ (ซึ่งมักไม่ใช่ลำดับที่เหมาะสมกับการเรียนรู้ด้วยตัวเอง) แล้วจัด cluster และเรียงลำดับเนื้อหาใหม่ตามสายโซ่ความรู้ทางการแพทย์ที่สมเหตุสมผล โดย **ไม่เพิ่มหรือลบเนื้อหาใดๆ** — เพียงแค่จัดลำดับและ cluster ใหม่

Output คือ `notes-resequenced.md`

---

## หลักการจัดลำดับ (Medical Learning Chain)

เรียงเนื้อหาตามลำดับ 7 ชั้นนี้ โดยแต่ละชั้นเป็นฐานของชั้นถัดไป:

```
Layer 1: ANCHOR         — นิยาม / Classification / ภาพรวมโรค
Layer 2: FOUNDATION     — Anatomy / Physiology / Biochemistry ที่เกี่ยวข้อง
Layer 3: MECHANISM      — Pathophysiology / กลไกการเกิดโรค (ทำไม → เกิดอะไร)
Layer 4: PRESENTATION   — Signs & Symptoms / Clinical Features
Layer 5: WORKUP         — Investigations / Diagnosis / Criteria
Layer 6: MANAGEMENT     — Treatment / Pharmacology / Procedures / Guidelines
Layer 7: OUTCOMES       — Complications / Prognosis / Prevention / Special populations
```

> **หลักคิดสำคัญ:** Layer ที่ต่ำกว่าคือ "ทำไม" ของ layer ที่สูงกว่า เสมอ
> ผู้เรียนควรเข้าใจ mechanism ก่อนจึงจะ predict clinical features ได้เอง
> และเข้าใจ pathophysiology ก่อนจึงจะเข้าใจว่า treatment ทำงานอย่างไร

---

## ขั้นตอนการทำงาน

### Step 1: Inventory Scan

อ่าน `notes-enriched.md` ทั้งหมดก่อน แล้วทำ mental inventory:
- ระบุ **topic หลัก** ของบทเรียนนี้คืออะไร (เช่น Atrial Fibrillation, DKA, Pneumonia)
- ระบุว่า **layer ไหนมีเนื้อหา** บ้าง และ **layer ไหนไม่มี** (ไม่มีก็ไม่ต้องสร้าง)
- ระบุเนื้อหาที่ **ข้ามไปมาหลาย layer** ในหัวข้อเดียว (เช่น สไลด์ที่พูดถึง mechanism และ treatment ปนกัน) — เหล่านี้ต้องแยก cluster

### Step 2: Assign Each Section to a Layer

จัดให้แต่ละ section / หัวข้อย่อยในไฟล์ต้นฉบับ อยู่ใน layer ที่เหมาะสม

**ตารางตัดสินใจ (ใช้เป็นแนวทาง):**

| เนื้อหาแบบนี้ | จัดอยู่ Layer |
|---|---|
| Definition, Classification, Epidemiology, Incidence | 1 — ANCHOR |
| Normal anatomy, physiology, homeostasis mechanism | 2 — FOUNDATION |
| Etiology, Risk factors, Pathophysiology, Mechanism of disease | 3 — MECHANISM |
| Symptoms, Signs, Physical exam findings, Clinical presentation | 4 — PRESENTATION |
| Lab, Imaging, Criteria, Scoring, DDx | 5 — WORKUP |
| Drug therapy, Surgery, Procedures, Guidelines, Dosing | 6 — MANAGEMENT |
| Complications, Prognosis, Mortality, Prevention, Special cases | 7 — OUTCOMES |

> หากเนื้อหาหนึ่งก้อนมีหลาย layer ปนกัน ให้ **แยกก้อน** แล้วส่งแต่ละส่วนไปยัง layer ที่ถูกต้อง
> รักษาเนื้อหาต้นฉบับทุกคำ อย่าตัดหรือสรุปเพิ่มเติม

### Step 3: Cluster ภายใน Layer

ภายใน layer เดียวกัน ถ้ามีหลายหัวข้อย่อยที่เกี่ยวกัน ให้จัดกลุ่มตาม **sub-topic cluster** ที่สัมพันธ์กันก่อน-หลัง ไม่ใช่ตามลำดับที่ปรากฏในสไลด์

ตัวอย่าง Layer 6 — MANAGEMENT อาจ cluster เป็น:
```
6.1 Acute stabilization
6.2 Definitive treatment
6.3 Long-term / Maintenance
6.4 Special scenarios (renal/hepatic impairment, pregnancy, etc.)
```

### Step 4: เขียน Output

สร้าง `notes-resequenced.md` ตาม template ด้านล่าง

---

## Output Template

```markdown
# [ชื่อ Topic] — Resequenced Notes
> 📋 เรียบเรียงจาก: [ชื่อไฟล์ต้นฉบับ]  
> 🔗 ลำดับการเรียนรู้: Anchor → Foundation → Mechanism → Presentation → Workup → Management → Outcomes

---

## 🔖 Layer 1 — ANCHOR: นิยามและภาพรวม
> *เริ่มที่นี่เสมอ — สร้างกรอบความคิดก่อนลงรายละเอียด*

[เนื้อหาจาก layer 1 ทั้งหมด ตรงตามต้นฉบับ]

---

## 🧬 Layer 2 — FOUNDATION: พื้นฐานที่ต้องรู้ก่อน
> *ความรู้ anatomy/physiology ที่เป็นฐานของกลไกในบทนี้*

[เนื้อหาจาก layer 2 ทั้งหมด — ถ้าไม่มีในไฟล์ ให้ข้าม layer นี้ไป]

---

## ⚙️ Layer 3 — MECHANISM: กลไกการเกิดโรค
> *เข้าใจ "ทำไม" ก่อน — ทุกอย่างใน Layer 4-7 ล้วนเป็นผลของ layer นี้*

[เนื้อหาจาก layer 3]

---

## 🩺 Layer 4 — PRESENTATION: อาการและอาการแสดง
> *อาการเหล่านี้เกิดเพราะกลไกใน Layer 3 — ลองเชื่อมโยงดู*

[เนื้อหาจาก layer 4]

---

## 🔬 Layer 5 — WORKUP: การตรวจวินิจฉัย
> *ตรวจอะไร เพื่อยืนยันหรือตัดแยกสมมติฐานจาก Layer 4*

[เนื้อหาจาก layer 5]

---

## 💊 Layer 6 — MANAGEMENT: การรักษา
> *รักษาโดยแทรกแซงกลไกใน Layer 3 หรือควบคุมอาการใน Layer 4*

[เนื้อหาจาก layer 6]

---

## 📈 Layer 7 — OUTCOMES: ภาวะแทรกซ้อนและผลลัพธ์
> *เกิดเมื่อกลไกหรือการรักษาไม่ได้ผล — เชื่อมกลับไป Layer 3 เสมอ*

[เนื้อหาจาก layer 7]

---

## 🗺️ Learning Chain Summary
> *แผนผังเชื่อมโยงฉบับย่อ — อ่านหลังจบทั้งหมด*

[เขียนสรุป chain สั้นๆ 3-5 บรรทัด ในรูปแบบ:
"[Foundation concept] → ทำให้เกิด [Mechanism] → แสดงออกเป็น [Key symptoms] → ตรวจด้วย [Key investigation] → รักษาด้วย [Key treatment] → ถ้าไม่รักษา/ล้มเหลว → [Key complication]"]
```

---

## กฎสำคัญ

1. **ห้ามเพิ่มเนื้อหาใหม่** — ทุกอักษรในไฟล์ output ต้องมาจากไฟล์ input เท่านั้น
2. **ห้ามตัดเนื้อหาออก** — เนื้อหาทุกชิ้นจากต้นฉบับต้องปรากฏใน output ครบ 100%
3. **รักษา formatting เดิม** — ตาราง, callout, emoji, สัญลักษณ์ `‼️`, bold ทุกอย่างคงไว้
4. **ข้าม layer ที่ว่างเปล่า** — ถ้าไฟล์ต้นฉบับไม่มีเนื้อหาของ layer ใด ไม่ต้องสร้าง section นั้นใน output
5. **Learning Chain Summary** — เขียนขึ้นใหม่โดย synthesize จากเนื้อหาในไฟล์ ไม่ใช่เพิ่มข้อมูลภายนอก

---

## ตัวอย่างการ Assign Layer

**ตัวอย่าง: เนื้อหาจาก DKA lecture**

```
สไลด์ต้นฉบับ (ปนกัน):
"Insulin deficiency → ↑ glucagon → lipolysis → ketone bodies (BHB, AcAc)
→ metabolic acidosis → Kussmaul breathing, fruity breath"

→ แยกเป็น:
  Layer 3 (Mechanism): Insulin deficiency → ↑ glucagon → lipolysis → ketone bodies → metabolic acidosis
  Layer 4 (Presentation): Kussmaul breathing, fruity breath [เกิดจากกลไกข้างบน]
```

```
สไลด์ต้นฉบับ:
"ให้ IV fluid 0.9% NSS 1L/hr ในชั่วโมงแรก ตาม ADA guideline 2024"

→ Layer 6 (Management): เนื้อหาทั้งก้อนนี้
```

---

## Checklist ก่อน Output

- [ ] ทุก section จากต้นฉบับถูก assign ลง layer แล้ว
- [ ] ไม่มีเนื้อหาตกหล่น (ตรวจด้วยการ scan หัวข้อเทียบกับต้นฉบับ)
- [ ] Layer ที่ไม่มีเนื้อหาถูก skip แล้ว ไม่มี section ว่าง
- [ ] Learning Chain Summary สะท้อน flow ของ topic นี้จริงๆ
- [ ] ชื่อไฟล์ output คือ `notes-resequenced.md`