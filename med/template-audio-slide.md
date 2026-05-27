---
name: audio-overview-medical
description: >
  สร้าง Audio Overview Script และลำดับการพูดสำหรับ Medical Podcast สไตล์ NotebookLM
  โดยมีผู้พูด 2 คน (Host + Expert) ให้สอดคล้องกับ Slide Overview ที่มีอยู่
  ใช้รูปแบบการพูดแบบ 9arm หรือ Doctor Tany — เป็นกันเอง ชัดเจน มีอารมณ์ขัน แต่ยังคงความน่าเชื่อถือทางการแพทย์

  ใช้ skill นี้เมื่อ:
  - ผู้ใช้ต้องการสร้าง script พูด podcast จาก slide หรือ markdown เนื้อหาทางการแพทย์
  - ผู้ใช้พูดถึง "audio overview", "podcast script", "ลำดับการพูด", "talking points", "สคริปต์พูด"
  - ผู้ใช้ต้องการแปลง slide deck หรือ markdown ให้เป็น conversational audio content
  - มีการกล่าวถึง NotebookLM, 9arm, Doctor Tany, หรือ medical podcast
  - ผู้ใช้ต้องการ "audio overview" คู่กับ slide ที่มีอยู่
---

# Audio Overview – Medical Podcast Skill

สร้าง script การพูดสำหรับ Medical Podcast สไตล์ NotebookLM (2 hosts) ที่สอดคล้องกับ slide deck

---

## ภาพรวม Workflow

```
Input (Markdown / Slide outline)
        ↓
1. วิเคราะห์โครงสร้าง slide และ key messages
        ↓
2. ออกแบบ Episode Arc (opening → core → close)
        ↓
3. เขียน Talking Points ต่อ slide/section
        ↓
4. เขียน Full Script (Host ↔ Expert)
        ↓
Output: Markdown สรุปลำดับพร้อม talking points + full script
```

---

## Personas ของผู้พูด

### 🎙️ Host (ผู้ดำเนินรายการ)
- บทบาท: ถามในมุมของคนทั่วไปหรือนักศึกษาแพทย์
- สไตล์: เป็นกันเอง กระตุ้นให้ Expert อธิบาย บางครั้งตลกขบขัน
- ชื่อตัวอย่าง: "ณัฐ" หรือ "คุณพิธีกร"
- ตัวอย่างประโยค: *"อ้าว แล้วถ้าคนไข้มาแบบนี้ เราจะรู้ได้ยังไงครับว่าเป็นอันนี้จริงๆ?"*

### 🩺 Expert (ผู้เชี่ยวชาญ)
- บทบาท: แพทย์ผู้เชี่ยวชาญ อธิบายเชิงลึกแต่เข้าใจง่าย
- สไตล์: มั่นใจ ใช้ analogy ดีๆ อธิบายกลไกชัด ไม่ใช้ศัพท์เทคนิคโดยไม่ขยาย
- ตัวอย่างชื่อ: "หมอต้น" หรือ "อาจารย์"
- ตัวอย่างประโยค: *"ใช่เลย พูดง่ายๆ ก็คือร่างกายมัน overreact ครับ เหมือน firewall ที่ sensitive เกินไป block ทุกอย่างเลย"*

---

## Voice Style Guide (สไตล์การพูด)

อิงจากสไตล์ **9arm** และ **Doctor Tany**:

| องค์ประกอบ | แนวทาง |
|---|---|
| ภาษา | ไทยผสมอังกฤษ (medical terms เป็นอังกฤษ, อธิบายเป็นไทย) |
| โทน | เป็นกันเอง ไม่เป็นทางการเกินไป แต่ยังดูน่าเชื่อถือ |
| Analogy | ใช้ analogy ชีวิตประจำวันอธิบาย mechanism เสมอ |
| Pace | สลับ Host ถาม / Expert ตอบ ไม่เกิน 3-4 ประโยคต่อเทิร์น |
| Humor | เบาๆ ไม่ล้อเลียนคนไข้ ยิงมุกเกี่ยวกับสถานการณ์ทางการแพทย์ได้ |
| Clinical pearls | Expert แทรก pearl สั้นๆ เป็นระยะ เช่น *"จำไว้เลยนะ..."* |
| Recap | ทุก section ใหญ่ Host สรุปสั้น 1-2 ประโยคก่อนไปต่อ |

---

## โครงสร้าง Output

### ส่วนที่ 1: Episode Map (สรุปลำดับ)

```markdown
## 🗺️ Episode Map

| ลำดับ | Slide/Section | ผู้พูดหลัก | Talking Points | เวลาประมาณ |
|---|---|---|---|---|
| 1 | Hook / Opening | Host | ... | ~1 min |
| 2 | Background | Expert | ... | ~2 min |
...
```

### ส่วนที่ 2: Full Podcast Script

```markdown
## 🎙️ Full Script

### [00:00] Opening Hook

**Host (ณัฐ):** ...
**Expert (หมอต้น):** ...

### [02:00] Section: [ชื่อ section]
...
```

