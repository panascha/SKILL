#!/usr/bin/env python3
"""
Lecture Pipeline Automation
============================
Automates the full medical lecture note processing workflow using
the Google Gemini API directly. No browser automation needed.

Workflow:
  1. PDF Slide  → lecture-markdown.md   (slide-to-markdown)
  2. [optional] transcript.txt + notes  → lecture-transcribe.md (lecture-synthesizer)
  3+4. Enrich → lecture-enrich.md, then Crystallize → lecture-summary.md  (same chat session)
  5. [optional] + Curriculum_Map.md     → Curriculum_Map_updated.md
  6. Package everything into a timestamped folder + zip

Usage:
  pip uninstall google-generativeai -y
  pip install google-genai flask
  python app.py
  Open http://localhost:5000
"""

import os, json, time, queue, threading, zipfile, uuid, shutil
from datetime import datetime
from pathlib import Path
import tempfile
import traceback

from flask import Flask, request, jsonify, Response, send_file

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB max upload

# ─────────────────────────────────────────────────────────────
# Prompt files (read from ./prompts/ directory next to app.py)
# ─────────────────────────────────────────────────────────────
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
# Session store  {session_id: {queue, output_dir, zip_path}}
# ─────────────────────────────────────────────────────────────
sessions: dict[str, dict] = {}

