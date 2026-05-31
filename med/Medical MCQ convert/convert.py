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

import os, sys, json, base64, re, subprocess, time, threading, uuid, html
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

PROMPT_FILE = BASE_DIR / "medical-quiz-converter.md"

# ─── Dynamic Category Parser & Helper ────────────────
def parse_filename_metadata(file_stem: str) -> dict:
    parts = re.split(r'[_ \-]+', file_stem.strip())
    
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

def sanitize_category(category_data, file_stem: str) -> list:
    """
    Standardizes the category array dynamically based on the input:
    Index 0: Default CategoryID (<SubjectCode>_<ExamGroup>)
    Index 1: Standardized CategoryID (<SubjectCode>_<SubGroupSuffix>_<TopicLabel>)
    """
    meta = parse_filename_metadata(file_stem)
    subject_code = meta["subject_code"]
    exam_group = meta["exam_group"]
    topic_label = meta["topic_label"]
    
    subgroups = ["ANA", "BIOCHEM", "PHYSIO", "MICRO", "PARASITO", "PATHO", "PHARM", "RADIO", "CLINICAL"]
    
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
        "ANA": ["ANA", "ANATOMY", "HISTO", "EMBRYO", "NEUROANA", "STRUCTURE", "GROSS", "กายวิภาค"],
        "BIOCHEM": ["BIOCHEM", "BIOCHEMISTRY", "MOLECULAR", "METABOLISM", "GENE", "CELL", "ชีวเคมี"],
        "PHYSIO": ["PHYSIO", "PHYSIOLOGY", "FUNCTION", "MECHANISM", "สรีรวิทยา"],
        "MICRO": ["MICRO", "MICROBIO", "MICROBIOLOGY", "VIRO", "BACTERIO", "IMMUNO", "INFECTION", "BACTERIA", "VIRUS", "จุลชีววิทยา"],
        "PARASITO": ["PARASITO", "PARASITOLOGY", "HELMINTH", "PROTOZOA", "WORM", "พยาธิใบไม้", "ปรสิต"],
        "PATHO": ["PATHO", "PATHOLOGY", "LESION", "BIOPSY", "HISTOPATHO", "พยาธิวิทยา"],
        "PHARM": ["PHARM", "PHARMA", "PHARMACOLOGY", "DRUG", "MEDICATION", "เภสัช"],
        "RADIO": ["RADIO", "RADIOLOGY", "XRAY", "IMAGING", "CT", "MRI", "ULTRASOUND", "รังสี"],
        "CLINICAL": ["CLINICAL", "MEDICINE", "SURGERY", "PEDIATRIC", "OBGYN", "DIAGNOSIS", "VIGNETTE", "CASE", "MANAGEMENT", "คลินิก"]
    }
    
    sub_group = None
    topic_upper = clean_topic.upper()
    
    # 1. Primary classification check on the actual topic name
    for g, keywords in SUBGROUP_KEYWORDS.items():
        for kw in keywords:
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
def extract_images(pdf_path: Path, images_dir: Path) -> int:
    images_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    
    try:
        import fitz  # PyMuPDF
        import io
        from PIL import Image
        
        pdf_file = fitz.open(str(pdf_path))
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
                        image_name = f"page_{page_index + 1}_img_{image_index}.{image_ext}"
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
            doc = pdfium.PdfDocument(str(pdf_path))
            for i, page in enumerate(doc):
                bitmap = page.render(scale=1.5)
                pil_img = bitmap.to_pil()
                out = images_dir / f"page_{i+1:03d}_render.png"
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

    stem     = pdf_path.stem
    out_dir  = OUTPUT_DIR / stem
    imgs_dir = out_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

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
    if "pro" in model_name.lower() or "3.5" in model_name:
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

    # ── Step 1: Extract images ──
    push_log(job, f"[{stem}] ดึงรูปภาพจาก PDF...", "info")
    try:
        n = extract_images(pdf_path, imgs_dir)
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
        pdf_bytes = pdf_path.read_bytes()
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
        for q in questions:
            if isinstance(q, dict):
                q["category"] = sanitize_category(q.get("category"), stem)
                
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
    all_batch_data = {}

    for i, pdf_path in enumerate(pdfs):
        if not pdf_path.exists():
            push_log(job, f"ไม่พบ {pdf_path.name}", "error")
            continue

        job["current_file"] = pdf_path.name
        job["progress"] = int(i / len(pdfs) * 100)

        summary, questions = process_pdf(job, client, model_name, pdf_path, subject_title, additional_prompt)
        job["results"].append(summary)
        job["done"] = i + 1

        # ส่วนที่ปรับปรุง: คีย์ของข้อมูลชุดข้อสอบใน quizdata.js จะถูกเปลี่ยนให้เป็น Default_CategoryID ของคำถาม
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
                meta = parse_filename_metadata(pdf_path.stem)
                default_cat_id = f"{meta['subject_code']}_{meta['exam_group']}"
                
            all_batch_data[default_cat_id] = questions

        # Add proactive cooldown delay to protect rate limit (RPM limit)
        if i < len(pdfs) - 1:
            cooldown_secs = 12
            push_log(job, f"⏳ พักระบบ {cooldown_secs} วินาทีก่อนเริ่มแปลงไฟล์ถัดไปเพื่อเลี่ยงการชนโควตา RPM...", "info")
            time.sleep(cooldown_secs)

    # Create Combined JS File at the root of OUTPUT_DIR
    combined_js_path = OUTPUT_DIR / "quizdata.js"
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
                
            for stem in [Path(n).stem for n in filenames]:
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
    return jsonify({**{k: v for k, v in job.items() if k != "logs"}, "logs": logs})

