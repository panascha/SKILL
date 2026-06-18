#!/usr/bin/env python3
"""
MCQ PDF → JSON Converter (Gemini Edition — google-genai SDK)
=============================================================
Web interface for batch PDF conversion using Google Gemini API.
Dynamically loads prompt rules from medical-quiz-converter.md.

API usage mirrors Lecture Pipeline Automation:
  - uses google-genai (new SDK): from google import genai
  - client = genai.Client(api_key=api_key)
  - client.models.generate_content(...)
  - Same model list and max_output_tokens logic

Usage:
  pip install google-genai flask pymupdf Pillow
  python convert.py
  Open http://localhost:8765
"""

import os, sys, json, base64, re, subprocess, time, threading, uuid, html, shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, Response, send_file
import tempfile, traceback

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB

# ─── Paths ───────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
INPUT_DIR  = BASE_DIR / "input_pdfs"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

PROMPT_FILE  = BASE_DIR / "medical-quiz-converter.md"
COURSES_DIR  = BASE_DIR / "courses"
COURSES_DIR.mkdir(exist_ok=True)

# ─── Dynamic Category Parser & Helper ────────────────
def parse_filename_metadata(file_stem: str) -> dict:
    file_stem = file_stem.strip()
    parts = re.split(r'[_ \-]+', file_stem)
    
    # 1. Extract SubjectCode: Check for known block systems first, else fall back to dynamic extraction
    known_subjects = ["CVS", "GI", "HEMATO", "MS", "NS", "EN"]
    subject_code = ""
    for s in known_subjects:
        if s in file_stem.upper():
            subject_code = s
            break
            
    if not subject_code:
        for p in parts:
            clean_p = re.sub(r'[^A-Za-z]', '', p).upper()
            if clean_p and len(clean_p) >= 2 and clean_p not in ["MCQ", "FMT", "QUIZ", "EXAM", "TEST", "BY", "AI", "PDF"]:
                subject_code = clean_p
                break
    if not subject_code:
        if parts:
            subject_code = re.sub(r'[^A-Za-z0-9]', '', parts[0]).upper()
        if not subject_code:
            subject_code = "CVS"

    # 2. Extract Exam Year & Type (e.g., 51MCQ1, 50MCQ, 51FMT)
    year = ""
    m_year = re.search(r'(?:MD|Y|Year|Class)?\s*(\d{2})', file_stem, re.IGNORECASE)
    if m_year:
        year = m_year.group(1)
    if not year:
        m_any_num = re.search(r'(\d+)', file_stem)
        if m_any_num:
            year = m_any_num.group(1)
    if not year:
        year = "51"
        
    exam_type = "MCQ"
    for t in ["MCQ", "FMT", "QUIZ", "EXAM", "TEST"]:
        if t in file_stem.upper():
            exam_type = t
            break
            
    m_full = re.search(r'(\d+(?:MCQ|FMT|QUIZ|EXAM|TEST)\d*)', file_stem.upper())
    if m_full:
        exam_group = m_full.group(1)
    else:
        m_num = re.search(r'(?:MCQ|FMT|QUIZ|EXAM|TEST)\s*(\d+)', file_stem.upper())
        if m_num:
            exam_group = f"{year}{exam_type}{m_num.group(1)}"
        else:
            exam_group = f"{year}{exam_type}1"

    # 3. Extract TopicLabel
    topic_parts = []
    for p in parts:
        p_upper = p.upper()
        if p_upper == subject_code or p_upper == exam_group:
            continue
        if p_upper in ["BY", "AI", "BY_AI", "MCQ", "FMT", "PDF", "CONVERTED", "QUIZ"] or re.search(r'MD\d+', p_upper):
            continue
        topic_parts.append(p)
    topic_label = " ".join(topic_parts) if topic_parts else "General Topic"
    
    return {
        "subject_code": subject_code,
        "exam_group": exam_group,
        "topic_label": topic_label
    }

def sanitize_category(category_data, file_stem: str, subject_code_override: str = "") -> list:
    """
    Standardizes the category array dynamically based on the input:
    Index 0: Default CategoryID (<SubjectCode>_<ExamGroup>)
    Index 1: Standardized CategoryID (<SubjectCode>_<SubGroupSuffix>_<TopicLabel>)
    subject_code_override: if provided, overrides the SubjectCode derived from filename.
    """
    file_stem = file_stem.strip()
    meta = parse_filename_metadata(file_stem)
    subject_code = subject_code_override.strip().upper() if subject_code_override else meta["subject_code"]
    exam_group = meta["exam_group"]
    topic_label = meta["topic_label"]

    subgroups = ["LEC", "ANA", "BIOCHEM", "PHYSIO", "MICRO", "PARASITO", "PATHO", "PHARM", "RADIO", "CLINICAL"]

    # Pre-build prefixes to remove from clean topic
    prefixes_to_remove = [
        f"{subject_code}_{exam_group}",
        f"{subject_code}",
        f"{exam_group}"
    ]
    for g in subgroups:
        prefixes_to_remove.append(f"{subject_code}_{exam_group}_{g}")
        prefixes_to_remove.append(f"{subject_code}_{g}")
        prefixes_to_remove.append(g)

    clean_topic = topic_label.strip()
    for pfx in prefixes_to_remove:
        if clean_topic.upper().startswith(pfx.upper()):
            clean_topic = clean_topic[len(pfx):].strip(" _-")
            
    model_topic = ""
    if isinstance(category_data, list) and len(category_data) > 1:
        model_topic = str(category_data[1]).strip()
    elif isinstance(category_data, list) and len(category_data) == 1:
        model_topic = str(category_data[0]).strip()
    elif category_data:
        model_topic = str(category_data).strip()
        
    if model_topic:
        for pfx in prefixes_to_remove:
            if model_topic.upper().startswith(pfx.upper()):
                model_topic = model_topic[len(pfx):].strip(" _-")
        if model_topic and len(model_topic) > 3:
            clean_topic = model_topic

    if not clean_topic or clean_topic == "General Topic":
        clean_topic = topic_label

    clean_topic = re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$', '', clean_topic).strip()
    if not clean_topic:
        clean_topic = "General Topic"

    # Classify subgroup dynamically based on clean_topic keywords
    SUBGROUP_KEYWORDS = {
        "LEC": ["LEC", "LECTURE"],
        "ANA": ["ANA", "ANATOMY", "HISTO", "EMBRYO", "NEUROANA", "STRUCTURE", "GROSS", "กายวิภาค"],
        "BIOCHEM": ["BIOCHEM", "BIOCHEMISTRY", "MOLECULAR", "METABOLISM", "GENE", "CELL", "ชีวเคมี"],
        "PHYSIO": ["PHYSIOLOGY", "FUNCTION", "MECHANISM", "สรีรวิทยา"],
        "MICRO": ["MICRO", "MICROBIO", "MICROBIOLOGY", "VIRO", "BACTERIO", "IMMUNO", "INFECTION", "BACTERIA", "VIRUS", "จุลชีววิทยา"],
        "PARASITO": ["PARASITO", "PARASITOLOGY", "HELMINTH", "PROTOZOA", "WORM", "พยาธิใบไม้", "ปรสิต"],
        "PATHO": ["PATHO", "PATHOLOGY", "LESION", "BIOPSY", "HISTOPATHO", "พยาธิวิทยา"],
        "PHARM": ["PHARM", "PHARMA", "PHARMACOLOGY", "DRUG", "MEDICATION", "เภสัช"],
        "RADIO": ["RADIO", "RADIOLOGY", "XRAY", "IMAGING", "CT", "MRI", "ULTRASOUND", "รังสี"],
        "CLINICAL": ["CLINICAL", "MEDICINE", "SURGERY", "PEDIATRIC", "OBGYN", "DIAGNOSIS", "VIGNETTE", "CASE", "MANAGEMENT", "คลินิก"]
    }
    
    sub_group = None

    # 0. Priority: if Gemini explicitly returned _LEC_ in category, trust it over keyword scan
    _raw_lec_check = ""
    if isinstance(category_data, list):
        _raw_lec_check = " ".join([str(x) for x in category_data]).upper()
    elif category_data:
        _raw_lec_check = str(category_data).upper()
    if "_LEC_" in _raw_lec_check:
        sub_group = "LEC"

    topic_upper = clean_topic.upper()

    # 1. Primary classification check on the actual topic name (skip if already set by priority check)
    if not sub_group:
        for g, keywords in SUBGROUP_KEYWORDS.items():
            for kw in keywords:
                if len(kw) <= 3:
                    pattern = r'\b' + re.escape(kw) + r'\b'
                    if re.search(pattern, topic_upper):
                        sub_group = g
                        break
                else:
                    if kw in topic_upper:
                        sub_group = g
                        break
            if sub_group:
                break

    # 2. Fallback check on API category data
    if not sub_group:
        raw_str = ""
        if isinstance(category_data, list) and len(category_data) > 0:
            raw_str = " ".join([str(x) for x in category_data]).upper()
        elif category_data:
            raw_str = str(category_data).upper()
        for g in subgroups:
            if g in raw_str:
                sub_group = g
                break
                
    # 3. Fallback check on filename stem
    if not sub_group:
        stem_upper = file_stem.upper()
        for g in subgroups:
            if g in stem_upper:
                sub_group = g
                break
                
    # Default fallback
    if not sub_group:
        sub_group = "CLINICAL"

    # Index 0: Only subject_code and exam_group (Default_CategoryID)
    final_idx_0 = f"{subject_code}_{exam_group}"
    # Index 1: Standardized_CategoryID
    final_idx_1 = f"{subject_code}_{sub_group}_{clean_topic}"
    
    return [final_idx_0, final_idx_1]

