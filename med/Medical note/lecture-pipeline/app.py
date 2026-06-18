#!/usr/bin/env python3
"""
Lecture Pipeline Automation — Batch Edition (Google AI Studio)
==============================================================
- Sequential batch runner with Cooldown Delay configuration
- Strict API Pacing Controller (5 RPM cap)
- Automatic retry on 503/429 Errors with Exponential Backoff
- Dynamic Fallback to stable model on failure
- Per-lecture output step selection (default: steps 1–3)
- Output folder named from input PDF / markdown filename

Usage:
  pip install google-genai flask
  python app.py
  Open http://localhost:5000
"""

import os, json, time, queue, threading, zipfile, uuid, shutil, random
from datetime import datetime
from pathlib import Path
import tempfile
import traceback

from flask import Flask, request, jsonify, Response, send_file

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB

PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}\n"
            f"Please place all .md prompt files in the 'prompts/' folder."
        )
    return path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────
# Google Model List
# ─────────────────────────────────────────────────────────────

GOOGLE_MODELS = [
    {"id": "gemini-2.5-flash",        "label": "gemini-2.5-flash (แนะนำ — เสถียร+เร็ว)"},
    {"id": "gemini-2.5-pro",          "label": "gemini-2.5-pro (คุณภาพสูง)"},
    {"id": "gemini-2.5-flash-lite",   "label": "gemini-2.5-flash-lite (ประหยัด quota)"},
    {"id": "gemini-3.5-flash",        "label": "gemini-3.5-flash (ใหม่ — เร็ว+คุณภาพ)"},
    {"id": "gemini-3.1-pro-preview",  "label": "gemini-3.1-pro-preview (วิเคราะห์เชิงลึก)"},
    {"id": "gemini-3.1-flash-lite",   "label": "gemini-3.1-flash-lite (ประหยัด+เร็ว)"},
    {"id": "gemini-3-flash-preview",  "label": "gemini-3-flash-preview"},
    {"id": "gemini-3-pro-preview",    "label": "gemini-3-pro-preview"},
]

@app.route("/api/models")
def api_models():
    return jsonify({"models": GOOGLE_MODELS})


# ─────────────────────────────────────────────────────────────
# Google AI Studio Provider
# ─────────────────────────────────────────────────────────────

class GoogleProvider:
    """Wraps google-genai SDK."""

    def __init__(self, api_key: str, model_name: str):
        from google import genai
        from google.genai import types
        self._types = types
        self.client = genai.Client(api_key=api_key)
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
        self._min_interval = 13.0

    def _pace(self, log_fn=None):
        now = time.time()
        elapsed = now - self._last_call
        if elapsed < self._min_interval:
            wait = self._min_interval - elapsed
            if log_fn:
                log_fn(f"⏳ เว้นจังหวะ API (Pacing Delay) {wait:.1f} วินาที...")
            time.sleep(wait)
        self._last_call = time.time()

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
                        import re
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
        """Return a copy of this provider pointing at a different model."""
        clone = object.__new__(GoogleProvider)
        clone._types = self._types
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

    def fallback_model(self) -> "tuple[GoogleProvider, str] | None":
        """Return a fallback provider for frontier models, or None."""
        is_frontier = any(m in self.model_name for m in ["3.5", "3.1"])
        if not is_frontier:
            return None
        fallback_name = "gemini-2.5-flash" if "flash" in self.model_name else "gemini-2.5-pro"
        return self.with_model(fallback_name), fallback_name


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _safe_stem(filename: str) -> str:
    """Convert a filename to a safe folder-name stem (no extension)."""
    stem = Path(filename).stem
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in stem).strip()
    return safe[:60] or "lecture"


# ─────────────────────────────────────────────────────────────
# Single-lecture pipeline
# ─────────────────────────────────────────────────────────────

# Step IDs in order
ALL_STEPS = ["slide_md", "transcript", "enrich", "crystal", "curriculum"]
DEFAULT_STEPS = {"slide_md", "transcript", "enrich"}