OUTPUT_BASE = Path(__file__).parent / "output"
OUTPUT_BASE.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────
def run_pipeline(
    session_id: str,
    api_key: str,
    model_name: str,
    slide_path: str | None,
    slide_name: str | None,
    transcript_path: str | None,
    curriculum_map_path: str | None,
    uploaded_markdown_path: str | None = None,
    uploaded_transcribe_path: str | None = None,
    uploaded_enrich_path: str | None = None,
    uploaded_summary_path: str | None = None,
):
    # นำเข้า SDK ชุดใหม่
    from google import genai
    from google.genai import types

    q: queue.Queue = sessions[session_id]["queue"]
    output_dir: Path = sessions[session_id]["output_dir"]

    def emit(event: str, **data):
        q.put(json.dumps({"event": event, **data}))

    def step_start(step_id: str, label: str):
        emit("step_start", step=step_id, label=label)

    def step_log(step_id: str, msg: str):
        emit("step_log", step=step_id, msg=msg)

    def step_done(step_id: str, filename: str = ""):
        emit("step_done", step=step_id, filename=filename)

    def step_error(step_id: str, error: str):
        emit("step_error", step=step_id, error=error)

    try:
        # กำหนดรูปแบบ Client ตัวใหม่ของ google-genai
        client = genai.Client(api_key=api_key)

        # ปรับจำนวน Token ขาออกอย่างยืดหยุ่นตามความสามารถสูงสุดของแต่ละโมเดล
        if "pro" in model_name.lower() or "3.5" in model_name:
            max_out = 65536  # โมเดล Pro และโมเดลรุ่น 3.5 รองรับเอาท์พุตขนาดใหญ่พิเศษ
        else:
            max_out = 8192   # ป้องกัน API Error บนโมเดลรุ่นทั่วไป/รุ่นเก่า

        generation_cfg = types.GenerateContentConfig(
            max_output_tokens=max_out,
            temperature=0.3,
        )

        # โหลดไฟล์ขั้นตอนกลางที่อัปโหลดมาเก็บลง Output Directory ล่วงหน้า
        lecture_markdown = None
        if uploaded_markdown_path:
            lecture_markdown = Path(uploaded_markdown_path).read_text(encoding="utf-8")
            (output_dir / "lecture-markdown.md").write_text(lecture_markdown, encoding="utf-8")

        lecture_transcribe = None
        if uploaded_transcribe_path:
            lecture_transcribe = Path(uploaded_transcribe_path).read_text(encoding="utf-8")
            (output_dir / "lecture-transcribe.md").write_text(lecture_transcribe, encoding="utf-8")

        lecture_enrich = None
        if uploaded_enrich_path:
            lecture_enrich = Path(uploaded_enrich_path).read_text(encoding="utf-8")
            (output_dir / "lecture-enrich.md").write_text(lecture_enrich, encoding="utf-8")

        lecture_summary = None
        if uploaded_summary_path:
            lecture_summary = Path(uploaded_summary_path).read_text(encoding="utf-8")
            (output_dir / "lecture-summary.md").write_text(lecture_summary, encoding="utf-8")

        # ── STEP 1: Slide PDF → Markdown ─────────────────────────────
        if lecture_markdown:
            step_start("slide_md", "📄 แปลง PDF สไลด์ → Markdown")
            step_log("slide_md", "ใช้ไฟล์ lecture-markdown.md จากรอบก่อนหน้านี้ (ข้ามการประมวลผล PDF)")
            step_done("slide_md", "lecture-markdown.md")
        elif slide_path:
            step_start("slide_md", "📄 แปลง PDF สไลด์ → Markdown")
            step_log("slide_md", f"กำลังอัพโหลดไฟล์ '{slide_name}' ไปยัง Gemini File API...")

            # อัพโหลดไฟล์ผ่านระบบ Files API ตัวใหม่
            uploaded_slide = client.files.upload(
                file=slide_path,
                config=types.UploadFileConfig(display_name=slide_name)
            )

            step_log("slide_md", "รอ Gemini ประมวลผลไฟล์...")
            wait = 0

            # ฟังก์ชันเช็คสถานะการแปลงไฟล์แบบปลอดภัย
            def get_state_str(file_obj):
                if not file_obj.state:
                    return "ACTIVE"
                return file_obj.state.name if hasattr(file_obj.state, "name") else str(file_obj.state)

            state_str = get_state_str(uploaded_slide)
            while state_str == "PROCESSING":
                time.sleep(3)
                wait += 3
                uploaded_slide = client.files.get(name=uploaded_slide.name)
                state_str = get_state_str(uploaded_slide)
                step_log("slide_md", f"  ประมวลผล... ({wait}s)")

            if state_str == "FAILED":
                raise RuntimeError("Gemini File API ไม่สามารถประมวลผลไฟล์ PDF ได้")

            prompt_slide_md = load_prompt("slide-to-markdown-gemini.md")
            step_log("slide_md", "กำลัง generate Markdown (อาจใช้เวลา 1–5 นาที)...")

            # เรียกใช้ generate_content ผ่าน client.models
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    uploaded_slide,
                    prompt_slide_md
                    + "\n\n---\nโปรดแปลง PDF สไลด์ที่อัพโหลดมาเป็น Markdown ตาม format และ rules ที่กำหนดไว้ข้างต้นทั้งหมด",
                ],
                config=generation_cfg,
            )

            lecture_markdown = response.text
            (output_dir / "lecture-markdown.md").write_text(lecture_markdown, encoding="utf-8")
            step_log("slide_md", f"✓ บันทึก lecture-markdown.md ({len(lecture_markdown):,} ตัวอักษร)")
            step_done("slide_md", "lecture-markdown.md")
        else:
            step_start("slide_md", "📄 แปลง PDF สไลด์ → Markdown")
            step_log("slide_md", "ข้ามการแปลงสไลด์ (เนื่องจากไม่มีไฟล์สไลด์ PDF หรือไฟล์ Markdown เริ่มต้น)")
            step_done("slide_md", "ข้ามขั้นตอน")

        # ── STEP 2: Transcript Synthesizer (optional) ────────────────
        if transcript_path or lecture_transcribe:
            step_start("transcript", "🎙️ สังเคราะห์ Transcript + Slide Notes")
            if lecture_transcribe:
                step_log("transcript", "ใช้ไฟล์ lecture-transcribe.md จากรอบก่อนหน้านี้ (ข้ามการสังเคราะห์)")
                step_done("transcript", "lecture-transcribe.md")
            else:
                step_log("transcript", "กำลังอ่านไฟล์ transcript...")

                transcript_text = Path(transcript_path).read_text(encoding="utf-8")
                prompt_synth = load_prompt("lecture-synthesizer.md")

                ref_markdown = lecture_markdown if lecture_markdown else ""

                step_log("transcript", "กำลัง generate notes-synthesized (อาจใช้เวลา 2–5 นาที)...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        f"## notes-raw.md (เนื้อหาจากสไลด์)\n\n{ref_markdown}",
                        f"## transcript.txt (คำบรรยายของอาจารย์)\n\n{transcript_text}",
                        prompt_synth
                        + "\n\n---\nโปรดสังเคราะห์ notes-synthesized.md จากไฟล์ทั้งสองข้างต้นตาม format ที่กำหนด",
                    ],
                    config=generation_cfg,
                )

                lecture_transcribe = response.text
                (output_dir / "lecture-transcribe.md").write_text(
                    lecture_transcribe, encoding="utf-8"
                )
                step_log(
                    "transcript",
                    f"✓ บันทึก lecture-transcribe.md ({len(lecture_transcribe):,} ตัวอักษร)",
                )
                step_done("transcript", "lecture-transcribe.md")

        # ── STEP 3: Slide Enrich (new chat session, multi-turn) ───────
        step_start("enrich", "🔬 เพิ่มกลไกทางการแพทย์ — Slide Enrich")
        if lecture_enrich:
            step_log("enrich", "ใช้ไฟล์ lecture-enrich.md จากรอบก่อนหน้านี้ (ข้ามขั้นตอน Enrich)")
            step_done("enrich", "lecture-enrich.md")
        else:
            step_log("enrich", "เตรียม context สำหรับ multi-turn session...")

            prompt_enrich = load_prompt("slide-enrich.md")

            # Build first message parts
            first_msg_parts = []
            if lecture_markdown:
                first_msg_parts.append(f"## lecture-markdown.md (notes-raw)\n\n{lecture_markdown}")
            if lecture_transcribe:
                first_msg_parts.append(f"## lecture-transcribe.md (notes-synthesized)\n\n{lecture_transcribe}")

            first_msg_parts.append(
                prompt_enrich
                + "\n\n---\nโปรดดำเนินการ enrich notes ตาม slide-enrich format ที่กำหนด โดยใช้ไฟล์ที่ให้มาข้างต้นเป็น input"
            )

            step_log("enrich", "กำลัง generate lecture-enrich.md (อาจใช้เวลา 3–8 นาที)...")
            
            # เริ่มต้นแชทและส่งข้อความผ่าน Client Chats API ตัวใหม่
            chat = client.chats.create(model=model_name, config=generation_cfg)
            response_enrich = chat.send_message(message=first_msg_parts)

            lecture_enrich = response_enrich.text
            (output_dir / "lecture-enrich.md").write_text(lecture_enrich, encoding="utf-8")
            step_log(
                "enrich",
                f"✓ บันทึก lecture-enrich.md ({len(lecture_enrich):,} ตัวอักษร)",
            )
            step_done("enrich", "lecture-enrich.md")

        # ── STEP 4: Crystallizer (SAME chat — sees enrich output) ─────
        step_start("crystal", "💎 ตกผลึกเนื้อหา — Lecture Crystallizer")
        if lecture_summary:
            step_log("crystal", "ใช้ไฟล์ lecture-summary.md จากรอบก่อนหน้านี้ (ข้ามขั้นตอน Crystallize)")
            step_done("crystal", "lecture-summary.md")
        else:
            prompt_crystal = load_prompt("lecture-crystallizer.md")
            # ถ้ามี active chat session เดิม ให้ส่งเมสเสจต่อ
            if 'chat' in locals() and chat is not None:
                step_log(
                    "crystal",
                    "กำลัง generate lecture-summary.md (ต่อจาก session เดิม)...",
                )
                response_crystal = chat.send_message(
                    message=prompt_crystal
                    + "\n\n---\nโปรดตกผลึกเนื้อหาจาก enriched notes ที่ได้ข้างต้น ตาม lecture-crystallizer format ทั้งหมด"
                )
                lecture_summary = response_crystal.text
            else:
                # ถ้าไม่มี ให้ตั้งต้น session ใหม่โดยใช้ lecture_enrich เป็น context (สำหรับกรณี Resume ขั้นตอนนี้)
                step_log(
                    "crystal",
                    "กำลัง generate lecture-summary.md (สร้าง session ใหม่จาก lecture-enrich.md)...",
                )
                if not lecture_enrich:
                    raise RuntimeError("ไม่พบเนื้อหาของ lecture-enrich.md สำหรับวิเคราะห์ในขั้นตอนนี้")
                
                response_crystal = client.models.generate_content(
                    model=model_name,
                    contents=[
                        f"## lecture-enrich.md (enriched notes)\n\n{lecture_enrich}",
                        prompt_crystal + "\n\n---\nโปรดตกผลึกเนื้อหาจาก enriched notes ที่ได้ข้างต้น ตาม lecture-crystallizer format ทั้งหมด"
                    ],
                    config=generation_cfg
                )
                lecture_summary = response_crystal.text

            (output_dir / "lecture-summary.md").write_text(
                lecture_summary, encoding="utf-8"
            )
            step_log(
                "crystal",
                f"✓ บันทึก lecture-summary.md ({len(lecture_summary):,} ตัวอักษร)",
            )
            step_done("crystal", "lecture-summary.md")

        # ── STEP 5: Curriculum Map (optional) ────────────────────────
        if curriculum_map_path:
            step_start("curriculum", "📚 อัปเดต Curriculum Map")
            step_log("curriculum", "กำลังอ่าน Curriculum_Map.md...")

            curriculum_map_text = Path(curriculum_map_path).read_text(encoding="utf-8")
            prompt_curriculum = load_prompt("curriculum-tracker.md")

            ref_enrich = lecture_enrich if lecture_enrich else ""

            step_log("curriculum", "กำลัง generate Curriculum_Map_updated.md...")
            response_curr = client.models.generate_content(
                model=model_name,
                contents=[
                    f"## notes-synthesized.md (ใช้ lecture-enrich.md เป็น input)\n\n{ref_enrich}",
                    f"## Curriculum_Map.md (ดัชนีความรู้สะสม)\n\n{curriculum_map_text}",
                    prompt_curriculum
                    + "\n\n---\nโปรดวิเคราะห์และอัปเดต Curriculum Map ตาม format ที่กำหนด",
                ],
                config=generation_cfg,
            )

            curriculum_updated: str = response_curr.text
            (output_dir / "Curriculum_Map_updated.md").write_text(
                curriculum_updated, encoding="utf-8"
            )
            step_log(
                "curriculum",
                f"✓ บันทึก Curriculum_Map_updated.md ({len(curriculum_updated):,} ตัวอักษร)",
            )
            step_done("curriculum", "Curriculum_Map_updated.md")

        # ── STEP 6: Package ───────────────────────────────────────────
        step_start("package", "📁 สร้างโฟลเดอร์และบีบอัดไฟล์")
        step_log("package", f"กำลังบีบอัดไฟล์ทั้งหมดใน {output_dir.name}/...")

        zip_path = OUTPUT_BASE / f"{output_dir.name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(output_dir.iterdir()):
                zf.write(f, f.name)
                step_log("package", f"  + {f.name}")

        sessions[session_id]["zip_path"] = str(zip_path)
        file_count = len(list(output_dir.iterdir()))
        step_log("package", f"✓ สร้าง {zip_path.name} ({file_count} ไฟล์)")
        step_done("package", zip_path.name)

        emit("done", folder=output_dir.name, zip=zip_path.name, session=session_id)

    except Exception as e:
        tb = traceback.format_exc()
        step_error("pipeline", f"{type(e).__name__}: {e}\n\n{tb}")
        emit("fatal_error", msg=str(e))
    finally:
        q.put(None)  # signal SSE stream end


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return HTML_PAGE