@app.route("/api/download/<job_id>")
def api_download(job_id: str):
    if job_id not in _jobs:
        return "ไม่พบ job", 404
    zip_path = _jobs[job_id].get("zip_path")
    if not zip_path or not Path(zip_path).exists():
        return "ไฟล์ยังไม่พร้อม", 404
    return send_file(zip_path, as_attachment=True)


# ─── Embedded HTML ────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCQ PDF Converter — Gemini</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:        #0d1117;
    --surface:   #161b22;
    --card:      #1c2230;
    --border:    #30363d;
    --accent:    #58a6ff;
    --accent2:   #3fb950;
    --warn:      #f0883e;
    --err:       #f85149;
    --purple:    #bc8cff;
    --text:      #e6edf3;
    --muted:     #8b949e;
    --mono:      'IBM Plex Mono', monospace;
    --sans:      'IBM Plex Sans Thai', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    height: 100vh;
    display: grid;
    grid-template-rows: 56px 1fr;
    overflow: hidden;
  }

  /* ── Header ── */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    padding: 0 24px;
    gap: 16px;
    flex-shrink: 0;
  }

  .brand {
    display: flex; align-items: center; gap: 10px;
    font-size: 15px; font-weight: 600; letter-spacing: -0.02em;
  }

  .brand-badge {
    width: 30px; height: 30px;
    background: linear-gradient(135deg, var(--accent), var(--purple));
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
  }

  .header-pill {
    margin-left: auto;
    font-family: var(--mono);
    font-size: 11px;
    padding: 4px 12px;
    border-radius: 20px;
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--muted);
    transition: all 0.3s;
  }

  .header-pill.running {
    background: rgba(88,166,255,0.1);
    border-color: var(--accent);
    color: var(--accent);
    animation: pulse-glow 2s infinite;
  }

  .header-pill.done {
    background: rgba(63,185,80,0.1);
    border-color: var(--accent2);
    color: var(--accent2);
  }

  @keyframes pulse-glow {
    0%,100% { box-shadow: 0 0 0 0 rgba(88,166,255,0.4); }
    50%      { box-shadow: 0 0 0 5px rgba(88,166,255,0); }
  }

  /* ── Main Layout ── */
  .main {
    display: grid;
    grid-template-columns: 360px 1fr;
    overflow: hidden;
  }

  /* ── Left Panel ── */
  .left {
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .config-section {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }

  .section-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
  }

  .field { margin-bottom: 10px; }
  .field:last-child { margin-bottom: 0; }

  .field label {
    display: block;
    font-size: 12px;
    font-weight: 500;
    color: var(--muted);
    margin-bottom: 5px;
  }

  .field .hint {
    font-size: 11px;
    color: var(--muted);
    opacity: 0.7;
    margin-bottom: 5px;
  }

  .input-wrap { position: relative; }

  .input-wrap input,
  .field input[type="text"],
  .field select {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: var(--sans);
    font-size: 12px;
    padding: 8px 10px;
    outline: none;
    transition: border-color 0.15s;
    -webkit-appearance: none;
  }

  .input-wrap input {
    padding-right: 36px;
    font-family: var(--mono);
  }

  .field select {
    padding-right: 28px;
    cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%238b949e' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
  }

  .field textarea {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: var(--sans);
    font-size: 12px;
    padding: 8px 10px;
    outline: none;
    resize: vertical;
    transition: border-color 0.15s;
  }

  .input-wrap input:focus,
  .field input[type="text"]:focus,
  .field select:focus,
  .field textarea:focus {
    border-color: var(--accent);
  }

  .eye-btn {
    position: absolute; right: 8px; top: 50%;
    transform: translateY(-50%);
    background: none; border: none;
    cursor: pointer; color: var(--muted);
    font-size: 13px; padding: 2px 4px;
    line-height: 1;
    transition: color 0.15s;
  }

  .eye-btn:hover { color: var(--text); }

  /* ── Config collapse wrapper ── */
  .config-sections-wrap {
    overflow: hidden;
    transition: max-height 0.3s ease;
  }
  .file-toolbar {
    padding: 8px 18px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .file-count-badge {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
    background: var(--bg);
    padding: 2px 8px;
    border-radius: 10px;
    border: 1px solid var(--border);
  }

  .tb-btn {
    font-size: 11px;
    color: var(--accent);
    background: none;
    border: none;
    cursor: pointer;
    font-family: var(--sans);
    padding: 2px 6px;
    border-radius: 4px;
    transition: background 0.15s;
  }

  .tb-btn:hover { background: rgba(88,166,255,0.1); }

  .tb-btn.refresh {
    margin-left: auto;
    color: var(--muted);
    border: 1px solid var(--border);
    padding: 3px 8px;
  }

  .tb-btn.refresh:hover { border-color: var(--accent); color: var(--accent); }

  .file-scroll {
    flex: 1;
    min-height: 200px;
    overflow-y: auto;
    padding: 8px 12px;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 6px;
    cursor: pointer;
    margin-bottom: 3px;
    border: 1px solid transparent;
    transition: all 0.12s;
    user-select: none;
  }

  .file-item:hover { background: var(--card); }

  .file-item.selected {
    background: rgba(88,166,255,0.08);
    border-color: rgba(88,166,255,0.25);
  }

  .file-item.processing {
    background: rgba(240,136,62,0.07);
    border-color: rgba(240,136,62,0.35);
  }

  .file-item.done {
    background: rgba(63,185,80,0.06);
    border-color: rgba(63,185,80,0.25);
  }

  .file-item.failed {
    background: rgba(248,81,73,0.06);
    border-color: rgba(248,81,73,0.25);
  }

  .file-checkbox {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 1.5px solid var(--border);
    background: var(--bg);
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px;
    transition: all 0.12s;
  }

  .file-item.selected .file-checkbox {
    background: var(--accent);
    border-color: var(--accent);
    color: #000;
  }

  .file-label {
    font-size: 12px;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .file-status-icon {
    font-size: 13px;
    flex-shrink: 0;
  }

  .empty-files {
    text-align: center;
    padding: 32px 16px;
    color: var(--muted);
    font-size: 13px;
  }

  .empty-files span {
    font-size: 28px;
    display: block;
    margin-bottom: 8px;
    opacity: 0.5;
  }

  /* ── Run Button ── */
  .run-wrap {
    padding: 14px 18px;
    border-top: 1px solid var(--border);
    flex-shrink: 0;
  }

  .run-btn {
    width: 100%;
    padding: 11px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
    color: #000;
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 700;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .run-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(88,166,255,0.3);
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
  }

  /* ── Right Panel ── */
  .right {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg);
  }

  /* Progress */
  .progress-bar-wrap {
    padding: 14px 22px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }

  .progress-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 7px;
    font-size: 12px;
  }

  .progress-label { font-weight: 500; }

  .progress-pct {
    font-family: var(--mono);
    color: var(--accent);
  }

  .progress-track {
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--purple));
    border-radius: 2px;
    transition: width 0.5s ease;
  }

  .progress-sub {
    margin-top: 5px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
    min-height: 15px;
  }

  /* Tabs */
  .tab-bar {
    display: flex;
    align-items: center;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 22px;
  }

  .tab {
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    color: var(--muted);
    border-bottom: 2px solid transparent;
    transition: all 0.15s;
    margin-right: 4px;
  }

  .tab.active {
    color: var(--text);
    border-bottom-color: var(--accent);
  }

  .tab-actions { margin-left: auto; display: flex; gap: 6px; }

  .icon-btn {
    font-size: 12px;
    color: var(--muted);
    background: none;
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 4px 10px;
    cursor: pointer;
    font-family: var(--sans);
    transition: all 0.15s;
  }

  .icon-btn:hover { border-color: var(--accent); color: var(--accent); }

  /* Log Console */
  .log-console {
    flex: 1;
    overflow-y: auto;
    padding: 14px 22px;
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.75;
  }

  .log-line {
    display: flex;
    gap: 12px;
    padding: 1px 0;
  }

  .log-ts { color: var(--muted); flex-shrink: 0; width: 60px; }
  .log-msg { word-break: break-word; flex: 1; }
  .log-msg.info  { color: var(--text); }
  .log-msg.ok    { color: var(--accent2); }
  .log-msg.warn  { color: var(--warn); }
  .log-msg.error { color: var(--err); }

  .log-empty {
    color: var(--muted);
    text-align: center;
    padding: 48px;
    font-size: 13px;
  }

  .log-empty span {
    font-size: 28px;
    display: block;
    margin-bottom: 8px;
    opacity: 0.4;
  }

  /* Results Grid */
  .results-grid {
    flex: 1;
    overflow-y: auto;
    padding: 16px 22px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
    align-content: start;
  }

  .result-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    transition: border-color 0.2s;
  }

  .result-card:hover { border-color: rgba(88,166,255,0.4); }

  .result-card.success { border-left: 3px solid var(--accent2); }
  .result-card.failed  { border-left: 3px solid var(--err); }

  .result-name {
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .result-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .tag {
    font-size: 11px;
    font-family: var(--mono);
    padding: 2px 7px;
    border-radius: 4px;
    background: rgba(255,255,255,0.05);
    color: var(--muted);
  }

  .tag.green { background: rgba(63,185,80,0.12); color: var(--accent2); }
  .tag.red   { background: rgba(248,81,73,0.12); color: var(--err); }
  .tag.blue  { background: rgba(88,166,255,0.12); color: var(--accent); }

  .result-empty {
    grid-column: 1/-1;
    text-align: center;
    color: var(--muted);
    font-size: 13px;
    padding: 48px;
  }

  .result-empty span {
    font-size: 28px;
    display: block;
    margin-bottom: 8px;
    opacity: 0.4;
  }

  /* Download banner */
  .done-banner {
    margin: 0 22px 14px;
    padding: 12px 16px;
    border-radius: 8px;
    background: rgba(63,185,80,0.08);
    border: 1px solid rgba(63,185,80,0.3);
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .done-banner p {
    font-size: 13px;
    flex: 1;
    line-height: 1.5;
  }

  .done-banner strong { color: var(--accent2); }

  .dl-btn {
    padding: 7px 16px;
    background: var(--accent2);
    color: #000;
    font-family: var(--sans);
    font-size: 13px;
    font-weight: 700;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: none;
    flex-shrink: 0;
    transition: opacity 0.15s;
  }

  .dl-btn:hover { opacity: 0.85; }

  /* ── Spinner ── */
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(255,255,255,0.2);
    border-top-color: var(--text);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Tablet: 640–900px ── */
  @media (max-width: 900px) and (min-width: 640px) {
    .main { grid-template-columns: 280px 1fr; }
    .config-collapse-btn { display: none; }
    .config-sections-wrap { max-height: none !important; }
    .config-section { padding: 10px 12px; }
    .section-label  { font-size: 9px; }
    .field label    { font-size: 11px; }
    .field select,
    .input-wrap input,
    .field textarea  { font-size: 11px; padding: 7px 9px; }
    .file-label      { font-size: 11px; }
    .log-console     { font-size: 11px; padding: 10px 14px; }
    .log-ts          { width: 50px; }
    .results-grid    { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
  }

  /* ── Desktop: hide collapse button ── */
  @media (min-width: 900px) {
    .config-collapse-btn { display: none; }
    .config-sections-wrap { max-height: none !important; }
  }

  /* ── Mobile: <640px ── */
  @media (max-width: 639px) {
    body {
      height: 100dvh;
      grid-template-rows: 48px 1fr;
      overflow: hidden;
    }
    header { padding: 0 14px; gap: 10px; }
    .brand { font-size: 13px; }
    .brand-badge { width: 26px; height: 26px; font-size: 14px; }
    .header-pill { font-size: 10px; padding: 3px 9px; }

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
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .config-section { padding: 10px 14px; }
    .section-label  { font-size: 9px; margin-bottom: 8px; }
    .field          { margin-bottom: 8px; }
    .field label    { font-size: 11px; }
    .field .hint    { font-size: 10px; }
    .input-wrap input,
    .field select,
    .field textarea { font-size: 12px; padding: 8px 10px; }

    .file-toolbar { padding: 6px 12px; gap: 6px; }
    .file-count-badge { font-size: 10px; padding: 2px 6px; }
    .tb-btn { font-size: 10px; }

    .file-scroll {
      flex: 1;
      min-height: 80px;
      max-height: 15vh;
      overflow-y: auto;
      padding: 6px 10px;
    }
    .file-item  { padding: 7px 8px; }
    .file-label { font-size: 11px; }

    .run-wrap { padding: 10px 12px; }
    .run-btn  { font-size: 13px; padding: 10px; }

    .right {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-height: 0;
    }
    .progress-bar-wrap { padding: 10px 14px; }
    .progress-row      { font-size: 11px; margin-bottom: 5px; }
    .progress-sub      { font-size: 10px; }

    .tab-bar  { padding: 0 14px; }
    .tab      { padding: 8px 10px; font-size: 11px; }
    .tab-actions { gap: 4px; }
    .icon-btn { font-size: 10px; padding: 3px 7px; }

    .log-console { font-size: 11px; line-height: 1.65; padding: 10px 14px; }
    .log-ts      { width: 48px; font-size: 10px; flex-shrink: 0; }
    .log-msg     { font-size: 11px; }

    .results-grid {
      padding: 12px 14px;
      grid-template-columns: 1fr;
      gap: 8px;
    }
    .result-card { padding: 12px; }
    .result-name { font-size: 11px; }

    .done-banner { margin: 0 14px 10px; padding: 10px 12px; }
    .done-banner p { font-size: 12px; }
    .dl-btn { font-size: 12px; padding: 7px 14px; }
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
</head>
<body>

<!-- Header -->
<header>
  <div class="brand">
    <div class="brand-badge">⚕️</div>
    MCQ PDF Converter
  </div>
  <div style="font-size:12px;color:var(--muted);font-family:var(--mono);margin-left:8px">
    Gemini Edition
  </div>
  <div class="header-pill" id="statusPill">พร้อมใช้งาน</div>
</header>

<!-- Main -->
<div class="main">

  <!-- Left Panel -->
  <div class="left">

  <!-- Mobile: collapsible config toggle -->
  <div class="config-collapse-btn open" id="configToggle" onclick="toggleConfig()">
    <span>⚙️ ตั้งค่า API &amp; Prompt</span>
    <em class="chevron">▲</em>
  </div>

  <div class="config-sections-wrap" id="configWrap">

    <!-- 1. API Configuration -->
    <div class="config-section">
      <div class="section-label">🔑 API Configuration</div>

      <div class="field">
        <label>Google AI API Key</label>
        <div class="hint">รับได้ที่ <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--accent)">aistudio.google.com</a></div>
        <div class="input-wrap">
          <input type="password" id="apiKey" placeholder="AIzaSy...">
          <button class="eye-btn" id="eyeBtn">👁</button>
        </div>
      </div>

      <div class="field">
        <label>Gemini Model</label>
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

    <!-- 2. Combined Quiz Configuration -->
    <div class="config-section">
      <div class="section-label">📝 Quiz Configuration</div>
      
      <div class="field">
        <label>วิชา และคำสั่งเพิ่มเติม (Subject &amp; Additional Prompt)</label>
        <textarea id="additionalPrompt" rows="4" placeholder="ระบุหัวข้อวิชา และกฎเกณฑ์พิเศษที่ต้องการส่งเพิ่มเติมในรอบนี้ ตัวอย่างเช่น:&#10;[วิชา]: CVS Physiology&#10;[คำสั่ง]: แปลข้ออธิบายข้ออื่นที่ผิดเป็นภาษาไทยให้ละเอียดขึ้น..."></textarea>
      </div>
    </div>

  </div><!-- /config-sections-wrap -->

    <div class="file-toolbar">
      <span class="file-count-badge" id="fileCount">0 ไฟล์</span>
      <button class="tb-btn" onclick="selectAll()">เลือกทั้งหมด</button>
      <button class="tb-btn" onclick="deselectAll()">ยกเลิก</button>
      <button class="tb-btn refresh" onclick="loadFiles()">🔄 รีเฟรช</button>
    </div>

    <div class="file-scroll" id="fileList">
      <div class="empty-files"><span>📂</span>กำลังโหลด...</div>
    </div>

    <div class="run-wrap">
      <button class="run-btn" id="runBtn" onclick="startConversion()">
        <span id="runIcon">▶</span>
        <span id="runLabel">เริ่มแปลง</span>
      </button>
    </div>

  </div><!-- /left -->

  <!-- Right Panel -->
  <div class="right">

    <div class="progress-bar-wrap">
      <div class="progress-row">
        <span class="progress-label" id="progLabel">พร้อมใช้งาน</span>
        <span class="progress-pct" id="progPct">0%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" id="progFill" style="width:0%"></div>
      </div>
      <div class="progress-sub" id="progSub"></div>
    </div>

    <div class="tab-bar">
      <div class="tab active" id="tabLog" onclick="switchTab('log')">📋 Log</div>
      <div class="tab" id="tabResults" onclick="switchTab('results')">✅ ผลลัพธ์</div>
      <div class="tab-actions">
        <button class="icon-btn" onclick="clearLog()">🗑 ล้าง Log</button>
        <button class="icon-btn" onclick="loadOutputs()">🔄 รีเฟรชผล</button>
      </div>
    </div>

    <div id="doneBannerWrap"></div>

    <!-- Log Panel -->
    <div id="panelLog" style="display:flex;flex-direction:column;flex:1;overflow:hidden">
      <div class="log-console" id="logConsole">
        <div class="log-empty"><span>🖥️</span>Log จะปรากฏที่นี่เมื่อเริ่มแปลง</div>
      </div>
    </div>

    <!-- Results Panel -->
    <div id="panelResults" style="display:none;flex-direction:column;flex:1;overflow:hidden">
      <div class="results-grid" id="resultsGrid">
        <div class="result-empty"><span>📁</span>ยังไม่มีผลลัพธ์</div>
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

// ─── Config collapse (mobile) ───
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
    // remove fixed height after transition so content can grow
    wrap.addEventListener('transitionend', () => { wrap.style.maxHeight = 'none'; }, { once: true });
  }
}
// Init collapse state: open on desktop, open on mobile too (default open)
window.addEventListener('DOMContentLoaded', () => {
  const wrap = document.getElementById('configWrap');
  wrap.style.maxHeight = 'none';
});

// ─── Eye button ───
document.getElementById('eyeBtn').onclick = () => {
  const inp = document.getElementById('apiKey');
  inp.type = inp.type === 'password' ? 'text' : 'password';
};

// ─── File list ───
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
    wrap.innerHTML = `<div class="empty-files"><span>📂</span>วาง PDF ใน input_pdfs/ แล้วกด รีเฟรช</div>`;
    return;
  }

  const resultMap = {};
  (results || []).forEach(r => resultMap[r.file] = r.status);

  wrap.innerHTML = allFiles.map(name => {
    const sel = selectedFiles.has(name);
    let cls = sel ? 'selected' : '';
    let icon = '';

    if (name === processingName) {
      cls = 'processing'; icon = '<span class="pulse">⚙️</span>';
    } else if (resultMap[name] === 'success') {
      cls = 'done'; icon = '✅';
    } else if (resultMap[name] === 'failed') {
      cls = 'failed'; icon = '❌';
    }

    return `<div class="file-item ${cls}" onclick="toggleFile('${name}')">
      <div class="file-checkbox">${sel ? '✓' : ''}</div>
      <div class="file-label" title="${name}">${name}</div>
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
  document.getElementById('logConsole').innerHTML = `<div class="log-empty"><span>🖥️</span>Log ถูกล้างแล้ว</div>`;
  lastLogCount = 0;
}

async function startConversion() {
  const apiKey    = document.getElementById('apiKey').value.trim();
  const model     = document.getElementById('modelSelect').value;
  const addPrompt = document.getElementById('additionalPrompt').value.trim();

  if (!apiKey) { alert('กรุณากรอก Gemini API Key'); return; }
  if (!selectedFiles.size) { alert('กรุณาเลือกไฟล์อย่างน้อย 1 ไฟล์'); return; }

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
        subject_title: '',
        additional_prompt: addPrompt
      })
    });
    const d = await r.json();
    if (!d.ok) { alert(d.error); return; }
    startPolling();
  } catch(e) {
    alert('เชื่อมต่อ server ไม่ได้: ' + e.message);
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
    pill.textContent = `กำลังรัน ${d.done}/${d.total}`;
    pill.className = 'header-pill running';
  } else if (d.done > 0) {
    pill.textContent = `เสร็จแล้ว ${d.done} ไฟล์`;
    pill.className = 'header-pill done';
  } else {
    pill.textContent = 'พร้อมใช้งาน';
    pill.className = 'header-pill';
  }

  document.getElementById('progFill').style.width = d.progress + '%';
  document.getElementById('progPct').textContent = d.progress + '%';

  if (d.running) {
    document.getElementById('progLabel').textContent = `กำลังแปลง ${d.done + 1}/${d.total}`;
    document.getElementById('progSub').textContent = d.current_file ? `⚙️ ${d.current_file}` : '';
  } else if (d.done > 0) {
    const ok = (d.results || []).filter(r => r.status === 'success').length;
    document.getElementById('progLabel').textContent = `เสร็จแล้ว — ${ok}/${d.done} สำเร็จ`;
    document.getElementById('progSub').textContent = '';
  }

  const btn  = document.getElementById('runBtn');
  const icon = document.getElementById('runIcon');
  const lbl  = document.getElementById('runLabel');

  if (d.running) {
    btn.disabled = true;
    btn.className = 'run-btn running-state';
    icon.innerHTML = '<div class="spinner"></div>';
    lbl.textContent = 'กำลังรัน...';
  } else {
    btn.disabled = false;
    btn.className = 'run-btn';
    icon.textContent = '▶';
    lbl.textContent = 'เริ่มแปลง';
  }

  renderFiles(d.current_file, d.results || []);

  const logs = d.logs || [];
  if (logs.length > lastLogCount) {
    const console_ = document.getElementById('logConsole');
    if (lastLogCount === 0) console_.innerHTML = '';
    for (let i = lastLogCount; i < logs.length; i++) {
      const e = logs[i];
      const line = document.createElement('div');
      line.className = 'log-line';
      line.innerHTML = `<span class="log-ts">${e.ts}</span><span class="log-msg ${e.level}">${escHtml(e.msg)}</span>`;
      console_.appendChild(line);
    }
    console_.scrollTop = console_.scrollHeight;
    lastLogCount = logs.length;
  }

  if (!d.running && d.done > 0 && d.zip_path) {
    const banner = document.getElementById('doneBannerWrap');
    if (!banner.innerHTML) {
      banner.innerHTML = `<div class="done-banner">
        <p>✅ แปลงเสร็จแล้ว <strong>${d.done} ไฟล์</strong><br>
        พร้อมดาวน์โหลดผลลัพธ์ทั้งหมด</p>
        <a class="dl-btn" href="/api/download/${currentJobId}">⬇ ดาวน์โหลด ZIP</a>
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
    grid.innerHTML = `<div class="result-empty"><span>📁</span>ยังไม่มีผลลัพธ์</div>`;
    return;
  }
  grid.innerHTML = outputs.map(o => `
    <div class="result-card success">
      <div class="result-name">📄 ${o.name}</div>
      <div class="result-meta">
        <span class="tag green">✅ ${o.questions} ข้อ</span>
        ${o.has_images ? '<span class="tag blue">🖼 มีรูป</span>' : ''}
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

// Init
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