def run_single_lecture(
    provider: GoogleProvider,
    lecture_idx: int,
    lecture_label: str,
    output_dir: Path,
    emit,
    # input files
    slide_path: str | None,
    slide_name: str | None,
    transcript_path: str | None,
    curriculum_map_path: str | None,
    # resume / pre-computed outputs
    uploaded_markdown_path: str | None = None,
    uploaded_transcribe_path: str | None = None,
    uploaded_enrich_path: str | None = None,
    uploaded_summary_path: str | None = None,
    # which steps to run
    requested_steps: set | None = None,
):
    if requested_steps is None:
        requested_steps = DEFAULT_STEPS

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

    # Load any pre-computed files
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
        (output_dir / "lecture-summary.md").write_text(lecture_summary, encoding="utf-8")

    # ── STEP 1: Slide PDF → Markdown ─────────────────────────
    if "slide_md" in requested_steps:
        step_start("slide_md", "📄 แปลง PDF สไลด์ → Markdown")
        if lecture_markdown:
            step_log("slide_md", "ใช้ไฟล์ lecture-markdown.md จากรอบก่อนหน้านี้")
            step_done("slide_md", "lecture-markdown.md")
        elif slide_path:
            step_log("slide_md", f"กำลังอัปโหลดไฟล์ '{slide_name}' ไปยัง Gemini File API...")
            uploaded_slide = provider.upload_file(
                file_path=slide_path,
                display_name=slide_name,
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
                    name=uploaded_slide.name,
                    log_fn=lambda msg: step_log("slide_md", msg),
                )
                state_str = get_state_str(uploaded_slide)
                step_log("slide_md", f"  ประมวลผล... ({wait}s)")

            if state_str == "FAILED":
                raise RuntimeError("Gemini File API ไม่สามารถประมวลผลไฟล์ PDF ได้")

            prompt_slide_md = load_prompt("slide-to-markdown-gemini.md")
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
        step_start("transcript", "🎙️ สังเคราะห์ Transcript + Slide Notes")
        if lecture_transcribe:
            step_log("transcript", "ใช้ไฟล์ lecture-transcribe.md จากรอบก่อนหน้านี้")
            step_done("transcript", "lecture-transcribe.md")
        else:
            step_log("transcript", "กำลังอ่านไฟล์ transcript...")
            transcript_text = Path(transcript_path).read_text(encoding="utf-8")
            prompt_synth = load_prompt("lecture-synthesizer.md")
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
        step_start("enrich", "🔬 เพิ่มกลไกทางการแพทย์ — Slide Enrich")
        if lecture_enrich:
            step_log("enrich", "ใช้ไฟล์ lecture-enrich.md จากรอบก่อนหน้านี้")
            step_done("enrich", "lecture-enrich.md")
        else:
            prompt_enrich = load_prompt("slide-enrich.md")
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
        step_start("crystal", "💎 ตกผลึกเนื้อหา — Lecture Crystallizer")
        if lecture_summary:
            step_log("crystal", "ใช้ไฟล์ lecture-summary.md จากรอบก่อนหน้านี้")
            step_done("crystal", "lecture-summary.md")
        else:
            prompt_crystal = load_prompt("lecture-crystallizer.md")
            if chat is not None:
                step_log("crystal", "กำลัง generate lecture-summary.md (ต่อจาก session เดิม)...")
                lecture_summary = provider.chat_send(
                    chat,
                    prompt_crystal + "\n\n---\nโปรดตกผลึกเนื้อหา",
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
            (output_dir / "lecture-summary.md").write_text(lecture_summary, encoding="utf-8")
            step_log("crystal", f"✓ บันทึก lecture-summary.md ({len(lecture_summary):,} ตัวอักษร)")
            step_done("crystal", "lecture-summary.md")

    # ── STEP 5: Curriculum Map ────────────────────────────────
    if "curriculum" in requested_steps and curriculum_map_path:
        step_start("curriculum", "📚 อัปเดต Curriculum Map")
        curriculum_map_text = Path(curriculum_map_path).read_text(encoding="utf-8")
        prompt_curriculum = load_prompt("curriculum-tracker.md")
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


# ─────────────────────────────────────────────────────────────
# Batch pipeline
# ─────────────────────────────────────────────────────────────

sessions: dict[str, dict] = {}
OUTPUT_BASE = Path(__file__).parent / "output"
OUTPUT_BASE.mkdir(exist_ok=True)


def run_batch_pipeline(session_id: str, api_key: str, model_name: str,
                       lectures: list[dict], cooldown: int):
    q: queue.Queue = sessions[session_id]["queue"]
    batch_dir: Path = sessions[session_id]["output_dir"]

    def emit(event: str, **data):
        q.put(json.dumps({"event": event, **data}))

    try:
        provider = GoogleProvider(api_key=api_key, model_name=model_name)
        emit("batch_start", total=len(lectures))

        for idx, lec in enumerate(lectures):
            label = lec.get("label", f"Lecture {idx + 1}")

            if idx > 0 and cooldown > 0:
                emit("step_start", lecture=idx, step="cooldown",
                     label=f"⏱️ Cooldown — รอ {cooldown} วินาที...")
                time.sleep(cooldown)
                emit("step_done", lecture=idx, step="cooldown")

            emit("lecture_start", lecture=idx, label=label, total=len(lectures))

            # Determine output folder name from input file
            folder_stem = lec.get("folder_stem", f"{idx+1:02d}_{label}")
            lec_dir = batch_dir / folder_stem
            if lec_dir.exists():
                shutil.rmtree(lec_dir)
            lec_dir.mkdir(parents=True, exist_ok=True)

            requested_steps = set(lec.get("steps", list(DEFAULT_STEPS)))

            lec_kwargs = dict(
                lecture_idx=idx,
                lecture_label=label,
                output_dir=lec_dir,
                emit=emit,
                slide_path=lec.get("slide_path"),
                slide_name=lec.get("slide_name"),
                transcript_path=lec.get("transcript_path"),
                curriculum_map_path=lec.get("curriculum_map_path"),
                uploaded_markdown_path=lec.get("uploaded_markdown_path"),
                uploaded_transcribe_path=lec.get("uploaded_transcribe_path"),
                uploaded_enrich_path=lec.get("uploaded_enrich_path"),
                uploaded_summary_path=lec.get("uploaded_summary_path"),
                requested_steps=requested_steps,
            )

            try:
                run_single_lecture(provider=provider, **lec_kwargs)
                emit("lecture_done", lecture=idx, label=label)
            except Exception as e:
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
                        emit("lecture_done", lecture=idx, label=label)
                    except Exception as fe:
                        tb = traceback.format_exc()
                        emit("lecture_error", lecture=idx, label=label,
                             error=f"ล้มเหลวในการสลับ fallback: {fe}\n\nข้อผิดพลาดเดิม:\n{type(e).__name__}: {e}\n\n{tb}")
                else:
                    tb = traceback.format_exc()
                    emit("lecture_error", lecture=idx, label=label,
                         error=f"{type(e).__name__}: {e}\n\n{tb}")

        # Package ZIP
        emit("step_start", lecture=-1, step="package", label="📁 สร้าง ZIP รวม")
        zip_path = OUTPUT_BASE / f"{batch_dir.name}.zip"
        file_count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(batch_dir.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(batch_dir))
                    emit("step_log", lecture=-1, step="package",
                         msg=f"  + {f.relative_to(batch_dir)}")
                    file_count += 1

        sessions[session_id]["zip_path"] = str(zip_path)
        emit("step_log", lecture=-1, step="package",
             msg=f"✓ {zip_path.name} ({file_count} ไฟล์)")
        emit("step_done", lecture=-1, step="package", filename=zip_path.name)
        emit("done", folder=batch_dir.name, zip=zip_path.name,
             session=session_id, total=len(lectures))

    except Exception as e:
        tb = traceback.format_exc()
        emit("fatal_error", msg=str(e), detail=tb)
    finally:
        q.put(None)


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HTML_PAGE


@app.route("/run", methods=["POST"])
def run_route():
    api_key    = request.form.get("api_key", "").strip()
    model_name = request.form.get("model", "").strip()

    if not api_key:
        return jsonify(error="กรุณาใส่ API Key"), 400
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

        uploaded_markdown  = request.files.get(f"uploaded_markdown_{i}")
        uploaded_transcribe = request.files.get(f"uploaded_transcribe_{i}")
        uploaded_enrich    = request.files.get(f"uploaded_enrich_{i}")
        uploaded_summary   = request.files.get(f"uploaded_summary_{i}")

        # Parse requested steps for this lecture
        raw_steps = request.form.getlist(f"steps_{i}")
        requested_steps = set(raw_steps) if raw_steps else set(DEFAULT_STEPS)

        has_slide = slide_file and slide_file.filename
        has_any = has_slide or any([
            uploaded_markdown  and uploaded_markdown.filename,
            uploaded_transcribe and uploaded_transcribe.filename,
            uploaded_enrich    and uploaded_enrich.filename,
            uploaded_summary   and uploaded_summary.filename,
        ])

        if not has_any:
            return jsonify(
                error=f"Lecture {i+1} ({label}): กรุณาอัปโหลดไฟล์ PDF สไลด์หรือไฟล์ขั้นตอนกลาง"
            ), 400

        lec_tmp = tmp_dir / f"lec_{i}"
        lec_tmp.mkdir()
        lec = {"label": label, "steps": list(requested_steps)}

        # Determine folder stem from primary input file
        if has_slide:
            lec["folder_stem"] = _safe_stem(slide_file.filename)
        elif uploaded_markdown and uploaded_markdown.filename:
            lec["folder_stem"] = _safe_stem(uploaded_markdown.filename)
        elif uploaded_enrich and uploaded_enrich.filename:
            lec["folder_stem"] = _safe_stem(uploaded_enrich.filename)
        else:
            safe_label = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in label
            )[:40]
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
    batch_name = f"batch_{timestamp}"
    batch_dir  = OUTPUT_BASE / batch_name
    batch_dir.mkdir(parents=True, exist_ok=True)

    sessions[session_id] = {
        "queue":         queue.Queue(),
        "output_dir":    batch_dir,
        "zip_path":      None,
        "tmp_dir":       str(tmp_dir),
        "lecture_count": len(lectures),
    }

    t = threading.Thread(
        target=run_batch_pipeline,
        args=(session_id, api_key, model_name, lectures, cooldown),
        daemon=True,
    )
    t.start()

    return jsonify(session_id=session_id, lecture_count=len(lectures))