@app.route("/run", methods=["POST"])
def run_route():
    api_key = request.form.get("api_key", "").strip()
    model_name = request.form.get("model", "gemini-3.5-flash").strip()

    if not api_key:
        return jsonify(error="กรุณาใส่ Google AI API Key"), 400

    slide_file = request.files.get("slide")
    transcript_file = request.files.get("transcript")
    transcript_text = request.form.get("transcript_text", "").strip()
    curriculum_file = request.files.get("curriculum_map")

    # ตรวจเช็คการอัปโหลดไฟล์ในขั้นตอน intermediate ของเดิม
    uploaded_markdown = request.files.get("uploaded_markdown")
    uploaded_transcribe = request.files.get("uploaded_transcribe")
    uploaded_enrich = request.files.get("uploaded_enrich")
    uploaded_summary = request.files.get("uploaded_summary")

    has_slide = slide_file and slide_file.filename != ""
    has_md = uploaded_markdown and uploaded_markdown.filename != ""
    has_trans = uploaded_transcribe and uploaded_transcribe.filename != ""
    has_enrich = uploaded_enrich and uploaded_enrich.filename != ""
    has_summary = uploaded_summary and uploaded_summary.filename != ""

    # ดำเนินการต่อได้ถ้าระบบตรวจพบไฟล์สไลด์ หรือไฟล์ในขั้นตอนกลางขั้นตอนใดขั้นตอนหนึ่ง
    if not (has_slide or has_md or has_trans or has_enrich or has_summary):
        return jsonify(error="กรุณาอัปโหลดไฟล์ PDF สไลด์ หรืออัปโหลดไฟล์เนื้อหาขั้นตอนกลางอย่างน้อย 1 ไฟล์เพื่อเริ่มดำเนินการ"), 400

    # Create temp dir for uploaded files
    tmp_dir = Path(tempfile.mkdtemp())

    # Save slide
    slide_path = None
    if has_slide:
        slide_path = str(tmp_dir / slide_file.filename)
        slide_file.save(slide_path)

    # Save transcript (optional) - รองรับทั้งแบบไฟล์ และแบบแปะข้อความ
    transcript_path = None
    if transcript_file and transcript_file.filename:
        transcript_path = str(tmp_dir / transcript_file.filename)
        transcript_file.save(transcript_path)
    elif transcript_text:
        transcript_path = str(tmp_dir / "transcript.txt")
        Path(transcript_path).write_text(transcript_text, encoding="utf-8")

    # Save curriculum map (optional)
    curriculum_map_path = None
    if curriculum_file and curriculum_file.filename:
        curriculum_map_path = str(tmp_dir / curriculum_file.filename)
        curriculum_file.save(curriculum_map_path)

    # Save uploaded intermediate files
    uploaded_markdown_path = None
    if has_md:
        uploaded_markdown_path = str(tmp_dir / "lecture-markdown.md")
        uploaded_markdown.save(uploaded_markdown_path)

    uploaded_transcribe_path = None
    if has_trans:
        uploaded_transcribe_path = str(tmp_dir / "lecture-transcribe.md")
        uploaded_transcribe.save(uploaded_transcribe_path)

    uploaded_enrich_path = None
    if has_enrich:
        uploaded_enrich_path = str(tmp_dir / "lecture-enrich.md")
        uploaded_enrich.save(uploaded_enrich_path)

    uploaded_summary_path = None
    if has_summary:
        uploaded_summary_path = str(tmp_dir / "lecture-summary.md")
        uploaded_summary.save(uploaded_summary_path)

    # Create session + output directory
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ตั้งชื่อโฟลเดอร์ตามบริบทไฟล์ที่มีอยู่
    if has_slide:
        lecture_name = Path(slide_file.filename).stem[:40]
    elif has_md:
        lecture_name = "resumed_markdown"
    elif has_trans:
        lecture_name = "resumed_transcribe"
    elif has_enrich:
        lecture_name = "resumed_enrich"
    else:
        lecture_name = "resumed_summary"

    folder_name = f"{lecture_name}_{timestamp}"
    output_dir = OUTPUT_BASE / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    sessions[session_id] = {
        "queue": queue.Queue(),
        "output_dir": output_dir,
        "zip_path": None,
        "tmp_dir": str(tmp_dir),
    }

    # Launch pipeline in background thread
    t = threading.Thread(
        target=run_pipeline,
        args=(
            session_id,
            api_key,
            model_name,
            slide_path,
            slide_file.filename if has_slide else None,
            transcript_path,
            curriculum_map_path,
            uploaded_markdown_path,
            uploaded_transcribe_path,
            uploaded_enrich_path,
            uploaded_summary_path,
        ),
        daemon=True,
    )
    t.start()

    return jsonify(session_id=session_id)


