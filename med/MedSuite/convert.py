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
import queue, random
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, Response, send_file
import tempfile, traceback

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB (large slide decks for Notes)

# ─── Paths ───────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
INPUT_DIR  = BASE_DIR / "input_pdfs"
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

PROMPT_FILE  = BASE_DIR / "medical-quiz-converter.md"
COURSES_DIR  = BASE_DIR / "courses"
COURSES_DIR.mkdir(exist_ok=True)

# ─── Generate-mode paths (grafted from MCQ generator) ─
LECTURE_DIR           = BASE_DIR / "input_lectures"
OLD_EXAMS_DIR         = BASE_DIR / "input_old_exams"
GENERATOR_PROMPT_FILE = BASE_DIR / "medical-ai-generator.md"
LECTURE_DIR.mkdir(exist_ok=True)
OLD_EXAMS_DIR.mkdir(exist_ok=True)

# ─── Notes-pipeline paths (grafted from Medical note/lecture-pipeline) ─
# Kept OUTSIDE output/ so api_outputs / organize_output.py never scan them.
NOTES_PROMPTS_DIR = BASE_DIR / "prompts"
NOTES_OUTPUT_BASE = BASE_DIR / "notes_output"
NOTES_OUTPUT_BASE.mkdir(exist_ok=True)

# ─── Saved API keys (phase d — gitignored, multi-key rotation) ─
SAVED_KEYS_FILE = BASE_DIR / "saved_keys.json"
_keys_lock = threading.Lock()  # guards read/write of SAVED_KEYS_FILE

def _sanitize_key(k: str) -> str:
    # Strip non-ASCII so httpx can encode the auth header without failing
    return re.sub(r'[^\x00-\x7F]+', '', k or '').strip()

def load_saved_keys() -> list:
    """Read the ordered saved-key list from disk. Never raises."""
    with _keys_lock:
        if not SAVED_KEYS_FILE.exists():
            return []
        try:
            data = json.loads(SAVED_KEYS_FILE.read_text(encoding="utf-8"))
            return [_sanitize_key(k) for k in data.get("keys", []) if _sanitize_key(k)]
        except Exception:
            return []

def save_saved_keys(keys: list) -> None:
    with _keys_lock:
        SAVED_KEYS_FILE.write_text(
            json.dumps({"keys": keys}, ensure_ascii=False, indent=2), encoding="utf-8")

def mask_key(k: str) -> str:
    """Return a display-safe masked form, e.g. AIza…3f9c."""
    k = k or ""
    if len(k) <= 8:
        return "•" * len(k)
    return f"{k[:4]}…{k[-4:]}"

def build_key_list(typed_key: str = "") -> list:
    """
    Ordered rotation list for a run: the ad-hoc typed key first (if any),
    then every saved key. Sanitized + de-duplicated, order preserved.
    """
    out, seen = [], set()
    for k in [typed_key, *load_saved_keys()]:
        k = _sanitize_key(k)
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


class KeyPool:
    """
    Ordered pool of Gemini API keys with lazy per-key client caching.
    Rotation policy (phase d): callers rotate() on a 429/RESOURCE_EXHAUSTED
    only; on 503/timeout the key is fine — do NOT rotate. rotate() returns
    False once every key has been tried (pool exhausted), signalling the
    caller to fall back to model downgrade and reset().
    """
    def __init__(self, keys: list, http_options: dict = None):
        self.keys = list(keys)
        self.http_options = http_options
        self.idx = 0
        self._clients: dict = {}

    @property
    def size(self) -> int:
        return len(self.keys)

    def _client(self, i: int):
        from google import genai
        if i not in self._clients:
            if self.http_options:
                self._clients[i] = genai.Client(api_key=self.keys[i], http_options=self.http_options)
            else:
                self._clients[i] = genai.Client(api_key=self.keys[i])
        return self._clients[i]

    @property
    def current_client(self):
        return self._client(self.idx)

    @property
    def current_masked(self) -> str:
        return mask_key(self.keys[self.idx])

    def rotate(self) -> bool:
        """Advance to the next key. False if already on the last key (exhausted)."""
        if self.idx + 1 < len(self.keys):
            self.idx += 1
            return True
        return False

    def reset(self) -> None:
        self.idx = 0

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
_quizdata_lock = threading.Lock()
_jobs_lock = threading.Lock()  # guards check-and-mark (running/create) in /api/run and /api/retry

