# ⚕️ MCQ PDF → JSON Converter
### Gemini Live-Reload Edition

เครื่องมือแปลงไฟล์ข้อสอบแพทย์แบบเลือกตอบ (MCQs / Clinical Vignettes) จาก PDF เป็นโครงสร้างข้อมูล JSON และ JavaScript Array แบบอัตโนมัติ สำหรับใช้งานในระบบ **MDKKU Manager Center** โดยขับเคลื่อนด้วย Google Gemini API

---

## 📂 โครงสร้างโปรเจกต์

```text
mcq_pipeline/
├── convert.py                  ← เซิร์ฟเวอร์หลักและ Web UI (รันไฟล์นี้)
├── medical-quiz-converter.md   ← กฎและ Prompt ที่ใช้สั่ง Gemini (แก้ไขได้โดยไม่ต้อง Restart)
├── README.md                   ← คู่มือนี้
├── input_pdfs/                 ← วางไฟล์ PDF ข้อสอบที่ต้องการแปลงไว้ที่นี่
└── output/                     ← ผลลัพธ์ทั้งหมดจะถูกสร้างที่นี่โดยอัตโนมัติ
```

---

## ✨ ฟีเจอร์หลัก

| ฟีเจอร์ | รายละเอียด |
|---|---|
| **Web UI แบบ Batch** | เลือกและแปลง PDF หลายไฟล์พร้อมกันผ่านหน้าเว็บ พร้อม Progress และ Log แบบ Real-time |
| **Live-Reload Prompt** | แก้ไข `medical-quiz-converter.md` แล้วกดแปลงได้เลย ไม่ต้อง Restart Server |
| **Image Extraction** | ดึงและ Render รูปภาพที่ฝังใน PDF ออกมาอัตโนมัติ เพื่อใช้เป็นส่วนประกอบในข้อสอบ |
| **Self-Healing Recovery** | กู้คืนโครงสร้างข้อสอบที่เสียหายจากการถูกตัดคำ (Truncation) ได้อัตโนมัติ |
| **Output พร้อมใช้** | ได้ทั้ง `.json` ที่คัดลอกใส่ระบบ MDKKU ได้ทันที |

---

## 🛠️ การติดตั้ง

### 1. ติดตั้ง Python Dependencies

```bash
pip install pymupdf pypdfium2 Pillow pdfplumber
```

> **หมายเหตุ:** ระบบจะพยายามใช้ไลบรารี **PyMuPDF (`fitz`)** ก่อนสำหรับการแยกรูปภาพที่ฝังอยู่ใน PDF หากไม่พบรูปหรือนำเข้าไลบรารีไม่ได้ จะสลับไปใช้ **`pypdfium2`** ในการ Render รูปภาพจากแต่ละหน้าแทนโดยอัตโนมัติ

### 2. วางไฟล์ PDF ข้อสอบ

สร้างโฟลเดอร์ `input_pdfs/` ในไดเรกทอรีเดียวกับ `convert.py` แล้วนำไฟล์ PDF ไปวางไว้:

```text
input_pdfs/
├── MCQ_Anatomy_2024.pdf
├── MCQ_Physiology.pdf
└── ClinicalVignettes_Set1.pdf
```

---

## ⚡ วิธีใช้งาน

### 1. เปิดเซิร์ฟเวอร์

```bash
python3 convert.py
```

### 2. เปิดหน้าเว็บ

```
http://localhost:8765
```

### 3. ขั้นตอนการแปลง

1. **กรอก Gemini API Key** — รับได้ฟรีที่ [Google AI Studio](https://aistudio.google.com/)
2. **เลือกไฟล์ PDF** ที่ต้องการแปลงจากรายการด้านซ้าย (กด 🔄 หากเพิ่งนำไฟล์ใหม่เข้ามา)
3. **กดปุ่ม "เริ่มแปลง"** แล้วติดตาม Log และ Progress ได้แบบ Real-time

---

## 📤 ผลลัพธ์ที่ได้รับ

ไฟล์ทั้งหมดจะถูกสร้างใน `output/<ชื่อไฟล์>/` โดยอัตโนมัติ:

```text
output/MCQ_Anatomy_2024/
├── MCQ_Anatomy_2024.json            ← โครงสร้าง JSON หลัก
├── quizdata.js                      ← JavaScript Array พร้อมใช้งาน
└── images/
    ├── img-001.png                  ← รูปภาพที่ฝังใน PDF (สกัดด้วย PyMuPDF)
    ├── img-002.png
    └── page_001_render.png          ← ภาพ Render จากแต่ละหน้า (ด้วย pypdfium2)
```

### รูปแบบข้อมูลใน `quizdata.js`

```javascript
var quizdata = [
  {
    "problem": "1. ข้อใดต่อไปนี้เป็นการรักษาที่เหมาะสมที่สุดสำหรับ...",
    "img": "",
    "choices": "ChoiceA///ChoiceB///ChoiceC///ChoiceD///ChoiceE",
    "answer": "ChoiceA",
    "select": "",
    "explain": "Clinical reasoning อธิบายเหตุผลของคำตอบ...",
    "state": false,
    "category": ["Default_CategoryID", "Standardized_CategoryID"]
  }
  // ...
];
```

> **หมายเหตุ:** `Standardized_CategoryID` จะอยู่ในรูปแบบ `<SubjectCode>_<SubGroup>_<TopicLabel>` เสมอ คำว่า `BY`, `AI`, หรือ `BY_AI` จะถูกกรองออกจาก ID หมวดหมู่โดยอัตโนมัติ

---

## 🔧 การปรับแต่ง Prompt

แก้ไขกฎการแปลงและแนวทางวิเคราะห์ทางการแพทย์ได้ที่ไฟล์ `medical-quiz-converter.md` ระบบจะโหลดกฎใหม่ทุกครั้งที่กดปุ่มเริ่มแปลง **โดยไม่ต้อง Restart Server**

---

## 🐛 การแก้ไขปัญหาเบื้องต้น

| ปัญหา | วิธีแก้ไข |
|---|---|
| ไม่พบไฟล์ PDF ในรายการ | กดปุ่ม 🔄 เพื่อรีเฟรชรายการไฟล์ |
| API Key ไม่ถูกต้อง | ตรวจสอบ Key ที่ [AI Studio](https://aistudio.google.com/) และแน่ใจว่าเปิดใช้งาน Gemini API แล้ว |
| Parse JSON ล้มเหลว | ตรวจสอบ Log บนหน้าเว็บแบบ Real-time หรือปรับ Prompt ใน `medical-quiz-converter.md` ระบบมีกลไก Self-Healing Recovery ที่จะพยายามกู้คืนข้อสอบจาก Response ที่เสียหายโดยอัตโนมัติ |
| รูปภาพไม่ครบหรือไม่พบ | ตรวจสอบว่าติดตั้ง `pymupdf` ครบถ้วนแล้ว (`pip install pymupdf`) หากยังไม่พบรูป ระบบจะสลับไป Render ด้วย `pypdfium2` โดยอัตโนมัติ |
| Token เกินขีดจำกัด | ระบบจำกัด Token อัตโนมัติตามรุ่นโมเดล: รุ่น Pro และ 3.5 ได้สูงสุด 65,536 tokens ส่วนรุ่นอื่น ๆ รวมถึง Flash-lite ได้ 8,192 tokens |