@app.route("/progress/<session_id>")
def progress_route(session_id: str):
    """Server-Sent Events stream for real-time progress."""
    if session_id not in sessions:
        return "Session not found", 404

    def generate():
        q: queue.Queue = sessions[session_id]["queue"]
        yield "retry: 3000\n\n"
        while True:
            try:
                item = q.get(timeout=30)
                if item is None:
                    yield "data: {\"event\":\"stream_end\"}\n\n"
                    break
                yield f"data: {item}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
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
# HTML (embedded — no separate templates folder needed)
# ─────────────────────────────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lecture Pipeline</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Thai:wght@300;400;500;600&display=swap');

  :root {
    --bg:       #0d1117;
    --surface:  #161b22;
    --border:   #30363d;
    --accent:   #58a6ff;
    --accent2:  #3fb950;
    --warn:     #f0883e;
    --err:      #f85149;
    --text:     #e6edf3;
    --muted:    #8b949e;
    --mono:     'IBM Plex Mono', monospace;
    --sans:     'IBM Plex Sans Thai', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    min-height: 100vh;
    padding: 2rem 1rem;
  }

  .container {
    max-width: 860px;
    margin: 0 auto;
  }

  header {
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
  }

  header h1 {
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: -0.02em;
  }

  header h1 span { color: var(--accent); }

  header p {
    color: var(--muted);
    font-size: 0.875rem;
    margin-top: 0.4rem;
    line-height: 1.6;
  }

  /* ── Card ── */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
  }

  .card-title {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 1rem;
  }

  /* ── Form ── */
  .field { margin-bottom: 1rem; }

  .field label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.4rem;
  }

  .field .hint {
    font-size: 0.78rem;
    color: var(--muted);
    margin-bottom: 0.4rem;
  }

  .field input[type=text],
  .field input[type=password],
  .field select,
  .field textarea {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: var(--mono);
    font-size: 0.875rem;
    padding: 0.6rem 0.75rem;
    transition: border-color 0.15s;
    outline: none;
  }

  .field textarea {
    font-family: var(--sans);
    resize: vertical;
  }

  .field input:focus, .field select:focus, .field textarea:focus {
    border-color: var(--accent);
  }

  /* ── Drop zone ── */
  .drop-zone {
    border: 2px dashed var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    position: relative;
  }

  .drop-zone:hover, .drop-zone.dragover {
    border-color: var(--accent);
    background: rgba(88, 166, 255, 0.05);
  }

  .drop-zone input[type=file] {
    position: absolute; inset: 0;
    opacity: 0; cursor: pointer; width: 100%; height: 100%;
  }

  .drop-zone .dz-icon { font-size: 1.5rem; margin-bottom: 0.4rem; }

  .drop-zone .dz-label {
    font-size: 0.875rem;
    color: var(--muted);
  }

  .drop-zone .dz-filename {
    font-family: var(--mono);
    font-size: 0.8rem;
    color: var(--accent2);
    margin-top: 0.4rem;
    word-break: break-all;
  }

  .optional-tag {
    font-size: 0.7rem;
    background: rgba(88, 166, 255, 0.15);
    color: var(--accent);
    border-radius: 4px;
    padding: 0.1rem 0.4rem;
    margin-left: 0.4rem;
    vertical-align: middle;
  }

  /* ── Row grid ── */
  .row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  @media (max-width: 600px) { .row-2 { grid-template-columns: 1fr; } }

  /* ── Run button ── */
  .btn-run {
    width: 100%;
    padding: 0.85rem;
    background: var(--accent);
    color: #000;
    font-family: var(--sans);
    font-size: 1rem;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.1s;
    margin-top: 0.5rem;
  }

  .btn-run:hover:not(:disabled) { opacity: 0.88; transform: translateY(-1px); }
  .btn-run:disabled { opacity: 0.4; cursor: not-allowed; }

  /* ── Progress panel ── */
  #progress-panel { display: none; }

  .step-list { list-style: none; }

  .step-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
  }

  .step-item:last-child { border-bottom: none; }

  .step-icon {
    width: 1.4rem;
    height: 1.4rem;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    margin-top: 0.05rem;
  }

  .step-body { flex: 1; min-width: 0; }

  .step-label {
    font-size: 0.9rem;
    font-weight: 500;
  }

  .step-log {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.35rem;
    white-space: pre-wrap;
    word-break: break-all;
  }

  .step-filename {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--accent2);
    margin-top: 0.2rem;
  }

  /* Step states */
  .step-item[data-state=waiting]  .step-icon::before { content: "○"; color: var(--muted); }
  .step-item[data-state=running]  .step-icon { animation: spin 1s linear infinite; }
  .step-item[data-state=running]  .step-icon::before { content: "◌"; color: var(--accent); }
  .step-item[data-state=done]     .step-icon::before { content: "✓"; color: var(--accent2); }
  .step-item[data-state=error]    .step-icon::before { content: "✗"; color: var(--err); }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }

  /* ── Done banner ── */
  .done-banner {
    background: rgba(63, 185, 80, 0.1);
    border: 1px solid var(--accent2);
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .done-banner p { font-size: 0.9rem; line-height: 1.5; }
  .done-banner p strong { color: var(--accent2); }

  .btn-download {
    padding: 0.65rem 1.25rem;
    background: var(--accent2);
    color: #000;
    font-family: var(--sans);
    font-size: 0.875rem;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    text-decoration: none;
    flex-shrink: 0;
  }

  .btn-download:hover { opacity: 0.85; }

  /* ── Error banner ── */
  .error-banner {
    background: rgba(248, 81, 73, 0.1);
    border: 1px solid var(--err);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    font-family: var(--mono);
    font-size: 0.78rem;
    white-space: pre-wrap;
    word-break: break-all;
    color: var(--err);
    max-height: 200px;
    overflow-y: auto;
  }

  /* ── Resume panel styles ── */
  .resume-section {
    margin-top: 1rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
  }

  .resume-section summary {
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--accent);
    padding: 0.6rem 0.8rem;
    user-select: none;
    outline: none;
  }

  .resume-grid {
    padding: 0 0.8rem 0.8rem 0.8rem;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
    border-top: 1px solid var(--border);
    margin-top: 0.2rem;
    padding-top: 0.8rem;
  }

  @media (max-width: 600px) { .resume-grid { grid-template-columns: 1fr; } }

  .resume-grid .field label {
    font-size: 0.8rem;
    color: var(--muted);
  }

  .resume-grid input[type=file] {
    font-family: var(--sans);
    font-size: 0.78rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    color: var(--text);
    padding: 0.35rem;
    width: 100%;
    outline: none;
  }
