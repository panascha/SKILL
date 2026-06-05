---
name: lecture-crystallizer
description: >
  ตัวตกผลึกเนื้อหาบทเรียนแพทย์เพื่อการจดจำและนำไปใช้จริง (Clinical Crystallization & Active Recall Enhancer)
  ใช้ skill นี้ทุกครั้งที่ผู้ใช้ต้องการ: (1) แปลงโน้ตสรุปบทเรียนแพทย์ให้เป็น High-Yield study material,
  (2) สร้าง mnemonics หรือ visual analogy สำหรับเนื้อหาทางการแพทย์, (3) สรุป pathophysiology ในรูปแบบ
  cause-and-effect chain, (4) แปลงความรู้ทฤษฎีให้เป็น clinical action plan, (5) ทำ active recall material
  จากสไลด์หรือโน้ตแพทย์ใดก็ตาม, (6) แปลง LaTeX math expressions ($...$, $$...$$) ในโน้ตแพทย์ให้เป็น
  Unicode plain text ที่อ่านได้ใน Notion หรือ Markdown viewer ทั่วไป แม้ผู้ใช้จะไม่ได้พูดถึง "crystallize"
  โดยตรง แต่ถ้าพูดถึงการสรุปบทเรียนแพทย์, High-Yield notes, การเตรียมสอบ NL/USMLE, แก้ LaTeX ในโน้ต
  แพทย์, หรือบอกว่า Notion แสดง math symbols ไม่ถูกต้อง ให้ trigger skill นี้เสมอ
---

# Lecture Crystallizer

สกิลสำหรับแปรรูปโน้ตบทเรียนแพทย์ให้เป็น High-Yield study material ในรูปแบบ 4 แกนหลัก

---

## 📥 Input ที่รองรับ

รับ input ได้หลายรูปแบบ — ไม่จำเป็นต้องเป็นชื่อไฟล์ใดชื่อหนึ่ง:
- ไฟล์ `.md` หรือ `.txt` ที่ผู้ใช้แนบมา (เช่น `notes-synthesized.md`, `lecture-notes.md`, ฯลฯ)
- ข้อความโน้ตที่วางมาตรงๆ ใน conversation
- หัวข้อบทเรียนที่ต้องการให้สร้าง crystallized notes จากความรู้ที่มีอยู่

> **ถ้าผู้ใช้ไม่ได้ระบุ input ชัดเจน:** ถามหาเนื้อหาหรือหัวข้อที่ต้องการก่อน อย่าสร้างเนื้อหาขึ้นมาเอง

---

## 🧹 Step 0: LaTeX Pre-processing (ก่อน Crystallize)

**ทำก่อนเสมอ** — ถ้า input มี LaTeX syntax (`$...$`, `$$...$$`) ให้แปลงเป็น Unicode plain text ทั้งหมดก่อน แล้วค่อย crystallize

### กฎหลัก
> แตะ **เฉพาะ LaTeX เท่านั้น** — ทุกอักขระนอก delimiter `$...$` / `$$...$$` ต้องคงเดิมทุก byte

### Conversion Reference

**Superscripts (`^`)**
| LaTeX | Unicode |
|---|---|
| `$x^2$`, `$x^3$` | `x²`, `x³` |
| `$10^6$` | `10⁶` |
| `$2^{\text{nd}}$` | `2nd` |
| `$CO_2^{2-}$` | `CO₂²⁻` |

Map: `0=⁰ 1=¹ 2=² 3=³ 4=⁴ 5=⁵ 6=⁶ 7=⁷ 8=⁸ 9=⁹ n=ⁿ +=⁺ -=⁻`

**Subscripts (`_`)**
| LaTeX | Unicode |
|---|---|
| `$O_2$`, `$CO_2$`, `$H_2O$` | `O₂`, `CO₂`, `H₂O` |
| `$Fe^{2+}$` | `Fe²⁺` |

Map: `0=₀ 1=₁ 2=₂ 3=₃ 4=₄ 5=₅ 6=₆ 7=₇ 8=₈ 9=₉`