def new_job() -> dict:
    return {
        "running": False,
        "cancel": False,
        "state": "idle",
        "current_file": "",
        "progress": 0,
        "total": 0,
        "done": 0,
        "results": [],
        "logs": [],
        "zip_path": None,
        "mode": "convert",
        "pending_units": [],
        "static_params": {},
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
def execute_with_retry(job: dict, func, *args, max_retries=2, initial_delay=8, **kwargs):
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
            is_unavailable = "503" in err_msg or "UNAVAILABLE" in err_msg or "demand" in err_msg.lower() or "overloaded" in err_msg.lower() or "timed out" in err_msg.lower() or "timeout" in err_msg.lower()
            
            if (is_rate_limit or is_unavailable) and attempt < max_retries - 1:
                # ปรับลดเวลารอลงเหลือ 8 วินาที และลดครั้ง Retry ลงเพื่อให้สลับสลับสิทธิ์โมเดลสำรองได้ทันทีโดยไม่ต้องรอค้างหน้าจอ
                sleep_time = delay + (8 * attempt)
                push_log(job, f"⚠️ โควตาจำกัด/เซิร์ฟเวอร์ตอบสนองช้า (Status: {err_msg[:60]}) "
                              f"ระบบจะหน่วงรอ {sleep_time:.1f} วินาทีก่อนลองใหม่ (ครั้งที่ {attempt+1}/{max_retries})...", "warn")
                time.sleep(sleep_time)
            else:
                raise e

# ─── Generate-mode helpers (grafted from MCQ generator) ─
def generate_content_with_fallback(job: dict, pool, primary_model: str, contents, config, max_retries=5):
    """
    Gemini generate_content with dynamic retry + model fallback. On 429/RESOURCE_EXHAUSTED
    it rotates to the next API key (same model) first; only 503/overloaded downgrades the
    model. Takes a KeyPool (phase d). Used by run_generation (Convert has its own
    per-file execution_chain in run_conversion).
    """
    FALLBACK_CHAINS = {
        "gemini-3.5-flash": ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"],
        "gemini-3.1-pro": ["gemini-3.1-pro", "gemini-2.5-pro", "gemini-3.5-flash"],
        "gemini-3.1-flash-lite": ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-3.5-flash"],
        "gemini-2.5-pro": ["gemini-2.5-pro", "gemini-3.1-pro", "gemini-2.5-flash"],
        "gemini-2.5-flash": ["gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash"],
    }
    fallback_models = FALLBACK_CHAINS.get(primary_model, [primary_model, "gemini-2.5-flash", "gemini-3.1-flash-lite"])

    last_exception = None
    for current_model in fallback_models:
        if current_model != primary_model:
            push_log(job, f"🔄 โมเดลหลัก {primary_model} ติดขัด (503) → สลับไปใช้โมเดลสำรอง: {current_model}", "warn")
        delay = 15
        for attempt in range(max_retries):
            try:
                return pool.current_client.models.generate_content(
                    model=current_model, contents=contents, config=config
                )
            except Exception as e:
                err_msg = str(e)
                last_exception = e
                is_rate_limit = "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
                is_unavailable = "503" in err_msg or "UNAVAILABLE" in err_msg or "demand" in err_msg.lower() or "overloaded" in err_msg.lower()
                if is_rate_limit:
                    # key first: rotate to the next key on the SAME model (no backoff — fresh key)
                    if pool.rotate():
                        push_log(job, f"🔑 คีย์ชนโควตา (429) → สลับไปคีย์ถัดไป {pool.current_masked} (โมเดลเดิม {current_model})", "warn")
                        continue
                    # every key exhausted on this model → downgrade model (last resort), retry from key 0
                    if current_model != fallback_models[-1]:
                        pool.reset()
                        push_log(job, f"🔑 ทุกคีย์ชนโควตาบนโมเดล {current_model} → สลับไปโมเดลสำรองถัดไป...", "warn")
                        break
                    raise e  # last model too → give up (unit becomes retryable/pending)
                if is_unavailable and attempt < max_retries - 1:
                    sleep_time = delay + (10 * attempt)
                    push_log(job, f"⚠️ [{current_model}] เซิร์ฟเวอร์ตอบสนองช้า/หนาแน่น "
                                  f"ระบบหน่วงรอ {sleep_time:.0f}s (ครั้งที่ {attempt+1}/{max_retries})...", "warn")
                    time.sleep(sleep_time)
                else:
                    if is_unavailable and current_model != fallback_models[-1]:
                        push_log(job, f"⚠️ [{current_model}] หนาแน่นสูงต่อเนื่อง (503) กำลังสลับไปโมเดลถัดไป...", "warn")
                        break
                    raise e
    if last_exception:
        raise last_exception

def extract_sample_questions(file_path: Path, max_samples=4) -> str:
    """Read an old-exam quizdata.js/.json and return up to max_samples questions as JSON text."""
    if not file_path.exists():
        return ""
    content = ""
    try:
        content = file_path.read_text(encoding="utf-8").strip()
        m = re.search(r'var\s+quizdata\s*=\s*(\{[\s\S]+?\})(?:\s*;?\s*)$', content)
        if not m:
            m = re.search(r'var\s+quizdata\s*=\s*(\{[\s\S]+\})', content)
        if m:
            json_str = m.group(1).strip()
            if json_str.endswith(';'):
                json_str = json_str[:-1].strip()
            data = json.loads(json_str)
        else:
            data = json.loads(content)

        samples = []
        count = 0
        if isinstance(data, dict):
            for key, q_list in data.items():
                if isinstance(q_list, list):
                    for q in q_list:
                        if count >= max_samples:
                            break
                        samples.append(q)
                        count += 1
        elif isinstance(data, list):
            samples = data[:max_samples]
        return json.dumps(samples, ensure_ascii=False, indent=2)
    except Exception:
        return f"Could not parse exam fully. Here is a raw sample of the file:\n{content[:2500]}"

def merge_into_global_quizdata(job: dict, job_new_data: dict):
    """
    Thread-safe merge of a job's new questions into the shared cumulative output/quizdata.js.
    Re-reads the current file under _quizdata_lock, merges by problem-text dedup, writes back.
    Shared by run_conversion and run_generation so both accumulate into ONE file identically.
    """
    if not job_new_data:
        return
    combined_js_path = OUTPUT_DIR / "quizdata.js"
    with _quizdata_lock:
        current_quizdata = {}
        if combined_js_path.exists():
            try:
                content = combined_js_path.read_text(encoding="utf-8").strip()
                m = re.search(r'var\s+quizdata\s*=\s*(\{[\s\S]+?\})(?:\s*;?\s*)$', content)
                if not m:
                    m = re.search(r'var\s+quizdata\s*=\s*(\{[\s\S]+\})', content)
                if m:
                    json_str = m.group(1).strip()
                    if json_str.endswith(';'):
                        json_str = json_str[:-1].strip()
                    current_quizdata = json.loads(json_str)
            except Exception as e:
                push_log(job, f"⚠️ ไม่สามารถดึงข้อมูลเดิมจาก quizdata.js ได้ (จะเขียนทับใหม่): {e}", "warn")

        for cat_id, new_questions in job_new_data.items():
            if cat_id not in current_quizdata:
                current_quizdata[cat_id] = []
            existing_problems = {q.get("problem") for q in current_quizdata[cat_id] if isinstance(q, dict)}
            for q in new_questions:
                if isinstance(q, dict) and q.get("problem") not in existing_problems:
                    current_quizdata[cat_id].append(q)

        try:
            quizdata_js_str = (
                "// Auto-generated Combined MCQ Quiz Data\n"
                f"var quizdata = {json.dumps(current_quizdata, ensure_ascii=False, indent=2)};\n"
            )
            combined_js_path.write_text(quizdata_js_str, encoding="utf-8")
            push_log(job, "📦 เขียนไฟล์ quizdata.js (Combined) สำหรับระบบส่วนกลางสำเร็จ", "ok")
        except Exception as e:
            push_log(job, f"เขียนไฟล์ quizdata.js ล้มเหลว: {e}", "warn")

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
    # ตั้งค่า 65536 เป็นมาตรฐานสำหรับทุกโมเดล (ตระกูล 2.5, 3.x และ Flash-Lite รองรับขีดจำกัด 65,535+ โทเค็นทั้งหมดแบบ Native)
    max_out = 65536

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
            
            # วนลูปเช็กสถานะจนกว่าไฟล์จะพร้อมให้โมเดลอ่าน
            push_log(job, f"[{stem}] รอให้ระบบประมวลผลไฟล์บนเซิร์ฟเวอร์...", "info")
            while True:
                f_info = execute_with_retry(job, client.files.get, name=uploaded_file.name)
                state_str = str(f_info.state).upper()
                if "ACTIVE" in state_str:
                    push_log(job, f"[{stem}] ไฟล์พร้อมใช้งานแล้ว", "ok")
                    break
                elif "FAILED" in state_str:
                    raise ValueError(f"การประมวลผลไฟล์ล้มเหลว (State: {state_str})")
                time.sleep(5)
                
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
    job = _jobs[job_id]
    job.update({"running": True, "cancel": False, "state": "running", "done": 0,
                "total": len(filenames), "results": [], "progress": 0, "logs": [],
                # ── retry-remaining metadata (mode + static params so /api/retry can re-invoke
                #    with only the unfinished files; api_key is NOT stored — resent on retry) ──
                "mode": "convert", "pending_units": [],
                "static_params": {"subject_title": subject_title, "additional_prompt": additional_prompt}})

    push_log(job, f"เริ่มแปลง {len(filenames)} ไฟล์ ด้วยโมเดล {model_name}", "info")

    # ── Build the key rotation pool: typed key first, then saved keys (phase d) ──
    keys = build_key_list(api_key)
    if not keys:
        push_log(job, "ไม่พบ API Key (พิมพ์ในช่อง หรือบันทึกไว้ในคลังคีย์)", "error")
        job["running"] = False
        job["state"] = "error"
        return
    try:
        pool = KeyPool(keys, http_options={'timeout': 600000})  # 10-min timeout guards a hung HTTP thread
        _ = pool.current_client  # eager-build first client so a malformed key fails fast here
    except Exception as e:
        push_log(job, f"สร้าง Gemini Client ล้มเหลว: {e}", "error")
        job["running"] = False
        job["state"] = "error"
        return
    if pool.size > 1:
        push_log(job, f"🔑 โหลด API Key {pool.size} คีย์ (หมุนเวียนอัตโนมัติเมื่อชนโควตา 429)", "info")

    # ป้องกัน Path Traversal โดยบังคับกรองเอาเฉพาะชื่อไฟล์เท่านั้นด้วย Path(n).name
    pdfs = [INPUT_DIR / Path(n).name for n in filenames]
    
    combined_js_path = OUTPUT_DIR / "quizdata.js"
    # ใช้ job_new_data เพื่อเก็บผลลัพธ์ของ Job นี้แยกต่างหาก แล้วค่อยย้ายไปเขียนทับใน Thread-safe merge lock ตอนท้ายงาน
    job_new_data = {}

    # ── ตั้งค่า Fallback Chain อย่างยืดหยุ่นด้วย Dynamic Execution Chain ──
    # ช่วยให้ผู้ใช้สามารถเลือกใช้โมเดล Pro และโมเดลอื่น ๆ นอกรายการได้อย่างสมบูรณ์ โดยยังคงมีระบบสลับตัวสำรองเมื่อชนขีดจำกัด
    base_fallbacks = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
    
    execution_chain = []
    if model_name not in base_fallbacks:
        execution_chain.append(model_name)
    execution_chain.extend(base_fallbacks)
    
    active_chain_idx = 0
    all_quota_exhausted = False
    cancelled = False

    for i, pdf_path in enumerate(pdfs):
        # ── ตรวจสอบคำสั่งหยุดที่ขอบเขตต่อไฟล์ (unit boundary) ก่อนเริ่มไฟล์ถัดไป ──
        # ไฟล์ที่กำลังส่งให้ Gemini อยู่จะทำงานจนจบ ส่วนไฟล์ถัดไปจะไม่เริ่ม แล้วบันทึกผลบางส่วนที่ทำเสร็จแล้ว
        if job.get("cancel"):
            cancelled = True
            push_log(job, f"⏹️ หยุดตามคำขอ ก่อนเริ่มไฟล์ {pdf_path.name} (บันทึกผลที่ทำเสร็จแล้ว {i} ไฟล์)", "warn")
            break

        if not pdf_path.exists():
            push_log(job, f"ไม่พบ {pdf_path.name}", "error")
            continue

        job["current_file"] = pdf_path.name
        job["progress"] = int(i / len(pdfs) * 100)

        summary, questions = {}, []
        for try_idx in range(active_chain_idx, len(execution_chain)):
            active_model = execution_chain[try_idx]
            if try_idx > active_chain_idx:
                push_log(job, f"🔄 สลับโมเดลเป็น {active_model} เนื่องจากโควตาของโมเดลก่อนหน้าหมดแล้ว", "warn")
            # ── inner key-rotation loop: on 429 rotate KEY (same model) before downgrading model ──
            while True:
                summary, questions = process_pdf(job, pool.current_client, active_model, pdf_path, subject_title, additional_prompt)
                if summary.get("status") == "success":
                    break
                errs = summary.get("errors", [])
                is_rate_limit = any(("429" in e or "RESOURCE_EXHAUSTED" in e or "limit: 0" in e) for e in errs)
                if is_rate_limit and pool.rotate():
                    push_log(job, f"🔑 คีย์ชนโควตา (429) → สลับไปคีย์ถัดไป {pool.current_masked} (โมเดลเดิม {active_model})", "warn")
                    continue  # retry SAME model with the next key
                break  # non-429 failure, or every key exhausted on this model
            if summary.get("status") == "success":
                active_chain_idx = try_idx  # ล็อกโมเดลล่าสุดที่ทำงานได้สำเร็จไว้สำหรับไฟล์ถัดไปใน Batch
                break
            errs = summary.get("errors", [])
            is_rate_limit = any(("429" in e or "RESOURCE_EXHAUSTED" in e or "limit: 0" in e) for e in errs)
            is_unavailable = any(("503" in e or "UNAVAILABLE" in e or "demand" in e.lower() or
                                  "timed out" in e.lower() or "timeout" in e.lower()) for e in errs)
            is_quota = is_rate_limit or is_unavailable
            if is_quota and try_idx < len(execution_chain) - 1:
                next_model = execution_chain[try_idx + 1]
                push_log(job, f"🔄 สลับโมเดลเป็น {next_model} อัตโนมัติ (เซิร์ฟเวอร์หลักไม่ตอบสนอง)", "warn")
                active_chain_idx = try_idx + 1  # ขยับดัชนีคิวสำรองถัดไปทันที
                if is_rate_limit:
                    pool.reset()  # every key hit quota on the prev model — give the downgraded model a fresh shot from key 0
                continue
            if is_quota:
                push_log(job, "🔑 โควตาหมดทุกโมเดลและทุกคีย์แล้ว กรุณาเปลี่ยน API Key แล้วลองใหม่", "error")
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
            if default_cat_id not in job_new_data:
                job_new_data[default_cat_id] = []
                
            # เพิ่มข้อมูลเข้าไปเฉพาะคำถามที่ไม่เคยซ้ำ (ตรวจสอบข้อความโจทย์)
            existing_problems = {q.get("problem") for q in job_new_data[default_cat_id] if isinstance(q, dict)}
            for q in questions:
                if isinstance(q, dict) and q.get("problem") not in existing_problems:
                    job_new_data[default_cat_id].append(q)

        # Add proactive cooldown delay to protect rate limit (RPM limit)
        if i < len(pdfs) - 1:
            # Billing Tier 1 ปลดล็อก RPM สูงมาก (Flash 1K-4K, Pro 25-150) จึงสามารถลดเวลา Cooldown ลงได้มหาศาล
            is_pro = "pro" in model_name.lower()
            cooldown_secs = 3 if is_pro else 1
            push_log(job, f"⏳ พักระบบ {cooldown_secs} วินาทีก่อนเริ่มแปลงไฟล์ถัดไปเพื่อเลี่ยงการชนโควตา RPM...", "info")
            time.sleep(cooldown_secs)

    # ── เขียนไฟล์รวมผลลัพธ์ quizdata.js คืนกลับโฟลเดอร์โดยใช้ Lock ป้องกัน Data Race ──
    merge_into_global_quizdata(job, job_new_data)

    # ── คำนวณไฟล์ที่ยังไม่สำเร็จ (ล้มเหลว/ยังไม่ถึง) สำหรับ retry-remaining ──
    succeeded = {r.get("file") for r in job["results"] if r.get("status") == "success"}
    pending = [n for n in filenames if Path(n).name not in succeeded]
    job["pending_units"] = pending

    job["running"] = False
    job["current_file"] = ""
    if cancelled:
        job["state"] = "stopped"
        push_log(job, f"⏹️ หยุดแล้ว — บันทึกผลบางส่วน {job['done']} จาก {len(filenames)} ไฟล์", "warn")
    elif pending:
        # ทำครบทุกไฟล์แล้วแต่บางไฟล์ล้มเหลว/โควตาหมด → retryable (partial)
        job["progress"] = 100
        job["state"] = "partial"
        push_log(job, f"⚠️ เสร็จแบบไม่สมบูรณ์ — สำเร็จ {len(succeeded)}, ค้าง {len(pending)} ไฟล์ (กด Retry เพื่อทำเฉพาะที่ค้าง)", "warn")
    else:
        job["progress"] = 100
        job["state"] = "done"
        push_log(job, f"✅ เสร็จสิ้นทั้งหมด {len(filenames)} ไฟล์", "ok")

    # Package zip (Only packing images/ directory, <stem>.json and the root quizdata.js)
    try:
        # ล้างเฉพาะไฟล์ ZIP เก่าที่หมดอายุ (เกิน 24 ชั่วโมง) เพื่อป้องกันการลบไฟล์ ZIP ของ Job อื่นที่ทำงานอยู่ร่วมกัน
        now_ts = time.time()
        for old_zip in OUTPUT_DIR.glob("mcq_output_*.zip"):
            try:
                if now_ts - old_zip.stat().st_mtime > 86400:
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


# ─── Background AI generator (grafted from MCQ generator, phase-b) ─────────────
def run_generation(job_id: str, api_key: str, model_name: str, lecture_files: list,
                   old_exam_filename: str, additional_prompt: str):
    """
    Generate brand-new MCQs from lecture slides. Shares the cancel/state engine and the
    cumulative output/quizdata.js (via merge_into_global_quizdata) with Convert mode.
    lecture_files: list of {"filename", "num_questions", "topic_title"} dicts.
    """
    from google.genai import types

    job = _jobs[job_id]
    job.update({"running": True, "cancel": False, "state": "running", "done": 0,
                "total": len(lecture_files), "results": [], "progress": 0, "logs": [],
                "mode": "generate", "pending_units": [],
                "static_params": {"old_exam_file": old_exam_filename,
                                  "additional_prompt": additional_prompt}})

    push_log(job, f"เริ่มสร้างข้อสอบ จาก {len(lecture_files)} สไลด์บทเรียน ด้วยโมเดล {model_name}", "info")

    # ── Build the key rotation pool: typed key first, then saved keys (phase d) ──
    keys = build_key_list(api_key)
    if not keys:
        push_log(job, "ไม่พบ API Key (พิมพ์ในช่อง หรือบันทึกไว้ในคลังคีย์)", "error")
        job["running"] = False
        job["state"] = "error"
        return
    try:
        pool = KeyPool(keys, http_options={'timeout': 600000})
        client = pool.current_client  # eager-build first client so a malformed key fails fast here
    except Exception as e:
        push_log(job, f"สร้าง Gemini Client ล้มเหลว: {e}", "error")
        job["running"] = False
        job["state"] = "error"
        return
    if pool.size > 1:
        push_log(job, f"🔑 โหลด API Key {pool.size} คีย์ (หมุนเวียนอัตโนมัติเมื่อชนโควตา 429)", "info")

    # ── Step 1: Read old-exam reference for style transfer ──
    old_exam_samples = ""
    if old_exam_filename:
        old_exam_path = OLD_EXAMS_DIR / Path(old_exam_filename).name
        push_log(job, f"กำลังอ่านข้อสอบเก่าอ้างอิง: {old_exam_filename} สำหรับถอดแบบสไตล์คำถาม...", "info")
        old_exam_samples = extract_sample_questions(old_exam_path)
        if old_exam_samples:
            push_log(job, "✓ ดึงแนวข้อสอบเก่าสำเร็จสำหรับการเรียนรู้และจำลองสไตล์", "ok")
        else:
            push_log(job, "⚠️ ไม่สามารถอ่านแนวข้อสอบได้ จะออกข้อสอบตามมาตรฐานสากล USMLE/NL แทน", "warn")

    # ── Step 2: Load generator prompt (live reload) ──
    if GENERATOR_PROMPT_FILE.exists():
        try:
            system_prompt = GENERATOR_PROMPT_FILE.read_text(encoding="utf-8")
            push_log(job, f"โหลดกติกาการออกข้อสอบจาก {GENERATOR_PROMPT_FILE.name}", "info")
        except Exception as e:
            system_prompt = ""
            push_log(job, f"อ่านกติกาไม่สำเร็จ: {e}", "warn")
    else:
        system_prompt = ""
        push_log(job, f"ไม่พบ {GENERATOR_PROMPT_FILE.name}", "warn")

    # ── Local accumulation → thread-safe merge into shared quizdata.js at the end ──
    job_new_data = {}
    cancelled = False

    for idx, item in enumerate(lecture_files):
        filename      = item.get("filename")
        num_questions = item.get("num_questions", 35)
        topic_title   = item.get("topic_title", "").strip()

        # ── cancel check at unit boundary (in-flight file finishes; next never starts) ──
        if job.get("cancel"):
            cancelled = True
            push_log(job, f"⏹️ หยุดตามคำขอ ก่อนเริ่มไฟล์ {filename} (บันทึกผลที่ทำเสร็จแล้ว {idx} ไฟล์)", "warn")
            break

        job["current_file"] = filename
        job["progress"] = int(idx / len(lecture_files) * 100)

        def _fail(msg):
            # record a failed unit + advance done at EVERY boundary (fixes lost-done bug + feeds retry)
            push_log(job, msg, "error")
            job["results"].append({"file": filename, "status": "failed", "questions": 0,
                                   "errors": [msg], "elapsed": 0})
            job["done"] = idx + 1

        p = LECTURE_DIR / Path(filename).name
        if not p.exists():
            _fail(f"ไม่พบไฟล์สไลด์: {filename}")
            continue

        push_log(job, f"[{filename}] เริ่มกระบวนการสร้างข้อสอบจำนวน {num_questions} ข้อ...", "info")

        # ── Build user query ──
        contents = []
        user_query = (
            f"วิเคราะห์สไลด์บทเรียนเพื่ออกข้อสอบใหม่ที่มีคุณภาพสูงระดับสากลและตรงตามเกณฑ์ National License (NL) จำนวน {num_questions} ข้อ "
            "โดยให้ถอดสไตล์ ความลึก ความยาก และสเกลอธิบายภาษาไทยปนอังกฤษจากข้อสอบอ้างอิงด้านล่างนี้:\n\n"
        )
        if old_exam_samples:
            user_query += f"--- SAMPLE EXAM REFERENCES ---\n{old_exam_samples}\n\n"
        if topic_title:
            user_query += (
                f"\n--- CATEGORY MANDATE ---\n"
                f"คำสั่งบังคับระดับสูงสุด: กำหนดให้คำถามทุกข้อที่สร้างจากไฟล์นี้ใช้ชื่อหมวดหมู่ (categoryID และฟิลด์ category ของคำถามทุกข้อ) คือ: \"{topic_title}\" เท่านั้น\n"
                f"ห้ามดัดแปลง ห้ามคิดชื่ออื่นเองเด็ดขาด!\n\n"
            )
        if additional_prompt:
            user_query += (
                f"\n--- CATEGORY NAMING INSTRUCTION ---\n"
                f"โปรดตั้งชื่อหมวดหมู่ (categoryID และฟิลด์ category ของคำถามทุกข้อ) ให้สอดคล้องกับคำสั่งนี้:\n"
                f"{additional_prompt}\n\n"
            )
        user_query += "ส่งคำตอบเป็น JSON Object ที่มีฟิลด์ 'quizdata' เป็นหลักเท่านั้น ห้ามมีเนื้อหาอื่นปนอยู่นอกเหนือจาก JSON"
        contents.append(user_query)

        # ── Attach slide: PDF inline (<20MB) → Files API fallback; .md/.txt as text ──
        INLINE_SIZE_LIMIT = 20 * 1024 * 1024
        uploaded_file = None
        if p.suffix.lower() == ".pdf":
            try:
                file_size = p.stat().st_size
                if file_size <= INLINE_SIZE_LIMIT:
                    pdf_bytes = p.read_bytes()
                    contents.insert(0, types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
                    push_log(job, f"[{filename}] ใช้ Inline PDF ({file_size/1024:.0f} KB)", "info")
                else:
                    push_log(job, f"[{filename}] ไฟล์ใหญ่ ({file_size/1024/1024:.1f} MB) → อัปโหลด Files API...", "info")
                    uploaded_file = execute_with_retry(job, client.files.upload, file=str(p))
                    push_log(job, f"อัปโหลดสำเร็จ (ID: {uploaded_file.name})", "ok")
                    contents.insert(0, uploaded_file)
            except Exception as e:
                _fail(f"[{filename}] อัปโหลด/อ่านสไลด์ PDF ล้มเหลว: {e}")
                continue
        else:
            try:
                txt = p.read_text(encoding="utf-8")
                contents.append(f"--- LECTURE CONTENT ({filename}) ---\n{txt}\n")
            except Exception as e:
                _fail(f"[{filename}] อ่านไฟล์ล้มเหลว: {e}")
                continue

        # ── Config ──
        if "pro" in model_name.lower() or "3.5" in model_name or "2.5" in model_name:
            max_out = 65536
        else:
            max_out = 8192
        thinking_cfg = None
        if "2.5" in model_name:
            if "flash" in model_name.lower():
                thinking_cfg = types.ThinkingConfig(thinking_budget=0)
            elif "pro" in model_name.lower():
                thinking_cfg = types.ThinkingConfig(thinking_budget=128)
        generation_cfg = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=max_out,
            temperature=0.7,
            response_mime_type="application/json",
            thinking_config=thinking_cfg,
        )

        try:
            response = generate_content_with_fallback(
                job, pool, primary_model=model_name, contents=contents, config=generation_cfg,
            )
            raw = response.text
            push_log(job, f"[{filename}] ได้รับผลลัพธ์ข้อสอบจาก AI ({len(raw):,} ตัวอักษร)", "ok")
        except Exception as e:
            _fail(f"[{filename}] เรียก Gemini API ล้มเหลว: {e}")
            continue
        finally:
            if uploaded_file:
                try:
                    client.files.delete(name=uploaded_file.name)
                except Exception:
                    pass

        # ── Parse + save per-lecture deliverables + accumulate ──
        try:
            res_data = parse_json_response(raw)
            quizdata_block = res_data["quizdata"] if isinstance(res_data, dict) and "quizdata" in res_data else res_data

            stem = p.stem.strip()
            folder_name = f"generated_{stem}"
            gen_dir = OUTPUT_DIR / folder_name
            gen_dir.mkdir(parents=True, exist_ok=True)

            questions_list = []
            if isinstance(quizdata_block, dict):
                for k, v in quizdata_block.items():
                    if isinstance(v, list):
                        questions_list.extend(v)
            elif isinstance(quizdata_block, list):
                questions_list = quizdata_block

            # Defer to MedSuite's canonical category system (prompt already mandates topic_title
            # into the model's category; no subject_code_override here).
            for q in questions_list:
                if isinstance(q, dict):
                    q["category"] = sanitize_category(q.get("category"), stem)

            categories_found = []
            for q in questions_list:
                if isinstance(q, dict) and isinstance(q.get("category"), list) and len(q["category"]) > 1:
                    cat_name = q["category"][1]
                    if cat_name and cat_name not in categories_found:
                        categories_found.append(cat_name)

            meta = {
                "source": p.name,
                "categoryID": folder_name,
                "converted": len(questions_list),
                "skipped_duplicates": 0,
                "completions_added": 0,
                "validation_warnings": 0,
                "categories_found": categories_found,
                "converted_at": datetime.now().isoformat(),
            }
            (gen_dir / f"{folder_name}.json").write_text(
                json.dumps({"meta": meta, "questions": questions_list}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # Accumulate into this job's new data (dedup by problem within the job)
            default_cat_id = None
            if (questions_list and isinstance(questions_list[0], dict)
                    and isinstance(questions_list[0].get("category"), list)
                    and len(questions_list[0]["category"]) > 0):
                default_cat_id = questions_list[0]["category"][0]
            if not default_cat_id:
                m2 = parse_filename_metadata(stem)
                default_cat_id = f"{m2['subject_code']}_{m2['exam_group']}"

            if default_cat_id not in job_new_data:
                job_new_data[default_cat_id] = []
            existing_problems = {q.get("problem") for q in job_new_data[default_cat_id] if isinstance(q, dict)}
            for q in questions_list:
                if isinstance(q, dict) and q.get("problem") not in existing_problems:
                    job_new_data[default_cat_id].append(q)

            job["results"].append({"file": filename, "status": "success",
                                   "questions": len(questions_list), "errors": [], "elapsed": 0})
            push_log(job, f"✓ [{filename}] สร้างสำเร็จ {len(questions_list)} ข้อ → output/{folder_name}/", "ok")
        except Exception as e:
            _fail(f"[{filename}] ประมวลผลคำตอบของ AI ล้มเหลว: {e}")
            continue

        job["done"] = idx + 1

    # ── Thread-safe merge into shared cumulative quizdata.js ──
    merge_into_global_quizdata(job, job_new_data)

    # ── Compute pending (failed/unreached) for retry-remaining ──
    succeeded = {r.get("file") for r in job["results"] if r.get("status") == "success"}
    pending = [item for item in lecture_files if item.get("filename") not in succeeded]
    job["pending_units"] = pending

    job["running"] = False
    job["current_file"] = ""
    if cancelled:
        job["state"] = "stopped"
        push_log(job, f"⏹️ หยุดแล้ว — บันทึกผลบางส่วน {job['done']} จาก {len(lecture_files)} ไฟล์", "warn")
    elif pending:
        job["progress"] = 100
        job["state"] = "partial"
        push_log(job, f"⚠️ เสร็จแบบไม่สมบูรณ์ — สำเร็จ {len(succeeded)}, ค้าง {len(pending)} ไฟล์ (กด Retry เพื่อทำเฉพาะที่ค้าง)", "warn")
    else:
        job["progress"] = 100
        job["state"] = "done"
        push_log(job, f"✅ สิ้นสุดกระบวนการสร้างข้อสอบเสร็จสมบูรณ์! ({len(lecture_files)} ไฟล์)", "ok")

    # ── Package ZIP of this job's generated files ──
    try:
        for old_zip in OUTPUT_DIR.glob("generated_quiz_*.zip"):
            try:
                old_zip.unlink()
            except Exception:
                pass
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = OUTPUT_DIR / f"generated_quiz_{ts}.zip"
        import zipfile
        combined_js_path = OUTPUT_DIR / "quizdata.js"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if combined_js_path.exists():
                zf.write(combined_js_path, combined_js_path.name)
            for item in lecture_files:
                stem = Path(item.get("filename")).stem.strip()
                d = OUTPUT_DIR / f"generated_{stem}"
                if d.exists():
                    for f in sorted(d.rglob("*")):
                        if f.is_file():
                            zf.write(f, f.relative_to(OUTPUT_DIR))
        job["zip_path"] = str(zip_path)
        push_log(job, f"📦 สร้าง ZIP สำหรับดาวน์โหลดผลลัพธ์สำเร็จ: {zip_path.name}", "ok")
    except Exception as e:
        push_log(job, f"สร้าง ZIP สำหรับดาวน์โหลดล้มเหลว: {e}", "warn")


# ══════════════════════════════════════════════════════════════════
# NOTES PIPELINE SUBSYSTEM  (grafted verbatim from lecture-pipeline/app.py)
# ------------------------------------------------------------------
# Kept on its own transport (SSE + notes_sessions + GoogleProvider) because
# the per-lecture×per-step progress TREE needs structured events that
# MedSuite's flat text-log polling can't reconstruct. Cancel is threaded in
# via the phase-a pattern (notes_sessions[sid]["cancel"], checked at every
# step boundary). NOTE for phase (d): this is a SECOND Gemini call site
# (GoogleProvider._call) — key rotation must wire in here too.
# ══════════════════════════════════════════════════════════════════

def notes_load_prompt(filename: str) -> str:
    path = NOTES_PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}\n"
            f"Please place all .md prompt files in the 'prompts/' folder."
        )
    return path.read_text(encoding="utf-8")


class NotesCancelled(Exception):
    """Raised at a step boundary when the notes job was cancelled."""
    pass


class GoogleProvider:
    """Wraps google-genai SDK for the notes pipeline."""

    def __init__(self, api_key: str, model_name: str, keys: list = None, pacing: float = 13.0):
        from google.genai import types
        self._types = types
        # phase d — key rotation pool. Rotates on 429 only (see _call). Chat-chain
        # (enrich→crystal) stays bound to the client that created the chat object, so a
        # 429 mid-chain degrades to model-fallback, not key rotation — acceptable gap.
        pool_keys = keys if keys else [_sanitize_key(api_key)]
        pool_keys = [k for k in pool_keys if k]
        self._pool = KeyPool(pool_keys)
        self.client = self._pool.current_client
        self.model_name = model_name

        if "pro" in model_name.lower() or "3.5" in model_name or "3.1" in model_name:
            max_out = 65536
        else:
            max_out = 8192

        self.generation_cfg = types.GenerateContentConfig(
            max_output_tokens=max_out,
            temperature=0.3,
        )

        # Rate limiter — 5 RPM cap
        self._last_call = 0.0
        self._min_interval = float(pacing)

    def _pace(self, log_fn=None):
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < self._min_interval:
            wait = self._min_interval - elapsed
            if log_fn:
                log_fn(f"⏳ เว้นจังหวะ API (Pacing Delay) {wait:.1f} วินาที...")
            time.sleep(wait)
        self._last_call = time.time()

    @property
    def current_masked(self) -> str:
        return self._pool.current_masked

    def rotate_key(self) -> bool:
        """
        Advance to the next saved key and rebuild the active client. Rotation for notes
        happens at the LECTURE level (run_notes_batch), NOT inside _call: a Files-API slide
        handle is bound to the key that uploaded it, so upload+generate must re-run together
        on the new key. Returns False when every key has been tried (pool exhausted).
        """
        if self._pool.rotate():
            self.client = self._pool.current_client
            return True
        return False

    def _call(self, func, *args, log_fn=None, **kwargs):
        from google.genai.errors import ServerError, ClientError
        max_retries = 4
        base_delay = 5.0
        for attempt in range(max_retries):
            self._pace(log_fn)
            try:
                res = func(*args, **kwargs)
                self._last_call = time.time()
                return res
            except (ServerError, ClientError) as e:
                self._last_call = time.time()
                is_503 = "503" in str(e) or "UNAVAILABLE" in str(e)
                is_429 = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                if (is_503 or is_429) and attempt < max_retries - 1:
                    retry_sec = base_delay * (2 ** attempt) + random.uniform(0.5, 1.5)
                    try:
                        m = re.search(r"retry in ([\d\.]+)s", str(e))
                        if m:
                            retry_sec = float(m.group(1)) + 1.0
                    except Exception:
                        pass
                    if log_fn:
                        label = "503" if is_503 else "429"
                        log_fn(f"⚠️ {label} — รอ {retry_sec:.1f}s (ครั้งที่ {attempt+1}/{max_retries})")
                    time.sleep(retry_sec)
                else:
                    raise
            except Exception:
                self._last_call = time.time()
                raise

    def upload_file(self, file_path: str, display_name: str, log_fn=None):
        return self._call(
            self.client.files.upload,
            file=file_path,
            config=self._types.UploadFileConfig(display_name=display_name),
            log_fn=log_fn,
        )

    def get_file(self, name: str, log_fn=None):
        return self._call(self.client.files.get, name=name, log_fn=log_fn)

    def generate(self, contents: list, log_fn=None) -> str:
        res = self._call(
            self.client.models.generate_content,
            model=self.model_name,
            contents=contents,
            config=self.generation_cfg,
            log_fn=log_fn,
        )
        return res.text

    def chat_create(self):
        return self.client.chats.create(model=self.model_name, config=self.generation_cfg)

    def chat_send(self, chat_obj, message, log_fn=None) -> str:
        res = self._call(chat_obj.send_message, message=message, log_fn=log_fn)
        return res.text

    def with_model(self, model_name: str) -> "GoogleProvider":
        clone = object.__new__(GoogleProvider)
        clone._types = self._types
        clone._pool = self._pool  # share the rotation pool so a downgraded model keeps rotated keys
        clone.client = self.client
        clone.model_name = model_name
        clone._last_call = self._last_call
        clone._min_interval = self._min_interval
        if "pro" in model_name.lower():
            max_out = 65536
        else:
            max_out = 8192
        clone.generation_cfg = self._types.GenerateContentConfig(
            max_output_tokens=max_out,
            temperature=0.3,
        )
        return clone

    def fallback_model(self):
        is_frontier = any(m in self.model_name for m in ["3.5", "3.1"])
        if not is_frontier:
            return None
        fallback_name = "gemini-2.5-flash" if "flash" in self.model_name else "gemini-2.5-pro"
        return self.with_model(fallback_name), fallback_name


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in stem).strip()
    return safe[:60] or "lecture"