---

## ขั้นตอนการสร้าง Script

### Step 1: วิเคราะห์ Input

อ่าน markdown/slide outline แล้วระบุ:
- **Main message** ของ episode คืออะไร (1 ประโยค)
- **Key sections** มีกี่ส่วน อะไรบ้าง
- **Clinical pearls** หรือ key takeaways ที่ต้องเน้น
- **Slide ที่ซับซ้อน** ที่ต้องใช้ analogy ช่วย

### Step 2: ออกแบบ Episode Arc

```
Opening Hook (30-60 วิ)
  → ตั้งคำถามหรือ scenario ที่น่าสนใจ
  → บอกว่า episode นี้จะตอบอะไร

Body Sections (สอดคล้องกับ slides)
  → แต่ละ section มี Host intro + Expert deep dive + Host recap

Clinical Pearl Moments
  → แทรกใน body ตอนที่ Expert อธิบาย concept สำคัญ

Closing Summary (1-2 นาที)
  → Host สรุป key points 3-5 ข้อ
  → Expert เพิ่ม pearl สุดท้าย
  → Call to action (ถ้ามี)
```

### Step 3: เขียน Talking Points ต่อ Section

สำหรับแต่ละ section ให้ระบุ:
- **Host opens with**: คำถาม หรือ scenario
- **Expert covers**: จุดสำคัญ 2-3 จุด
- **Analogy to use**: (ถ้ามี)
- **Pearl moment**: ประโยคจำง่าย
- **Host recap**: 1 ประโยคสรุป

### Step 4: เขียน Full Script

- สลับ Host ↔ Expert ทุก 2-4 ประโยค
- Expert ไม่พูดยาวเกิน 5 ประโยคต่อเทิร์น
- Host ถามหรือ react เสมอ ไม่เงียบเฉย
- ใส่ timestamp โดยประมาณ ทุก section
- ใส่ `[หัวเราะ]` หรือ `[เน้น]` เพื่อบอก delivery hint

---

## ตัวอย่าง Script Fragment

```markdown
### [03:30] Section: Pathophysiology

**Host (ณัฐ):** โอเค แล้วตอนที่มันเกิดขึ้น ร่างกายมัน... ทำอะไรอยู่ครับ? ในระดับ cell น่ะ

**Expert (หมอต้น):** ดีเลยที่ถาม — จริงๆ มันเริ่มที่ macrophage ก่อนเลยครับ 
พอ pathogen เข้ามา มันจะ activate แล้วปล่อย cytokine ออกมาเต็มไปหมด 
ลองนึกภาพว่ามันเหมือนกด alarm ในห้างครับ แล้วทุกคนวิ่งออกมาพร้อมกัน

**Host (ณัฐ):** [หัวเราะ] แล้วก็วุ่นวายไปทั้งห้างเลย

**Expert (หมอต้น):** ใช่เลย! และถ้า alarm ดังนานเกินไป — 
นั่นแหละคือ cytokine storm ครับ จำไว้เลยนะ: 
*"ไม่ใช่ virus ที่ฆ่าคนไข้ แต่เป็น immune response ของตัวเองที่รุนแรงเกินไป"*

**Host (ณัฐ):** โห... โอเค นั่นเป็น key point มากเลยครับ 
งั้นสรุปคือ เราต้องไปหยุด immune response นั้น ไม่ใช่แค่ฆ่า virus ใช่ไหมครับ?

**Expert (หมอต้น):** ถูกต้องครับ นั่นคือ rationale ของการใช้ steroid ในบางกรณีเลย
```

---

## การจัดการ Slide แต่ละประเภท

| ประเภท Slide | วิธีแปลงเป็น Audio |
|---|---|
| **Title/Overview** | Host แนะนำ topic + Expert preview ว่าจะเรียนรู้อะไร |
| **Pathophysiology** | Expert ใช้ analogy + diagram เป็นคำพูด |
| **Diagnosis criteria** | Expert อธิบาย + Host ถามกรณีขอบเขต ("แล้วถ้า...?") |
| **Management/Treatment** | Expert เดิน step-by-step, Host ถามเหตุผล |
| **Complications** | Host แสดงความตกใจ, Expert อธิบายกลไก |
| **Summary/Pearls** | Host สรุป, Expert เพิ่มเติมและปิดด้วย pearl |

---

## Output Format สุดท้าย

ส่ง output เป็น Markdown ไฟล์เดียว ประกอบด้วย:

1. **Episode Info** (หัวข้อ, เวลารวมโดยประมาณ, กลุ่มเป้าหมาย)
2. **Episode Map** (ตารางลำดับ)
3. **Full Script** (พร้อม timestamp และ delivery hints)
4. **Clinical Pearls Summary** (รวม pearls ทั้งหมดของ episode)

บันทึกเป็น `audio-overview-[topic].md` ใน `/mnt/user-data/outputs/`