# ─── Default Prompt ───────────────────────────────────
DEFAULT_SYSTEM_PROMPT = """You are a medical quiz converter. Your task is to convert medical exam questions (MCQs, clinical vignettes) from the provided PDF into a specific JSON structure.

Strictly adhere to the following rules and output format:

--- Output Schema ---
Return a single JSON Object with 'meta' and 'questions' keys:
{
  "meta": {
    "source": "Filename.pdf",
    "categoryID": "SubjectCode_YearGroup_TopicLabel",
    "converted": 10,
    "skipped_duplicates": 0,
    "completions_added": 0,
    "validation_warnings": 0,
    "categories_found": ["LectureTopic1", "LectureTopic2"]
  },
  "questions": [
    {
      "problem": "1. Full question text verbatim...",
      "img": "",
      "choices": "Choice A///Choice B///Choice C///Choice D///Choice E",
      "answer": "Choice A",
      "select": "",
      "explain": "อธิบายหลักการแพทย์และเหตุผลทางการแพทย์อย่างละเอียด (ภาษาไทยผสมผสานคำศัพท์ทางการแพทย์ภาษาอังกฤษ/medical terminology เท่านั้น ห้ามอธิบายเป็นภาษาอังกฤษล้วนโดยเด็ดขาด!)...",
      "category": ["Default_CategoryID", "Standardized_CategoryID"],
      "state": false
    }
  ]
}

--- Workflow & Rules ---
1. problem (Extraction + Completion):
   - Copy entire question stem / clinical vignette verbatim (vitale, lab values, medication names, dosages, timelines, etc.). Do NOT summarize, shorten or restructure.
   - Prepend the question number: "1. A 45-year-old man..."
   - Incomplete Question Handling: If a question is missing key clinical elements, complete it with medically appropriate content and append the tag: " [⚠️ เพิ่มเติมเพื่อความสมบูรณ์: <รายละเอียดที่เพิ่ม>]" at the end of the problem string.

2. select & state:
   - Always "select": "" and "state": false.

3. choices:
   - Separator is exactly "///" (no spaces before or after).
   - Exactly 5 choices per question. If the source has fewer than 5, generate realistic medical distractors.

4. answer:
   - Must match character-for-character with one of the segments in the "choices" string.

5. img:
   - Default: "". If the question references visual data (e.g., ECG, X-Ray): "require_img".

6. explain:
   - MUST be written in ภาษาไทย prose mixed with English medical terminology (ศัพท์แพทย์).
   - Absolutely NO pure English explanations allowed (ห้ามใช้ภาษาอังกฤษล้วนในการอธิบายคำอธิบายโดยเด็ดขาด).
   - Single continuous line/paragraph (absolutely no line breaks, no bullet lists inside this string!).
   - Structure: 1) Key Concept, 2) Why Correct (using clues), 3) Rule Out each distractor (e.g. "ส่วนข้อ B ผิดเพราะ... (because...)"), 4) Clinical Pearl (optional).

7. category:
   - A 2-element array: ["Default_CategoryID", "Standardized_CategoryID"]
   - First element (Default_CategoryID): Formatted strictly as "<SubjectCode>_<ExamGroup>" (e.g., "CVS_51MCQ1").
   - Second element (Standardized_CategoryID): Formatted strictly as "<SubjectCode>_<SubGroupSuffix>_<TopicLabel>" (e.g., "CVS_ANA_Anatomy of Heart").
     * <SubGroupSuffix>: Must be chosen from this exact list: [ANA, BIOCHEM, PHYSIO, MICRO, PARASITO, PATHO, PHARM, RADIO, CLINICAL].
8. JSON Safety:
   - No unescaped double quotes, backslashes, or literal newlines in any string value. All values must be on a single physical line in the JSON output.
"""

# ─── Global job state ─────────────────────────────────
_jobs: dict[str, dict] = {}
_log_lock = threading.Lock()

def new_job() -> dict:
    return {
        "running": False,
        "current_file": "",
        "progress": 0,
        "total": 0,
        "done": 0,
        "results": [],
        "logs": [],
        "zip_path": None,
    }

def push_log(job: dict, msg: str, level: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    with _log_lock:
        job["logs"].append({"ts": ts, "msg": msg, "level": level})
    print(f"[{ts}] {msg}", flush=True)

# ─── Image extraction ─────────────────────────────────
def extract_images(pdf_bytes: bytes, images_dir: Path, stem: str = "") -> int:
    images_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    prefix = f"{stem}_" if stem else ""

    try:
        import fitz  # PyMuPDF
        import io
        from PIL import Image

        pdf_file = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_index in range(len(pdf_file)):
            page = pdf_file[page_index]
            image_list = page.get_images(full=True)

            if image_list:
                for image_index, img in enumerate(image_list, start=1):
                    xref = img[0]
                    base_image = pdf_file.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    if len(image_bytes) < 2000:
                        continue

                    try:
                        image = Image.open(io.BytesIO(image_bytes))
                        image_name = f"{prefix}page_{page_index + 1}_img_{image_index}.{image_ext}"
                        image_path = images_dir / image_name
                        image.save(image_path)
                        count += 1
                    except Exception:
                        pass
        pdf_file.close()
    except ImportError:
        pass
    except Exception:
        pass

    if count == 0:
        try:
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(pdf_bytes)
            for i, page in enumerate(doc):
                bitmap = page.render(scale=1.5)
                pil_img = bitmap.to_pil()
                out = images_dir / f"{prefix}page_{i+1:03d}_render.png"
                pil_img.save(out)
                count += 1
            doc.close()
        except Exception:
            pass

    return count


# ─── Robust JSON Parsing & Recovery Helpers ──────────
def extract_valid_questions_from_broken_json(raw: str) -> list:
    questions = []
    idx = 0
    while True:
        idx = raw.find('{', idx)
        if idx == -1:
            break
        
        brace_count = 0
        in_string = False
        escape = False
        match_found = False
        end_idx = idx
        
        for i in range(idx, len(raw)):
            char = raw[i]
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        match_found = True
                        break
        
        if match_found:
            candidate = raw[idx : end_idx + 1]
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict) and "problem" in obj and "choices" in obj:
                    questions.append(obj)
            except Exception:
                pass
            idx = end_idx + 1
        else:
            idx += 1
            
    return questions

def extract_meta_from_broken_json(raw: str) -> dict:
    idx = 0
    while True:
        idx = raw.find('{', idx)
        if idx == -1:
            break
        
        brace_count = 0
        in_string = False
        escape = False
        match_found = False
        end_idx = idx
        
        for i in range(idx, len(raw)):
            char = raw[i]
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        match_found = True
                        break
        
        if match_found:
            candidate = raw[idx : end_idx + 1]
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict) and ("source" in obj or "categoryID" in obj):
                    return obj
            except Exception:
                pass
            idx = end_idx + 1
        else:
            idx += 1
    return {}


# ─── JSON parsing ─────────────────────────────────────
def parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json|javascript|js)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try finding an outer object {} first
    m_obj = re.search(r"(\{[\s\S]+\})", raw)
    if m_obj:
        try:
            return json.loads(m_obj.group(1))
        except Exception:
            pass

    # Try finding an outer array [] next
    m_arr = re.search(r"(\[[\s\S]+\])", raw)
    if m_arr:
        try:
            arr = json.loads(m_arr.group(1))
            return {"questions": arr}
        except Exception:
            pass

    # Fallback Self-Healing Recovery Parser (For truncated / incomplete JSON payloads)
    try:
        recovered_questions = extract_valid_questions_from_broken_json(raw)
        if recovered_questions:
            recovered_meta = extract_meta_from_broken_json(raw) or {}
            return {
                "meta": recovered_meta,
                "questions": recovered_questions
            }
    except Exception:
        pass

    raise ValueError("ไม่พบ JSON object หรือ JSON array ใน response และไม่สามารถกู้คืนโครงสร้างที่ถูกตัดทอนได้")