@app.route("/progress/<session_id>")
def progress_route(session_id: str):
    if session_id not in sessions:
        return "Session not found", 404

    def generate():
        q: queue.Queue = sessions[session_id]["queue"]
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


@app.route("/download/<session_id>")
def download_route(session_id: str):
    if session_id not in sessions:
        return "Session not found", 404
    zip_path = sessions[session_id].get("zip_path")
    if not zip_path or not Path(zip_path).exists():
        return "ไฟล์ยังไม่พร้อม", 404
    return send_file(zip_path, as_attachment=True)


# ─────────────────────────────────────────────────────────────
# HTML UI
# ─────────────────────────────────────────────────────────────

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lecture Pipeline — Batch Edition</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Thai:wght@300;400;500;600&display=swap');
  :root {
    --bg:#0d1117;--surface:#161b22;--surface2:#1c2330;--border:#30363d;
    --accent:#58a6ff;--accent2:#3fb950;--warn:#f0883e;--err:#f85149;
    --text:#e6edf3;--muted:#8b949e;
    --mono:'IBM Plex Mono',monospace;--sans:'IBM Plex Sans Thai',sans-serif;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;padding:2rem 1rem}
  .container{max-width:920px;margin:0 auto}
  header{margin-bottom:2rem;padding-bottom:1.25rem;border-bottom:1px solid var(--border)}
  header h1{font-size:1.5rem;font-weight:600;letter-spacing:-.02em}
  header h1 span{color:var(--accent)}
  header p{color:var(--muted);font-size:.875rem;margin-top:.35rem;line-height:1.6}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:1.5rem;margin-bottom:1.25rem}
  .card-title{font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:1rem}
  .field{margin-bottom:.9rem}
  .field label{display:block;font-size:.875rem;font-weight:500;margin-bottom:.35rem}
  .field .hint{font-size:.75rem;color:var(--muted);margin-bottom:.35rem}
  .field input[type=text],.field input[type=password],.field select,
  .field textarea,.field input[type=number]{
    width:100%;background:var(--bg);border:1px solid var(--border);border-radius:6px;
    color:var(--text);font-family:var(--mono);font-size:.875rem;padding:.55rem .7rem;
    outline:none;transition:border-color .15s}
  .field input:focus,.field select:focus,.field textarea:focus,
  .field input[type=number]:focus{border-color:var(--accent)}
  .field textarea{font-family:var(--sans);resize:vertical}
  .row-2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
  .row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1rem}
  @media(max-width:600px){.row-2,.row-3{grid-template-columns:1fr}}

  /* ── Step checkboxes ── */
  .steps-selector{margin:.75rem 0}
  .steps-selector label.group-label{font-size:.78rem;font-weight:600;color:var(--muted);
    text-transform:uppercase;letter-spacing:.06em;display:block;margin-bottom:.5rem}
  .steps-grid{display:flex;flex-wrap:wrap;gap:.4rem}
  .step-toggle{display:inline-flex;align-items:center;gap:.4rem;padding:.35rem .65rem;
    border-radius:5px;border:1px solid var(--border);cursor:pointer;font-size:.8rem;
    background:transparent;color:var(--muted);transition:all .15s;user-select:none}
  .step-toggle input{display:none}
  .step-toggle.checked{border-color:var(--accent);color:var(--accent);
    background:rgba(88,166,255,.1)}
  .step-toggle.step-crystal.checked{border-color:var(--warn);color:var(--warn);
    background:rgba(240,136,62,.1)}
  .step-toggle.step-curriculum.checked{border-color:var(--accent2);color:var(--accent2);
    background:rgba(63,185,80,.1)}

  /* ── Lecture cards ── */
  .lectures-wrap{display:flex;flex-direction:column;gap:.75rem;margin-bottom:1rem}
  .lecture-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;overflow:hidden}
  .lecture-header{display:flex;align-items:center;gap:.75rem;padding:.75rem 1rem;
    background:var(--surface);cursor:pointer;user-select:none;border-bottom:1px solid var(--border)}
  .lecture-header:hover{background:#1e2530}
  .lecture-num{font-family:var(--mono);font-size:.8rem;color:var(--muted);min-width:1.6rem}
  .lecture-header input[type=text]{flex:1;background:transparent;border:none;color:var(--text);
    font-family:var(--sans);font-size:.9rem;font-weight:500;padding:0;outline:none}
  .lecture-header input[type=text]::placeholder{color:var(--muted)}
  .chevron{font-size:.7rem;color:var(--muted);transition:transform .2s;margin-left:auto;flex-shrink:0}
  .lecture-card.open .chevron{transform:rotate(180deg)}
  .btn-remove{background:none;border:none;color:var(--err);cursor:pointer;font-size:1rem;
    padding:0 .25rem;line-height:1;flex-shrink:0;opacity:.7}
  .btn-remove:hover{opacity:1}
  .lecture-body{padding:1rem;display:none}
  .lecture-card.open .lecture-body{display:block}

  /* drop zone */
  .drop-zone{border:2px dashed var(--border);border-radius:6px;padding:1rem;text-align:center;
    cursor:pointer;position:relative;transition:border-color .2s,background .2s}
  .drop-zone:hover,.drop-zone.dragover{border-color:var(--accent);background:rgba(88,166,255,.05)}
  .drop-zone input[type=file]{position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%}
  .drop-zone .dz-icon{font-size:1.25rem;margin-bottom:.25rem}
  .drop-zone .dz-label{font-size:.8rem;color:var(--muted)}
  .drop-zone .dz-filename{font-family:var(--mono);font-size:.75rem;color:var(--accent2);
    margin-top:.25rem;word-break:break-all}
  .optional-tag{font-size:.68rem;background:rgba(88,166,255,.15);color:var(--accent);
    border-radius:4px;padding:.05rem .35rem;margin-left:.35rem;vertical-align:middle}

  /* resume */
  .resume-section{margin-top:.75rem;border:1px solid var(--border);border-radius:6px;background:var(--bg)}
  .resume-section summary{cursor:pointer;font-size:.82rem;font-weight:600;color:var(--accent);
    padding:.5rem .75rem;user-select:none;outline:none}
  .resume-grid{padding:.75rem;display:grid;grid-template-columns:1fr 1fr;gap:.6rem;
    border-top:1px solid var(--border);margin-top:.15rem}
  @media(max-width:600px){.resume-grid{grid-template-columns:1fr}}
  .resume-grid .field label{font-size:.78rem;color:var(--muted)}
  .resume-grid input[type=file]{font-family:var(--sans);font-size:.75rem;background:var(--surface);
    border:1px solid var(--border);border-radius:4px;color:var(--text);padding:.3rem;width:100%;outline:none}

  /* buttons */
  .btn-add-lecture{width:100%;padding:.65rem;background:transparent;color:var(--accent);
    border:2px dashed var(--accent);border-radius:8px;font-family:var(--sans);font-size:.9rem;
    font-weight:500;cursor:pointer;transition:background .15s;margin-bottom:1rem}
  .btn-add-lecture:hover{background:rgba(88,166,255,.08)}
  .btn-run{width:100%;padding:.85rem;background:var(--accent);color:#000;font-family:var(--sans);
    font-size:1rem;font-weight:600;border:none;border-radius:8px;cursor:pointer;
    transition:opacity .15s,transform .1s}
  .btn-run:hover:not(:disabled){opacity:.88;transform:translateY(-1px)}
  .btn-run:disabled{opacity:.4;cursor:not-allowed}

  /* Progress */
  #progress-panel{display:none}
  .batch-summary{font-size:.85rem;color:var(--muted);margin-bottom:1rem;padding:.6rem .75rem;
    background:var(--surface2);border-radius:6px;border-left:3px solid var(--accent)}
  .lec-progress{border:1px solid var(--border);border-radius:8px;margin-bottom:.75rem;overflow:hidden}
  .lec-progress-header{display:flex;align-items:center;gap:.75rem;padding:.75rem 1rem;
    background:var(--surface);cursor:pointer;user-select:none}
  .lec-progress-header:hover{background:#1e2530}
  .lec-badge{font-family:var(--mono);font-size:.75rem;padding:.15rem .45rem;border-radius:4px;
    background:var(--border);color:var(--muted);flex-shrink:0}
  .lec-badge.running{background:rgba(88,166,255,.2);color:var(--accent)}
  .lec-badge.done{background:rgba(63,185,80,.2);color:var(--accent2)}
  .lec-badge.error{background:rgba(248,81,73,.2);color:var(--err)}
  .lec-progress-title{flex:1;font-size:.9rem;font-weight:500}
  .lec-progress-body{display:none;padding:.75rem 1rem;border-top:1px solid var(--border)}
  .lec-progress.open .lec-progress-body{display:block}
  .step-list{list-style:none}
  .step-item{display:flex;align-items:flex-start;gap:.65rem;padding:.6rem 0;
    border-bottom:1px solid var(--border)}
  .step-item:last-child{border-bottom:none}
  .step-icon{width:1.3rem;height:1.3rem;flex-shrink:0;display:flex;align-items:center;
    justify-content:center;font-size:.95rem;margin-top:.05rem}
  .step-body{flex:1;min-width:0}
  .step-label{font-size:.875rem;font-weight:500}
  .step-log{font-family:var(--mono);font-size:.72rem;color:var(--muted);margin-top:.3rem;
    white-space:pre-wrap;word-break:break-all}
  .step-filename{font-family:var(--mono);font-size:.72rem;color:var(--accent2);margin-top:.15rem}
  .step-item[data-state=waiting] .step-icon::before{content:"○";color:var(--muted)}
  .step-item[data-state=running] .step-icon{animation:spin 1s linear infinite}
  .step-item[data-state=running] .step-icon::before{content:"◌";color:var(--accent)}
  .step-item[data-state=done]    .step-icon::before{content:"✓";color:var(--accent2)}
  .step-item[data-state=error]   .step-icon::before{content:"✗";color:var(--err)}
  .package-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;
    padding:1rem 1.25rem;margin-bottom:.75rem}
  .done-banner{background:rgba(63,185,80,.1);border:1px solid var(--accent2);border-radius:8px;
    padding:1.1rem 1.4rem;display:flex;align-items:center;justify-content:space-between;
    gap:1rem;flex-wrap:wrap}
  .done-banner p{font-size:.875rem;line-height:1.5}
  .done-banner p strong{color:var(--accent2)}
  .btn-download{padding:.6rem 1.2rem;background:var(--accent2);color:#000;font-family:var(--sans);
    font-size:.875rem;font-weight:600;border:none;border-radius:6px;cursor:pointer;
    text-decoration:none;flex-shrink:0}
  .btn-download:hover{opacity:.85}
  .error-banner{background:rgba(248,81,73,.1);border:1px solid var(--err);border-radius:8px;
    padding:1rem 1.25rem;font-family:var(--mono);font-size:0.75rem;white-space:pre-wrap;
    word-break:break-all;color:var(--err);max-height:220px;overflow-y:auto}
  @keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="container">

<header>
  <h1>🏥 <span>Lecture</span> Pipeline <span style="font-size:.9rem;color:var(--muted);font-weight:400">— Batch Edition</span></h1>
  <p>ประมวลผลสไลด์หลาย Lecture ด้วย <strong style="color:var(--accent)">Google AI Studio</strong> — กำหนด output step ได้อิสระต่อ lecture</p>
</header>

<div id="upload-section">

  <div class="card">
    <div class="card-title">🔑 Google AI Studio</div>
    <div class="row-3">
      <div class="field" style="grid-column:1/3">
        <label>Google AI API Key</label>
        <div class="hint">รับ key ที่ <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--accent)">aistudio.google.com/app/apikey</a></div>
        <input type="password" id="api_key" placeholder="AIzaSy..." autocomplete="off">
      </div>
      <div class="field">
        <label>⏱️ Cooldown (วินาที)</label>
        <div class="hint">หน่วงเวลาระหว่าง Lecture</div>
        <input type="number" id="cooldown" value="10" min="0" max="120">
      </div>
    </div>
    <div class="field">
      <label>Gemini Model</label>
      <select id="model"></select>
    </div>
  </div>

  <div class="card">
    <div class="card-title">📚 Lectures <span id="lec-count-badge" style="color:var(--accent);font-size:.85rem;text-transform:none;letter-spacing:0">(1 lecture)</span></div>
    <div class="lectures-wrap" id="lectures-wrap"></div>
    <button class="btn-add-lecture" onclick="addLecture()">＋ เพิ่ม Lecture</button>
  </div>

  <button class="btn-run" id="btn-run" onclick="startBatch()">▶ Run Pipeline</button>
