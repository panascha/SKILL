# ⚕️ MCQ PDF Converter & Generator — Gemini Edition

เครื่องมือ Web-based สำหรับแปลงข้อสอบ PDF เป็น JSON และสร้างข้อสอบใหม่อัตโนมัติด้วย Google Gemini AI
ออกแบบมาสำหรับนักศึกษาแพทย์และอาจารย์ที่เตรียมสอบ National License (NL) และ USMLE

---

## 📋 สารบัญ

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Directory Structure](#-directory-structure)
- [Usage Guide](#-usage-guide)
  - [Convert Mode — แปลงข้อสอบเดิม](#convert-mode--แปลงข้อสอบเดิม)
  - [Generate Mode — ออกข้อสอบใหม่ด้วย AI](#generate-mode--ออกข้อสอบใหม่ด้วย-ai)
- [Output Format](#-output-format)
- [Prompt Customization](#-prompt-customization)
- [CategoryID System](#-categoryid-system)
- [Configuration Reference](#-configuration-reference)
- [Known Issues & Improvements](#-known-issues--improvements)
- [FAQ](#-faq)

---

## ✨ Features

| Feature | รายละเอียด |
|---|---|
| **PDF → JSON Conversion** | แปลง MCQ/Clinical Vignette จาก PDF เป็น JSON โครงสร้างพร้อมใช้ |
| **AI Question Generation** | ออกข้อสอบใหม่จากสไลด์บทเรียน ถอดสไตล์จากข้อสอบเก่า |
| **Thai-English Explanations** | คำอธิบายทุกข้อเป็นภาษาไทยผสม medical terminology |
| **Self-Healing JSON Parser** | กู้คืน JSON ที่ถูกตัดทอนโดยอัตโนมัติ |
| **Rate Limit Auto-Retry** | จัดการ 429/503 errors ด้วย progressive backoff |
| **Batch Processing** | แปลงหลาย PDF พร้อมกัน สะสมผลลัพธ์ใน `quizdata.js` เดียว |
| **Real-time Log Console** | ติดตามสถานะการประมวลผลแบบ live ผ่าน SSE polling |
| **ZIP Deliverables** | ดาวน์โหลดผลลัพธ์ครบชุดเป็น ZIP เดียว |

---

## 🔧 Requirements

```
Python >= 3.9
Flask
google-genai        # ใหม่ — ไม่ใช่ google-generativeai
PyMuPDF (fitz)      # สำหรับดึงรูปภาพจาก PDF
Pillow
```

> **หมายเหตุ:** ต้องการ Google AI Studio API Key จาก [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## 🚀 Installation

```bash
# 1. Clone หรือวางไฟล์โปรเจกต์
cd your-project-folder

# 2. ติดตั้ง dependencies
pip install google-genai flask pymupdf Pillow

# 3. รันเซิร์ฟเวอร์
python convert.py

# 4. เปิดเบราว์เซอร์
# http://localhost:8765
```

---

## ⚡ Quick Start

1. รัน `python convert.py`
2. เปิด `http://localhost:8765`
3. ใส่ **Gemini API Key**
4. วาง PDF ข้อสอบลงใน `input_pdfs/`
5. กดรีเฟรช → เลือกไฟล์ → กด **เริ่มประมวลผล**
6. ดาวน์โหลด ZIP จาก banner เมื่อเสร็จสิ้น

---

## 📂 Directory Structure

```
project/
├── convert.py                  # Main application
├── medical-quiz-converter.md   # Prompt rules สำหรับ Convert Mode (live-reload)
├── medical-ai-generator.md     # Prompt rules สำหรับ Generate Mode (live-reload)
│
├── input_pdfs/                 # วาง PDF ข้อสอบที่ต้องการแปลงที่นี่
├── input_lectures/             # วางสไลด์บทเรียน (PDF/MD/TXT) ที่นี่
├── input_old_exams/            # วางข้อสอบเก่าอ้างอิง (.js/.json) ที่นี่
│
└── output/
    ├── quizdata.js             # ไฟล์รวมสะสม (อัปเดตทุก batch)
    ├── <stem>/
    │   ├── <stem>.json         # JSON ผลลัพธ์รายไฟล์
    │   ├── <stem>.pdf          # สำเนา PDF ต้นฉบับ
    │   └── images/             # รูปภาพที่ดึงออกมาจาก PDF
    └── mcq_output_<ts>.zip     # ZIP deliverable ล่าสุด
```

---

## 📖 Usage Guide

### Convert Mode — แปลงข้อสอบเดิม

ใช้สำหรับแปลงไฟล์ PDF ข้อสอบที่มีอยู่แล้วเป็น JSON

**ขั้นตอน:**

1. วางไฟล์ PDF ลงในโฟลเดอร์ `input_pdfs/`
2. เลือก **📝 แปลงข้อสอบเดิม** (โหมด Convert)
3. กด **🔄 รีเฟรช** เพื่อโหลดรายชื่อไฟล์
4. เลือกไฟล์ที่ต้องการแปลง (เลือกหลายไฟล์ได้)
5. กรอก API Key และเลือก Model
6. ใส่ **Extra Prompt Instruction** เพื่อระบุหัวข้อวิชา หรือคำสั่งพิเศษ (ไม่บังคับ)
7. กด **เริ่มประมวลผล**

**ตัวอย่าง Extra Prompt Instruction:**
```
[วิชา]: CVS — Cardiovascular Physiology
[คำสั่ง]: ให้อธิบายกลไกยาในช้อ distractor ทุกตัวอย่างละเอียด
```

**ตั้งชื่อไฟล์ให้ระบบแยกหมวดหมู่ได้อัตโนมัติ:**
```
CVS_51MCQ1_Physiology.pdf       → CategoryID: CVS_51MCQ1
GI_50FMT2_Pathology.pdf         → CategoryID: GI_50FMT2
NS_51MCQ1_Neurology.pdf         → CategoryID: NS_51MCQ1
```

---

### Generate Mode — ออกข้อสอบใหม่ด้วย AI

ใช้สำหรับสร้างข้อสอบใหม่จากสไลด์บทเรียน โดยถอดสไตล์จากข้อสอบเก่า

**ขั้นตอน:**

1. เลือก **🧠 ออกข้อสอบใหม่ด้วย AI** (โหมด Generate)
2. อัปโหลดสไลด์บทเรียน (`.pdf`, `.md`, `.txt`) ผ่านปุ่ม **➕ อัปโหลด**
3. อัปโหลดข้อสอบเก่าอ้างอิง (`.js` หรือ `.json` ในฟอร์แมต `var quizdata`) ไม่บังคับ
4. เลือกสไลด์ที่ต้องการใช้ (เลือกหลายไฟล์ได้)
5. เลือกข้อสอบเก่าต้นแบบ 1 ชุด (ถ้ามี)
6. ตั้งจำนวนข้อสอบที่ต้องการ (ค่าเริ่มต้น: 35)
7. กด **เริ่มประมวลผล**

**ผลลัพธ์ Generate Mode:**
- `output/generated_<timestamp>/quizdata.js`
- `output/generated_<timestamp>/quizdata.json`
- `output/quizdata.js` (อัปเดต global file ด้วย)

---

## 📄 Output Format

### JSON รายไฟล์ (`<stem>.json`)

```json
{
  "meta": {
    "source": "CVS_51MCQ1.pdf",
    "categoryID": "CVS_51MCQ1",
    "converted": 42,
    "skipped_duplicates": 0,
    "completions_added": 2,
    "validation_warnings": 0,
    "categories_found": ["CVS_PHYSIO_Heart Failure", "CVS_PHARM_Antihypertensives"],
    "converted_at": "2025-06-01T14:30:00.000000"
  },
  "questions": [
    {
      "problem": "1. A 65-year-old man presents with...",
      "img": "",
      "choices": "ACE inhibitor///ARB///Beta-blocker///Diuretic///Digoxin",
      "answer": "ACE inhibitor",
      "select": "",
      "explain": "ผู้ป่วยรายนี้มีภาวะ HFrEF...",
      "category": ["CVS_51MCQ1", "CVS_PHARM_Antihypertensives"],
      "state": false
    }
  ]
}
```

### Combined quizdata.js

```js
// Auto-generated Combined MCQ Quiz Data
var quizdata = {
    "CVS_51MCQ1": [ /* questions array */ ],
    "GI_50FMT2":  [ /* questions array */ ]
};
```

> **โน้ต:** `quizdata.js` สะสมข้อมูลจากทุก batch โดยไม่ลบข้อมูลเก่า และ de-duplicate ด้วย `problem` text

---

## ✏️ Prompt Customization

ไฟล์ `.md` ทั้งสองรองรับ **live-reload** — แก้ไขได้โดยไม่ต้องรีสตาร์ทเซิร์ฟเวอร์

| ไฟล์ | ใช้สำหรับ |
|---|---|
| `medical-quiz-converter.md` | กติกาการแปลง PDF → JSON |
| `medical-ai-generator.md` | กติกาการออกข้อสอบใหม่ |

**ปรับแต่งที่นิยม:**

```markdown
# เพิ่มวิชาใหม่ใน known_subjects (ใน convert.py)
known_subjects = ["CVS", "GI", "HEMATO", "MS", "NS", "EN", "RENAL", "RESP"]

# เพิ่ม SubGroupSuffix ใหม่ใน medical-quiz-converter.md
* <SubGroupSuffix>: [ANA, BIOCHEM, PHYSIO, ..., EMERGENCY, GENETICS]
```

---

## 🏷️ CategoryID System

ระบบใช้ CategoryID 2 ระดับในทุกข้อสอบ:

```
category[0] = "CVS_51MCQ1"                          ← Default (SubjectCode_ExamGroup)
category[1] = "CVS_PHARM_Antihypertensive Drugs"    ← Standardized (SubjectCode_SubGroup_Topic)
```

**SubGroupSuffix ที่รองรับ:**

| Suffix | หมวดหมู่ |
|---|---|
| `ANA` | Anatomy, Histology, Embryology |
| `BIOCHEM` | Biochemistry, Molecular Biology |
| `PHYSIO` | Physiology, Mechanisms |
| `MICRO` | Microbiology, Virology, Immunology |
| `PARASITO` | Parasitology |
| `PATHO` | Pathology, Histopathology |
| `PHARM` | Pharmacology, Drug therapy |
| `RADIO` | Radiology, Imaging |
| `CLINICAL` | Clinical Medicine, Surgery, Management |

**วิธีตั้งชื่อไฟล์ให้ถูก detect อัตโนมัติ:**

```
<SubjectCode>_<YearExamType>[Number]_<TopicLabel>.pdf

ตัวอย่าง:
  CVS_51MCQ1_Cardiology.pdf
  GI_50FMT2_GastroPathology.pdf
  NS_51MCQ3_Neuropharmacology.pdf
  HEMATO_51MCQ1_Anemias.pdf
```

---

## ⚙️ Configuration Reference

### Model Selection

| Model | ใช้เมื่อ | max_tokens |
|---|---|---|
| `gemini-3.5-flash` | งานทั่วไป เร็ว ประหยัด (**แนะนำ**) | 65,536 |
| `gemini-3.1-pro` | ต้องการความแม่นยำสูง วิเคราะห์เชิงลึก | 65,536 |
| `gemini-3.1-flash-lite` | ประหยัด quota สูงสุด | 8,192 |
| `gemini-2.5-pro` | เสถียร ไม่ต้องการ feature ใหม่ | 65,536 |
| `gemini-2.5-flash` | เสถียร ทั่วไป | 8,192 |

### Rate Limit Management

ระบบมี 2 ชั้นป้องกัน:

1. **Proactive cooldown** — หน่วง 12 วินาทีระหว่างแต่ละไฟล์
2. **Auto-retry** — เมื่อเจอ 429/503 จะรอ `20 + 12×attempt` วินาที (สูงสุด 5 ครั้ง)

ปรับค่าได้ใน `convert.py`:

```python
cooldown_secs = 12      # หน่วงระหว่างไฟล์ (บรรทัดประมาณ 390)
initial_delay = 20      # delay ครั้งแรกเมื่อโดน rate limit
max_retries   = 5       # จำนวนครั้ง retry สูงสุด
```

### Inline vs Files API

ระบบเลือกช่องทางส่ง PDF อัตโนมัติตามขนาดไฟล์:

| ขนาดไฟล์ | ช่องทาง | เหตุผล |
|---|---|---|
| ≤ 20 MB | **Inline** | ประหยัด quota (ไม่ต้องเรียก upload/delete) |
| > 20 MB | **Files API** | จำเป็นสำหรับไฟล์ขนาดใหญ่ |

---

## 🐛 Known Issues & Improvements

### 🔴 ปัญหาที่ควรแก้ไข (Bugs)

**1. model name ใน UI ไม่ตรงกับ Gemini API จริง**

Model options ใน dropdown (`gemini-3.5-flash`, `gemini-3.1-pro`) เป็น placeholder ที่ยังไม่ verify กับ API จริง ควรตรวจสอบชื่อจาก [Google AI documentation](https://ai.google.dev/gemini-api/docs/models) และอัปเดตให้ตรง เช่น `gemini-2.5-flash`, `gemini-2.5-pro`

**2. Generate Mode ไม่ใช้ Inline PDF**

`run_generation()` อัปโหลดสไลด์ PDF ผ่าน Files API ทุกครั้ง แม้ขนาดจะน้อยกว่า 20 MB ควรนำ inline logic มาใช้เหมือน `process_pdf()` เพื่อประหยัด quota

```python
# แก้ไขใน run_generation() ช่วง "Bundle Lectures"
pdf_bytes = p.read_bytes()
if len(pdf_bytes) <= INLINE_SIZE_LIMIT:
    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
    contents.insert(0, pdf_part)
else:
    uploaded = client.files.upload(file=str(p))
    ...
```

**3. Generate Mode นับ `done` ไม่ถูกต้อง**

`job["done"]` ไม่ถูก increment ใน `run_generation()` ทำให้ header pill แสดง "ประมวลผลสำเร็จ 0 ไฟล์" แม้จะเสร็จแล้ว

```python
# เพิ่มใน run_generation() ก่อน job["running"] = False
job["done"] = 1
```

**4. `file_stem` ใช้ส่งตรงเข้า regex โดยไม่ escape**

ใน `parse_filename_metadata()` ชื่อไฟล์ที่มีอักขระพิเศษ regex อาจก่อให้เกิด `re.error` ควร sanitize ก่อน

```python
# เพิ่มก่อน re.search(...)
file_stem_safe = re.escape(file_stem)
```

**5. Race condition ใน `_jobs` dict**

`_jobs` เป็น shared state ที่อ่าน/เขียนจากหลาย thread โดยไม่มี lock ในบางส่วน ควรใช้ `threading.Lock()` ครอบ critical sections ทั้งหมด

---

### 🟡 ควรปรับปรุง (Improvements)

**6. Hard-coded `subject_title` ถูกลบออกจาก `/api/run`**

ฝั่ง Python รับค่า `subject_title` จาก request แต่ HTML UI ลบ input field นี้ออกไปแล้ว ผลคือส่งมาเป็น `""` เสมอ — ควรเพิ่ม field กลับเข้า UI หรือลบ logic ออกจาก backend ให้สอดคล้องกัน

**7. Error handling ใน `run_generation()` ไม่แสดงรายละเอียด JSON parse error**

ถ้า AI ส่ง response ที่ parse ไม่ได้ ระบบแสดงแค่ `"เกิดข้อผิดพลาด..."` ควร log raw response ด้วยเพื่อ debug

```python
except Exception as e:
    push_log(job, f"เกิดข้อผิดพลาด: {e}\n--- RAW (500 chars) ---\n{raw[:500]}", "error")
```

**8. `setInterval(loadFiles, 15000)` ทำงานแม้ไม่ได้ใช้งาน**

Polling ทุก 15 วินาทีทำให้มี network request สม่ำเสมอ ควรหยุดเมื่อ tab ไม่ active

```javascript
document.addEventListener('visibilitychange', () => {
    if (document.hidden) clearInterval(fileRefreshTimer);
    else fileRefreshTimer = setInterval(loadFiles, 15000);
});
```

**9. ไม่มี input validation ฝั่ง backend สำหรับ `num_questions`**

ถ้าส่ง `num_questions` เป็น string หรือ negative number จะ crash ควรเพิ่ม validation

```python
num_questions = max(1, min(200, int(data.get("num_questions", 35))))
```

**10. ขาด `Content-Security-Policy` header**

Flask app ที่ embed HTML ขนาดใหญ่ควรมี CSP header เพื่อความปลอดภัย

```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
```

**11. ไม่มี authentication บน `/api/download`**

ใครก็ตามที่รู้ `job_id` (ซึ่งเป็น timestamp ที่ predict ได้) สามารถดาวน์โหลดผลลัพธ์ได้ ควรเพิ่ม token หรือ session check ถ้า deploy บน server สาธารณะ

---

### 🟢 Feature Requests ที่น่าพิจารณา

| Feature | ประโยชน์ |
|---|---|
| **Preview modal** | ดูตัวอย่างข้อสอบก่อนดาวน์โหลด ใน UI |
| **Per-question retry** | retry เฉพาะข้อที่ parse ไม่ได้ แทนที่จะ fail ทั้งไฟล์ |
| **Subject mapping file** | ไฟล์ config แยกสำหรับ known_subjects และ SubGroupSuffix |
| **Duplicate detection cross-file** | ตรวจ duplicate ข้ามไฟล์ ไม่ใช่แค่ภายใน batch เดียว |
| **Export to ANKI format** | สร้าง `.apkg` สำหรับใช้กับ Anki flashcard |

---

## ❓ FAQ

**Q: ทำไม Gemini ตอบ JSON ไม่ครบ (truncated)?**

A: เกิดจาก token limit ลอง (1) ลดจำนวน PDF ต่อ batch (2) เปลี่ยนเป็น `gemini-2.5-pro` ที่มี context window ใหญ่กว่า (3) ระบบจะพยายาม self-heal ด้วย `extract_valid_questions_from_broken_json()` อัตโนมัติ

**Q: อัปโหลดสไลด์แล้วไม่เห็นในรายการ?**

A: กดปุ่ม **🔄 รีเฟรช** ใน Generate Mode และตรวจสอบว่านามสกุลไฟล์เป็น `.pdf`, `.md` หรือ `.txt`

**Q: `quizdata.js` หายหรือข้อมูลหาย?**

A: ไฟล์ `quizdata.js` ถูก overwrite ทุกครั้งที่ batch เสร็จ แต่จะโหลดข้อมูลเก่ากลับมารวมก่อนเสมอ ถ้าไฟล์ corrupt ให้ลบ `output/quizdata.js` แล้วรันใหม่

**Q: ต้องการแก้ภาษาในคำอธิบาย explain?**

A: แก้ไขที่ `medical-quiz-converter.md` ในส่วน rule ที่ 6 (explain) ไม่ต้องรีสตาร์ทเซิร์ฟเวอร์

**Q: รัน batch ใหญ่ (>10 ไฟล์) แล้วโดน rate limit?**

A: เพิ่ม `cooldown_secs` ใน `convert.py` จาก 12 เป็น 30 วินาที หรือแบ่งรันเป็น batch ย่อย

---

## 📜 License

ใช้งานภายในเพื่อการศึกษาและการเตรียมสอบ National License เท่านั้น