</style>
</head>
<body>
<div class="container">

  <header>
    <h1>🏥 <span>Lecture</span> Pipeline</h1>
    <p>
      อัปโหลดไฟล์สไลด์ PDF และ (ไม่บังคับ) transcript + Curriculum Map<br>
      กด <strong>Run Pipeline</strong> เพื่อประมวลผลอัตโนมัติทุกขั้นตอนผ่าน Gemini API
    </p>
  </header>

  <!-- ── Upload Form ── -->
  <div id="upload-section">

    <div class="card">
      <div class="card-title">🔑 API Configuration</div>

      <div class="row-2">
        <div class="field">
          <label>Google AI API Key</label>
          <div class="hint">รับได้ที่ <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--accent)">aistudio.google.com/app/apikey</a></div>
          <input type="password" id="api_key" placeholder="AIzaSy..." autocomplete="off">
        </div>
        <div class="field">
          <label>Gemini Model</label>
          <div class="hint">เลือกโมเดลเพื่อประมวลผล</div>
          <select id="model">
            <!-- Gemini 3.5 & 3.1 Frontier Models -->
            <option value="gemini-3.5-flash">gemini-3.5-flash (เร็วสูงสุด · ความสามารถระดับ Pro · แนะนำ)</option>
            <option value="gemini-3.1-pro">gemini-3.1-pro (วิเคราะห์เชิงลึกและ Coding สูงสุด)</option>
            <option value="gemini-3.1-flash-lite">gemini-3.1-flash-lite (ประหยัดค่าใช้จ่ายและประมวลผลเร็ว)</option>
            <!-- Gemini 2.5 Production-Ready Stable Models -->
            <option value="gemini-2.5-pro">gemini-2.5-pro (โมเดลระดับ Pro ความเสถียรสูง)</option>
            <option value="gemini-2.5-flash">gemini-2.5-flash (โมเดลทั่วไป ความเสถียรสูง)</option>
          </select>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">📂 Files</div>

      <div class="field">
        <label>📄 PDF Slide File <span style="color:var(--err)">*</span></label>
        <div class="hint">ไฟล์สไลด์บทเรียน (PDF) (ไม่บังคับ หากเลือกอัปโหลดไฟล์ขั้นตอนกลางที่ด้านล่างแทน)</div>
        <div class="drop-zone" id="dz-slide">
          <input type="file" id="slide_file" accept=".pdf" onchange="setFilename('dz-slide', this)">
          <div class="dz-icon">📑</div>
          <div class="dz-label">คลิกหรือลากไฟล์ PDF มาวาง</div>
          <div class="dz-filename" id="fn-slide"></div>
        </div>
      </div>

      <div class="row-2">
        <div class="field">
          <label>🎙️ Transcript <span class="optional-tag">optional</span></label>
          <div class="hint">ไฟล์ .txt ถอดเทปคำบรรยาย หรือวางข้อความด้านล่าง</div>
          <div class="drop-zone" id="dz-transcript" style="margin-bottom: 0.5rem;">
            <input type="file" id="transcript_file" accept=".txt" onchange="setFilename('dz-transcript', this)">
            <div class="dz-icon">🎤</div>
            <div class="dz-label">transcript.txt</div>
            <div class="dz-filename" id="fn-transcript"></div>
          </div>
          <textarea id="transcript_text" placeholder="หรือ วางข้อความ Transcript ของผู้สอนที่นี่..." rows="4"></textarea>
        </div>

        <div class="field">
          <label>📚 Curriculum Map <span class="optional-tag">optional</span></label>
          <div class="hint">ไฟล์ Curriculum_Map.md จากรอบก่อน</div>
          <div class="drop-zone" id="dz-curriculum">
            <input type="file" id="curriculum_file" accept=".md,.txt" onchange="setFilename('dz-curriculum', this)">
            <div class="dz-icon">🗂️</div>
            <div class="dz-label">Curriculum_Map.md</div>
            <div class="dz-filename" id="fn-curriculum"></div>
          </div>
        </div>
      </div>

      <!-- ── Resume from Intermediate Files ── -->
      <details class="resume-section">
        <summary>🔄 ดำเนินการต่อจากขั้นตอนก่อนหน้า (Resume / Upload Intermediate Files)</summary>
        <div class="resume-grid">
          <div class="field">
            <label>1. lecture-markdown.md</label>
            <input type="file" id="uploaded_markdown" accept=".md">
          </div>
          <div class="field">
            <label>2. lecture-transcribe.md</label>
            <input type="file" id="uploaded_transcribe" accept=".md">
          </div>
          <div class="field">
            <label>3. lecture-enrich.md</label>
            <input type="file" id="uploaded_enrich" accept=".md">
          </div>
          <div class="field">
            <label>4. lecture-summary.md</label>
            <input type="file" id="uploaded_summary" accept=".md">
          </div>
        </div>
      </details>

    </div>

    <button class="btn-run" id="btn-run" onclick="startPipeline()">
      ▶ Run Pipeline
    </button>

  </div><!-- /upload-section -->

  <!-- ── Progress Panel ── -->
  <div id="progress-panel">
    <div class="card">
      <div class="card-title">⚡ Pipeline Progress</div>
      <ul class="step-list" id="step-list"></ul>
    </div>
    <div id="result-area"></div>
  </div>