</div>

<!-- Progress Panel -->
<div id="progress-panel">
  <div class="batch-summary" id="batch-summary">กำลังเตรียมระบบ...</div>
  <div id="lectures-progress"></div>
  <div class="package-card" id="package-card" style="display:none">
    <div style="font-size:.78rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:.75rem">📁 Package</div>
    <ul class="step-list" id="package-step-list"></ul>
  </div>
  <div id="result-area"></div>
</div>

</div>

<script>
// ── Model list (populated from /api/models) ───────────────────
async function loadModels() {
  const sel = document.getElementById('model');
  try {
    const res  = await fetch('/api/models');
    const data = await res.json();
    sel.innerHTML = '';
    for (const m of data.models) {
      const opt = document.createElement('option');
      opt.value = m.id;
      opt.textContent = m.label;
      sel.appendChild(opt);
    }
  } catch(e) {
    console.error('loadModels:', e);
  }
}

// ── Step definitions ─────────────────────────────────────────
const STEP_DEFS = [
  { id:'slide_md',    label:'1. PDF → Markdown', cls:'',               defaultOn:true  },
  { id:'transcript',  label:'2. Transcript',     cls:'',               defaultOn:true  },
  { id:'enrich',      label:'3. Slide Enrich',   cls:'',               defaultOn:true  },
  { id:'crystal',     label:'4. Crystallizer',   cls:'step-crystal',   defaultOn:false },
  { id:'curriculum',  label:'5. Curriculum Map', cls:'step-curriculum',defaultOn:false },
];