**Math Symbols**
| LaTeX | Unicode |
|---|---|
| `\uparrow` / `\downarrow` | `↑` / `↓` |
| `\rightarrow` / `\leftarrow` | `→` / `←` |
| `\pm`, `\times`, `\div` | `±`, `×`, `÷` |
| `\geq`, `\leq`, `\neq`, `\approx` | `≥`, `≤`, `≠`, `≈` |
| `\alpha`, `\beta`, `\gamma`, `\delta`, `\Delta` | `α`, `β`, `γ`, `δ`, `Δ` |
| `\mu`, `\sigma`, `\infty`, `\cdot` | `μ`, `σ`, `∞`, `·` |
| `\text{...}` | ตัด command คงข้อความ inner ไว้ |

**Fractions**
| LaTeX | Plain |
|---|---|
| `$\frac{1}{2}$`, `$\frac{1}{4}$`, `$\frac{3}{4}$` | `½`, `¼`, `¾` |
| `$\frac{a}{b}$` (อื่นๆ) | `a/b` |

Map เพิ่มเติม: `1/3=⅓  2/3=⅔  1/8=⅛  3/8=⅜  5/8=⅝  7/8=⅞`

**Block equations `$$...$$`** → แปลงเป็น single-line Unicode แล้วลบ delimiter ทิ้ง
- `$$\sum_{i=1}^{n} x_i$$` → `Σᵢ₌₁ⁿ xᵢ`

### Algorithm
1. Scan `$$...$$` ก่อน (block) → แปลง
2. Scan `$...$` (inline) → แปลง
3. ถ้าแปลงไม่ได้: strip delimiters + LaTeX commands, ใช้ ASCII fallback + marker `[?]`
4. **ถ้า input ไม่มี LaTeX เลย** → ข้าม Step 0 ทันที ไม่ต้องรายงาน

### Output ของ Step 0
- ถ้ามีการแปลง: แสดง **Conversion Summary** ย่อๆ (ตาราง ก่อน/หลัง/จำนวน) ก่อน crystallized notes
- ถ้ามี `[?]` markers: รายการแยกพร้อม note ให้ผู้ใช้ตรวจสอบ

---

## ⚙️ โครงสร้าง 4 แกนหลัก (The 4 Core Pillars)

วิเคราะห์แต่ละหัวข้อหลัก (Topic/Section) แล้วสังเคราะห์ครบทั้ง 4 แกน:


### แกนที่ 1 🎯 ประเด็นเด่นต้องจำ (High-Yield Focus Points)
- เน้น **Key Diagnostic criteria** และ **Clinical decision points**
- ระบุ **Exam traps** — จุดที่ข้อสอบ NL/USMLE มักใช้เป็น distractor
- ระบุ **Classic vs. Atypical presentations** ถ้ามี

### แกนที่ 2 🧠 สายโซ่ความเป็นเหตุเป็นผล (Cause-and-Effect Chain)
- เขียนในรูปแบบ **mechanistic chain**: `A → B → C → Clinical manifestation`
- ใช้ลูกศร (`→`, `↑`, `↓`) แทนการบรรยายยาว
- แต่ละ chain ควรครอบคลุม: trigger → pathophysiology → symptom/sign

### แกนที่ 3 💡 คลังเทคนิคช่วยจำ (Memory Matrix)
- สร้างหรือใช้ **Mnemonic** ที่มีอยู่แล้วในทางการแพทย์ (EN หรือ TH)
- เพิ่ม **Visual analogy** — อุปมาอุปไมยที่ทำให้เห็นภาพกลไกได้ง่ายขึ้น
- ถ้าไม่มี mnemonic ที่เหมาะสม: สร้างใหม่ให้จำได้จริง แล้วระบุว่าเป็น "custom"

### แกนที่ 4 🏥 แผนปฏิบัติในหน้างานจริง (Clinical Action Plan)
- **PE (Physical Examination):** ตรวจอะไร ที่ไหน อย่างไร
- **Red Flags:** อาการใดที่ต้องรีบแก้ไขหรือ refer ด่วน
- **Initial Plan:** ลำดับการสั่งตรวจ/รักษาเบื้องต้น (Ix → Dx → Rx)