</div><!-- /container -->

<script>
// ── Drag & drop helpers ──
document.querySelectorAll('.drop-zone').forEach(dz => {
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('dragover');
    const input = dz.querySelector('input[type=file]');
    if (e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      input.dispatchEvent(new Event('change'));
    }
  });
});

function setFilename(dzId, input) {
  const fnEl = document.getElementById('fn-' + dzId.replace('dz-', ''));
  fnEl.textContent = input.files[0] ? input.files[0].name : '';
}

// ── Step registry: order matters ──
const STEPS = [
  { id: 'slide_md',   label: '📄 แปลง PDF สไลด์ → Markdown' },
  { id: 'transcript', label: '🎙️ สังเคราะห์ Transcript' },
  { id: 'enrich',     label: '🔬 Slide Enrich' },
  { id: 'crystal',    label: '💎 Lecture Crystallizer' },
  { id: 'curriculum', label: '📚 Curriculum Map Update' },
  { id: 'package',    label: '📁 Package & Zip' },
];

let sessionId = null;
let es = null;

function buildStepList(hasTranscript, hasCurriculum) {
  const list = document.getElementById('step-list');
  list.innerHTML = '';
  STEPS.forEach(s => {
    if (s.id === 'transcript' && !hasTranscript) return;
    if (s.id === 'curriculum' && !hasCurriculum) return;
    const li = document.createElement('li');
    li.className = 'step-item';
    li.dataset.state = 'waiting';
    li.dataset.stepId = s.id;
    li.innerHTML = `
      <div class="step-icon"></div>
      <div class="step-body">
        <div class="step-label">${s.label}</div>
        <div class="step-log" id="log-${s.id}"></div>
        <div class="step-filename" id="fn-out-${s.id}"></div>
      </div>`;
    list.appendChild(li);
  });
}