function buildStepsSelector(idx) {
  const div = document.createElement('div');
  div.className = 'steps-selector';
  div.innerHTML = '<label class="group-label">📤 Output steps ที่ต้องการ</label><div class="steps-grid" id="steps-grid-'+idx+'"></div>';
  const grid = div.querySelector('.steps-grid');
  for (const s of STEP_DEFS) {
    const lbl = document.createElement('label');
    lbl.className = 'step-toggle' + (s.cls ? ' '+s.cls : '') + (s.defaultOn ? ' checked' : '');
    lbl.dataset.step = s.id;
    lbl.dataset.lec  = idx;
    lbl.innerHTML = `<input type="checkbox" ${s.defaultOn?'checked':''} onchange="toggleStep(this)">${s.label}`;
    grid.appendChild(lbl);
  }
  return div;
}

function toggleStep(inp) {
  const lbl = inp.closest('.step-toggle');
  if (inp.checked) lbl.classList.add('checked');
  else             lbl.classList.remove('checked');
}

// ── Lecture cards ─────────────────────────────────────────────
let lectureCount = 0;

function addLecture(defaults = {}) {
  const idx  = lectureCount++;
  const wrap = document.getElementById('lectures-wrap');
  const div  = document.createElement('div');
  div.className = 'lecture-card open';
  div.dataset.idx = idx;
  div.innerHTML = `
    <div class="lecture-header" onclick="toggleLectureCard(${idx})">
      <span class="lecture-num">#${idx+1}</span>
      <input type="text" data-field="label_${idx}" placeholder="ชื่อ Lecture ${idx+1}"
             value="${defaults.label||''}" onclick="event.stopPropagation()" oninput="updateRunLabel()">
      <span class="chevron">▼</span>
      <button class="btn-remove" onclick="removeLecture(${idx},event)" title="ลบ">✕</button>
    </div>
    <div class="lecture-body">
      <div class="field">
        <label>📄 PDF Slide <span style="color:var(--err)">*</span></label>
        <div class="hint">ชื่อโฟลเดอร์ output จะใช้ชื่อไฟล์ PDF นี้</div>
        <div class="drop-zone" id="dz-slide-${idx}">
          <input type="file" data-field="slide_${idx}" accept=".pdf"
                 onchange="setDzFilename('dz-slide-${idx}',this)">
          <div class="dz-icon">📑</div>
          <div class="dz-label">คลิกหรือลากไฟล์ PDF มาวาง</div>
          <div class="dz-filename" id="fn-slide-${idx}"></div>
        </div>
      </div>
      <div class="row-2">
        <div class="field">
          <label>🎙️ Transcript <span class="optional-tag">optional</span></label>
          <div class="drop-zone" id="dz-trans-${idx}" style="margin-bottom:.5rem">
            <input type="file" data-field="transcript_${idx}" accept=".txt"
                   onchange="setDzFilename('dz-trans-${idx}',this)">
            <div class="dz-icon">🎤</div>
            <div class="dz-label">transcript.txt</div>
            <div class="dz-filename" id="fn-trans-${idx}"></div>
          </div>
          <textarea data-field="transcript_text_${idx}" placeholder="หรือวางข้อความ transcript..." rows="3"></textarea>
        </div>
        <div class="field">
          <label>📚 Curriculum Map <span class="optional-tag">optional</span></label>
          <div class="drop-zone" id="dz-curr-${idx}">
            <input type="file" data-field="curriculum_map_${idx}" accept=".md,.txt"
                   onchange="setDzFilename('dz-curr-${idx}',this)">
            <div class="dz-icon">🗂️</div>
            <div class="dz-label">Curriculum_Map.md</div>
            <div class="dz-filename" id="fn-curr-${idx}"></div>
          </div>
        </div>
      </div>
      <details class="resume-section">
        <summary>🔄 Resume จากขั้นตอนกลาง (ชื่อ output folder จะใช้ชื่อไฟล์ที่อัปโหลด)</summary>
        <div class="resume-grid">
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

  // Insert step selector after drop zones
  const body = div.querySelector('.lecture-body');
  body.appendChild(buildStepsSelector(idx));

  wrap.appendChild(div);
  setupDropZones(div);
  renumberCards();
  updateRunLabel();
}

function removeLecture(idx, e) {
  e.stopPropagation();
  const wrap = document.getElementById('lectures-wrap');
  if (wrap.querySelectorAll('.lecture-card').length <= 1) {
    alert('ต้องมีอย่างน้อย 1 Lecture'); return;
  }
  wrap.querySelector(`.lecture-card[data-idx="${idx}"]`)?.remove();
  renumberCards(); updateRunLabel();
}

function renumberCards() {
  document.querySelectorAll('#lectures-wrap .lecture-card').forEach((c, i) => {
    c.querySelector('.lecture-num').textContent = `#${i+1}`;
    const lbl = c.querySelector('input[type=text]');
    if (lbl && !lbl.value) lbl.placeholder = `ชื่อ Lecture ${i+1}`;
  });
  const n = document.querySelectorAll('#lectures-wrap .lecture-card').length;
  document.getElementById('lec-count-badge').textContent = `(${n} lecture${n>1?'s':''})`;
}