# ─── Self-Healing API Quota Manager ───────────────────
def execute_with_retry(job: dict, func, *args, max_retries=5, initial_delay=20, **kwargs):
    """
    Executes a Gemini API call, catching Rate Limits (429) or Server Demands (503),
    applying progressive delay to auto-heal requests.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_msg = str(e)
            is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
            is_unavailable = "503" in err_msg or "UNAVAILABLE" in err_msg or "demand" in err_msg.lower() or "overloaded" in err_msg.lower()
            
            if (is_rate_limit or is_unavailable) and attempt < max_retries - 1:
                sleep_time = delay + (12 * attempt)
                push_log(job, f"⚠️ โควตาจำกัด/เซิร์ฟเวอร์ตอบสนองช้า (Status: {err_msg[:60]}) "
                              f"ระบบจะหน่วงรอ {sleep_time:.1f} วินาทีก่อนลองใหม่ (ครั้งที่ {attempt+1}/{max_retries})...", "warn")
                time.sleep(sleep_time)
            else:
                raise e

# ─── Process one PDF ──────────────────────────────────
def process_pdf(job: dict, client, model_name: str, pdf_path: Path, subject_title: str = "", additional_prompt: str = "") -> tuple[dict, list]:
    from google.genai import types

    # Strip any trailing whitespace from the file stem to maintain Windows path compatibility
    stem     = pdf_path.stem.strip()
    out_dir  = OUTPUT_DIR / stem
    imgs_dir = out_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    # คัดลอกไฟล์ PDF ต้นฉบับไปยังโฟลเดอร์ผลลัพธ์
    try:
        shutil.copy2(pdf_path, out_dir / pdf_path.name)
        push_log(job, f"[{stem}] คัดลอกไฟล์ต้นฉบับ PDF ไปยังโฟลเดอร์ผลลัพธ์เรียบร้อย", "ok")
    except Exception as e:
        push_log(job, f"[{stem}] คัดลอกไฟล์ต้นฉบับ PDF ล้มเหลว: {e}", "warn")

    summary = {
        "file": pdf_path.name,
        "status": "pending",
        "questions": 0,
        "images": 0,
        "errors": [],
        "elapsed": 0,
    }

    # ── Load prompt (live reload) ──
    if PROMPT_FILE.exists():
        try:
            system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
            push_log(job, f"[{stem}] โหลดกติกาจาก {PROMPT_FILE.name}", "info")
        except Exception as e:
            system_prompt = DEFAULT_SYSTEM_PROMPT
            push_log(job, f"[{stem}] อ่าน prompt ไม่สำเร็จ ใช้ Default: {e}", "warn")
    else:
        system_prompt = DEFAULT_SYSTEM_PROMPT
        push_log(job, f"[{stem}] ไม่พบ {PROMPT_FILE.name} — ใช้ Default Prompt", "warn")

    # ── max_output_tokens ──
    if "pro" in model_name.lower() or "3.5" in model_name or "3.0" in model_name:
        max_out = 65536
    else:
        max_out = 8192

    generation_cfg = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=max_out,
        temperature=0.1,
        response_mime_type="application/json",
    )

    start = time.time()

    # ── Read PDF bytes once (shared by image extraction and Gemini call) ──
    try:
        pdf_bytes = pdf_path.read_bytes()
    except Exception as e:
        push_log(job, f"[{stem}] อ่านไฟล์ PDF ล้มเหลว: {e}", "error")
        summary["status"] = "failed"
        summary["errors"].append(str(e))
        summary["elapsed"] = round(time.time() - start, 1)
        return summary, []

    # ── Step 1: Extract images ──
    push_log(job, f"[{stem}] ดึงรูปภาพจาก PDF...", "info")
    try:
        n = extract_images(pdf_bytes, imgs_dir, stem=stem)
        summary["images"] = n
        push_log(job, f"[{stem}] รูปภาพ {n} ไฟล์", "ok")
    except Exception as e:
        push_log(job, f"[{stem}] ดึงรูปภาพล้มเหลว: {e}", "warn")

    # ── Step 2: Build user query ──
    user_query = (
        f"แปลงข้อสอบทุกข้อในไฟล์ PDF นี้ ({pdf_path.name}) เป็น JSON ตามกฎกติกาที่กำหนดไว้ใน system instruction ทั้งหมด "
        "ห้ามข้ามข้อใด ส่งกลับมาเป็น Raw JSON Object ที่มีฟิลด์ 'meta' และ 'questions' ตามรูปแบบที่กำหนดเท่านั้น "
        "ห้ามมีตัวอักษรอื่นปนอยู่นอกเหนือจากรูปแบบ JSON"
    )
    if subject_title:
        user_query += f"\n\n[หัวข้อ/วิชาของข้อสอบชุดนี้]: {subject_title}"
        push_log(job, f"[{stem}] ระบุหัวข้อวิชา: {subject_title}", "info")
    if additional_prompt:
        user_query += f"\n\n[คำสั่งพิเศษเพิ่มเติมรอบนี้]:\n{additional_prompt}"
        push_log(job, f"[{stem}] เพิ่มคำสั่งพิเศษ: {additional_prompt[:40]}...", "info")

    # ── Step 3: Send to Gemini — inline first, Files API as fallback ──
    # Inline PDF avoids 2 extra quota calls (upload + delete) per file.
    # Falls back to Files API only if the payload is too large for inline.
    INLINE_SIZE_LIMIT = 20 * 1024 * 1024  # 20 MB
    uploaded_file = None
    push_log(job, f"[{stem}] ส่งคำวิเคราะห์ไปยัง Gemini API...", "info")
    try:
        if len(pdf_bytes) <= INLINE_SIZE_LIMIT:
            # Inline path — no upload/delete calls needed
            pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
            contents = [pdf_part, user_query]
            push_log(job, f"[{stem}] ใช้ Inline PDF ({len(pdf_bytes)/1024:.0f} KB)", "info")
        else:
            # Files API path — only for large PDFs
            push_log(job, f"[{stem}] ไฟล์ใหญ่ ({len(pdf_bytes)/1024/1024:.1f} MB) → อัปโหลด Files API...", "info")
            uploaded_file = execute_with_retry(job, client.files.upload, file=str(pdf_path))
            push_log(job, f"[{stem}] อัปโหลดไฟล์เสร็จสิ้น (ID: {uploaded_file.name})", "ok")
            contents = [uploaded_file, user_query]

        response = execute_with_retry(
            job,
            client.models.generate_content,
            model=model_name,
            contents=contents,
            config=generation_cfg,
        )
        raw = response.text
        push_log(job, f"[{stem}] ได้รับ response ({len(raw):,} chars)", "ok")
    except Exception as e:
        push_log(job, f"[{stem}] Gemini API error: {e}", "error")
        summary["status"] = "failed"
        summary["errors"].append(str(e))
        summary["elapsed"] = round(time.time() - start, 1)
        return summary, []
    finally:
        # Step 4: Clean up Files API upload if one was created
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
                push_log(job, f"[{stem}] ลบไฟล์ชั่วคราวออกจากเซิร์ฟเวอร์เสร็จสิ้น", "info")
            except Exception:
                pass

    # ── Step 5: Parse JSON ──
    push_log(job, f"[{stem}] Parse JSON...", "info")
    try:
        res_data = parse_json_response(raw)
        
        if "questions" in res_data:
            questions = res_data["questions"]
            meta_block = res_data.get("meta", {})
        else:
            if isinstance(res_data, list):
                questions = res_data
                meta_block = {}
            else:
                questions = [res_data]
                meta_block = {}

        # Sanitize category field for each question
        subject_code_ov = subject_title.strip().upper() if subject_title else ""
        for q in questions:
            if isinstance(q, dict):
                q["category"] = sanitize_category(q.get("category"), stem, subject_code_override=subject_code_ov)
                
        summary["questions"] = len(questions)
        push_log(job, f"[{stem}] {len(questions)} ข้อ", "ok")
    except Exception as e:
        push_log(job, f"[{stem}] Parse JSON ล้มเหลว: {e}", "error")
        summary["status"] = "failed"
        summary["errors"].append(str(e))
        summary["elapsed"] = round(time.time() - start, 1)
        return summary, []

    # ── Step 6: Extract Metadata & Categories ──
    categories_found = []
    for q in questions:
        if isinstance(q, dict) and "category" in q and isinstance(q["category"], list) and len(q["category"]) > 1:
            cat_name = q["category"][1]
            if cat_name and cat_name not in categories_found:
                categories_found.append(cat_name)

    meta = {
        "source": pdf_path.name,
        "categoryID": stem,
        "converted": len(questions),
        "skipped_duplicates": meta_block.get("skipped_duplicates", 0) if isinstance(meta_block, dict) else 0,
        "completions_added": meta_block.get("completions_added", 0) if isinstance(meta_block, dict) else 0,
        "validation_warnings": meta_block.get("validation_warnings", 0) if isinstance(meta_block, dict) else 0,
        "categories_found": categories_found,
        "converted_at": datetime.now().isoformat(),
    }

    # ── Step 7: Save Clean Deliverables Only ──
    obj = {
        "meta": meta,
        "questions": questions,
    }
    (out_dir / f"{stem}.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    push_log(job, f"[{stem}] ✓ บันทึกสำเร็จ → output/{stem}/", "ok")

    summary["status"] = "success"
    summary["elapsed"] = round(time.time() - start, 1)
    return summary, questions

# ─── Background job runner ────────────────────────────
def run_conversion(job_id: str, api_key: str, model_name: str, filenames: list, subject_title: str = "", additional_prompt: str = ""):
    from google import genai

    # Sanitize API key to ensure pure ASCII string for the HTTP client headers
    api_key = re.sub(r'[^\x00-\x7F]+', '', api_key).strip()

    job = _jobs[job_id]
    job.update({"running": True, "done": 0, "total": len(filenames),
                "results": [], "progress": 0, "logs": []})

    push_log(job, f"เริ่มแปลง {len(filenames)} ไฟล์ ด้วยโมเดล {model_name}", "info")

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        push_log(job, f"สร้าง Gemini Client ล้มเหลว: {e}", "error")
        job["running"] = False
        return

    pdfs = [INPUT_DIR / n for n in filenames]
    
    # ── โหลดข้อมูลสะสมจาก quizdata.js เดิมขึ้นมาก่อน (ถ้ามีอยู่แล้ว) เพื่อรองรับการแปลงสะสมเรื่อย ๆ ──
    combined_js_path = OUTPUT_DIR / "quizdata.js"
    all_batch_data = {}
    if combined_js_path.exists():
        try:
            content = combined_js_path.read_text(encoding="utf-8").strip()
            # ค้นหาข้อความแบบยืดหยุ่นระหว่าง { และ } ของ var quizdata
            m = re.search(r'var\s+quizdata\s*=\s*(\{[\s\S]+?\})(?:\s*;?\s*)$', content)
            if not m:
                m = re.search(r'var\s+quizdata\s*=\s*(\{[\s\S]+\})', content)
            if m:
                json_str = m.group(1).strip()
                if json_str.endswith(';'):
                    json_str = json_str[:-1].strip()
                all_batch_data = json.loads(json_str)
                total_prev = sum(len(v) for v in all_batch_data.values() if isinstance(v, list))
                push_log(job, f"📦 โหลดข้อสอบเดิมจำนวน {total_prev} ข้อ จาก quizdata.js เพื่อรวมสะสมสำเร็จ", "info")
        except Exception as e:
            push_log(job, f"⚠️ ไม่สามารถดึงข้อมูลเดิมจาก quizdata.js ได้ (จะเขียนทับใหม่): {e}", "warn")

    FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.0-flash", "gemini-2.5-flash"]
    # Start from the user-chosen model if it's in the chain, else start at 0
    try:
        active_model_idx = FALLBACK_MODELS.index(model_name)
    except ValueError:
        active_model_idx = 0

    all_quota_exhausted = False

    for i, pdf_path in enumerate(pdfs):
        if not pdf_path.exists():
            push_log(job, f"ไม่พบ {pdf_path.name}", "error")
            continue

        job["current_file"] = pdf_path.name
        job["progress"] = int(i / len(pdfs) * 100)

        summary, questions = {}, []
        for try_idx in range(active_model_idx, len(FALLBACK_MODELS)):
            active_model = FALLBACK_MODELS[try_idx]
            if try_idx > active_model_idx:
                push_log(job, f"🔄 สลับโมเดลเป็น {active_model} เนื่องจากโควตาของโมเดลก่อนหน้าหมดแล้ว", "warn")
            summary, questions = process_pdf(job, client, active_model, pdf_path, subject_title, additional_prompt)
            if summary.get("status") == "success":
                active_model_idx = try_idx  # stay on this model for remaining files
                break
            is_quota = any(
                ("429" in e or "RESOURCE_EXHAUSTED" in e or "limit: 0" in e)
                for e in summary.get("errors", [])
            )
            if is_quota and try_idx < len(FALLBACK_MODELS) - 1:
                active_model_idx = try_idx + 1  # advance for all remaining files
                continue
            if is_quota:
                push_log(job, "🔑 โควตาหมดทุกโมเดลแล้ว กรุณาเปลี่ยน API Key แล้วลองใหม่", "error")
                all_quota_exhausted = True
            break

        job["results"].append(summary)
        job["done"] = i + 1

        if all_quota_exhausted:
            break

        # ── นำคำถามมารวมเข้ากับข้อมูลชุดสะสมตาม Default_CategoryID ──
        if summary.get("status") == "success" and questions:
            default_cat_id = None
            
            # ดึง Default_CategoryID (Index 0) จากข้อสอบข้อแรกที่ประมวลผลเสร็จสิ้น
            if (len(questions) > 0 and 
                isinstance(questions[0], dict) and 
                "category" in questions[0] and 
                isinstance(questions[0]["category"], list) and 
                len(questions[0]["category"]) > 0):
                default_cat_id = questions[0]["category"][0]
            
            # กรณีโครงสร้างข้อมูลผิดพลาด ให้ถอยกลับไปสกัดรูปแบบจากชื่อไฟล์โดยตรง
            if not default_cat_id:
                meta = parse_filename_metadata(pdf_path.stem.strip())
                default_cat_id = f"{meta['subject_code']}_{meta['exam_group']}"
            
            # สร้างอาเรย์เปล่ารอ หากเป็นหมวดหมู่ใหม่
            if default_cat_id not in all_batch_data:
                all_batch_data[default_cat_id] = []
                
            # เพิ่มข้อมูลเข้าไปเฉพาะคำถามที่ไม่เคยซ้ำ (ตรวจสอบข้อความโจทย์)
            existing_problems = {q.get("problem") for q in all_batch_data[default_cat_id] if isinstance(q, dict)}
            for q in questions:
                if isinstance(q, dict) and q.get("problem") not in existing_problems:
                    all_batch_data[default_cat_id].append(q)

        # Add proactive cooldown delay to protect rate limit (RPM limit)
        if i < len(pdfs) - 1:
            cooldown_secs = 12
            push_log(job, f"⏳ พักระบบ {cooldown_secs} วินาทีก่อนเริ่มแปลงไฟล์ถัดไปเพื่อเลี่ยงการชนโควตา RPM...", "info")
            time.sleep(cooldown_secs)

    # ── เขียนไฟล์รวมผลลัพธ์ quizdata.js คืนกลับโฟลเดอร์ ──
    if all_batch_data:
        try:
            quizdata_js_str = (
                "// Auto-generated Combined MCQ Quiz Data\n"
                f"var quizdata = {json.dumps(all_batch_data, ensure_ascii=False, indent=2)};\n"
            )
            combined_js_path.write_text(quizdata_js_str, encoding="utf-8")
            push_log(job, "📦 เขียนไฟล์ quizdata.js (Combined) สำหรับระบบส่วนกลางสำเร็จ", "ok")
        except Exception as e:
            push_log(job, f"เขียนไฟล์ quizdata.js ล้มเหลว: {e}", "warn")

    job["progress"] = 100
    job["running"] = False
    job["current_file"] = ""
    push_log(job, f"✅ เสร็จสิ้นทั้งหมด {len(filenames)} ไฟล์", "ok")

    # Package zip (Only packing images/ directory, <stem>.json and the root quizdata.js)
    try:
        for old_zip in OUTPUT_DIR.glob("mcq_output_*.zip"):
            try:
                old_zip.unlink()
            except Exception:
                pass

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = OUTPUT_DIR / f"mcq_output_{ts}.zip"
        import zipfile
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if combined_js_path.exists():
                zf.write(combined_js_path, combined_js_path.name)
                
            for stem in [Path(n).stem.strip() for n in filenames]:
                d = OUTPUT_DIR / stem
                if d.exists():
                    for f in sorted(d.rglob("*")):
                        if f.is_file():
                            zf.write(f, f.relative_to(OUTPUT_DIR))
        job["zip_path"] = str(zip_path)
        push_log(job, f"📦 สร้าง ZIP สำเร็จ: {zip_path.name}", "ok")
    except Exception as e:
        push_log(job, f"สร้าง ZIP ล้มเหลว: {e}", "warn")


# ─── Flask Routes ─────────────────────────────────────
@app.route("/")
def index():
    return HTML_PAGE

@app.route("/api/files")
def api_files():
    files = sorted([f.name for f in INPUT_DIR.glob("*.pdf")])
    return jsonify({"files": files})

@app.route("/api/outputs")
def api_outputs():
    results = []
    for d in sorted(OUTPUT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not d.is_dir():
            continue
        jf = d / f"{d.name}.json"
        if jf.exists():
            try:
                meta_data = json.loads(jf.read_text(encoding="utf-8"))
                if "meta" in meta_data:
                    meta = meta_data["meta"]
                    questions_count = meta.get("converted", 0)
                    converted_at = meta.get("converted_at", "")
                else:
                    questions_count = meta_data.get("total_questions", 0)
                    converted_at = meta_data.get("converted_at", "")

                results.append({
                    "name": d.name,
                    "questions": questions_count,
                    "converted_at": converted_at,
                    "has_images": (d / "images").exists() and any((d / "images").iterdir()),
                })
            except Exception:
                pass
    return jsonify({"outputs": results})

@app.route("/api/run", methods=["POST"])
def api_run():
    data      = request.get_json(force=True)
    api_key   = data.get("api_key", "").strip()
    
    # Strip non-ASCII characters from raw input to prevent httpx ASCII encode failure on API requests
    api_key = re.sub(r'[^\x00-\x7F]+', '', api_key).strip()

    model_name= data.get("model", "gemini-3.5-flash").strip()
    filenames = data.get("files", [])
    job_id    = data.get("job_id", "default")
    
    subject_title     = data.get("subject_title", "").strip()
    additional_prompt = data.get("additional_prompt", "").strip()

    if not api_key:
        return jsonify(ok=False, error="กรุณาระบุ Gemini API Key"), 400
    if not filenames:
        return jsonify(ok=False, error="กรุณาเลือกไฟล์อย่างน้อย 1 ไฟล์"), 400

    if job_id not in _jobs:
        _jobs[job_id] = new_job()

    if _jobs[job_id].get("running"):
        return jsonify(ok=False, error="กำลังรันอยู่แล้ว"), 400

    _jobs[job_id]["running"] = True  # mark before thread start to close TOCTOU window

    t = threading.Thread(
        target=run_conversion,
        args=(job_id, api_key, model_name, filenames, subject_title, additional_prompt),
        daemon=True,
    )
    t.start()
    return jsonify(ok=True, job_id=job_id)

@app.route("/api/status/<job_id>")
def api_status(job_id: str):
    if job_id not in _jobs:
        return jsonify(ok=False, error="ไม่พบ job"), 404
    job = _jobs[job_id]
    with _log_lock:
        logs = list(job["logs"][-300:])
        total_log_count = len(job["logs"])
    return jsonify({**{k: v for k, v in job.items() if k != "logs"}, "logs": logs, "total_log_count": total_log_count})

@app.route("/api/courses")
def api_courses():
    courses = []
    for f in sorted(COURSES_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            courses.append({"id": f.stem, "name": data.get("name", f.stem)})
        except Exception:
            pass
    return jsonify(courses=courses)

@app.route("/api/courses/<course_id>")
def api_course(course_id: str):
    path = COURSES_DIR / f"{course_id}.json"
    if not path.exists():
        return jsonify(ok=False, error="Course not found"), 404
    return jsonify(json.loads(path.read_text(encoding="utf-8")))

@app.route("/api/download/<job_id>")
def api_download(job_id: str):
    if job_id not in _jobs:
        return "ไม่พบ job", 404
    zip_path = _jobs[job_id].get("zip_path")
    if not zip_path or not Path(zip_path).exists():
        return "ไฟล์ยังไม่พร้อม", 404
    return send_file(zip_path, as_attachment=True)


# ─── Embedded HTML (Refined Design & Scrolling Fixed) ────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCQ PDF Converter — Gemini Edition</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:          #080b11;
    --surface:     #0e1320;
    --card:        #151c2e;
    --border:      rgba(255, 255, 255, 0.08);
    --border-hover: rgba(255, 255, 255, 0.16);
    --accent:      #0ea5e9; /* Sky 500 */
    --accent-light:#38bdf8; /* Sky 400 */
    --accent2:     #10b981; /* Emerald 500 */
    --accent2-light:#34d399; /* Emerald 400 */
    --warn:        #f97316; /* Orange 500 */
    --err:         #ef4444; /* Red 500 */
    --purple:      #8b5cf6; /* Violet 500 */
    --purple-light:#a78bfa; /* Violet 400 */
    --text:        #f1f5f9; /* Slate 100 */
    --muted:       #94a3b8; /* Slate 400 */
    --mono:        'IBM Plex Mono', 'JetBrains Mono', 'Fira Code', monospace;
    --sans:        'IBM Plex Sans Thai', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    height: 100vh;
    display: grid;
    grid-template-rows: 64px 1fr;
    overflow: hidden;
  }

  /* ── Header ── */
  header {
    background: rgba(14, 19, 32, 0.85);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 28px;
    gap: 16px;
    flex-shrink: 0;
    backdrop-filter: blur(12px);
    z-index: 10;
  }

  .brand {
    display: flex; align-items: center; gap: 12px;
    font-size: 16px; font-weight: 700; letter-spacing: -0.02em;
    color: #fff;
  }

  .brand-badge {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--accent), var(--purple));
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
  }

  .header-version {
    font-size: 11px;
    color: var(--muted);
    font-family: var(--mono);
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid var(--border);
  }

  .header-pill {
    margin-left: auto;
    font-family: var(--sans);
    font-size: 12px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 30px;
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--muted);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .header-pill::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--muted);
    display: inline-block;
  }

  .header-pill.running {
    background: rgba(14, 165, 233, 0.1);
    border-color: rgba(14, 165, 233, 0.3);
    color: var(--accent-light);
    animation: pulse-glow 2s infinite;
  }

  .header-pill.running::before {
    background: var(--accent-light);
  }

  .header-pill.done {
    background: rgba(16, 185, 129, 0.1);
    border-color: rgba(16, 185, 129, 0.3);
    color: var(--accent2-light);
  }

  .header-pill.done::before {
    background: var(--accent2-light);
  }

  @keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.4); }
    50%      { box-shadow: 0 0 0 6px rgba(14, 165, 233, 0); }
  }

  /* ── Main Layout ── */
  .main {
    display: grid;
    grid-template-columns: 380px 1fr;
    overflow: hidden;
  }

  /* ── Left Sidebar Panel ── */
  .left {
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden; /* Outer viewport is clipped */
    height: 100%;
  }

  /* Scrollable Container for Settings & Files inside Sidebar */
  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  /* Config Accordion Button */
  .config-collapse-btn {
    background: rgba(255, 255, 255, 0.02);
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    border-bottom: 1px solid var(--border);
    user-select: none;
    color: #fff;
    transition: background 0.15s;
  }

  .config-collapse-btn:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  .config-collapse-btn span {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .config-collapse-btn em {
    font-style: normal;
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    display: inline-block;
  }

  /* When open, chevron rotates (points up) */
  .config-collapse-btn.open em {
    transform: rotate(180deg);
  }

  .config-section {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .field { margin-bottom: 12px; }
  .field:last-child { margin-bottom: 0; }

  .field label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: #cbd5e1;
    margin-bottom: 6px;
  }

  .field .hint {
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 6px;
  }

  .input-wrap { position: relative; }

  .input-wrap input,
  .field input[type="text"],
  .field select {
    width: 100%;
    background: rgba(8, 11, 17, 0.7);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: var(--sans);
    font-size: 13px;
    padding: 10px 12px;
    outline: none;
    transition: all 0.2s;
    -webkit-appearance: none;
  }

  .input-wrap input {
    padding-right: 40px;
    font-family: var(--mono);
    letter-spacing: 0.05em;
  }

  .field select {
    padding-right: 32px;
    cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2394a3b8' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
  }

  .field textarea {
    width: 100%;
    background: rgba(8, 11, 17, 0.7);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: var(--sans);
    font-size: 13px;
    padding: 10px 12px;
    outline: none;
    resize: none;
    transition: all 0.2s;
  }

  .input-wrap input:focus,
  .field input[type="text"]:focus,
  .field select:focus,
  .field textarea:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
    background: rgba(8, 11, 17, 0.9);
  }

  .eye-btn {
    position: absolute; right: 10px; top: 50%;
    transform: translateY(-50%);
    background: none; border: none;
    cursor: pointer; color: var(--muted);
    font-size: 15px; padding: 4px;
    line-height: 1;
    transition: color 0.15s;
  }

  .eye-btn:hover { color: var(--text); }

  /* ── Config collapse wrapper ── */
  .config-sections-wrap {
    overflow: hidden;
    transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Toolbar */
  .file-toolbar {
    padding: 10px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    background: rgba(14, 19, 32, 0.4);
  }

  .file-count-badge {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--accent-light);
    background: rgba(14, 165, 233, 0.1);
    padding: 2px 8px;
    border-radius: 12px;
    border: 1px solid rgba(14, 165, 233, 0.2);
  }

  .tb-btn {
    font-size: 11px;
    font-weight: 500;
    color: var(--text);
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border);
    cursor: pointer;
    font-family: var(--sans);
    padding: 4px 10px;
    border-radius: 6px;
    transition: all 0.15s;
  }

  .tb-btn:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: var(--border-hover);
  }

  .tb-btn.refresh {
    margin-left: auto;
    color: var(--accent-light);
    border-color: rgba(14, 165, 233, 0.3);
    background: rgba(14, 165, 233, 0.05);
  }

  .tb-btn.refresh:hover {
    background: rgba(14, 165, 233, 0.1);
    border-color: var(--accent);
  }

  /* File Scroll Container */
  .file-scroll {
    flex: 1;
    min-height: 180px;
    overflow-y: auto;
    padding: 12px 16px;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 6px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.01);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    user-select: none;
  }

  .file-item:hover {
    background: rgba(255, 255, 255, 0.03);
    border-color: var(--border-hover);
  }

  .file-item.selected {
    background: rgba(14, 165, 233, 0.06);
    border-color: rgba(14, 165, 233, 0.3);
  }

  .file-item.processing {
    background: rgba(249, 115, 22, 0.05);
    border-color: rgba(249, 115, 22, 0.3);
    animation: pulse-border 2.5s infinite;
  }

  @keyframes pulse-border {
    0%, 100% { border-color: rgba(249, 115, 22, 0.3); }
    50%      { border-color: var(--warn); }
  }

  .file-item.done {
    background: rgba(16, 185, 129, 0.05);
    border-color: rgba(16, 185, 129, 0.3);
  }

  .file-item.failed {
    background: rgba(239, 68, 68, 0.05);
    border-color: rgba(239, 68, 68, 0.3);
  }

  .file-checkbox {
    width: 18px; height: 18px;
    border-radius: 5px;
    border: 1.5px solid rgba(255, 255, 255, 0.2);
    background: rgba(8, 11, 17, 0.6);
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px;
    font-weight: bold;
    color: transparent;
    transition: all 0.15s;
  }

  .file-item.selected .file-checkbox {
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
  }

  .file-label {
    font-size: 13px;
    font-weight: 500;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #e2e8f0;
  }

  .file-status-icon {
    font-size: 13px;
    flex-shrink: 0;
  }

  .empty-files {
    text-align: center;
    padding: 48px 16px;
    color: var(--muted);
    font-size: 13px;
  }

  .empty-files span {
    font-size: 32px;
    display: block;
    margin-bottom: 12px;
    opacity: 0.4;
  }

  /* ── Run Button (Sticky Footer) ── */
  .run-wrap {
    padding: 16px 20px;
    border-top: 1px solid var(--border);
    flex-shrink: 0;
    background: var(--surface);
    z-index: 5;
  }

  .run-btn {
    width: 100%;
    padding: 12px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
    color: #fff;
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.5px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.25);
  }

  .run-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
    filter: brightness(1.1);
  }

  .run-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .run-btn.running-state {
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--muted);
    box-shadow: none;
  }

  /* ── Right Panel ── */
  .right {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg);
  }

  /* Progress Section */
  .progress-bar-wrap {
    padding: 16px 28px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }

  .progress-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 13px;
  }

  .progress-label {
    font-weight: 600;
    color: #f1f5f9;
  }

  .progress-pct {
    font-family: var(--mono);
    font-weight: 600;
    color: var(--accent-light);
  }

  .progress-track {
    height: 6px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--purple));
    border-radius: 3px;
    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 8px rgba(14, 165, 233, 0.5);
  }

  .progress-sub {
    margin-top: 6px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
    min-height: 16px;
  }

  /* Tabs Bar */
  .tab-bar {
    display: flex;
    align-items: center;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 28px;
    height: 48px;
  }

  .tab {
    padding: 0 16px;
    height: 100%;
    display: flex;
    align-items: center;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    color: var(--muted);
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    margin-right: 8px;
    user-select: none;
  }

  .tab:hover {
    color: #cbd5e1;
  }

  .tab.active {
    color: var(--accent-light);
    border-bottom-color: var(--accent);
  }

  .tab-actions { margin-left: auto; display: flex; gap: 8px; }

  .icon-btn {
    font-size: 12px;
    font-weight: 500;
    color: var(--muted);
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 5px 12px;
    cursor: pointer;
    font-family: var(--sans);
    transition: all 0.15s;
  }

  .icon-btn:hover {
    border-color: var(--accent);
    color: var(--accent-light);
    background: rgba(14, 165, 233, 0.05);
  }

  /* Log Console */
  .log-console {
    flex: 1;
    overflow-y: auto;
    padding: 16px 28px;
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.8;
    background: #05070c;
  }

  .log-line {
    display: flex;
    gap: 16px;
    padding: 2px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.01);
  }

  .log-ts { color: rgba(148, 163, 184, 0.5); flex-shrink: 0; width: 64px; }
  .log-msg { word-break: break-word; flex: 1; }
  .log-msg.info  { color: #94a3b8; }
  .log-msg.ok    { color: var(--accent2-light); }
  .log-msg.warn  { color: var(--warn); }
  .log-msg.error { color: var(--err); font-weight: 600; }

  .log-empty {
    color: var(--muted);
    text-align: center;
    padding: 64px;
    font-size: 13px;
  }

  .log-empty span {
    font-size: 32px;
    display: block;
    margin-bottom: 12px;
    opacity: 0.3;
  }

  /* Results Grid */
  .results-grid {
    flex: 1;
    overflow-y: auto;
    padding: 20px 28px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
    align-content: start;
  }

  .result-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
  }

  .result-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    background: var(--border);
    transition: background 0.2s;
  }

  .result-card:hover {
    transform: translateY(-2px);
    border-color: rgba(14, 165, 233, 0.3);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  .result-card.success::before { background: var(--accent2); }
  .result-card.failed::before  { background: var(--err); }

  .result-name {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #fff;
    padding-left: 4px;
  }

  .result-name-link {
    text-decoration: none;
    color: inherit;
  }

  .result-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding-left: 4px;
  }

  .tag {
    font-size: 11px;
    font-family: var(--sans);
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.04);
    color: var(--muted);
    border: 1px solid var(--border);
  }

  .tag.green {
    background: rgba(16, 185, 129, 0.08);
    color: var(--accent2-light);
    border-color: rgba(16, 185, 129, 0.15);
  }
  .tag.red {
    background: rgba(239, 68, 68, 0.08);
    color: var(--err);
    border-color: rgba(239, 68, 68, 0.15);
  }
  .tag.blue {
    background: rgba(14, 165, 233, 0.08);
    color: var(--accent-light);
    border-color: rgba(14, 165, 233, 0.15);
  }

  .result-empty {
    grid-column: 1/-1;
    text-align: center;
    color: var(--muted);
    font-size: 13px;
    padding: 64px;
  }

  .result-empty span {
    font-size: 32px;
    display: block;
    margin-bottom: 12px;
    opacity: 0.3;
  }

  /* Download Banner */
  .done-banner {
    margin: 16px 28px 0;
    padding: 14px 20px;
    border-radius: 8px;
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.25);
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
    animation: slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes slide-up {
    from { transform: translateY(10px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }

  .done-banner p {
    font-size: 13px;
    flex: 1;
    line-height: 1.6;
    color: #e2e8f0;
  }

  .done-banner strong { color: var(--accent2-light); }

  .dl-btn {
    padding: 8px 20px;
    background: var(--accent2);
    color: #fff;
    font-family: var(--sans);
    font-size: 13px;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: none;
    flex-shrink: 0;
    transition: all 0.2s;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
  }

  .dl-btn:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
  }

  /* ── Spinner ── */
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(255, 255, 255, 0.25);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Responsive Tablet ── */
  @media (max-width: 900px) and (min-width: 640px) {
    .main { grid-template-columns: 300px 1fr; }
    .config-section { padding: 12px 14px; }
    .section-label  { font-size: 10px; }
    .field label    { font-size: 11px; }
    .field select,
    .input-wrap input,
    .field textarea  { font-size: 12px; padding: 8px 10px; }
    .file-label      { font-size: 12px; }
    .log-console     { font-size: 11px; padding: 12px 18px; }
    .results-grid    { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
  }

  /* ── Mobile Layout ── */
  @media (max-width: 639px) {
    body {
      height: 100dvh;
      grid-template-rows: 56px 1fr;
    }
    header { padding: 0 16px; gap: 8px; }
    .brand { font-size: 14px; }
    .brand-badge { width: 28px; height: 28px; font-size: 15px; }
    .header-pill { font-size: 11px; padding: 4px 10px; }

    .main {
      display: flex;
      flex-direction: column;
      overflow: hidden;
      height: 100%;
    }
    .left {
      border-right: none;
      border-bottom: 1px solid var(--border);
      flex-shrink: 0;
      max-height: 50vh;
    }
    
    .config-collapse-btn {
      background: var(--card);
      padding: 10px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      border-bottom: 1px solid var(--border);
      user-select: none;
    }
    .config-collapse-btn span { display: flex; align-items: center; gap: 6px; }
    .config-collapse-btn em { font-style: normal; transition: transform 0.2s; }
    .config-collapse-btn.open em { transform: rotate(180deg); }

    .config-sections-wrap {
      max-height: 0; /* Default closed on mobile to save vertical space */
    }

    .config-section { padding: 10px 16px; }
    .section-label  { font-size: 9px; margin-bottom: 8px; }
    .field          { margin-bottom: 8px; }
    .field label    { font-size: 11px; }
    .input-wrap input,
    .field select,
    .field textarea { font-size: 12px; padding: 8px 10px; }

    .file-toolbar { padding: 8px 14px; gap: 6px; }
    .file-count-badge { font-size: 10px; padding: 2px 6px; }
    .tb-btn { font-size: 10px; padding: 4px 8px; }

    .file-scroll {
      flex: 1;
      min-height: 100px;
      max-height: 18vh;
      padding: 8px 12px;
    }
    .file-item  { padding: 8px 10px; margin-bottom: 4px; }
    .file-label { font-size: 12px; }

    .run-wrap { padding: 10px 14px; }
    .run-btn  { font-size: 13px; padding: 10px; }

    .right {
      flex: 1;
      min-height: 0;
    }
    .progress-bar-wrap { padding: 12px 16px; }
    .progress-row      { font-size: 11px; margin-bottom: 6px; }
    .progress-sub      { font-size: 10px; }

    .tab-bar  { padding: 0 16px; height: 42px; }
    .tab      { padding: 0 12px; font-size: 12px; margin-right: 4px; }
    .tab-actions { gap: 4px; }
    .icon-btn { font-size: 10px; padding: 4px 8px; }

    .log-console { font-size: 11px; line-height: 1.7; padding: 12px 16px; }
    .log-ts      { width: 52px; font-size: 10px; }

    .results-grid {
      padding: 12px 16px;
      grid-template-columns: 1fr;
      gap: 10px;
    }
    .result-card { padding: 12px; }
    .result-name { font-size: 12px; }

    .done-banner { margin: 12px 16px 0; padding: 10px 14px; }
    .done-banner p { font-size: 12px; }
    .dl-btn { font-size: 12px; padding: 6px 12px; }
  }

  /* Custom Scrollbar Styles */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border-hover); border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
</head>
<body>

<!-- Header -->
<header>
  <div class="brand">
    <div class="brand-badge">⚕️</div>
    MCQ PDF Converter
  </div>
  <div class="header-version">
    Gemini Engine
  </div>
  <div class="header-pill" id="statusPill">พร้อมใช้งาน</div>
</header>

<!-- Main Interface -->
<div class="main">

  <!-- Left Sidebar Panel -->
  <div class="left">
    
    <!-- Scrollable container for settings and file elements -->
    <div class="sidebar-content">
      
      <!-- Collapsible Settings Accordion (Active across all screen resolutions) -->
      <div class="config-collapse-btn open" id="configToggle" onclick="toggleConfig()">
        <span>⚙️ ตั้งค่า API &amp; Model Instruction</span>
        <em class="chevron">▼</em>
      </div>

      <div class="config-sections-wrap" id="configWrap">

        <!-- 1. API Configuration -->
        <div class="config-section">
          <div class="section-label">🔑 API CONFIGURATION</div>

          <div class="field">
            <label>Google AI Studio API Key</label>
            <div class="hint">รับโทเค็นความปลอดภัยที่ <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--accent-light); text-decoration:none">aistudio.google.com</a></div>
            <div class="input-wrap">
              <input type="password" id="apiKey" placeholder="AIzaSy...">
              <button class="eye-btn" id="eyeBtn" type="button">👁</button>
            </div>
          </div>

          <div class="field">
            <label>Gemini Model Selector</label>
            <select id="modelSelect">
              <!-- Gemini 3.5 & 3.1 Frontier Models -->
              <option value="gemini-3.5-flash" selected>gemini-3.5-flash (เร็วสูงสุด · ความสามารถระดับ Pro · แนะนำ)</option>
              <option value="gemini-3.1-pro">gemini-3.1-pro (วิเคราะห์เชิงลึกและ Coding สูงสุด)</option>
              <option value="gemini-3.1-flash-lite">gemini-3.1-flash-lite (ประหยัดค่าใช้จ่ายและประมวลผลเร็ว)</option>
              <!-- Gemini 2.5 Production-Ready Stable Models -->
              <option value="gemini-2.5-pro">gemini-2.5-pro (โมเดลระดับ Pro ความเสถียรสูง)</option>
              <option value="gemini-2.5-flash">gemini-2.5-flash (โมเดลทั่วไป ความเสถียรสูง)</option>
            </select>
          </div>
        </div>

        <!-- 2. Course Preset & Prompt Configuration -->
        <div class="config-section">
          <div class="section-label">📚 COURSE PRESET</div>

          <div class="field">
            <label>โหลด Course Preset</label>
            <div class="hint">เลือกวิชาที่บันทึกไว้เพื่อโหลด Subject Code และ Lecture Topics อัตโนมัติ</div>
            <select id="coursePreset" onchange="applyCourse()">
              <option value="">— เลือก Course Preset หรือกรอกเองด้านล่าง —</option>
            </select>
          </div>

          <div class="field">
            <label>Subject Code <span style="font-weight:400;opacity:.7">(กรอกเองหรือโหลดจาก Preset)</span></label>
            <input type="text" id="subjectTitle" placeholder="เช่น EMBRYO, CVS, GI, HEMATO" style="text-transform:uppercase">
          </div>
        </div>

        <!-- 3. Extra Prompt Instruction -->
        <div class="config-section">
          <div class="section-label">📝 EXTRA PROMPT INSTRUCTION</div>

          <div class="field">
            <label>Lecture Topics / คำสั่งเฉพาะวิชาเพิ่มเติม</label>
            <textarea id="additionalPrompt" rows="4" placeholder="ระบุรายชื่อ Lecture Topics หรือคำสั่งเสริมพิเศษรอบนี้&#10;(จะถูกโหลดอัตโนมัติเมื่อเลือก Course Preset)"></textarea>
          </div>
        </div>

      </div><!-- /config-sections-wrap -->

      <!-- File selection list -->
      <div class="file-toolbar">
        <span class="file-count-badge" id="fileCount">0 ไฟล์</span>
        <button class="tb-btn" onclick="selectAll()">เลือกทั้งหมด</button>
        <button class="tb-btn" onclick="deselectAll()">ยกเลิก</button>
        <button class="tb-btn refresh" onclick="loadFiles()">🔄 รีเฟรช</button>
      </div>

      <div class="file-scroll" id="fileList">
        <div class="empty-files"><span>📂</span>กำลังโหลด...</div>
      </div>

    </div><!-- /sidebar-content -->

    <!-- Sticky Footer Run Button -->
    <div class="run-wrap">
      <button class="run-btn" id="runBtn" onclick="startConversion()">
        <span id="runIcon">▶</span>
        <span id="runLabel">เริ่มประมวลผลข้อสอบ</span>
      </button>
    </div>

  </div><!-- /left sidebar -->

  <!-- Right Log and Results Panel -->
  <div class="right">

    <!-- Progress panel -->
    <div class="progress-bar-wrap">
      <div class="progress-row">
        <span class="progress-label" id="progLabel">รอการเริ่มประมวลผล</span>
        <span class="progress-pct" id="progPct">0%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" id="progFill" style="width:0%"></div>
      </div>
      <div class="progress-sub" id="progSub"></div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tab-bar">
      <div class="tab active" id="tabLog" onclick="switchTab('log')">📋 Log Console</div>
      <div class="tab" id="tabResults" onclick="switchTab('results')">✅ ผลลัพธ์การแปลง</div>
      <div class="tab-actions">
        <button class="icon-btn" onclick="clearLog()">🗑 ล้าง Log</button>
        <button class="icon-btn" onclick="loadOutputs()">🔄 อัปเดตตารางผลลัพธ์</button>
      </div>
    </div>

    <!-- Placement wrapper for output zip banner -->
    <div id="doneBannerWrap"></div>

    <!-- Tab 1: Terminal Log Panel -->
    <div id="panelLog" style="display:flex;flex-direction:column;flex:1;overflow:hidden">
      <div class="log-console" id="logConsole">
        <div class="log-empty"><span>🖥️</span>รอสัญญาณเริ่มแปลงไฟล์... Log จะแสดงขึ้นที่นี่</div>
      </div>
    </div>

    <!-- Tab 2: Converted Results View Panel -->
    <div id="panelResults" style="display:none;flex-direction:column;flex:1;overflow:hidden">
      <div class="results-grid" id="resultsGrid">
        <div class="result-empty"><span>📁</span>ยังไม่มีข้อมูลที่จัดเก็บในเซิร์ฟเวอร์</div>
      </div>
    </div>

  </div><!-- /right -->

</div><!-- /main -->

<script>
let selectedFiles = new Set();
let allFiles = [];
let pollTimer = null;
let lastLogCount = 0;
let currentTab = 'log';
let currentJobId = null;

// ─── Collapsible API & Configuration ───
function toggleConfig() {
  const wrap = document.getElementById('configWrap');
  const btn  = document.getElementById('configToggle');
  const isOpen = btn.classList.contains('open');
  if (isOpen) {
    wrap.style.maxHeight = wrap.scrollHeight + 'px';
    requestAnimationFrame(() => { wrap.style.maxHeight = '0'; });
    btn.classList.remove('open');
  } else {
    wrap.style.maxHeight = wrap.scrollHeight + 'px';
    btn.classList.add('open');
    wrap.addEventListener('transitionend', () => { 
      if (btn.classList.contains('open')) wrap.style.maxHeight = 'none'; 
    }, { once: true });
  }
}

// Initial structural settings loaded dynamically
// ─── Course Preset Loader ───
async function loadCourses() {
  try {
    const r = await fetch('/api/courses');
    const d = await r.json();
    const sel = document.getElementById('coursePreset');
    sel.innerHTML = '<option value="">— เลือก Course Preset หรือกรอกเองด้านล่าง —</option>';
    (d.courses || []).forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      sel.appendChild(opt);
    });
  } catch(e) {}
}

async function applyCourse() {
  const id = document.getElementById('coursePreset').value;
  if (!id) return;
  try {
    const r = await fetch('/api/courses/' + id);
    const d = await r.json();
    if (d.subject_code) {
      document.getElementById('subjectTitle').value = d.subject_code;
    }
    if (d.subgroup === 'LEC' && d.topics && d.topics.length) {
      let prompt = 'รายชื่อหัวข้อบรรยาย (Lecture Topics) สำหรับการ assign category[1]:\n';
      d.topics.forEach((t, i) => { prompt += `${i + 1}. ${t}\n`; });
      prompt += '\nคำสั่งพิเศษ:\n';
      prompt += `- SubjectCode = ${d.subject_code}\n`;
      prompt += `- SubGroupSuffix = LEC\n`;
      prompt += `- category[1] = ${d.subject_code}_LEC_<TopicLabel> (ต้องตรงกับรายชื่อ lecture ทุกตัวอักษร)\n`;
      prompt += `- ถ้าข้อสอบไม่ตรงกับ lecture ใดเลย ให้ใช้ topic ที่ใกล้เคียงที่สุดจากรายการ`;
      document.getElementById('additionalPrompt').value = prompt;
    } else if (Array.isArray(d.subgroup) && d.subgroup.length) {
      let prompt = '📝 EXTRA PROMPT INSTRUCTION\n\n';
      prompt += `SubjectCode = ${d.subject_code}\n`;
      prompt += `SubGroupSuffix = auto-classify จาก disciplines ต่อไปนี้: ${d.subgroup.join(', ')}\n\n`;
      prompt += 'คำสั่งพิเศษ:\n';
      prompt += `- category[0] = ${d.subject_code}_<ExamGroup>\n`;
      prompt += `- category[1] = ${d.subject_code}_<SubGroupSuffix>_<TopicLabel>\n`;
      prompt += `- <SubGroupSuffix> ต้องเป็นหนึ่งใน: ${d.subgroup.join(' / ')}\n`;
      prompt += '- เลือก SubGroupSuffix ที่ตรงกับเนื้อหาหลักของข้อสอบแต่ละข้อ (keyword-based)\n';
      prompt += '- ห้ามใช้ LEC เป็น SubGroupSuffix';
      document.getElementById('additionalPrompt').value = prompt;
    }
  } catch(e) { alert('โหลด Course Preset ล้มเหลว: ' + e.message); }
}

window.addEventListener('DOMContentLoaded', () => {
  loadCourses();
  const wrap = document.getElementById('configWrap');
  const btn  = document.getElementById('configToggle');
  
  if (window.innerWidth >= 900) {
    wrap.style.maxHeight = 'none';
    btn.classList.add('open');
  } else {
    wrap.style.maxHeight = '0';
    btn.classList.remove('open');
  }
});

// ─── Interactive Key Toggle (Eye Button) ───
document.getElementById('eyeBtn').onclick = () => {
  const inp = document.getElementById('apiKey');
  inp.type = inp.type === 'password' ? 'text' : 'password';
};

// ─── Async File List Loader ───
async function loadFiles() {
  try {
    const r = await fetch('/api/files');
    const d = await r.json();
    allFiles = d.files || [];
    renderFiles();
  } catch(e) {}
}

function renderFiles(processingName = '', results = []) {
  const wrap = document.getElementById('fileList');
  document.getElementById('fileCount').textContent = `${allFiles.length} ไฟล์`;

  if (!allFiles.length) {
    wrap.innerHTML = `<div class="empty-files"><span>📂</span>ไม่พบ PDF ในโฟลเดอร์ input_pdfs/ กรุณาตรวจสอบแล้วกดรีเฟรช</div>`;
    return;
  }

  const resultMap = {};
  (results || []).forEach(r => resultMap[r.file] = r.status);

  wrap.innerHTML = allFiles.map(name => {
    const sel = selectedFiles.has(name);
    let cls = sel ? 'selected' : '';
    let icon = '';

    if (name === processingName) {
      cls = 'processing'; icon = '<span class="spinner"></span>';
    } else if (resultMap[name] === 'success') {
      cls = 'done'; icon = '✅';
    } else if (resultMap[name] === 'failed') {
      cls = 'failed'; icon = '❌';
    }

    return `<div class="file-item ${cls}" data-name="${escHtml(name)}" onclick="toggleFile(this.dataset.name)">
      <div class="file-checkbox">${sel ? '✓' : ''}</div>
      <div class="file-label" title="${escHtml(name)}">${escHtml(name)}</div>
      <div class="file-status-icon">${icon}</div>
    </div>`;
  }).join('');
}

function toggleFile(name) {
  if (selectedFiles.has(name)) selectedFiles.delete(name);
  else selectedFiles.add(name);
  renderFiles();
}

function selectAll()   { selectedFiles = new Set(allFiles); renderFiles(); }
function deselectAll() { selectedFiles.clear(); renderFiles(); }

function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tabLog').classList.toggle('active', tab === 'log');
  document.getElementById('tabResults').classList.toggle('active', tab === 'results');
  document.getElementById('panelLog').style.display     = tab === 'log'     ? 'flex' : 'none';
  document.getElementById('panelResults').style.display = tab === 'results' ? 'flex' : 'none';
  if (tab === 'results') loadOutputs();
}

function clearLog() {
  document.getElementById('logConsole').innerHTML = `<div class="log-empty"><span>🖥️</span>ประวัติ Log ปัจจุบันถูกล้างเรียบร้อยแล้ว</div>`;
  lastLogCount = 0;
}

async function startConversion() {
  const apiKey    = document.getElementById('apiKey').value.trim();
  const model     = document.getElementById('modelSelect').value;
  const addPrompt    = document.getElementById('additionalPrompt').value.trim();
  const subjectTitle = document.getElementById('subjectTitle').value.trim().toUpperCase();

  if (!apiKey) { alert('กรุณาระบุ Gemini API Key ให้สมบูรณ์ก่อนดำเนินการ'); return; }
  if (!selectedFiles.size) { alert('กรุณาเลือกไฟล์อย่างน้อย 1 รายการเพื่อดำเนินระบบ'); return; }

  lastLogCount = 0;
  document.getElementById('logConsole').innerHTML = '';
  document.getElementById('doneBannerWrap').innerHTML = '';

  currentJobId = 'job_' + Date.now();

  try {
    const r = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        model: model,
        files: [...selectedFiles],
        job_id: currentJobId,
        subject_title: subjectTitle,
        additional_prompt: addPrompt
      })
    });
    const d = await r.json();
    if (!d.ok) { alert(d.error); return; }
    startPolling();
  } catch(e) {
    alert('ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ระบบ: ' + e.message);
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(pollStatus, 1200);
  pollStatus();
}

async function pollStatus() {
  if (!currentJobId) return;
  try {
    const r = await fetch(`/api/status/${currentJobId}`);
    const d = await r.json();
    updateUI(d);
    if (!d.running) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  } catch(e) {}
}

function updateUI(d) {
  const pill = document.getElementById('statusPill');
  if (d.running) {
    pill.textContent = `กำลังประมวลผล ${d.done}/${d.total}`;
    pill.className = 'header-pill running';
  } else if (d.done > 0) {
    pill.textContent = `ประมวลผลสำเร็จ ${d.done} ไฟล์`;
    pill.className = 'header-pill done';
  } else {
    pill.textContent = 'พร้อมใช้งาน';
    pill.className = 'header-pill';
  }

  document.getElementById('progFill').style.width = d.progress + '%';
  document.getElementById('progPct').textContent = d.progress + '%';

  if (d.running) {
    document.getElementById('progLabel').textContent = `กำลังดำเนินการไฟล์ที่ ${d.done + 1} จากทั้งหมด ${d.total}`;
    document.getElementById('progSub').textContent = d.current_file ? `⚙️ ${d.current_file}` : '';
  } else if (d.done > 0) {
    const ok = (d.results || []).filter(r => r.status === 'success').length;
    document.getElementById('progLabel').textContent = `กระบวนการแปลงเสร็จสมบูรณ์ — สำเร็จ ${ok}/${d.done} ไฟล์`;
    document.getElementById('progSub').textContent = '';
  }

  const btn  = document.getElementById('runBtn');
  const icon = document.getElementById('runIcon');
  const lbl  = document.getElementById('runLabel');

  if (d.running) {
    btn.disabled = true;
    btn.className = 'run-btn running-state';
    icon.innerHTML = '<div class="spinner"></div>';
    lbl.textContent = 'ระบบกำลังทำงานค้างอยู่...';
  } else {
    btn.disabled = false;
    btn.className = 'run-btn';
    icon.textContent = '▶';
    lbl.textContent = 'เริ่มประมวลผลข้อสอบ';
  }

  renderFiles(d.current_file, d.results || []);

  const logs = d.logs || [];
  const total = d.total_log_count ?? logs.length;
  const sliceOffset = total - logs.length;
  if (total > lastLogCount) {
    const console_ = document.getElementById('logConsole');
    if (lastLogCount === 0) console_.innerHTML = '';
    const startInSlice = Math.max(0, lastLogCount - sliceOffset);
    for (let i = startInSlice; i < logs.length; i++) {
      const e = logs[i];
      const line = document.createElement('div');
      line.className = 'log-line';
      line.innerHTML = `<span class="log-ts">${e.ts}</span><span class="log-msg ${e.level}">${escHtml(e.msg)}</span>`;
      console_.appendChild(line);
    }
    console_.scrollTop = console_.scrollHeight;
    lastLogCount = total;
  }

  if (!d.running && d.done > 0 && d.zip_path) {
    const banner = document.getElementById('doneBannerWrap');
    if (!banner.innerHTML) {
      banner.innerHTML = `<div class="done-banner">
        <p>🎉 ระบบดำเนินการวิเคราะห์และแปลงไฟล์ข้อสอบจำนวน <strong>${d.done} ไฟล์</strong> เรียบร้อยแล้ว!<br>
        คุณสามารถดาวน์โหลดผลสัมฤทธิ์ทั้งหมด (เอกสาร JSON พร้อมสื่อภาพประกอบแยกหน้า) ในรูปแบบ ZIP Archive ได้ที่นี่</p>
        <a class="dl-btn" href="/api/download/${currentJobId}">⬇ ดาวน์โหลดแฟ้มผลลัพธ์ ZIP</a>
      </div>`;
    }
  }

  if (!d.running && d.done > 0 && currentTab === 'log') {
    setTimeout(() => switchTab('results'), 1500);
  }
}

async function loadOutputs() {
  try {
    const r = await fetch('/api/outputs');
    const d = await r.json();
    renderOutputs(d.outputs || []);
  } catch(e) {}
}

function renderOutputs(outputs) {
  const grid = document.getElementById('resultsGrid');
  if (!outputs.length) {
    grid.innerHTML = `<div class="result-empty"><span>📁</span>ยังไม่มีข้อมูลที่จัดเก็บในระบบ</div>`;
    return;
  }
  grid.innerHTML = outputs.map(o => `
    <div class="result-card success">
      <div class="result-name" title="${escHtml(o.name)}">📄 ${escHtml(o.name)}</div>
      <div class="result-meta">
        <span class="tag green">✓ ${o.questions} คำถาม</span>
        ${o.has_images ? '<span class="tag blue">🖼 มีภาพประกอบ</span>' : ''}
        <span class="tag">${o.converted_at ? o.converted_at.slice(0,16).replace('T',' ') : ''}</span>
      </div>
    </div>
  `).join('');
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;');
}

// Initial Load Commands
loadFiles();
loadOutputs();
setInterval(loadFiles, 15000);
</script>
</body>
</html>
"""


# ─── Entry point ──────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  MCQ PDF Converter — http://localhost:8765")
    print("=" * 55)
    print(f"  Input dir   : {INPUT_DIR}")
    print(f"  Output dir  : {OUTPUT_DIR}")
    print(f"  Prompt file : {PROMPT_FILE}")
    print()

    # Dynamic Live-Reload Initializer
    if not PROMPT_FILE.exists():
        try:
            PROMPT_FILE.write_text(DEFAULT_SYSTEM_PROMPT, encoding="utf-8")
            print(f"📝 Created default markdown rule file: {PROMPT_FILE}")
        except Exception as e:
            print(f"⚠️ Failed to write default rule file: {e}")
            
    app.run(debug=False, host="0.0.0.0", port=8765, threaded=True)