# Step IDs in order
NOTES_ALL_STEPS = ["slide_md", "transcript", "enrich", "crystal", "curriculum"]
NOTES_DEFAULT_STEPS = {"slide_md", "transcript"}

notes_sessions: dict = {}


def run_single_lecture(
    provider, lecture_idx, lecture_label, output_dir, emit,
    slide_path, slide_name, transcript_path, curriculum_map_path,
    uploaded_markdown_path=None, uploaded_transcribe_path=None,
    uploaded_enrich_path=None, uploaded_summary_path=None,
    requested_steps=None, cancel_check=None,
):
    if requested_steps is None:
        requested_steps = NOTES_DEFAULT_STEPS

    def _ck():
        if cancel_check and cancel_check():
            raise NotesCancelled()

    def step_start(step_id, label):
        emit("step_start", lecture=lecture_idx, step=step_id, label=label)

    def step_log(step_id, msg):
        emit("step_log", lecture=lecture_idx, step=step_id, msg=msg)

    def step_done(step_id, filename=""):
        emit("step_done", lecture=lecture_idx, step=step_id, filename=filename)

    chat = None
    lecture_markdown  = None
    lecture_transcribe = None
    lecture_enrich    = None
    lecture_summary   = None

    # Load any pre-computed files (resume-from-stage)
    if uploaded_markdown_path:
        lecture_markdown = Path(uploaded_markdown_path).read_text(encoding="utf-8")
        (output_dir / "lecture-markdown.md").write_text(lecture_markdown, encoding="utf-8")
    if uploaded_transcribe_path:
        lecture_transcribe = Path(uploaded_transcribe_path).read_text(encoding="utf-8")
        (output_dir / "lecture-transcribe.md").write_text(lecture_transcribe, encoding="utf-8")
    if uploaded_enrich_path:
        lecture_enrich = Path(uploaded_enrich_path).read_text(encoding="utf-8")
        (output_dir / "lecture-enrich.md").write_text(lecture_enrich, encoding="utf-8")
    if uploaded_summary_path:
        lecture_summary = Path(uploaded_summary_path).read_text(encoding="utf-8")
        src_name = slide_name or lecture_label or ""
        title = re.sub(r"[-_\s]+", " ", Path(src_name).stem).strip() if src_name else ""
        if title and not lecture_summary.lstrip().startswith("#"):
            lecture_summary = f"# {title}\n\n{lecture_summary}"
        (output_dir / "lecture-summary.md").write_text(lecture_summary, encoding="utf-8")

    # ── STEP 1: Slide PDF → Markdown ─────────────────────────
    if "slide_md" in requested_steps:
        _ck()
        step_start("slide_md", "📄 แปลง PDF สไลด์ → Markdown")
        if lecture_markdown:
            step_log("slide_md", "ใช้ไฟล์ lecture-markdown.md จากรอบก่อนหน้านี้")
            step_done("slide_md", "lecture-markdown.md")
        elif slide_path:
            step_log("slide_md", f"กำลังอัปโหลดไฟล์ '{slide_name}' ไปยัง Gemini File API...")
            uploaded_slide = provider.upload_file(
                file_path=slide_path, display_name=slide_name,
                log_fn=lambda msg: step_log("slide_md", msg),
            )
            step_log("slide_md", "รอ Gemini ประมวลผลไฟล์...")
            wait = 0

            def get_state_str(file_obj):
                if not file_obj.state:
                    return "ACTIVE"
                return file_obj.state.name if hasattr(file_obj.state, "name") else str(file_obj.state)

            state_str = get_state_str(uploaded_slide)
            while state_str == "PROCESSING":
                time.sleep(3)
                wait += 3
                uploaded_slide = provider.get_file(
                    name=uploaded_slide.name, log_fn=lambda msg: step_log("slide_md", msg),
                )
                state_str = get_state_str(uploaded_slide)
                step_log("slide_md", f"  ประมวลผล... ({wait}s)")

            if state_str == "FAILED":
                raise RuntimeError("Gemini File API ไม่สามารถประมวลผลไฟล์ PDF ได้")

            prompt_slide_md = notes_load_prompt("slide-to-markdown-gemini.md")
            step_log("slide_md", "กำลัง generate Markdown (อาจใช้เวลา 1–5 นาที)...")
            lecture_markdown = provider.generate(
                [uploaded_slide, prompt_slide_md + "\n\n---\nโปรดแปลง PDF สไลด์ที่อัปโหลดมาเป็น Markdown ตาม format ที่กำหนด"],
                log_fn=lambda msg: step_log("slide_md", msg),
            )
            (output_dir / "lecture-markdown.md").write_text(lecture_markdown, encoding="utf-8")
            step_log("slide_md", f"✓ บันทึก lecture-markdown.md ({len(lecture_markdown):,} ตัวอักษร)")
            step_done("slide_md", "lecture-markdown.md")
        else:
            step_log("slide_md", "ข้ามการแปลงสไลด์ (ไม่มีไฟล์ PDF หรือ Markdown เริ่มต้น)")
            step_done("slide_md", "ข้ามขั้นตอน")

    # ── STEP 2: Transcript Synthesizer ───────────────────────
    if "transcript" in requested_steps and (transcript_path or lecture_transcribe):
        _ck()
        step_start("transcript", "🎙️ สังเคราะห์ Transcript + Slide Notes")
        if lecture_transcribe:
            step_log("transcript", "ใช้ไฟล์ lecture-transcribe.md จากรอบก่อนหน้านี้")
            step_done("transcript", "lecture-transcribe.md")
        else:
            step_log("transcript", "กำลังอ่านไฟล์ transcript...")
            transcript_text = Path(transcript_path).read_text(encoding="utf-8")
            prompt_synth = notes_load_prompt("lecture-synthesizer.md")
            ref_markdown = lecture_markdown if lecture_markdown else ""
            step_log("transcript", "กำลัง generate notes-synthesized...")
            lecture_transcribe = provider.generate(
                [
                    f"## notes-raw.md\n\n{ref_markdown}",
                    f"## transcript.txt\n\n{transcript_text}",
                    prompt_synth + "\n\n---\nโปรดสังเคราะห์ notes-synthesized.md",
                ],
                log_fn=lambda msg: step_log("transcript", msg),
            )
            (output_dir / "lecture-transcribe.md").write_text(lecture_transcribe, encoding="utf-8")
            step_log("transcript", f"✓ บันทึก lecture-transcribe.md ({len(lecture_transcribe):,} ตัวอักษร)")
            step_done("transcript", "lecture-transcribe.md")

    # ── STEP 3: Slide Enrich ──────────────────────────────────
    if "enrich" in requested_steps:
        _ck()
        step_start("enrich", "🔬 เพิ่มกลไกทางการแพทย์ — Slide Enrich")
        if lecture_enrich:
            step_log("enrich", "ใช้ไฟล์ lecture-enrich.md จากรอบก่อนหน้านี้")
            step_done("enrich", "lecture-enrich.md")
        else:
            prompt_enrich = notes_load_prompt("slide-enrich.md")
            first_msg_parts = []
            if lecture_markdown:
                first_msg_parts.append(f"## lecture-markdown.md\n\n{lecture_markdown}")
            if lecture_transcribe:
                first_msg_parts.append(f"## lecture-transcribe.md\n\n{lecture_transcribe}")
            first_msg_parts.append(prompt_enrich + "\n\n---\nโปรดดำเนินการ enrich notes")

            step_log("enrich", "กำลัง generate lecture-enrich.md (อาจใช้เวลา 3–8 นาที)...")
            chat = provider.chat_create()
            lecture_enrich = provider.chat_send(
                chat, first_msg_parts, log_fn=lambda msg: step_log("enrich", msg)
            )
            (output_dir / "lecture-enrich.md").write_text(lecture_enrich, encoding="utf-8")
            step_log("enrich", f"✓ บันทึก lecture-enrich.md ({len(lecture_enrich):,} ตัวอักษร)")
            step_done("enrich", "lecture-enrich.md")

    # ── STEP 4: Crystallizer ──────────────────────────────────
    if "crystal" in requested_steps:
        _ck()
        step_start("crystal", "💎 ตกผลึกเนื้อหา — Lecture Crystallizer")
        if lecture_summary:
            step_log("crystal", "ใช้ไฟล์ lecture-summary.md จากรอบก่อนหน้านี้")
            step_done("crystal", "lecture-summary.md")
        else:
            prompt_crystal = notes_load_prompt("lecture-crystallizer.md")
            if chat is not None:
                step_log("crystal", "กำลัง generate lecture-summary.md (ต่อจาก session เดิม)...")
                lecture_summary = provider.chat_send(
                    chat, prompt_crystal + "\n\n---\nโปรดตกผลึกเนื้อหา",
                    log_fn=lambda msg: step_log("crystal", msg),
                )
            else:
                step_log("crystal", "กำลัง generate lecture-summary.md (สร้าง session ใหม่)...")
                if not lecture_enrich:
                    raise RuntimeError("ไม่พบเนื้อหา lecture-enrich.md สำหรับขั้นตอนนี้")
                lecture_summary = provider.generate(
                    [
                        f"## lecture-enrich.md\n\n{lecture_enrich}",
                        prompt_crystal + "\n\n---\nโปรดตกผลึกเนื้อหา",
                    ],
                    log_fn=lambda msg: step_log("crystal", msg),
                )
            src_name = slide_name or lecture_label or ""
            title = re.sub(r"[-_\s]+", " ", Path(src_name).stem).strip() if src_name else ""
            if title and not lecture_summary.lstrip().startswith("#"):
                lecture_summary = f"# {title}\n\n{lecture_summary}"
            (output_dir / "lecture-summary.md").write_text(lecture_summary, encoding="utf-8")
            step_log("crystal", f"✓ บันทึก lecture-summary.md ({len(lecture_summary):,} ตัวอักษร)")
            step_done("crystal", "lecture-summary.md")

    # ── STEP 5: Curriculum Map ────────────────────────────────
    if "curriculum" in requested_steps and curriculum_map_path:
        _ck()
        step_start("curriculum", "📚 อัปเดต Curriculum Map")
        curriculum_map_text = Path(curriculum_map_path).read_text(encoding="utf-8")
        prompt_curriculum = notes_load_prompt("curriculum-tracker.md")
        ref_enrich = lecture_enrich if lecture_enrich else ""
        step_log("curriculum", "กำลัง generate Curriculum_Map_updated.md...")
        curriculum_updated = provider.generate(
            [
                f"## notes-synthesized.md\n\n{ref_enrich}",
                f"## Curriculum_Map.md\n\n{curriculum_map_text}",
                prompt_curriculum + "\n\n---\nโปรดวิเคราะห์และอัปเดต Curriculum Map",
            ],
            log_fn=lambda msg: step_log("curriculum", msg),
        )
        (output_dir / "Curriculum_Map_updated.md").write_text(curriculum_updated, encoding="utf-8")
        step_log("curriculum", f"✓ บันทึก Curriculum_Map_updated.md ({len(curriculum_updated):,} ตัวอักษร)")
        step_done("curriculum", "Curriculum_Map_updated.md")