function toggleLectureCard(idx) {
  document.querySelector(`.lecture-card[data-idx="${idx}"]`)?.classList.toggle('open');
}

function updateRunLabel() {
  const n = document.querySelectorAll('#lectures-wrap .lecture-card').length;
  document.getElementById('btn-run').textContent =
    n === 1 ? '▶ Run Pipeline' : `▶ Run All ${n} Lectures`;
}

function setDzFilename(dzId, inp) {
  const fn = document.querySelector(`#${dzId} .dz-filename`);
  if (fn) fn.textContent = inp.files[0] ? inp.files[0].name : '';
}

function setupDropZones(root) {
  root.querySelectorAll('.drop-zone').forEach(dz => {
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
    dz.addEventListener('drop', e => {
      e.preventDefault(); dz.classList.remove('dragover');
      const inp = dz.querySelector('input[type=file]');
      if (e.dataTransfer.files.length && inp) {
        inp.files = e.dataTransfer.files;
        inp.dispatchEvent(new Event('change'));
      }
    });
  });
}

function buildFormData() {
  const fd = new FormData();
  fd.append('api_key',  document.getElementById('api_key').value.trim());
  fd.append('model',    document.getElementById('model').value);
  fd.append('cooldown', document.getElementById('cooldown').value);

  const cards = document.querySelectorAll('#lectures-wrap .lecture-card');
  fd.append('lecture_count', cards.length);

  cards.forEach((card, i) => {
    const labelEl = card.querySelector('input[type=text]');
    fd.append(`label_${i}`, labelEl ? labelEl.value.trim() || `Lecture ${i+1}` : `Lecture ${i+1}`);

    // Collect checked steps
    card.querySelectorAll('.step-toggle input:checked').forEach(inp => {
      const lbl = inp.closest('.step-toggle');
      if (lbl) fd.append(`steps_${i}`, lbl.dataset.step);
    });

    // File inputs — remap index to sequential i
    card.querySelectorAll('input[type=file]').forEach(inp => {
      if (inp.dataset.field && inp.files[0]) {
        const remapped = inp.dataset.field.replace(/_\d+$/, `_${i}`);
        fd.append(remapped, inp.files[0]);
      }
    });

    const ta = card.querySelector('textarea');
    if (ta && ta.value.trim()) fd.append(`transcript_text_${i}`, ta.value.trim());
  });
  return fd;
}

