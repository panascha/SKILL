# 🏥 Lecture Pipeline

ระบบประมวลผลโน้ตบทเรียนแพทย์อัตโนมัติผ่าน Gemini API
อัพโหลดสไลด์ PDF กดรันครั้งเดียว — ได้ครบทุกขั้นตอน

---

## 📁 โครงสร้างโฟลเดอร์

```
lecture-pipeline/
├── app.py                          ← Flask application (ตัวหลัก)
├── requirements.txt                ← Python dependencies
├── README.md                       ← ไฟล์นี้
└── prompts/                        ← ไฟล์ prompt ทั้งหมด (ต้องวางเองก่อนรัน)
    ├── slide-to-markdown-gemini.md
    ├── lecture-synthesizer.md
    ├── slide-enrich.md
    ├── lecture-crystallizer.md
    └── curriculum-tracker.md
```

> **หมายเหตุ:** โฟลเดอร์ `output/` จะถูกสร้างอัตโนมัติเมื่อรันครั้งแรก

---

## ⚙️ การติดตั้ง

### 1. ติดตั้ง Python dependencies

```bash
pip install -r requirements.txt
```

### 2. วาง prompt files

คัดลอกไฟล์ `.md` ทั้ง 5 ไฟล์ไปไว้ในโฟลเดอร์ `prompts/`:

| ไฟล์ | หน้าที่ |
|------|--------|
| `slide-to-markdown-gemini.md` | แปลง PDF สไลด์ → Markdown |
| `lecture-synthesizer.md` | สังเคราะห์ transcript + slide notes |
| `slide-enrich.md` | เพิ่มกลไกทางการแพทย์ |
| `lecture-crystallizer.md` | ตกผลึกเนื้อหาสำหรับจดจำ |
| `curriculum-tracker.md` | อัปเดต Curriculum Map |

### 3. รัน

```bash
python app.py
```

เปิดเบราว์เซอร์ที่ **http://localhost:5000**

---

## 🔑 รับ API Key

1. ไปที่ [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. คลิก **Create API key**
3. คัดลอก key ไปวางในหน้าเว็บตอนรัน

---

## 🔄 Pipeline ทั้งหมด

```
PDF Slide ──────────────────────────────────────────────► lecture-markdown.md
                                                               │
transcript.txt (optional) ────────────────────────────► lecture-transcribe.md
                                                               │
                                                               ▼
                                              ┌─── slide-enrich ────────────────► lecture-enrich.md
                                              │                                        │
                                              └─── lecture-crystallizer ───────► lecture-summary.md
                                                                                       │
Curriculum_Map.md (optional) ────────── curriculum-tracker ────────► Curriculum_Map_updated.md
```

| ขั้นตอน | Input | Output | ไฟล์ |
|---------|-------|--------|------|
| 1 | PDF Slide | Markdown notes | `lecture-markdown.md` |
| 2 *(optional)* | Transcript + Slide notes | Synthesized notes | `lecture-transcribe.md` |
| 3 | Enriched notes | Medical mechanism added | `lecture-enrich.md` |
| 4 | Enriched notes | High-yield study material | `lecture-summary.md` |
| 5 *(optional)* | Enrich + Curriculum Map | Updated map | `Curriculum_Map_updated.md` |
| 6 | ทุกไฟล์ | ZIP ดาวน์โหลด | `[ชื่อไฟล์]_[timestamp].zip` |

---

## 📂 Output

ทุกครั้งที่รัน ระบบจะสร้างโฟลเดอร์ใหม่อัตโนมัติใน `output/`:

```
output/
└── ชื่อสไลด์_20250527_143022/
    ├── lecture-markdown.md
    ├── lecture-transcribe.md        ← มีถ้าใส่ transcript
    ├── lecture-enrich.md
    ├── lecture-summary.md
    └── Curriculum_Map_updated.md    ← มีถ้าใส่ Curriculum Map
```

พร้อม ZIP ให้ดาวน์โหลดจากหน้าเว็บทันที

---

## 🤖 Model ที่รองรับ

| Model | ความเร็ว | คุณภาพ | แนะนำสำหรับ |
|-------|---------|--------|------------|
| `gemini-2.0-flash` | ⚡⚡⚡ เร็ว | ดี | ใช้งานทั่วไป **(แนะนำ)** |
| `gemini-2.5-flash` | ⚡⚡ ปานกลาง | ดีมาก | ต้องการคุณภาพสูงขึ้น |
| `gemini-1.5-pro` | ⚡ ช้า | สูงสุด | เนื้อหาซับซ้อนมาก |

---

## 🚨 แก้ปัญหาเบื้องต้น

**`FileNotFoundError: Prompt file not found`**
→ ตรวจสอบว่าไฟล์ `.md` ทั้ง 5 อยู่ในโฟลเดอร์ `prompts/` ครบแล้ว

**`Invalid API Key`**
→ ตรวจสอบ key ที่ [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) และลอง generate ใหม่

**Pipeline หยุดกลางทาง**
→ ดู error message ในหน้าเว็บ หรือดู terminal ที่รัน `python app.py` เพื่อดู traceback เต็ม

**ไฟล์ PDF ใหญ่มาก (>50MB)**
→ ลองบีบอัด PDF ก่อน หรือใช้ model `gemini-1.5-pro` ที่รองรับ context ยาวกว่า