NOTES_FLAT_KINDS = {
    "slide":  "lecture-markdown.md",
    "trans":  "lecture-transcribe.md",
    "enrich": "lecture-enrich.md",
    "summary":"lecture-summary.md",
    "curriculum": "Curriculum_Map_updated.md",
}

def publish_notes_flat(lec_label, lec_dir):
    """Copy each produced .md from lec_dir to NOTES_OUTPUT_BASE/<lec_label>.md. Overwrites on collision."""
    if not lec_dir or not lec_dir.is_dir():
        return
    safe_name = re.sub(r'[^\w\-. ]', '_', lec_label).strip() or "untitled"
    for kind, fname in NOTES_FLAT_KINDS.items():
        src = lec_dir / fname
        if src.is_file():
            dest = NOTES_OUTPUT_BASE / f"{safe_name}.{kind}.md"
            shutil.copyfile(src, dest)


def run_notes_batch(session_id, api_key, model_name, lectures, cooldown):
    import zipfile
    sess = notes_sessions[session_id]
    q = sess["queue"]
    batch_dir = sess["output_dir"]

    def emit(event, **data):
        q.put(json.dumps({"event": event, **data}))

    def cancelled():
        return sess.get("cancel", False)

    try:
        provider = GoogleProvider(api_key=api_key, model_name=model_name, keys=build_key_list(api_key), pacing=0)
        sess["state"] = "running"
        emit("batch_start", total=len(lectures))

        was_cancelled = False
        for idx, lec in enumerate(lectures):
            if cancelled():
                was_cancelled = True
                break
            label = lec.get("label", f"Lecture {idx + 1}")

            if idx > 0 and cooldown > 0:
                emit("step_start", lecture=idx, step="cooldown",
                     label=f"⏱️ Cooldown — รอ {cooldown} วินาที...")
                time.sleep(cooldown)
                emit("step_done", lecture=idx, step="cooldown")

            emit("lecture_start", lecture=idx, label=label, total=len(lectures))

            folder_stem = lec.get("folder_stem", f"{idx+1:02d}_{label}")
            lec_dir = batch_dir / folder_stem
            if lec_dir.exists():
                shutil.rmtree(lec_dir)
            lec_dir.mkdir(parents=True, exist_ok=True)
            # Phase (f) tweak: also publish individual .md files at NOTES_OUTPUT_BASE root
            # so each lecture stands alone (no batch folder required). Collisions = last-run wins.
            sess["_flat_lec_dir"] = lec_dir   # remember so we can copy out after run_single_lecture

            requested_steps = set(lec.get("steps", list(NOTES_DEFAULT_STEPS)))

            lec_kwargs = dict(
                lecture_idx=idx, lecture_label=label, output_dir=lec_dir, emit=emit,
                slide_path=lec.get("slide_path"), slide_name=lec.get("slide_name"),
                transcript_path=lec.get("transcript_path"),
                curriculum_map_path=lec.get("curriculum_map_path"),
                uploaded_markdown_path=lec.get("uploaded_markdown_path"),
                uploaded_transcribe_path=lec.get("uploaded_transcribe_path"),
                uploaded_enrich_path=lec.get("uploaded_enrich_path"),
                uploaded_summary_path=lec.get("uploaded_summary_path"),
                requested_steps=requested_steps, cancel_check=cancelled,
            )

            # ── Per-lecture run. On 429 rotate KEY and re-run the WHOLE lecture (upload+generate
            #    must land on ONE key — a Files-API slide handle is bound to its uploader's key,
            #    so _call-level rotation would hand key0's file to key1). Model-fallback is the
            #    last resort, only once every key is exhausted (phase d: key first, model last). ──
            lecture_settled = False
            while not lecture_settled:
                try:
                    run_single_lecture(provider=provider, **lec_kwargs)
                    publish_notes_flat(label, sess.get("_flat_lec_dir"))
                    emit("lecture_done", lecture=idx, label=label)
                    lecture_settled = True
                except NotesCancelled:
                    was_cancelled = True
                    emit("lecture_error", lecture=idx, label=label,
                         error="⏹️ ยกเลิกโดยผู้ใช้ (partial output ถูกบันทึกไว้)")
                    break
                except Exception as e:
                    is_rate_limit = any(code in str(e) for code in
                        ["429", "RESOURCE_EXHAUSTED", "Resource Exhausted", "ResourceExhausted"])
                    if is_rate_limit and provider.rotate_key():
                        emit("step_start", lecture=idx, step="rotate",
                             label=f"🔑 คีย์ชนโควตา (429) → สลับไปคีย์ถัดไป {provider.current_masked}, รันเลกเชอร์ใหม่")
                        if lec_dir.exists():
                            shutil.rmtree(lec_dir)
                        lec_dir.mkdir(parents=True, exist_ok=True)
                        continue  # re-run the whole lecture on the rotated key
                    # not 429, or all keys exhausted → model-fallback (last resort)
                    fallback_result = provider.fallback_model()
                    is_server_error = any(code in str(e) for code in
                        ["500", "503", "429", "UNAVAILABLE", "Resource Exhausted",
                         "ResourceExhausted", "ServerError"])
                    if fallback_result and is_server_error:
                        fallback_prov, fallback_name = fallback_result
                        emit("step_start", lecture=idx, step="fallback",
                             label=f"🔄 สลับไปใช้โมเดลสำรอง ({fallback_name})...")
                        if lec_dir.exists():
                            shutil.rmtree(lec_dir)
                        lec_dir.mkdir(parents=True, exist_ok=True)
                        try:
                            run_single_lecture(provider=fallback_prov, **lec_kwargs)
                            publish_notes_flat(label, sess.get("_flat_lec_dir"))
                            emit("lecture_done", lecture=idx, label=label)
                        except NotesCancelled:
                            was_cancelled = True
                            emit("lecture_error", lecture=idx, label=label,
                                 error="⏹️ ยกเลิกโดยผู้ใช้ (partial output ถูกบันทึกไว้)")
                            break
                        except Exception as fe:
                            tb = traceback.format_exc()
                            emit("lecture_error", lecture=idx, label=label,
                                 error=f"ล้มเหลวในการสลับ fallback: {fe}\n\nข้อผิดพลาดเดิม:\n{type(e).__name__}: {e}\n\n{tb}")
                    else:
                        tb = traceback.format_exc()
                        emit("lecture_error", lecture=idx, label=label,
                             error=f"{type(e).__name__}: {e}\n\n{tb}")
                    lecture_settled = True  # fallback path is terminal for this lecture

            if was_cancelled:
                break  # break the batch loop → package whatever landed as partial ZIP

        # Package ZIP of whatever landed (partial save on cancel)
        emit("step_start", lecture=-1, step="package", label="📁 สร้าง ZIP รวม")
        zip_path = NOTES_OUTPUT_BASE / f"{batch_dir.name}.zip"
        file_count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(batch_dir.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(batch_dir))
                    emit("step_log", lecture=-1, step="package",
                         msg=f"  + {f.relative_to(batch_dir)}")
                    file_count += 1

        sess["zip_path"] = str(zip_path)
        sess["state"] = "stopped" if was_cancelled else "done"
        emit("step_log", lecture=-1, step="package",
             msg=f"✓ {zip_path.name} ({file_count} ไฟล์)")
        emit("step_done", lecture=-1, step="package", filename=zip_path.name)
        emit("done", folder=batch_dir.name, zip=zip_path.name,
             session=session_id, total=len(lectures), cancelled=was_cancelled)

    except Exception as e:
        sess["state"] = "error"
        tb = traceback.format_exc()
        emit("fatal_error", msg=str(e), detail=tb)
    finally:
        q.put(None)


# ─── Flask Routes ─────────────────────────────────────
@app.route("/")
def index():
    return HTML_PAGE

@app.route("/api/files")
def api_files():
    files = sorted([f.name for f in INPUT_DIR.glob("*.pdf")])
    return jsonify({"files": files})

@app.route("/api/generator-files")
def api_generator_files():
    lectures = sorted([f.name for f in LECTURE_DIR.glob("*") if f.suffix.lower() in [".pdf", ".md", ".txt"]])
    old_exams = sorted([f.name for f in OLD_EXAMS_DIR.glob("*") if f.suffix.lower() in [".js", ".json"]])
    return jsonify({"lectures": lectures, "old_exams": old_exams})

@app.route("/api/upload/<file_type>", methods=["POST"])
def api_upload_file(file_type):
    if "file" not in request.files:
        return jsonify(ok=False, error="ไม่พบไฟล์"), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify(ok=False, error="ชื่อไฟล์ว่างเปล่า"), 400
    filename = Path(f.filename).name  # strip any path components (traversal guard)
    if file_type == "lecture":
        f.save(LECTURE_DIR / filename)
    elif file_type == "old-exam":
        f.save(OLD_EXAMS_DIR / filename)
    else:
        return jsonify(ok=False, error="ประเภทไฟล์ไม่ถูกต้อง"), 400
    return jsonify(ok=True, filename=filename)

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
    job_id    = data.get("job_id", "default")
    mode      = data.get("mode", "convert").strip()

    additional_prompt = data.get("additional_prompt", "").strip()

    # phase d — accept an empty typed key if saved keys exist (rotation pool covers the run)
    if not build_key_list(api_key):
        return jsonify(ok=False, error="กรุณาระบุ Gemini API Key หรือบันทึกคีย์ไว้ในคลังคีย์"), 400

    # ── Build the target runner + args by mode; validate inputs before claiming the job ──
    if mode == "generate":
        lecture_files = data.get("lecture_files", [])
        old_exam_file = data.get("old_exam_file", "").strip()
        if not lecture_files:
            return jsonify(ok=False, error="กรุณาเลือกไฟล์สไลด์อย่างน้อย 1 ไฟล์"), 400
        target = run_generation
        args = (job_id, api_key, model_name, lecture_files, old_exam_file, additional_prompt)
    else:
        filenames = data.get("files", [])
        subject_title = data.get("subject_title", "").strip()
        if not filenames:
            return jsonify(ok=False, error="กรุณาเลือกไฟล์อย่างน้อย 1 ไฟล์"), 400
        target = run_conversion
        args = (job_id, api_key, model_name, filenames, subject_title, additional_prompt)

    # ── check-and-mark under lock so two POSTs can't both start the same job_id ──
    with _jobs_lock:
        if job_id not in _jobs:
            _jobs[job_id] = new_job()
        if _jobs[job_id].get("running"):
            return jsonify(ok=False, error="กำลังรันอยู่แล้ว"), 400
        _jobs[job_id]["running"] = True  # mark before thread start to close TOCTOU window

    threading.Thread(target=target, args=args, daemon=True).start()
    return jsonify(ok=True, job_id=job_id)

@app.route("/api/retry/<job_id>", methods=["POST"])
def api_retry(job_id: str):
    """Re-run ONLY the failed/unreached units of a finished job (Stop+Retry shared engine)."""
    if job_id not in _jobs:
        return jsonify(ok=False, error="ไม่พบ job"), 404
    job = _jobs[job_id]
    data = request.get_json(force=True)
    api_key = re.sub(r'[^\x00-\x7F]+', '', data.get("api_key", "").strip()).strip()
    model_name = data.get("model", "gemini-3.5-flash").strip()
    # phase d — accept an empty typed key if saved keys exist (rotation pool covers the retry)
    if not build_key_list(api_key):
        return jsonify(ok=False, error="กรุณาระบุ Gemini API Key หรือบันทึกคีย์ไว้ในคลังคีย์"), 400

    pending = job.get("pending_units") or []
    if not pending:
        return jsonify(ok=False, error="ไม่มีไฟล์ค้างให้ทำซ้ำ"), 400

    mode   = job.get("mode", "convert")
    static = job.get("static_params", {})
    if mode == "generate":
        target = run_generation
        args = (job_id, api_key, model_name, pending,
                static.get("old_exam_file", ""), static.get("additional_prompt", ""))
    else:
        target = run_conversion
        args = (job_id, api_key, model_name, pending,
                static.get("subject_title", ""), static.get("additional_prompt", ""))

    with _jobs_lock:
        if job.get("running"):
            return jsonify(ok=False, error="กำลังรันอยู่แล้ว"), 400
        job["running"] = True

    threading.Thread(target=target, args=args, daemon=True).start()
    return jsonify(ok=True, job_id=job_id, retrying=len(pending))

@app.route("/api/cancel/<job_id>", methods=["POST"])
def api_cancel(job_id: str):
    # ตั้งค่าธง cancel; worker จะตรวจที่ขอบเขตต่อไฟล์แล้วหยุดอย่างสะอาด บันทึกผลบางส่วน แล้วมาร์คสถานะ stopped
    if job_id not in _jobs:
        return jsonify(ok=False, error="ไม่พบ job"), 404
    job = _jobs[job_id]
    if not job.get("running"):
        return jsonify(ok=False, error="ไม่มีงานที่กำลังรันอยู่"), 400
    job["cancel"] = True
    push_log(job, "⏹️ ได้รับคำขอหยุด — จะหยุดหลังไฟล์ปัจจุบันเสร็จ", "warn")
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


# ─── Saved-key management (phase d — gitignored saved_keys.json) ───
@app.route("/api/keys", methods=["GET"])
def api_keys_list():
    keys = load_saved_keys()
    return jsonify(ok=True, keys=[{"index": i, "masked": mask_key(k)} for i, k in enumerate(keys)])

@app.route("/api/keys", methods=["POST"])
def api_keys_add():
    data = request.get_json(force=True)
    new_key = _sanitize_key(data.get("key", ""))
    if not new_key:
        return jsonify(ok=False, error="คีย์ว่างเปล่า"), 400
    keys = load_saved_keys()
    if new_key in keys:
        return jsonify(ok=False, error="มีคีย์นี้อยู่แล้ว"), 400
    keys.append(new_key)
    save_saved_keys(keys)
    return jsonify(ok=True, keys=[{"index": i, "masked": mask_key(k)} for i, k in enumerate(keys)])

@app.route("/api/keys/<int:idx>", methods=["DELETE"])
def api_keys_delete(idx: int):
    keys = load_saved_keys()
    if idx < 0 or idx >= len(keys):
        return jsonify(ok=False, error="ไม่พบคีย์"), 404
    keys.pop(idx)
    save_saved_keys(keys)
    return jsonify(ok=True, keys=[{"index": i, "masked": mask_key(k)} for i, k in enumerate(keys)])


# ─── Notes-pipeline routes (SSE transport, namespaced /api/notes/*) ───
@app.route("/api/notes/run", methods=["POST"])
def api_notes_run():
    api_key    = request.form.get("api_key", "").strip()
    model_name = request.form.get("model", "").strip()
    # phase d — accept an empty typed key if saved keys exist (rotation pool covers the run)
    if not build_key_list(api_key):
        return jsonify(error="กรุณาใส่ API Key หรือบันทึกคีย์ไว้ในคลังคีย์"), 400
    if not model_name:
        return jsonify(error="กรุณาเลือก Model"), 400

    try:
        cooldown = int(request.form.get("cooldown", "10"))
    except ValueError:
        cooldown = 10
    try:
        lecture_count = int(request.form.get("lecture_count", "1"))
    except ValueError:
        return jsonify(error="lecture_count ไม่ถูกต้อง"), 400
    if lecture_count < 1 or lecture_count > 20:
        return jsonify(error="รองรับ 1–20 lectures ต่อรอบ"), 400

    tmp_dir = Path(tempfile.mkdtemp())
    lectures = []

    for i in range(lecture_count):
        slide_file       = request.files.get(f"slide_{i}")
        transcript_file  = request.files.get(f"transcript_{i}")
        transcript_text  = request.form.get(f"transcript_text_{i}", "").strip()
        curriculum_file  = request.files.get(f"curriculum_map_{i}")
        label            = request.form.get(f"label_{i}", f"Lecture {i+1}").strip() or f"Lecture {i+1}"

        uploaded_markdown   = request.files.get(f"uploaded_markdown_{i}")
        uploaded_transcribe = request.files.get(f"uploaded_transcribe_{i}")
        uploaded_enrich     = request.files.get(f"uploaded_enrich_{i}")
        uploaded_summary    = request.files.get(f"uploaded_summary_{i}")

        raw_steps = request.form.getlist(f"steps_{i}")
        requested_steps = set(raw_steps) if raw_steps else set(NOTES_DEFAULT_STEPS)

        has_slide = slide_file and slide_file.filename
        has_any = has_slide or any([
            uploaded_markdown   and uploaded_markdown.filename,
            uploaded_transcribe and uploaded_transcribe.filename,
            uploaded_enrich     and uploaded_enrich.filename,
            uploaded_summary    and uploaded_summary.filename,
        ])
        if not has_any:
            return jsonify(
                error=f"Lecture {i+1} ({label}): กรุณาอัปโหลดไฟล์ PDF สไลด์หรือไฟล์ขั้นตอนกลาง"
            ), 400

        lec_tmp = tmp_dir / f"lec_{i}"
        lec_tmp.mkdir()
        lec = {"label": label, "steps": list(requested_steps)}

        if has_slide:
            lec["folder_stem"] = _safe_stem(slide_file.filename)
        elif uploaded_markdown and uploaded_markdown.filename:
            lec["folder_stem"] = _safe_stem(uploaded_markdown.filename)
        elif uploaded_enrich and uploaded_enrich.filename:
            lec["folder_stem"] = _safe_stem(uploaded_enrich.filename)
        else:
            safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)[:40]
            lec["folder_stem"] = f"{i+1:02d}_{safe_label}"

        if has_slide:
            p = str(lec_tmp / slide_file.filename)
            slide_file.save(p)
            lec["slide_path"] = p
            lec["slide_name"] = slide_file.filename

        if transcript_file and transcript_file.filename:
            p = str(lec_tmp / transcript_file.filename)
            transcript_file.save(p)
            lec["transcript_path"] = p
        elif transcript_text:
            p = str(lec_tmp / "transcript.txt")
            Path(p).write_text(transcript_text, encoding="utf-8")
            lec["transcript_path"] = p

        if curriculum_file and curriculum_file.filename:
            p = str(lec_tmp / curriculum_file.filename)
            curriculum_file.save(p)
            lec["curriculum_map_path"] = p

        for field, key, fname in [
            (uploaded_markdown,   "uploaded_markdown_path",  "lecture-markdown.md"),
            (uploaded_transcribe, "uploaded_transcribe_path","lecture-transcribe.md"),
            (uploaded_enrich,     "uploaded_enrich_path",    "lecture-enrich.md"),
            (uploaded_summary,    "uploaded_summary_path",   "lecture-summary.md"),
        ]:
            if field and field.filename:
                p = str(lec_tmp / fname)
                field.save(p)
                lec[key] = p

        lectures.append(lec)

    session_id = str(uuid.uuid4())
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir  = NOTES_OUTPUT_BASE / f"batch_{timestamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    notes_sessions[session_id] = {
        "queue":         queue.Queue(),
        "output_dir":    batch_dir,
        "zip_path":      None,
        "tmp_dir":       str(tmp_dir),
        "lecture_count": len(lectures),
        "cancel":        False,
        "state":         "idle",
    }

    t = threading.Thread(
        target=run_notes_batch,
        args=(session_id, api_key, model_name, lectures, cooldown),
        daemon=True,
    )
    t.start()
    return jsonify(session_id=session_id, lecture_count=len(lectures))