// ── Progress ─────────────────────────────────────────────────
let sessionId = null, es = null;
let lectureStates = [];

function buildProgressPanel(labels) {
  lectureStates = labels.map(() => 'waiting');
  const wrap = document.getElementById('lectures-progress');
  wrap.innerHTML = '';
  labels.forEach((lbl, i) => {
    const div = document.createElement('div');
    div.className = 'lec-progress';
    div.id = `lec-prog-${i}`;
    div.innerHTML = `
      <div class="lec-progress-header" onclick="this.parentElement.classList.toggle('open')">
        <span class="lec-badge" id="lec-badge-${i}">⏳ รอ</span>
        <span class="lec-progress-title">${escHtml(lbl)}</span>
        <span class="chevron" style="font-size:.7rem;color:var(--muted)">▼</span>
      </div>
      <div class="lec-progress-body"><ul class="step-list" id="step-list-${i}"></ul></div>`;
    wrap.appendChild(div);
  });
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function setLecState(i, state) {
  const badge = document.getElementById(`lec-badge-${i}`);
  const card  = document.getElementById(`lec-prog-${i}`);
  if (!badge) return;
  const map = {
    waiting:['⏳ รอ',''], running:['⚡ กำลังรัน','running'],
    done:['✓ เสร็จ','done'], error:['✗ ผิดพลาด','error'],
  };
  const [text, cls] = map[state] || map.waiting;
  badge.textContent = text;
  badge.className = `lec-badge${cls ? ' '+cls : ''}`;
  if (state === 'running') card.classList.add('open');
}

function ensureStep(li, stepId, label) {
  const list = document.getElementById(`step-list-${li}`);
  if (!list || list.querySelector(`[data-step-id="${stepId}"]`)) return;
  const el = document.createElement('li');
  el.className = 'step-item'; el.dataset.state = 'waiting'; el.dataset.stepId = stepId;
  el.innerHTML = `<div class="step-icon"></div>
    <div class="step-body">
      <div class="step-label">${label}</div>
      <div class="step-log" id="log-${li}-${stepId}"></div>
      <div class="step-filename" id="sfn-${li}-${stepId}"></div>
    </div>`;
  list.appendChild(el);
}

function setStepState(li, stepId, state) {
  const listId = li === -1 ? 'package-step-list' : `step-list-${li}`;
  document.querySelector(`#${listId} [data-step-id="${stepId}"]`)?.setAttribute('data-state', state);
}

function appendStepLog(li, stepId, msg) {
  const el = document.getElementById(`log-${li}-${stepId}`);
  if (el) el.textContent += (el.textContent ? '\n' : '') + msg;
}

function setStepFilename(li, stepId, fn) {
  const el = document.getElementById(`sfn-${li}-${stepId}`);
  if (el && fn) el.textContent = '→ ' + fn;
}

function ensurePackageStep(stepId, label) {
  document.getElementById('package-card').style.display = '';
  const list = document.getElementById('package-step-list');
  if (list.querySelector(`[data-step-id="${stepId}"]`)) return;
  const el = document.createElement('li');
  el.className = 'step-item'; el.dataset.state = 'waiting'; el.dataset.stepId = stepId;
  el.innerHTML = `<div class="step-icon"></div>
    <div class="step-body">
      <div class="step-label">${label}</div>
      <div class="step-log" id="log-pkg-${stepId}"></div>
      <div class="step-filename" id="sfn-pkg-${stepId}"></div>
    </div>`;
  list.appendChild(el);
}

function handleEvent(d) {
  const isPkg = d.lecture === -1 || d.lecture === undefined;

  if (d.event === 'batch_start') {
    document.getElementById('batch-summary').textContent =
      `กำลังประมวลผล ${d.total} lecture${d.total>1?'s':''}...`;
    return;
  }
  if (d.event === 'lecture_start') {
    setLecState(d.lecture, 'running');
    document.getElementById('batch-summary').textContent =
      `Lecture ${d.lecture+1}/${d.total}: ${d.label}`;
    return;
  }
  if (d.event === 'lecture_done')  { setLecState(d.lecture, 'done'); return; }
  if (d.event === 'lecture_error') {
    setLecState(d.lecture, 'error');
    const list = document.getElementById(`step-list-${d.lecture}`);
    if (list) {
      const li = document.createElement('li');
      li.className = 'step-item'; li.dataset.state = 'error';
      li.innerHTML = `<div class="step-icon"></div>
        <div class="step-body">
          <div class="step-label" style="color:var(--err);font-weight:600">เกิดข้อผิดพลาด</div>
          <div class="step-log" style="color:var(--err);background:rgba(248,81,73,.05);padding:.5rem;border:1px solid rgba(248,81,73,.2);border-radius:4px;margin-top:.4rem">${escHtml(d.error)}</div>
        </div>`;
      list.appendChild(li);
    }
    return;
  }
  if (d.event === 'step_start') {
    if (isPkg) { ensurePackageStep(d.step, d.label); setStepState(-1, d.step, 'running'); }
    else { ensureStep(d.lecture, d.step, d.label || d.step); setStepState(d.lecture, d.step, 'running'); }
    return;
  }
  if (d.event === 'step_log') {
    if (isPkg) {
      const el = document.getElementById(`log-pkg-${d.step}`);
      if (el) el.textContent += (el.textContent ? '\n' : '') + d.msg;
    } else {
      appendStepLog(d.lecture, d.step, d.msg);
    }
    return;
  }
  if (d.event === 'step_done') {
    if (isPkg) {
      setStepState(-1, d.step, 'done');
      const el = document.getElementById(`sfn-pkg-${d.step}`);
      if (el && d.filename) el.textContent = '→ ' + d.filename;
    } else {
      setStepState(d.lecture, d.step, 'done');
      setStepFilename(d.lecture, d.step, d.filename);
    }
    return;
  }
  if (d.event === 'step_error') {
    if (!isPkg) {
      setStepState(d.lecture, d.step, 'error');
      appendStepLog(d.lecture, d.step, '‼️ ' + d.error);
    }
    return;
  }
  if (d.event === 'done')       { showDone(d.session, d.folder, d.zip, d.total); if(es) es.close(); return; }
  if (d.event === 'fatal_error'){ showFatalError(d.msg+(d.detail?'\n\n'+d.detail:'')); if(es) es.close(); return; }
  if (d.event === 'stream_end') { if(es) es.close(); }
}

function showDone(sid, folder, zip, total) {
  document.getElementById('batch-summary').textContent =
    `✅ เสร็จสมบูรณ์ ${total} lecture${total>1?'s':''}`;
  document.getElementById('result-area').innerHTML = `
    <div class="done-banner">
      <p>✅ Batch สำเร็จ!<br><strong>${escHtml(folder)}</strong> — ${total} lecture${total>1?'s':''}</p>
      <a class="btn-download" href="/download/${sid}">⬇ ดาวน์โหลด ZIP</a>
    </div>`;
}

function showFatalError(msg) {
  document.getElementById('result-area').innerHTML =
    `<div class="error-banner">❌ Fatal Error:\n${escHtml(msg)}</div>`;
  document.getElementById('btn-run').disabled = false;
}

async function startBatch() {
  const apiKey = document.getElementById('api_key').value.trim();
  if (!apiKey) { alert('กรุณาใส่ API Key'); return; }

  const cards = document.querySelectorAll('#lectures-wrap .lecture-card');
  const labels = Array.from(cards).map((c, i) => {
    const inp = c.querySelector('input[type=text]');
    return inp ? inp.value.trim() || `Lecture ${i+1}` : `Lecture ${i+1}`;
  });

  document.getElementById('btn-run').disabled = true;
  document.getElementById('upload-section').style.display = 'none';
  document.getElementById('progress-panel').style.display = 'block';
  buildProgressPanel(labels);

  try {
    const res  = await fetch('/run', { method:'POST', body:buildFormData() });
    const data = await res.json();
    if (!res.ok) { showFatalError(data.error || 'Unknown error'); return; }
    sessionId = data.session_id;
    es = new EventSource(`/progress/${sessionId}`);
    es.onmessage = e => handleEvent(JSON.parse(e.data));
    es.onerror = () => {};
  } catch(e) { showFatalError(e.message); }
}

// ── Init ─────────────────────────────────────────────────────
loadModels();
addLecture();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("=" * 58)
    print("  Lecture Pipeline (Google AI Studio) — http://localhost:5000")
    print("=" * 58)
    print(f"  Prompts dir : {PROMPTS_DIR}")
    print(f"  Output dir  : {OUTPUT_BASE}")
    print()

    expected = [
        "slide-to-markdown-gemini.md",
        "lecture-synthesizer.md",
        "slide-enrich.md",
        "lecture-crystallizer.md",
        "curriculum-tracker.md",
    ]
    missing = [f for f in expected if not (PROMPTS_DIR / f).exists()]
    if missing:
        print("⚠️  Missing prompt files in prompts/:")
        for f in missing:
            print(f"     prompts/{f}")
        print()

    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)