> **ถ้าเนื้อหาบางส่วนไม่มีข้อมูลเพียงพอสำหรับแกนใดแกนหนึ่ง:** เขียน `> ⚠️ ไม่มีข้อมูลเพียงพอสำหรับแกนนี้ในเนื้อหาที่ให้มา` แทนการสร้างข้อมูลขึ้นเอง

---

## 📄 Format ของ Output (`notes-crystallized.md`)

```markdown
# 💎 Crystallized Notes: [ชื่อวิชา/หัวข้อรวม]
> 📅 Source: [ชื่อไฟล์ต้นฉบับ หรือ "จาก conversation"] | ตกผลึก: [วันที่ถ้ามี]

---

## 💎 [ชื่อหัวข้อหลัก]

### 1. 🧠 สายโซ่ความเป็นเหตุเป็นผล
- **[ชื่อกลไก]:** [trigger] → [pathophysiology] → [clinical manifestation]
- **[ชื่อกลไก]:** [สาเหตุ] → [การปรับตัว/remodeling] → [ผลระยะยาว]

### 2. 🎯 ประเด็นเด่นต้องจำ
- 📌 **[ประเด็น]:** [คำอธิบายสั้น + ความสำคัญ]
- 📌 **Exam Trap:** [จุดที่มักออกสอบหรือ distractor ที่ควรระวัง]

### 3. 💡 คลังเทคนิคช่วยจำ
- 🔑 **Mnemonic:** `[คำย่อ]` → [แจกแจงแต่ละตัว]
- 👁️ **Visual/Analogy:** [อุปมาอุปไมย เช่น "เหมือน... เพราะ..."]

### 4. 🏥 แผนปฏิบัติในหน้างานจริง
- 🩺 **PE:** [วิธีตรวจ + ตำแหน่ง + สิ่งที่คาดว่าจะพบ]
- 🚨 **Red Flags:** [อาการที่พบแล้วต้องรีบทำ action]
- 📝 **Initial Plan:** [Ix ก่อน → แล้วจึง Dx/Rx]

---
```

ทำซ้ำ block นี้สำหรับทุก section ใน notes ต้นฉบับ ตามลำดับที่ปรากฏ

---

## 📏 Scope และความยาว Output

| ขนาด Input | Output โดยประมาณ |
|---|---|
| 1 หัวข้อ (< 1 หน้า) | 1 block ~200–350 คำ |
| 3–5 หัวข้อ | 3–5 blocks ~1,000–1,800 คำ |
| บทเรียนเต็ม (> 10 หัวข้อ) | แจ้งผู้ใช้ว่าจะใช้เวลา แล้ว process ทีละ section |

> สำหรับ input ขนาดใหญ่: ถามผู้ใช้ว่าต้องการ crystallize ทั้งหมดหรือเฉพาะ section ที่สนใจ

---

## 🚫 ข้อจำกัดสำคัญ

- **ภาษา:** ศัพท์แพทย์เฉพาะทางและตัวย่อ — คงภาษาอังกฤษตามต้นฉบับ; คำอธิบาย, analogy, และ action plan — ใช้ภาษาไทยกระชับ
- **LaTeX Pre-processing:** แปลง LaTeX → Unicode ก่อนเสมอ; ห้ามให้ `$...$` หลงเหลือใน output; ถ้าแปลงไม่ได้ใช้ `[?]` แทน hallucinate
- **ห้ามสร้างข้อมูลเอง:** ถ้าเนื้อหาต้นฉบับไม่มีข้อมูลเพียงพอ ให้ระบุชัดเจน อย่า hallucinate ข้อมูลทางการแพทย์
- **ห้ามบรรยายยาว:** ใช้ `→`, `↑`, `↓`, `≥`, `≤`, bullet points แทนประโยคยาว
- **ความถูกต้องมาก่อน:** ถ้า mnemonic ที่มีอยู่ในวงการแพทย์ใช้ได้ — ใช้ mnemonic นั้น; อย่าสร้างใหม่จนทำให้สับสนกับของเดิม