@app.route("/api/notes/progress/<session_id>")
def api_notes_progress(session_id: str):
    if session_id not in notes_sessions:
        return "Session not found", 404

    def generate():
        q = notes_sessions[session_id]["queue"]
        yield "retry: 3000\n\n"
        while True:
            try:
                item = q.get(timeout=30)
                if item is None:
                    yield 'data: {"event":"stream_end"}\n\n'
                    break
                yield f"data: {item}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/notes/cancel/<session_id>", methods=["POST"])
def api_notes_cancel(session_id: str):
    sess = notes_sessions.get(session_id)
    if not sess:
        return jsonify(error="ไม่พบ session"), 404
    if sess.get("state") != "running":
        return jsonify(error="job ไม่ได้กำลังทำงาน"), 400
    sess["cancel"] = True
    return jsonify(ok=True)


@app.route("/api/notes/download/<session_id>")
def api_notes_download(session_id: str):
    if session_id not in notes_sessions:
        return "Session not found", 404
    zip_path = notes_sessions[session_id].get("zip_path")
    if not zip_path or not Path(zip_path).exists():
        return "ไฟล์ยังไม่พร้อม", 404
    return send_file(zip_path, as_attachment=True)


# ─── Phase (e): manual-handoff chaining — Notes .md → Generate input ─────────────
# File handoff (NOT a shared DB): scan finished Notes batches on disk and let the user
# copy an enrich/summary .md into LECTURE_DIR, where the unchanged Generate pipeline
# reads it as lecture text. Scans the FS (not notes_sessions) so a later session picks
# up an earlier run. Generate-only scope: Convert globs *.pdf and extracts existing MCQs.
NOTES_HANDOFF_KINDS = {"enrich": "lecture-enrich.md", "summary": "lecture-summary.md"}