function setStepState(stepId, state) {
  const li = document.querySelector(`[data-step-id="${stepId}"]`);
  if (li) li.dataset.state = state;
}

function appendLog(stepId, msg) {
  const el = document.getElementById('log-' + stepId);
  if (!el) return;
  el.textContent += (el.textContent ? '\n' : '') + msg;
}

function setStepFilename(stepId, filename) {
  const el = document.getElementById('fn-out-' + stepId);
  if (el && filename) el.textContent = '→ ' + filename;
}

async function startPipeline() {
  const apiKey = document.getElementById('api_key').value.trim();
  const model  = document.getElementById('model').value;
  const slideFile = document.getElementById('slide_file').files[0];
  const transcriptFile = document.getElementById('transcript_file').files[0];
  const transcriptText = document.getElementById('transcript_text').value.trim();
  const curriculumFile = document.getElementById('curriculum_file').files[0];

  // ไฟล์สำหรับ Resume ขั้นตอนกลาง
  const uploadedMarkdown = document.getElementById('uploaded_markdown').files[0];
  const uploadedTranscribe = document.getElementById('uploaded_transcribe').files[0];
  const uploadedEnrich = document.getElementById('uploaded_enrich').files[0];
  const uploadedSummary = document.getElementById('uploaded_summary').files[0];

  if (!apiKey) { alert('กรุณาใส่ Google AI API Key'); return; }

  const hasSlide = !!slideFile;
  const hasIntermediate = !!uploadedMarkdown || !!uploadedTranscribe || !!uploadedEnrich || !!uploadedSummary;

  if (!hasSlide && !hasIntermediate) {
    alert('กรุณาเลือกไฟล์ PDF สไลด์ หรือเลือกไฟล์ขั้นตอนกลาง (Intermediate File) อย่างน้อย 1 ไฟล์ที่ด้านล่าง เพื่อดำเนินการต่อ');
    return;
  }

  // Disable button
  document.getElementById('btn-run').disabled = true;

  // Build form data
  const fd = new FormData();
  fd.append('api_key', apiKey);
  fd.append('model', model);
  if (slideFile) fd.append('slide', slideFile);
  if (transcriptFile) fd.append('transcript', transcriptFile);
  if (transcriptText) fd.append('transcript_text', transcriptText);
  if (curriculumFile) fd.append('curriculum_map', curriculumFile);

  // อัปโหลดไฟล์ Intermediate เพื่อใช้ Resume
  if (uploadedMarkdown) fd.append('uploaded_markdown', uploadedMarkdown);
  if (uploadedTranscribe) fd.append('uploaded_transcribe', uploadedTranscribe);
  if (uploadedEnrich) fd.append('uploaded_enrich', uploadedEnrich);
  if (uploadedSummary) fd.append('uploaded_summary', uploadedSummary);

  // Show progress panel
  document.getElementById('upload-section').style.display = 'none';
  document.getElementById('progress-panel').style.display = 'block';

  // ตรวจสอบว่าใน Session นี้มีการใช้งาน Transcript หรือไม่
  const hasTranscript = !!transcriptFile || !!transcriptText || !!uploadedTranscribe;
  const hasCurriculum = !!curriculumFile;
  buildStepList(hasTranscript, hasCurriculum);

  try {
    const res = await fetch('/run', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) { showFatalError(data.error); return; }
    sessionId = data.session_id;
    startSSE(sessionId);
  } catch(e) {
    showFatalError(e.message);
  }
}