@app.route("/api/notes/outputs")
def api_notes_outputs():
    """List both flat .md files (per-lecture) and batch subdirs (for phase-e handoff)."""
    outs = []
    # Flat per-lecture .md files at NOTES_OUTPUT_BASE root
    for f in sorted(NOTES_OUTPUT_BASE.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        outs.append({
            "source": "flat",
            "name": f.name,
            "size": f.stat().st_size,
            "mtime": f.stat().st_mtime,
        })
    # Batch subdirectories (legacy phase-e handoff + ZIP)
    batches = sorted(
        [d for d in NOTES_OUTPUT_BASE.glob("batch_*") if d.is_dir()],
        key=lambda x: x.stat().st_mtime, reverse=True,
    )
    for batch in batches:
        for lec_dir in sorted(d for d in batch.iterdir() if d.is_dir()):
            for kind, fname in NOTES_HANDOFF_KINDS.items():
                f = lec_dir / fname
                if f.exists():
                    outs.append({
                        "source": "batch",
                        "batch": batch.name,
                        "lecture": lec_dir.name,
                        "kind": kind,
                        "size": f.stat().st_size,
                    })
    return jsonify({"outputs": outs})

@app.route("/api/notes/use-as-lecture", methods=["POST"])
def api_notes_use_as_lecture():
    data = request.get_json(force=True, silent=True) or {}
    batch = Path(str(data.get("batch", ""))).name    # strip path components
    lecture = Path(str(data.get("lecture", ""))).name
    kind = str(data.get("kind", ""))
    if kind not in NOTES_HANDOFF_KINDS:
        return jsonify(ok=False, error="ประเภทไฟล์ไม่ถูกต้อง"), 400
    src = (NOTES_OUTPUT_BASE / batch / lecture / NOTES_HANDOFF_KINDS[kind]).resolve()
    # traversal guard: source must resolve to a real file under NOTES_OUTPUT_BASE
    if NOTES_OUTPUT_BASE.resolve() not in src.parents or not src.is_file():
        return jsonify(ok=False, error="ไม่พบไฟล์"), 404
    # snapshot copy; re-pick overwrites (re-run Notes → re-pick to refresh) — intended
    dest_name = f"{lecture}_{kind}.md"
    shutil.copyfile(src, LECTURE_DIR / dest_name)
    return jsonify(ok=True, filename=dest_name)


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
    --bg:          #f8fafc; /* Slate 50 - พื้นหลังโปร่งเบา */
    --surface:     #ffffff; /* ขาวบริสุทธิ์สำหรับ Card และ Panel */
    --card:        #f1f5f9; /* Slate 100 สำหรับกล่องและ Preset */
    --border:      #e2e8f0; /* Slate 200 เส้นขอบตัดคม */
    --border-hover:#cbd5e1; /* Slate 300 เส้นขอบเมื่อ Hover */
    --accent:      #0284c7; /* Sky 600 สีน้ำเงินเข้มสำหรับ Light Theme */
    --accent-light:#0ea5e9; /* Sky 500 สำหรับ Highlight */
    --accent2:     #059669; /* Emerald 600 สีเขียวเพื่อการยืนยัน */
    --accent2-light:#10b981; /* Emerald 500 */
    --warn:        #ea580c; /* Orange 600 */
    --err:         #dc2626; /* Red 600 */
    --purple:      #7c3aed; /* Violet 600 */
    --purple-light:#8b5cf6; /* Violet 500 */
    --text:        #0f172a; /* Slate 900 สีอักษรคมชัดสูง */
    --muted:       #475569; /* Slate 600 อักษรสนับสนุน */
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
    background: rgba(255, 255, 255, 0.85);
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
    color: var(--text);
  }

  .brand-badge {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--accent-light), var(--purple));
    border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    color: #fff;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.2);
  }

  .header-version {
    font-size: 11px;
    color: var(--muted);
    font-family: var(--mono);
    background: rgba(0, 0, 0, 0.04);
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
    background: var(--surface);
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
    background: rgba(14, 165, 233, 0.08);
    border-color: rgba(14, 165, 233, 0.25);
    color: var(--accent);
    animation: pulse-glow 2s infinite;
  }

  .header-pill.running::before {
    background: var(--accent-light);
  }

  .header-pill.done {
    background: rgba(16, 185, 129, 0.08);
    border-color: rgba(16, 185, 129, 0.25);
    color: var(--accent2);
  }

  .header-pill.done::before {
    background: var(--accent2-light);
  }

  @keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.2); }
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
    overflow: hidden;
    height: 100%;
  }

  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  /* Config Accordion Button */
  .config-collapse-btn {
    background: rgba(0, 0, 0, 0.02);
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    border-bottom: 1px solid var(--border);
    user-select: none;
    color: var(--text);
    transition: background 0.15s;
  }

  .config-collapse-btn:hover {
    background: rgba(0, 0, 0, 0.04);
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
    color: #334155;
    margin-bottom: 6px;
  }

  .field .hint {
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 6px;
  }
  .field .hint .mono { font-family: var(--mono); color: var(--accent); }

  .sk-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
  .sk-empty { font-size: 12px; color: var(--muted); font-style: italic; padding: 4px 0; }
  .sk-row {
    display: flex; align-items: center; justify-content: space-between;
    background: #f8fafc; border: 1px solid var(--border);
    border-radius: 8px; padding: 7px 10px;
  }
  .sk-row .sk-key { font-family: var(--mono); font-size: 12px; color: var(--text); }
  .sk-row .sk-del {
    background: transparent; border: none; color: var(--muted); cursor: pointer;
    font-size: 14px; padding: 2px 6px; border-radius: 6px; line-height: 1;
  }
  .sk-row .sk-del:hover { color: var(--err); background: rgba(239, 68, 68, 0.08); }
  .sk-add {
    width: 100%; background: rgba(14, 165, 233, 0.06); color: var(--accent);
    border: 1px solid var(--border); border-radius: 8px; padding: 8px;
    font-family: var(--sans); font-size: 12px; cursor: pointer;
  }
  .sk-add:hover { border-color: var(--accent-light); background: rgba(14, 165, 233, 0.12); }

  .input-wrap { position: relative; }

  .input-wrap input,
  .field input[type="text"],
  .field select {
    width: 100%;
    background: #ffffff;
    border: 1px solid #cbd5e1;
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
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2364748b' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
  }

  .field textarea {
    width: 100%;
    background: #ffffff;
    border: 1px solid #cbd5e1;
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
    border-color: var(--accent-light);
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.12);
    background: #ffffff;
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
    background: rgba(0, 0, 0, 0.02);
  }

  .file-count-badge {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--accent);
    background: rgba(14, 165, 233, 0.08);
    padding: 2px 8px;
    border-radius: 12px;
    border: 1px solid rgba(14, 165, 233, 0.15);
  }

  .tb-btn {
    font-size: 11px;
    font-weight: 500;
    color: var(--text);
    background: #ffffff;
    border: 1px solid var(--border);
    cursor: pointer;
    font-family: var(--sans);
    padding: 4px 10px;
    border-radius: 6px;
    transition: all 0.15s;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
  }

  .tb-btn:hover {
    background: #f8fafc;
    border-color: var(--border-hover);
  }

  .tb-btn.refresh {
    margin-left: auto;
    color: var(--accent);
    border-color: rgba(14, 165, 233, 0.25);
    background: rgba(14, 165, 233, 0.04);
  }

  .tb-btn.refresh:hover {
    background: rgba(14, 165, 233, 0.08);
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
    background: #ffffff;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    user-select: none;
    box-shadow: 0 1px 2px rgba(0,0,0,0.01);
  }

  .file-item:hover {
    background: #f8fafc;
    border-color: var(--border-hover);
  }

  .file-item.selected {
    background: rgba(14, 165, 233, 0.05);
    border-color: rgba(14, 165, 233, 0.3);
  }

  .file-item.processing {
    background: rgba(249, 115, 22, 0.04);
    border-color: rgba(249, 115, 22, 0.25);
    animation: pulse-border 2.5s infinite;
  }

  @keyframes pulse-border {
    0%, 100% { border-color: rgba(249, 115, 22, 0.3); }
    50%      { border-color: var(--warn); }
  }

  .file-item.done {
    background: rgba(16, 185, 129, 0.04);
    border-color: rgba(16, 185, 129, 0.25);
  }

  .file-item.failed {
    background: rgba(239, 68, 68, 0.04);
    border-color: rgba(239, 68, 68, 0.25);
  }

  .file-checkbox {
    width: 18px; height: 18px;
    border-radius: 5px;
    border: 1.5px solid #cbd5e1;
    background: #ffffff;
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
    color: var(--text);
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

  /* ── Run Button ── */
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
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
  }

  .run-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(14, 165, 233, 0.25);
    filter: brightness(1.05);
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
    color: var(--text);
  }

  .progress-pct {
    font-family: var(--mono);
    font-weight: 600;
    color: var(--accent);
  }

  .progress-track {
    height: 6px;
    background: #e2e8f0;
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--purple));
    border-radius: 3px;
    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 6px rgba(14, 165, 233, 0.3);
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
    color: var(--text);
  }

  .tab.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }

  .tab-actions { margin-left: auto; display: flex; gap: 8px; }

  .icon-btn {
    font-size: 12px;
    font-weight: 500;
    color: var(--muted);
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 5px 12px;
    cursor: pointer;
    font-family: var(--sans);
    transition: all 0.15s;
  }

  .icon-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(14, 165, 233, 0.04);
  }

  /* Log Console */
  .log-console {
    flex: 1;
    overflow-y: auto;
    padding: 16px 28px;
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.8;
    background: #f8fafc;
    border: 1px solid var(--border);
  }

  .log-line {
    display: flex;
    gap: 16px;
    padding: 2px 0;
    border-bottom: 1px solid rgba(0, 0, 0, 0.03);
  }

  .log-ts { color: var(--muted); flex-shrink: 0; width: 64px; }
  .log-msg { word-break: break-word; flex: 1; }
  .log-msg.info  { color: #475569; }
  .log-msg.ok    { color: var(--accent2); }
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
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
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
    border-color: rgba(14, 165, 233, 0.25);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
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
    color: var(--text);
    padding-left: 4px;
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
    background: rgba(0, 0, 0, 0.03);
    color: var(--muted);
    border: 1px solid var(--border);
  }

  .tag.green {
    background: rgba(16, 185, 129, 0.06);
    color: var(--accent2);
    border-color: rgba(16, 185, 129, 0.12);
  }
  .tag.red {
    background: rgba(239, 68, 68, 0.06);
    color: var(--err);
    border-color: rgba(239, 68, 68, 0.12);
  }
  .tag.blue {
    background: rgba(14, 165, 233, 0.06);
    color: var(--accent);
    border-color: rgba(14, 165, 233, 0.12);
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
    background: rgba(16, 185, 129, 0.06);
    border: 1px solid rgba(16, 185, 129, 0.2);
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.05);
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
    color: #334155;
  }

  .done-banner strong { color: var(--accent2); }

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
    box-shadow: 0 4px 10px rgba(16, 185, 129, 0.15);
  }

  .dl-btn:hover {
    filter: brightness(1.05);
    transform: translateY(-1px);
  }

  /* ── Spinner ── */
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(14, 165, 233, 0.2);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Mode switcher ── */
  .mode-switch { display:flex; gap:6px; margin: 16px 20px 10px; background:var(--card);
    border:1px solid var(--border); border-radius:10px; padding:4px; }
  .mode-btn { flex:1; padding:9px 8px; border:0; border-radius:7px; cursor:pointer;
    background:transparent; color:var(--muted); font-size:12.5px; font-weight:600;
    font-family:inherit; transition:all .15s; }
  .mode-btn:hover { color:var(--text); }
  .mode-btn.active { background:#ffffff;
    color:var(--accent); box-shadow:0 2px 6px rgba(0,0,0,0.05); border: 1px solid var(--border); }

  /* ── Generate lecture rows ── */
  .lec-item { border:1px solid var(--border); border-radius:8px; padding:8px 10px; margin-bottom:8px;
    background:#ffffff; }
  .lec-head { display:flex; align-items:center; gap:8px; cursor:pointer; }
  .lec-head .file-label { flex:1; font-size:12.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .lec-item.selected { border-color:var(--accent); }
  .lec-meta { display:none; gap:8px; margin-top:8px; }
  .lec-item.selected .lec-meta { display:flex; }
  .lec-meta input { background:#ffffff; border:1px solid #cbd5e1; border-radius:6px;
    color:var(--text); padding:6px 8px; font-size:12px; font-family:inherit; }
  .lec-meta input.lec-num { width:72px; }
  .lec-meta input.lec-topic { flex:1; min-width:0; }
  .lec-status { font-size:14px; width:18px; text-align:center; }
  .upload-row { display:flex; gap:6px; margin: 8px 16px 12px; }
  .upload-row .tb-btn { flex:1; padding: 8px; }
  #actionBtn { margin-top:8px; width:100%; padding:11px; border:0; border-radius:9px; cursor:pointer;
    font-size:13px; font-weight:700; font-family:inherit; color:#fff; display:none; }
  #actionBtn.stop  { background:var(--warn); }
  #actionBtn.retry { background:linear-gradient(135deg,var(--accent2),var(--accent2-light)); }

  /* Custom Scrollbar Styles */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--muted); }

  /* ══ NOTES MODE ══ */
  #notesRunWrap #notesStopBtn { margin-top:8px; width:100%; padding:11px; border:0; border-radius:9px;
    cursor:pointer; font-family:var(--sans); font-size:.95rem; font-weight:600; color:#fff; background:var(--warn); }
  #notesRunWrap #notesStopBtn:disabled { opacity:.6; cursor:default; }

  #sectionNotes .n-lectures-wrap { display:flex; flex-direction:column; gap:.6rem; margin:.5rem 16px .75rem; }
  #sectionNotes .n-lecture-card { background:#ffffff; border:1px solid var(--border); border-radius:8px; overflow:hidden; }
  #sectionNotes .n-lecture-header { display:flex; align-items:center; gap:.6rem; padding:.6rem .75rem;
    background:var(--card); cursor:pointer; user-select:none; border-bottom:1px solid var(--border); }
  #sectionNotes .n-lecture-num { font-family:var(--mono); font-size:.75rem; color:var(--muted); min-width:1.5rem; }
  #sectionNotes .n-lecture-header input[type=text] { flex:1; background:transparent; border:none; color:var(--text);
    font-family:var(--sans); font-size:.85rem; font-weight:500; padding:0; outline:none; }
  #sectionNotes .n-chevron { font-size:.65rem; color:var(--muted); transition:transform .2s; margin-left:auto; }
  #sectionNotes .n-lecture-card.open .n-chevron { transform:rotate(180deg); }
  #sectionNotes .n-btn-remove { background:none; border:none; color:var(--err); cursor:pointer; font-size:.95rem;
    padding:0 .2rem; line-height:1; opacity:.7; }
  #sectionNotes .n-btn-remove:hover { opacity:1; }
  #sectionNotes .n-lecture-body { padding:.75rem; display:none; }
  #sectionNotes .n-lecture-card.open .n-lecture-body { display:block; }
  #sectionNotes .n-row-2 { display:grid; grid-template-columns:1fr 1fr; gap:.75rem; }
  #sectionNotes .n-opt { font-size:.65rem; background:rgba(14, 165, 233, 0.08); color:var(--accent);
    border-radius:4px; padding:.05rem .35rem; margin-left:.35rem; }
  #sectionNotes .n-drop-zone { border:2px dashed var(--border); border-radius:6px; padding:.85rem; text-align:center;
    cursor:pointer; position:relative; transition:border-color .2s, background .2s; }
  #sectionNotes .n-drop-zone:hover, #sectionNotes .n-drop-zone.dragover { border-color:var(--accent); background:rgba(14, 165, 233, 0.04); }
  #sectionNotes .n-drop-zone input[type=file] { position:absolute; inset:0; opacity:0; cursor:pointer; width:100%; height:100%; }
  #sectionNotes .n-dz-icon { font-size:1.1rem; margin-bottom:.2rem; }
  #sectionNotes .n-dz-label { font-size:.75rem; color:var(--muted); }
  #sectionNotes .n-dz-filename { font-family:var(--mono); font-size:.7rem; color:var(--accent2); margin-top:.25rem; word-break:break-all; }
  #sectionNotes .n-resume { margin-top:.6rem; border:1px solid var(--border); border-radius:6px; background:#f8fafc; }
  #sectionNotes .n-resume summary { cursor:pointer; font-size:.78rem; font-weight:600; color:var(--accent); padding:.5rem .7rem; }
  #sectionNotes .n-resume-grid { padding:.7rem; display:grid; grid-template-columns:1fr 1fr; gap:.5rem; border-top:1px solid var(--border); }
  #sectionNotes .n-resume-grid input[type=file] { font-size:.72rem; color:var(--text); width:100%; }
  #sectionNotes .n-steps-selector { margin:.7rem 0 .2rem; }
  #sectionNotes .n-group-label { font-size:.72rem; font-weight:600; color:var(--muted); text-transform:uppercase;
    letter-spacing:.05em; display:block; margin-bottom:.45rem; }
  #sectionNotes .n-steps-grid { display:flex; flex-wrap:wrap; gap:.4rem; }
  #sectionNotes .n-step-toggle { display:inline-flex; align-items:center; gap:.35rem; padding:.3rem .6rem; border-radius:5px;
    border:1px solid var(--border); cursor:pointer; font-size:.75rem; background:transparent; color:var(--muted); user-select:none; }
  #sectionNotes .n-step-toggle input { display:none; }
  #sectionNotes .n-step-toggle.checked { border-color:var(--accent); color:var(--accent); background:rgba(14, 165, 233, 0.06); }
  #sectionNotes .n-step-toggle.n-s-crystal.checked { border-color:var(--warn); color:var(--warn); background:rgba(249, 115, 22, 0.06); }
  #sectionNotes .n-step-toggle.n-s-curr.checked { border-color:var(--accent2); color:var(--accent2); background:rgba(16, 185, 129, 0.06); }
  #sectionNotes .n-btn-add { width: calc(100% - 32px); padding:.6rem; background:transparent; color:var(--accent);
    border:2px dashed var(--accent); border-radius:8px; font-family:var(--sans); font-size:.85rem; font-weight:500; cursor:pointer; margin: 0 16px 12px; }
  #sectionNotes .n-btn-add:hover { background:rgba(14, 165, 233, 0.04); }

  /* Notes right panel */
  #notesRightPanel.rpanel, #cgRightPanel.rpanel { display:flex; flex-direction:column; flex:1; min-height:0; overflow:hidden; }
  #notesRightPanel .n-batch-summary { font-size:.85rem; color:var(--muted); margin-bottom:.75rem; padding:.6rem .75rem;
    background:var(--surface); border-radius:6px; border-left:3px solid var(--accent); }
  #notesRightPanel .n-progress-scroll { flex:1; overflow-y:auto; min-height:0; padding-right:.25rem; }
  #notesRightPanel .n-lec-prog { border:1px solid var(--border); border-radius:8px; margin-bottom:.6rem; overflow:hidden; }
  #notesRightPanel .n-lp-header { display:flex; align-items:center; gap:.6rem; padding:.6rem .75rem; background:var(--surface); cursor:pointer; }
  #notesRightPanel .n-lec-badge { font-family:var(--mono); font-size:.7rem; padding:.15rem .45rem; border-radius:4px; background:var(--card); color:var(--muted); flex-shrink:0; }
  #notesRightPanel .n-lec-badge.running { background:rgba(14, 165, 233, 0.1); color:var(--accent); }
  #notesRightPanel .n-lec-badge.done { background:rgba(16, 185, 129, 0.1); color:var(--accent2); }
  #notesRightPanel .n-lec-badge.error { background:rgba(239, 68, 68, 0.1); color:var(--err); }
  #notesRightPanel .n-lp-title { flex:1; font-size:.85rem; font-weight:500; }
  #notesRightPanel .n-chevron { font-size:.65rem; color:var(--muted); }
  #notesRightPanel .n-lp-body { display:none; padding:.6rem .75rem; border-top:1px solid var(--border); background: #ffffff; }
  #notesRightPanel .n-lec-prog.open .n-lp-body { display:block; }
  #notesRightPanel .n-step-list { list-style:none; margin:0; padding:0; }
  #notesRightPanel .n-step-item { display:flex; align-items:flex-start; gap:.6rem; padding:.5rem 0; border-bottom:1px solid var(--border); }
  #notesRightPanel .n-step-item:last-child { border-bottom:none; }
  #notesRightPanel .n-step-icon { width:1.2rem; flex-shrink:0; display:flex; justify-content:center; font-size:.9rem; margin-top:.05rem; }
  #notesRightPanel .n-step-body { flex:1; min-width:0; }
  #notesRightPanel .n-step-label { font-size:.82rem; font-weight:500; }
  #notesRightPanel .n-step-log { font-family:var(--mono); font-size:.7rem; color:var(--muted); margin-top:.25rem; white-space:pre-wrap; word-break:break-all; }
  #notesRightPanel .n-err-box { color:var(--err); background:rgba(239, 68, 68, 0.04); padding:.5rem; border:1px solid rgba(239, 68, 68, 0.15); border-radius:4px; margin-top:.3rem; }
  #notesRightPanel .n-step-fn { font-family:var(--mono); font-size:.7rem; color:var(--accent2); margin-top:.15rem; }
  #notesRightPanel .n-step-item[data-state=waiting] .n-step-icon::before { content:"○"; color:var(--muted); }
  #notesRightPanel .n-step-item[data-state=running] .n-step-icon::before { content:"◌"; color:var(--accent); animation:nspin 1s linear infinite; display:inline-block; }
  #notesRightPanel .n-step-item[data-state=done] .n-step-icon::before { content:"✓"; color:var(--accent2); }
  #notesRightPanel .n-step-item[data-state=error] .n-step-icon::before { content:"✗"; color:var(--err); }
  #notesRightPanel .n-package-card { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:.85rem 1rem; margin-top:.6rem; }
  #notesRightPanel .n-package-title { font-size:.72rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-bottom:.6rem; }
  #notesRightPanel .n-done-banner { margin-top:.75rem; background:rgba(16, 185, 129, 0.08); border:1px solid var(--accent2); border-radius:8px;
    padding:1rem 1.2rem; display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap; }
  #notesRightPanel .n-done-banner.cancelled { background:rgba(249, 115, 22, 0.08); border-color:var(--warn); }
  #notesRightPanel .n-done-banner p { font-size:.82rem; line-height:1.5; color: #334155; }
  #notesRightPanel .n-done-banner strong { color:var(--accent2); }
  #notesRightPanel .n-btn-download { padding:.55rem 1.1rem; background:var(--accent2); color:#ffffff; font-family:var(--sans);
    font-size:.82rem; font-weight:600; border:none; border-radius:6px; cursor:pointer; text-decoration:none; flex-shrink:0; }
  @keyframes nspin { from{transform:rotate(0)} to{transform:rotate(360deg)} }

  /* ── Tablet Responsive Layout (Under 1024px) ── */
  @media (max-width: 1024px) {
    .main { grid-template-columns: 320px 1fr; }
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

  /* ── Mobile Responsive Layout (Under 768px) ── */
  @media (max-width: 768px) {
    body {
      height: auto;
      overflow-y: auto;
    }
    header { padding: 0 16px; gap: 8px; }
    .brand { font-size: 14px; }
    .brand-badge { width: 28px; height: 28px; font-size: 15px; }
    .header-pill { font-size: 11px; padding: 4px 10px; }

    .main {
      display: flex;
      flex-direction: column;
      overflow: visible;
      height: auto;
    }
    .left {
      border-right: none;
      border-bottom: 1px solid var(--border);
      flex-shrink: 0;
      height: auto;
      max-height: none;
    }
    
    .config-collapse-btn {
      background: rgba(0,0,0,0.01);
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
      max-height: 0; /* Default closed on mobile */
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
      flex: none;
      min-height: 120px;
      max-height: 200px;
      padding: 8px 12px;
    }
    .file-item  { padding: 8px 10px; margin-bottom: 4px; }
    .file-label { font-size: 12px; }

    .run-wrap { padding: 10px 14px; }
    .run-btn  { font-size: 13px; padding: 10px; }

    .right {
      flex: none;
      height: auto;
      overflow: visible;
    }
    .progress-bar-wrap { padding: 12px 16px; }
    .progress-row      { font-size: 11px; margin-bottom: 6px; }
    .progress-sub      { font-size: 10px; }

    .tab-bar  { padding: 0 16px; height: 42px; }
    .tab      { padding: 0 12px; font-size: 12px; margin-right: 4px; }
    .tab-actions { gap: 4px; }
    .icon-btn { font-size: 10px; padding: 4px 8px; }

    .log-console { height: 350px; font-size: 11px; line-height: 1.7; padding: 12px 16px; }
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

      <!-- Mode Switcher: Convert (PDF→JSON) / Generate (slides→new MCQs) -->
      <div class="mode-switch">
        <button class="mode-btn active" id="modeConvertBtn" onclick="setMode('convert')">📄 แปลงข้อสอบ</button>
        <button class="mode-btn" id="modeGenerateBtn" onclick="setMode('generate')">✨ สร้างข้อสอบใหม่</button>
        <button class="mode-btn" id="modeNotesBtn" onclick="setMode('notes')">📝 สรุปเลกเชอร์</button>
      </div>

      <!-- ══ CONVERT MODE: pick PDFs from input_pdfs/ ══ -->
      <div id="sectionConvert">
        <div class="file-toolbar">
          <span class="file-count-badge" id="fileCount">0 ไฟล์</span>
          <button class="tb-btn" onclick="selectAll()">เลือกทั้งหมด</button>
          <button class="tb-btn" onclick="deselectAll()">ยกเลิก</button>
          <button class="tb-btn refresh" onclick="loadFiles()">🔄 รีเฟรช</button>
        </div>
        <div class="file-scroll" id="fileList">
          <div class="empty-files"><span>📂</span>กำลังโหลด...</div>
        </div>
      </div>

      <!-- ══ GENERATE MODE: slides → new MCQs ══ -->
      <div id="sectionGenerate" style="display:none">

        <!-- Old-exam reference (style transfer) -->
        <div class="field" style="padding: 16px 20px 0;">
          <label>ข้อสอบเก่าอ้างอิง <span style="font-weight:400;opacity:.7">(.js/.json — ถอดสไตล์คำถาม)</span></label>
          <select id="oldExamSelect">
            <option value="">— ไม่ใช้ข้อสอบอ้างอิง (ออกตามมาตรฐาน NL/USMLE) —</option>
          </select>
          <div class="upload-row" style="margin: 8px 0 0; padding: 0;">
            <button class="tb-btn" style="width: 100%; padding: 8px;" onclick="document.getElementById('oldExamUpload').click()">⬆ อัปโหลดข้อสอบเก่า</button>
          </div>
          <input type="file" id="oldExamUpload" accept=".js,.json" style="display:none"
                 onchange="uploadFile('old-exam', this)">
        </div>

        <!-- Lecture slides -->
        <div class="file-toolbar" style="margin-top: 14px;">
          <span class="file-count-badge" id="lecCount">0 สไลด์</span>
          <button class="tb-btn refresh" onclick="loadGeneratorFiles()">🔄 รีเฟรช</button>
        </div>
        <div class="upload-row">
          <button class="tb-btn" onclick="document.getElementById('lectureUpload').click()">⬆ อัปโหลดสไลด์ (.pdf/.md/.txt)</button>
        </div>
        <input type="file" id="lectureUpload" accept=".pdf,.md,.txt" style="display:none"
               onchange="uploadFile('lecture', this)">
        <div class="file-scroll" id="lectureList">
          <div class="empty-files"><span>📂</span>กำลังโหลด...</div>
        </div>

        <!-- Phase (e): pull a finished Notes .md (enrich/summary) in as a slide input -->
        <div class="file-toolbar" style="margin-top:14px">
          <span class="file-count-badge">📥 จาก Notes</span>
          <button class="tb-btn refresh" onclick="loadNotesOutputs()">🔄 รีเฟรช</button>
        </div>
        <div class="hint" style="margin:6px 20px 6px">เลือกไฟล์สรุปจากแท็บ Notes มาใช้เป็นสไลด์สำหรับออกข้อสอบ</div>
        <div class="file-scroll" id="notesOutputList">
          <div class="empty-files"><span>📝</span>กำลังโหลด...</div>
        </div>
      </div>

      <!-- ══ NOTES MODE: 5-stage lecture-note pipeline ══ -->
      <div id="sectionNotes" style="display:none">
        <div class="field" style="padding: 16px 20px 0;">
          <label>⏱️ Cooldown ระหว่าง Lecture (วินาที)</label>
          <div class="hint">หน่วงเวลากัน quota เต็มเมื่อประมวลผลหลาย lecture</div>
          <input type="number" id="notesCooldown" value="10" min="0" max="120">
        </div>
        <div class="n-lectures-wrap" id="notesLecturesWrap"></div>
        <button class="n-btn-add" onclick="notesAddLecture()">＋ เพิ่ม Lecture</button>
      </div>

    </div><!-- /sidebar-content -->

    <!-- Sticky Footer Run Button -->
    <div class="run-wrap">
      <button class="run-btn" id="runBtn" onclick="run()">
        <span id="runIcon">▶</span>
        <span id="runLabel">เริ่มประมวลผลข้อสอบ</span>
      </button>
      <!-- Morphing secondary: Stop while running → Retry when ended with pending units -->
      <button id="actionBtn"></button>
    </div>

    <!-- Notes-mode footer (separate lifecycle: SSE, no polling/retry engine) -->
    <div class="run-wrap" id="notesRunWrap" style="display:none">
      <button class="run-btn" id="notesRunBtn" onclick="notesStart()">
        <span>▶</span><span id="notesRunLabel">เริ่มสรุปเลกเชอร์</span>
      </button>
      <button id="notesStopBtn" class="stop" style="display:none" onclick="notesStop()">⏹️ หยุด</button>
    </div>

  </div><!-- /left sidebar -->

  <!-- Right Log and Results Panel -->
  <div class="right">

   <!-- Convert/Generate right panel (polling log + results) -->
   <div id="cgRightPanel" class="rpanel">

    <!-- Progress panel -->
    <!-- Moved config accordion here -->
    <div class="config-box" id="rightConfigBox">
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
            <div class="hint">รับโทเค็นความปลอดภัยที่ <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--accent); text-decoration:none">aistudio.google.com</a></div>
            <div class="input-wrap">
              <input type="password" id="apiKey" placeholder="AIzaSy...">
              <button class="eye-btn" id="eyeBtn" type="button">👁</button>
            </div>
          </div>

          <!-- Saved keys + auto-rotation (phase d) -->
          <div class="field">
            <label>คลังคีย์ (หมุนเวียนอัตโนมัติเมื่อชนโควตา 429)</label>
            <div class="hint">เก็บในเซิร์ฟเวอร์ที่ <span class="mono">saved_keys.json</span> (ไม่ commit). ใส่คีย์ในช่องด้านบนแล้วกดบันทึก เพื่อให้ระบบสลับคีย์เองเมื่อคีย์แรกเต็มโควตา — ไม่ต้องพิมพ์คีย์ตอนรันก็ได้</div>
            <div id="savedKeysList" class="sk-list"><div class="sk-empty">ยังไม่มีคีย์ที่บันทึกไว้</div></div>
            <button class="sk-add" id="saveKeyBtn" type="button">➕ บันทึกคีย์ในช่องด้านบน</button>
          </div>

          <div class="field">
            <label>Gemini Model Selector</label>
            <select id="modelSelect">
              <option value="gemini-3.5-flash" selected>gemini-3.5-flash (เร็วสูงสุด · ความสามารถระดับ Pro · แนะนำ)</option>
              <option value="gemini-3.1-pro">gemini-3.1-pro (วิเคราะห์เชิงลึกและ Coding สูงสุด)</option>
              <option value="gemini-3.1-flash-lite">gemini-3.1-flash-lite (ประหยัดค่าใช้จ่ายและประมวลผลเร็ว)</option>
              <option value="gemini-2.5-pro">gemini-2.5-pro (โมเดลระดับ Pro ความเสถียรสูง)</option>
              <option value="gemini-2.5-flash">gemini-2.5-flash (โมเดลทั่วไป ความเสถียรสูง)</option>
            </select>
          </div>
        </div>

        <!-- 2. Course Preset & Prompt Configuration -->
        <div class="config-section cg-only">
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
        <div class="config-section cg-only">
          <div class="section-label">📝 EXTRA PROMPT INSTRUCTION</div>

          <div class="field">
            <label>Lecture Topics / คำสั่งเฉพาะวิชาเพิ่มเติม</label>
            <textarea id="additionalPrompt" rows="4" placeholder="ระบุรายชื่อ Lecture Topics หรือคำสั่งเสริมพิเศษรอบนี้&#10;(จะถูกโหลดอัตโนมัติเมื่อเลือก Course Preset)"></textarea>
          </div>
        </div>

      </div><!-- /config-sections-wrap -->
    </div>

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

   </div><!-- /cgRightPanel -->

   <!-- Notes right panel (SSE per-lecture × per-step tree) -->
   <div id="notesRightPanel" class="rpanel" style="display:none">
     <div class="n-batch-summary" id="notesBatchSummary" style="padding: 16px 28px 0; background: var(--bg);">รอการเริ่มสรุปเลกเชอร์...</div>
     <div class="n-progress-scroll" style="padding: 16px 28px;">
       <div id="notesLecturesProgress"></div>
       <div class="n-package-card" id="notesPackageCard" style="display:none">
         <div class="n-package-title">📁 Package</div>
         <ul class="n-step-list" id="notesPackageList"></ul>
       </div>
       <div id="notesFlatFilesArea" style="margin-top:16px;"></div>
       <div id="notesResultArea"></div>
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

// ─── Generate-mode state ───
let currentMode = 'convert';
let allLectures = [];
let selectedLectures = new Set();
let lectureMeta = {};            // filename → { num, topic }
let generatorLoaded = false;

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
    if (d.subgroup === 'MAPPED' && Array.isArray(d.topics) && d.topics.length && typeof d.topics[0] === 'object') {
      let prompt = 'รายชื่อหัวข้อบรรยายพร้อมกลุ่มวิชา (Lecture Topics with Subgroup mapping):\n';
      d.topics.forEach((t, i) => { prompt += `${i + 1}. [${t.subgroup}] ${t.topic}\n`; });
      prompt += '\nคำสั่งพิเศษ:\n';
      prompt += `- SubjectCode = ${d.subject_code}\n`;
      prompt += `- category[0] = ${d.subject_code}_<ExamGroup>\n`;
      prompt += `- category[1] = ${d.subject_code}_<SubGroupSuffix>_<TopicLabel>\n`;
      prompt += '  โดย <SubGroupSuffix> ต้องตรงกับกลุ่มวิชาในวงเล็บ [...] ของ topic นั้น (ตามรายการด้านบน)\n';
      prompt += '  และ <TopicLabel> ต้องตรงกับชื่อ lecture ทุกตัวอักษร\n';
      prompt += '- ถ้าข้อสอบไม่ตรงกับ lecture ใดเลย ให้ใช้ topic ที่ใกล้เคียงที่สุดจากรายการ';
      document.getElementById('additionalPrompt').value = prompt;
    } else if (d.subgroup === 'LEC' && d.topics && d.topics.length) {
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

// ─── Saved keys + auto-rotation (phase d) ───
let savedKeyCount = 0;
function renderSavedKeys(keys) {
  savedKeyCount = keys ? keys.length : 0;
  const box = document.getElementById('savedKeysList');
  if (!keys || !keys.length) {
    box.innerHTML = '<div class="sk-empty">ยังไม่มีคีย์ที่บันทึกไว้</div>';
    return;
  }
  box.innerHTML = keys.map(k =>
    `<div class="sk-row"><span class="sk-key">${escHtml(k.masked)}</span>` +
    `<button class="sk-del" type="button" title="ลบคีย์" onclick="deleteSavedKey(${k.index})">✕</button></div>`
  ).join('');
}
async function loadSavedKeys() {
  try {
    const r = await fetch('/api/keys');
    const d = await r.json();
    if (d.ok) renderSavedKeys(d.keys);
  } catch (e) { /* server not ready — ignore */ }
}
async function addSavedKey() {
  const inp = document.getElementById('apiKey');
  const key = inp.value.trim();
  if (!key) { alert('พิมพ์คีย์ในช่อง API Key ด้านบนก่อนกดบันทึก'); return; }
  const r = await fetch('/api/keys', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key })
  });
  const d = await r.json();
  if (d.ok) { renderSavedKeys(d.keys); inp.value = ''; }
  else alert(d.error || 'บันทึกคีย์ไม่สำเร็จ');
}
async function deleteSavedKey(idx) {
  const r = await fetch('/api/keys/' + idx, { method: 'DELETE' });
  const d = await r.json();
  if (d.ok) renderSavedKeys(d.keys);
  else alert(d.error || 'ลบคีย์ไม่สำเร็จ');
}
document.getElementById('saveKeyBtn').onclick = addSavedKey;
loadSavedKeys();

// ─── Mode switcher: Convert (PDF→JSON) vs Generate (slides→new MCQs) ───
function setMode(mode) {
  currentMode = mode;
  const isNotes = mode === 'notes';
  document.getElementById('modeConvertBtn').classList.toggle('active', mode === 'convert');
  document.getElementById('modeGenerateBtn').classList.toggle('active', mode === 'generate');
  document.getElementById('modeNotesBtn').classList.toggle('active', isNotes);

  document.getElementById('sectionConvert').style.display  = mode === 'convert'  ? 'block' : 'none';
  document.getElementById('sectionGenerate').style.display = mode === 'generate' ? 'block' : 'none';
  document.getElementById('sectionNotes').style.display    = isNotes ? 'block' : 'none';

  // Course-preset + extra-prompt config sections are Convert/Generate only
  document.querySelectorAll('.cg-only').forEach(el => el.style.display = isNotes ? 'none' : 'block');
  // Subject Code applies to Convert only
  document.getElementById('subjectTitle').closest('.field').style.display = mode === 'convert' ? 'block' : 'none';

  // Footers: shared polling footer vs notes SSE footer
  document.querySelector('.run-wrap:not(#notesRunWrap)').style.display = isNotes ? 'none' : 'block';
  document.getElementById('notesRunWrap').style.display = isNotes ? 'block' : 'none';

  // Right panels
  document.getElementById('cgRightPanel').style.display    = isNotes ? 'none' : 'flex';
  document.getElementById('notesRightPanel').style.display = isNotes ? 'flex' : 'none';

  if (!isNotes)
    document.getElementById('runLabel').textContent = mode === 'generate' ? 'เริ่มสร้างข้อสอบใหม่' : 'เริ่มประมวลผลข้อสอบ';
  if (mode === 'generate' && !generatorLoaded) { generatorLoaded = true; loadGeneratorFiles(); loadNotesOutputs(); }
  if (isNotes && !document.querySelector('#notesLecturesWrap .n-lecture-card')) notesAddLecture();
}

// ─── Generate: load lecture slides + old-exam references ───
async function loadGeneratorFiles() {
  try {
    const r = await fetch('/api/generator-files');
    const d = await r.json();
    allLectures = d.lectures || [];
    renderLectures();
    const sel = document.getElementById('oldExamSelect');
    const keep = sel.value;
    sel.innerHTML = '<option value="">— ไม่ใช้ข้อสอบอ้างอิง (ออกตามมาตรฐาน NL/USMLE) —</option>';
    (d.old_exams || []).forEach(name => {
      const opt = document.createElement('option');
      opt.value = name; opt.textContent = name;
      sel.appendChild(opt);
    });
    if ([...sel.options].some(o => o.value === keep)) sel.value = keep;
  } catch(e) {}
}

// ─── Phase (e): list finished Notes .md outputs, pick one → copy into LECTURE_DIR ───
async function loadNotesOutputs() {
  const wrap = document.getElementById('notesOutputList');
  try {
    const r = await fetch('/api/notes/outputs');
    const d = await r.json();
    const outs = d.outputs || [];
    if (!outs.length) {
      wrap.innerHTML = `<div class="empty-files"><span>📝</span>ยังไม่มีผลลัพธ์จาก Notes — รันแท็บ Notes ก่อน</div>`;
      return;
    }
    const kindLabel = { enrich: 'Enrich (ละเอียด)', summary: 'Summary (สรุป)' };
    wrap.innerHTML = outs.map(o => {
      const kb = Math.max(1, Math.round(o.size / 1024));
      const desc = `${o.lecture} · ${kindLabel[o.kind] || o.kind} · ${kb} KB`;
      return `<div class="lec-item">
        <div class="lec-head" style="cursor:default">
          <div class="file-label" title="${escHtml(o.batch)}/${escHtml(o.lecture)}">${escHtml(desc)}</div>
          <button class="tb-btn" onclick="useNotesOutput('${escJs(o.batch)}','${escJs(o.lecture)}','${escJs(o.kind)}')">＋ ใช้</button>
        </div>
      </div>`;
    }).join('');
  } catch(e) {
    wrap.innerHTML = `<div class="empty-files"><span>⚠️</span>โหลดไม่สำเร็จ</div>`;
  }
}

async function useNotesOutput(batch, lecture, kind) {
  try {
    const r = await fetch('/api/notes/use-as-lecture', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch, lecture, kind }),
    });
    const d = await r.json();
    if (!d.ok) { alert(d.error || 'ดึงไฟล์ไม่สำเร็จ'); return; }
    await loadGeneratorFiles();
    selectedLectures.add(d.filename);
    if (!lectureMeta[d.filename]) lectureMeta[d.filename] = { num: 35, topic: '' };
    renderLectures();
  } catch(e) { alert('ดึงไฟล์ไม่สำเร็จ: ' + e.message); }
}

function renderLectures() {
  const wrap = document.getElementById('lectureList');
  document.getElementById('lecCount').textContent = `${allLectures.length} สไลด์`;
  if (!allLectures.length) {
    wrap.innerHTML = `<div class="empty-files"><span>📂</span>ยังไม่มีสไลด์ — อัปโหลดหรือวางไฟล์ใน input_lectures/ แล้วกดรีเฟรช</div>`;
    return;
  }
  wrap.innerHTML = allLectures.map(name => {
    const sel = selectedLectures.has(name);
    const meta = lectureMeta[name] || { num: 35, topic: '' };
    return `<div class="lec-item ${sel ? 'selected' : ''}" data-name="${escHtml(name)}">
      <div class="lec-head" onclick="toggleLecture(this.parentElement.dataset.name)">
        <div class="file-checkbox">${sel ? '✓' : ''}</div>
        <div class="file-label" title="${escHtml(name)}">${escHtml(name)}</div>
        <div class="lec-status" data-status="${escHtml(name)}"></div>
      </div>
      <div class="lec-meta">
        <input class="lec-num" type="number" min="1" max="100" value="${meta.num}"
               title="จำนวนข้อ" oninput="setLectureMeta('${escJs(name)}','num',this.value)">
        <input class="lec-topic" type="text" placeholder="ชื่อหมวดหมู่ (topic_title) — เว้นว่างได้" value="${escHtml(meta.topic)}"
               oninput="setLectureMeta('${escJs(name)}','topic',this.value)">
      </div>
    </div>`;
  }).join('');
}

function toggleLecture(name) {
  if (selectedLectures.has(name)) selectedLectures.delete(name);
  else { selectedLectures.add(name); if (!lectureMeta[name]) lectureMeta[name] = { num: 35, topic: '' }; }
  renderLectures();
}

function setLectureMeta(name, key, val) {
  if (!lectureMeta[name]) lectureMeta[name] = { num: 35, topic: '' };
  lectureMeta[name][key] = key === 'num' ? (parseInt(val) || 35) : val;
}

// ─── Upload a lecture slide or old-exam reference ───
async function uploadFile(fileType, input) {
  const file = input.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  try {
    const r = await fetch('/api/upload/' + fileType, { method: 'POST', body: fd });
    const d = await r.json();
    if (!d.ok) { alert(d.error || 'อัปโหลดล้มเหลว'); return; }
    await loadGeneratorFiles();
    if (fileType === 'lecture') {
      selectedLectures.add(d.filename);
      if (!lectureMeta[d.filename]) lectureMeta[d.filename] = { num: 35, topic: '' };
      renderLectures();
    } else {
      document.getElementById('oldExamSelect').value = d.filename;
    }
  } catch(e) { alert('อัปโหลดล้มเหลว: ' + e.message); }
  input.value = '';
}

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

// Reset log/banner/action state before a fresh run OR retry (both runners reset job logs+done).
function beginJobUI() {
  lastLogCount = 0;
  document.getElementById('logConsole').innerHTML = '';
  document.getElementById('doneBannerWrap').innerHTML = '';
  document.getElementById('actionBtn').style.display = 'none';
}

// Run-button dispatcher → Convert or Generate by current mode.
function run() {
  if (currentMode === 'generate') startGeneration();
  else startConversion();
}

async function startGeneration() {
  const apiKey = document.getElementById('apiKey').value.trim();
  const model  = document.getElementById('modelSelect').value;
  const addPrompt = document.getElementById('additionalPrompt').value.trim();
  const oldExam   = document.getElementById('oldExamSelect').value;

  if (!apiKey && !savedKeyCount) { alert('กรุณาระบุ Gemini API Key หรือบันทึกคีย์ไว้ในคลังคีย์'); return; }
  if (!selectedLectures.size) { alert('กรุณาเลือกไฟล์สไลด์อย่างน้อย 1 รายการ'); return; }

  const lecture_files = [...selectedLectures].map(name => {
    const m = lectureMeta[name] || { num: 35, topic: '' };
    return { filename: name, num_questions: m.num || 35, topic_title: (m.topic || '').trim() };
  });

  beginJobUI();
  currentJobId = 'job_' + Date.now();

  try {
    const r = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey, model, job_id: currentJobId,
        mode: 'generate',
        lecture_files,
        old_exam_file: oldExam,
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

// Retry ONLY the failed/unreached units — must reuse the SAME job_id (server holds pending_units).
async function startRetry() {
  if (!currentJobId) return;
  const apiKey = document.getElementById('apiKey').value.trim();
  const model  = document.getElementById('modelSelect').value;
  if (!apiKey && !savedKeyCount) { alert('กรุณาระบุ Gemini API Key หรือบันทึกคีย์ไว้ในคลังคีย์'); return; }

  beginJobUI();
  try {
    const r = await fetch('/api/retry/' + currentJobId, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, model })
    });
    const d = await r.json();
    if (!d.ok) { alert(d.error); return; }
    startPolling();
  } catch(e) {
    alert('ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์: ' + e.message);
  }
}

async function stopJob() {
  if (!currentJobId) return;
  try {
    await fetch('/api/cancel/' + currentJobId, { method: 'POST' });
  } catch(e) {}
}