function startSSE(sid) {
  es = new EventSource(`/progress/${sid}`);
  es.onmessage = function(e) {
    const d = JSON.parse(e.data);
    handleEvent(d);
  };
  es.onerror = function() {
    // SSE connection closed — pipeline likely done
  };
}

function handleEvent(d) {
  switch(d.event) {
    case 'step_start':
      setStepState(d.step, 'running');
      break;
    case 'step_log':
      appendLog(d.step, d.msg);
      break;
    case 'step_done':
      setStepState(d.step, 'done');
      setStepFilename(d.step, d.filename);
      break;
    case 'step_error':
      setStepState(d.step, 'error');
      appendLog(d.step, '‼️ ' + d.error);
      break;
    case 'done':
      showDone(d.session, d.folder, d.zip);
      if (es) es.close();
      break;
    case 'fatal_error':
      showFatalError(d.msg);
      if (es) es.close();
      break;
    case 'stream_end':
      if (es) es.close();
      break;
  }
}

function showDone(sid, folder, zip) {
  const area = document.getElementById('result-area');
  area.innerHTML = `
    <div class="done-banner">
      <p>
        ✅ Pipeline เสร็จสมบูรณ์!<br>
        <strong>${folder}</strong> — พร้อมดาวน์โหลด
      </p>
      <a class="btn-download" href="/download/${sid}">
        ⬇ ดาวน์โหลด ZIP
      </a>
    </div>`;
}

function showFatalError(msg) {
  const area = document.getElementById('result-area');
  area.innerHTML = `<div class="error-banner">❌ Error:\n${msg}\n\nโปรดตรวจสอบ:\n• API Key ถูกต้องไหม\n• ไฟล์ prompts/ อยู่ถูกที่ไหม\n• Log ใน terminal สำหรับรายละเอียดเพิ่มเติม</div>`;
  document.getElementById('btn-run').disabled = false;
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("=" * 55)
    print("  Lecture Pipeline — http://localhost:5000")
    print("=" * 55)
    print(f"  Prompts dir : {PROMPTS_DIR}")
    print(f"  Output dir  : {OUTPUT_BASE}")
    print()

    # Warn if any prompt files are missing
    expected = [
        "slide-to-markdown-gemini.md",
        "lecture-synthesizer.md",
        "slide-enrich.md",
        "lecture-crystallizer.md",
        "curriculum-tracker.md",
    ]
    missing = [f for f in expected if not (PROMPTS_DIR / f).exists()]
    if missing:
        print("⚠️  Missing prompt files:")
        for f in missing:
            print(f"     prompts/{f}")
        print("   โปรดวาง .md files ทั้งหมดไว้ใน prompts/ folder")
        print()

    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)