async function startConversion() {
  const apiKey    = document.getElementById('apiKey').value.trim();
  const model     = document.getElementById('modelSelect').value;
  const addPrompt    = document.getElementById('additionalPrompt').value.trim();
  const subjectTitle = document.getElementById('subjectTitle').value.trim().toUpperCase();

  if (!apiKey && !savedKeyCount) { alert('กรุณาระบุ Gemini API Key หรือบันทึกคีย์ไว้ในคลังคีย์'); return; }
  if (!selectedFiles.size) { alert('กรุณาเลือกไฟล์อย่างน้อย 1 รายการเพื่อดำเนินระบบ'); return; }

  beginJobUI();

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
  const act  = document.getElementById('actionBtn');

  if (d.running) {
    btn.disabled = true;
    btn.className = 'run-btn running-state';
    icon.innerHTML = '<div class="spinner"></div>';
    lbl.textContent = 'ระบบกำลังทำงานค้างอยู่...';
    // Morph → Stop
    act.className = 'stop';
    act.textContent = '⏹ หยุดหลังไฟล์ปัจจุบัน';
    act.onclick = stopJob;
    act.style.display = 'block';
  } else {
    btn.disabled = false;
    btn.className = 'run-btn';
    icon.textContent = '▶';
    lbl.textContent = currentMode === 'generate' ? 'เริ่มสร้างข้อสอบใหม่' : 'เริ่มประมวลผลข้อสอบ';
    // Morph → Retry when the job ended with unfinished units
    const pending = (d.pending_units || []).length;
    if (pending && (d.state === 'stopped' || d.state === 'partial')) {
      act.className = 'retry';
      act.textContent = `🔁 ทำซ้ำที่ค้าง (${pending} ไฟล์)`;
      act.onclick = startRetry;
      act.style.display = 'block';
    } else {
      act.style.display = 'none';
    }
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

// Escape for embedding inside a single-quoted inline JS handler attribute.
function escJs(s) {
  return String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'");
}

// ══════════════════════════════════════════════════════════════
// NOTES MODE — 5-stage lecture pipeline (SSE transport)
// ══════════════════════════════════════════════════════════════
const NOTES_STEP_DEFS = [
  { id:'slide_md',   label:'1. PDF → Markdown', cls:'',            on:true  },
  { id:'transcript', label:'2. Transcript',     cls:'',            on:true  },
  { id:'enrich',     label:'3. Slide Enrich',   cls:'n-s-enrich',  on:false },
  { id:'crystal',    label:'4. Crystallizer',   cls:'n-s-crystal', on:false },
  { id:'curriculum', label:'5. Curriculum Map', cls:'n-s-curr',    on:false },
];
let notesLectureCount = 0;
let notesSessionId = null, notesES = null;

function notesBuildStepsSelector(idx) {
  const div = document.createElement('div');
  div.className = 'n-steps-selector';
  div.innerHTML = '<label class="n-group-label">📤 Output steps ที่ต้องการ</label><div class="n-steps-grid"></div>';
  const grid = div.querySelector('.n-steps-grid');
  for (const s of NOTES_STEP_DEFS) {
    const lbl = document.createElement('label');
    lbl.className = 'n-step-toggle' + (s.cls ? ' '+s.cls : '') + (s.on ? ' checked' : '');
    lbl.dataset.step = s.id;
    lbl.innerHTML = `<input type="checkbox" ${s.on?'checked':''} onchange="notesToggleStep(this)">${s.label}`;
    grid.appendChild(lbl);
  }
  return div;
}
function notesToggleStep(inp) {
  inp.closest('.n-step-toggle').classList.toggle('checked', inp.checked);
}

function notesAddLecture(defaults = {}) {
  const idx  = notesLectureCount++;
  const wrap = document.getElementById('notesLecturesWrap');
  const div  = document.createElement('div');
  div.className = 'n-lecture-card open';
  div.dataset.idx = idx;
  div.innerHTML = `
    <div class="n-lecture-header" onclick="notesToggleCard(${idx})">
      <span class="n-lecture-num">#${idx+1}</span>
      <input type="text" data-field="label_${idx}" placeholder="ชื่อ Lecture ${idx+1}"
             value="${defaults.label||''}" onclick="event.stopPropagation()">
      <span class="n-chevron">▼</span>
      <button class="n-btn-remove" onclick="notesRemoveLecture(${idx},event)" title="ลบ">✕</button>
    </div>
    <div class="n-lecture-body">
      <div class="field">
        <label>📄 PDF Slide <span style="color:var(--err)">*</span></label>
        <div class="hint">ชื่อโฟลเดอร์ output จะใช้ชื่อไฟล์ PDF นี้</div>
        <div class="n-drop-zone" id="ndz-slide-${idx}">
          <input type="file" data-field="slide_${idx}" accept=".pdf" onchange="notesSetDz('ndz-slide-${idx}',this)">
          <div class="n-dz-icon">📑</div>
          <div class="n-dz-label">คลิกหรือลากไฟล์ PDF มาวาง</div>
          <div class="n-dz-filename" id="nfn-slide-${idx}"></div>
        </div>
      </div>
      <div class="n-row-2">
        <div class="field">
          <label>🎙️ Transcript <span class="n-opt">optional</span></label>
          <div class="n-drop-zone" id="ndz-trans-${idx}" style="margin-bottom:.5rem">
            <input type="file" data-field="transcript_${idx}" accept=".txt" onchange="notesSetDz('ndz-trans-${idx}',this)">
            <div class="n-dz-icon">🎤</div>
            <div class="n-dz-label">transcript.txt</div>
            <div class="n-dz-filename" id="nfn-trans-${idx}"></div>
          </div>
          <textarea data-field="transcript_text_${idx}" placeholder="หรือวางข้อความ transcript..." rows="3"></textarea>
        </div>
        <div class="field">
          <label>📚 Curriculum Map <span class="n-opt">optional</span></label>
          <div class="n-drop-zone" id="ndz-curr-${idx}">
            <input type="file" data-field="curriculum_map_${idx}" accept=".md,.txt" onchange="notesSetDz('ndz-curr-${idx}',this)">
            <div class="n-dz-icon">🗂️</div>
            <div class="n-dz-label">Curriculum_Map.md</div>
            <div class="n-dz-filename" id="nfn-curr-${idx}"></div>
          </div>
        </div>
      </div>
      <details class="n-resume">
        <summary>🔄 Resume จากขั้นตอนกลาง (อัปโหลดไฟล์ .md ที่ทำไว้แล้ว)</summary>
        <div class="n-resume-grid">
          <div class="field"><label>1. lecture-markdown.md</label>
            <input type="file" data-field="uploaded_markdown_${idx}" accept=".md"></div>
          <div class="field"><label>2. lecture-transcribe.md</label>
            <input type="file" data-field="uploaded_transcribe_${idx}" accept=".md"></div>
          <div class="field"><label>3. lecture-enrich.md</label>
            <input type="file" data-field="uploaded_enrich_${idx}" accept=".md"></div>
          <div class="field"><label>4. lecture-summary.md</label>
            <input type="file" data-field="uploaded_summary_${idx}" accept=".md"></div>
        </div>
      </details>
    </div>`;
  const body = div.querySelector('.n-lecture-body');
  body.appendChild(notesBuildStepsSelector(idx));
  wrap.appendChild(div);
  notesSetupDropZones(div);
  notesRenumber();
}

function notesRemoveLecture(idx, e) {
  e.stopPropagation();
  const wrap = document.getElementById('notesLecturesWrap');
  if (wrap.querySelectorAll('.n-lecture-card').length <= 1) { alert('ต้องมีอย่างน้อย 1 Lecture'); return; }
  wrap.querySelector(`.n-lecture-card[data-idx="${idx}"]`)?.remove();
  notesRenumber();
}
function notesRenumber() {
  document.querySelectorAll('#notesLecturesWrap .n-lecture-card').forEach((c, i) => {
    c.querySelector('.n-lecture-num').textContent = `#${i+1}`;
  });
}
function notesToggleCard(idx) {
  document.querySelector(`.n-lecture-card[data-idx="${idx}"]`)?.classList.toggle('open');
}
function notesSetDz(dzId, inp) {
  const fn = document.querySelector(`#${dzId} .n-dz-filename`);
  if (fn) fn.textContent = inp.files[0] ? inp.files[0].name : '';
}
function notesSetupDropZones(root) {
  root.querySelectorAll('.n-drop-zone').forEach(dz => {
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
    dz.addEventListener('drop', e => {
      e.preventDefault(); dz.classList.remove('dragover');
      const inp = dz.querySelector('input[type=file]');
      if (e.dataTransfer.files.length && inp) { inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change')); }
    });
  });
}

function notesBuildFormData() {
  const fd = new FormData();
  fd.append('api_key',  document.getElementById('apiKey').value.trim());
  fd.append('model',    document.getElementById('modelSelect').value);
  fd.append('cooldown', document.getElementById('notesCooldown').value);
  const cards = document.querySelectorAll('#notesLecturesWrap .n-lecture-card');
  fd.append('lecture_count', cards.length);
  cards.forEach((card, i) => {
    const labelEl = card.querySelector('input[type=text]');
    fd.append(`label_${i}`, labelEl ? (labelEl.value.trim() || `Lecture ${i+1}`) : `Lecture ${i+1}`);
    card.querySelectorAll('.n-step-toggle input:checked').forEach(inp => {
      fd.append(`steps_${i}`, inp.closest('.n-step-toggle').dataset.step);
    });
    card.querySelectorAll('input[type=file]').forEach(inp => {
      if (inp.dataset.field && inp.files[0]) {
        fd.append(inp.dataset.field.replace(/_\d+$/, `_${i}`), inp.files[0]);
      }
    });
    const ta = card.querySelector('textarea');
    if (ta && ta.value.trim()) fd.append(`transcript_text_${i}`, ta.value.trim());
  });
  return fd;
}

// ── Notes progress rendering ──
let notesLecStates = [];
function notesBuildProgress(labels) {
  notesLecStates = labels.map(() => 'waiting');
  const wrap = document.getElementById('notesLecturesProgress');
  wrap.innerHTML = '';
  document.getElementById('notesPackageCard').style.display = 'none';
  document.getElementById('notesResultArea').innerHTML = '';
  labels.forEach((lbl, i) => {
    const div = document.createElement('div');
    div.className = 'n-lec-prog';
    div.id = `n-lp-${i}`;
    div.innerHTML = `
      <div class="n-lp-header" onclick="this.parentElement.classList.toggle('open')">
        <span class="n-lec-badge" id="n-badge-${i}">⏳ รอ</span>
        <span class="n-lp-title">${escHtml(lbl)}</span>
        <span class="n-chevron">▼</span>
      </div>
      <div class="n-lp-body"><ul class="n-step-list" id="n-steps-${i}"></ul></div>`;
    wrap.appendChild(div);
  });
}
function notesSetLec(i, state) {
  const badge = document.getElementById(`n-badge-${i}`);
  const card  = document.getElementById(`n-lp-${i}`);
  if (!badge) return;
  const map = { waiting:['⏳ รอ',''], running:['⚡ กำลังรัน','running'], done:['✓ เสร็จ','done'], error:['✗ ผิดพลาด','error'] };
  const [text, cls] = map[state] || map.waiting;
  badge.textContent = text;
  badge.className = 'n-lec-badge' + (cls ? ' '+cls : '');
  if (state === 'running') card.classList.add('open');
}
function notesEnsureStep(li, stepId, label) {
  const list = document.getElementById(`n-steps-${li}`);
  if (!list || list.querySelector(`[data-step-id="${stepId}"]`)) return;
  const el = document.createElement('li');
  el.className = 'n-step-item'; el.dataset.state = 'waiting'; el.dataset.stepId = stepId;
  el.innerHTML = `<div class="n-step-icon"></div><div class="n-step-body">
      <div class="n-step-label">${escHtml(label)}</div>
      <div class="n-step-log" id="n-log-${li}-${stepId}"></div>
      <div class="n-step-fn" id="n-fn-${li}-${stepId}"></div></div>`;
  list.appendChild(el);
}
function notesSetStep(li, stepId, state) {
  const listId = li === -1 ? 'notesPackageList' : `n-steps-${li}`;
  document.querySelector(`#${listId} [data-step-id="${stepId}"]`)?.setAttribute('data-state', state);
}
function notesLogStep(li, stepId, msg) {
  const el = document.getElementById(li === -1 ? `n-log-pkg-${stepId}` : `n-log-${li}-${stepId}`);
  if (el) el.textContent += (el.textContent ? '\n' : '') + msg;
}
function notesEnsurePkgStep(stepId, label) {
  document.getElementById('notesPackageCard').style.display = '';
  const list = document.getElementById('notesPackageList');
  if (list.querySelector(`[data-step-id="${stepId}"]`)) return;
  const el = document.createElement('li');
  el.className = 'n-step-item'; el.dataset.state = 'waiting'; el.dataset.stepId = stepId;
  el.innerHTML = `<div class="n-step-icon"></div><div class="n-step-body">
      <div class="n-step-label">${escHtml(label)}</div>
      <div class="n-step-log" id="n-log-pkg-${stepId}"></div>
      <div class="n-step-fn" id="n-fn-pkg-${stepId}"></div></div>`;
  list.appendChild(el);
}
function notesHandleEvent(d) {
  const isPkg = d.lecture === -1 || d.lecture === undefined;
  switch (d.event) {
    case 'batch_start':
      document.getElementById('notesBatchSummary').textContent = `กำลังประมวลผล ${d.total} lecture${d.total>1?'s':''}...`;
      return;
    case 'lecture_start':
      notesSetLec(d.lecture, 'running');
      document.getElementById('notesBatchSummary').textContent = `Lecture ${d.lecture+1}/${d.total}: ${d.label}`;
      return;
    case 'lecture_done': notesSetLec(d.lecture, 'done'); return;
    case 'lecture_error': {
      notesSetLec(d.lecture, 'error');
      const list = document.getElementById(`n-steps-${d.lecture}`);
      if (list) {
        const li = document.createElement('li');
        li.className = 'n-step-item'; li.dataset.state = 'error';
        li.innerHTML = `<div class="n-step-icon"></div><div class="n-step-body">
            <div class="n-step-label" style="color:var(--err);font-weight:600">เกิดข้อผิดพลาด</div>
            <div class="n-step-log n-err-box">${escHtml(d.error)}</div></div>`;
        list.appendChild(li);
      }
      return;
    }
    case 'step_start':
      if (isPkg) { notesEnsurePkgStep(d.step, d.label); notesSetStep(-1, d.step, 'running'); }
      else { notesEnsureStep(d.lecture, d.step, d.label || d.step); notesSetStep(d.lecture, d.step, 'running'); }
      return;
    case 'step_log': notesLogStep(isPkg ? -1 : d.lecture, d.step, d.msg); return;
    case 'step_done': {
      notesSetStep(isPkg ? -1 : d.lecture, d.step, 'done');
      const el = document.getElementById(isPkg ? `n-fn-pkg-${d.step}` : `n-fn-${d.lecture}-${d.step}`);
      if (el && d.filename) el.textContent = '→ ' + d.filename;
      return;
    }
    case 'done':        notesShowDone(d.session, d.folder, d.total, d.cancelled); notesEndRun(); return;
    case 'fatal_error': notesShowFatal(d.msg + (d.detail ? '\n\n'+d.detail : '')); notesEndRun(); return;
    case 'stream_end':  notesEndRun(); return;
  }
}
function notesShowDone(sid, folder, total, cancelled) {
  document.getElementById('notesBatchSummary').textContent =
    cancelled ? `⏹️ หยุดแล้ว — บันทึก partial output` : `✅ เสร็จสมบูรณ์ ${total} lecture${total>1?'s':''}`;
  document.getElementById('notesResultArea').innerHTML = `
    <div class="n-done-banner ${cancelled?'cancelled':''}">
      <p>${cancelled?'⏹️ หยุดกลางคัน':'✅ Batch สำเร็จ!'}<br><strong>${escHtml(folder)}</strong></p>
      <a class="n-btn-download" href="/api/notes/download/${sid}">⬇ ดาวน์โหลด ZIP</a>
    </div>`;
  // Also refresh flat file list
  loadNotesFlatFiles();

}
function notesShowFatal(msg) {
  document.getElementById('notesResultArea').innerHTML = `<div class="n-err-box" style="padding:1rem">❌ Fatal Error:\n${escHtml(msg)}</div>`;
}
function notesEndRun() {
  if (notesES) { notesES.close(); notesES = null; }
  document.getElementById('notesRunBtn').style.display = 'flex';
  document.getElementById('notesStopBtn').style.display = 'none';
}

async function notesStart() {
  const apiKey = document.getElementById('apiKey').value.trim();
  if (!apiKey && !savedKeyCount) { alert('กรุณาใส่ API Key หรือบันทึกคีย์ไว้ในคลังคีย์'); return; }
  const cards = document.querySelectorAll('#notesLecturesWrap .n-lecture-card');
  const labels = Array.from(cards).map((c, i) => {
    const inp = c.querySelector('input[type=text]');
    return inp ? (inp.value.trim() || `Lecture ${i+1}`) : `Lecture ${i+1}`;
  });
  document.getElementById('notesRunBtn').style.display = 'none';
  const stopBtn = document.getElementById('notesStopBtn');
  stopBtn.style.display = 'block';
  stopBtn.disabled = false;
  stopBtn.textContent = '⏹️ หยุด';
  notesBuildProgress(labels);
  document.getElementById('notesBatchSummary').textContent = 'กำลังเตรียมระบบ...';
  try {
    const res  = await fetch('/api/notes/run', { method:'POST', body: notesBuildFormData() });
    const data = await res.json();
    if (!res.ok) { notesShowFatal(data.error || 'Unknown error'); notesEndRun(); return; }
    notesSessionId = data.session_id;
    notesES = new EventSource(`/api/notes/progress/${notesSessionId}`);
    notesES.onmessage = e => notesHandleEvent(JSON.parse(e.data));
    notesES.onerror = () => {};
  } catch(e) { notesShowFatal(e.message); notesEndRun(); }
}

async function notesStop() {
  if (!notesSessionId) return;
  document.getElementById('notesStopBtn').disabled = true;
  try { await fetch(`/api/notes/cancel/${notesSessionId}`, { method:'POST' }); } catch(e) {}
  document.getElementById('notesStopBtn').textContent = '⏳ กำลังหยุด...';
}

// Initial Load Commands
loadFiles();
loadOutputs();
loadNotesFlatFiles();
setInterval(loadFiles, 15000);

async function loadNotesFlatFiles() {
  try {
    const res = await fetch('/api/notes/outputs');
    const data = await res.json();
    const flat = data.outputs.filter(o => o.source === 'flat');
    const area = document.getElementById('notesFlatFilesArea');
    if (!area) return;
    area.innerHTML = '';
    if (flat.length === 0) { area.innerHTML = '<div class="n-flat-empty">ยังไม่มีสรุปเลกเชอร์แบบเดี่ยว</div>'; return; }
    for (const f of flat) {
      const div = document.createElement('div');
      div.className = 'n-flat-file';
      div.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;padding:.5rem 0">
        <div style="font-weight:600">${escHtml(f.name)}</div>
        <div><a href="/notes/static/${encodeURIComponent(f.name)}" target="_blank">⬇ เปิด/ดาวน์โหลด</a></div>
      </div>`;
      area.appendChild(div);
    }
  } catch(e) { console.warn('loadNotesFlatFiles', e); }
}


// Static route for flat notes files
</script>
</body>
</html>
"""


# Static route for flat notes files (served by Flask, not embedded HTML)
@app.route('/notes/static/<path:fname>')
def notes_static(fname):
    p = NOTES_OUTPUT_BASE / Path(fname).name
    if not p.exists() or not p.is_file():
        return 'Not found', 404
    return send_file(p, as_attachment=True)


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