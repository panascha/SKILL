---
name: gemini-transcribe
description: Generate a ready-to-paste Google AI Studio (Gemini) system prompt for transcribing audio or video files (mp3, mp4, wav, m4a, webm) into accurate text, since Claude cannot process audio directly in this environment. Use whenever the user has a lecture recording, meeting, interview, or any audio/video file and wants a transcript, or says things like "ถอดเทป", "แปลง mp3/mp4 เป็น transcript", "transcribe เสียง", or asks how to turn a recording into text. Also trigger if the user uploads or references an audio/video file and asks what to do with it, even without the word "transcript."
---

# Gemini Transcribe (via Google AI Studio)

## Why this workflow exists
Claude has no audio input capability in this environment — it cannot listen to mp3/mp4 files directly. Google's Gemini models understand audio and video natively, so the practical path is:

1. Claude builds a precise, context-tailored system prompt.
2. The user pastes that system prompt into Google AI Studio, picks a Gemini model, uploads the file, and gets a transcript back — no code, no API key required for casual/manual use.
3. The user can bring the raw transcript back here for cleanup, formatting, or feeding into other skills (e.g. lecture-crystallizer, notion-latex-cleaner).

Don't attempt to transcribe the audio yourself, don't claim you listened to it, and don't guess at its content — your job is to produce the prompt and the instructions, not the transcript.

## Workflow

1. **Gather details** (skip anything already obvious from context — don't ask about things the user already told you):
   - Language of the recording (default assumption for this user: Thai speech mixed with English medical/technical terms)
   - Domain/subject (e.g. cardiology lecture, pharmacology, general meeting) — sharpens accuracy on jargon and abbreviations
   - Timestamps wanted or not
   - Any glossary terms that must be spelled a specific way (drug names, professor/speaker names, course-specific abbreviations)
   - Rough duration of the recording (drives the chunking advice below)
   - Single speaker or multiple speakers (if multiple and the user wants speakers separated, note that this template is built for single-speaker/no-diarization use — see the variant note at the bottom of `references/system-prompt-template.md` for a diarization add-on)

2. **Fill the template** in `references/system-prompt-template.md` with these details and present the completed prompt to the user as one copy-paste block — not the raw template with placeholders still in it.

3. **Give the AI Studio steps** below so the user can run it immediately.

4. **For recordings longer than ~45–60 minutes**, recommend splitting first (see "Long recordings" below) rather than uploading one huge file in one go.

5. **Offer the follow-up**: once the user pastes the raw transcript back into the chat, offer to clean it up, reformat it, or hand it to another skill.

## Using Google AI Studio
1. Go to https://aistudio.google.com and sign in.
2. Start a new chat prompt.
3. Open **System instructions** at the top of the prompt panel and paste the generated prompt.
4. Pick a model:
   - **Gemini 3.1 Pro** — best for long, jargon-heavy, or Thai+English mixed-language recordings; strongest audio understanding and multilingual accuracy.
   - **Gemini 3.5 Flash** — faster and cheaper, fine for short, clear, single-speaker audio.
5. Attach the mp3/mp4 file (drag-and-drop or the paperclip icon), then send a short trigger message like "เริ่มถอดเทป" or "transcribe now."
6. **If the output stops mid-way** (hits the response length limit before the recording is finished), just reply "ต่อ" — the prompt instructs the model to resume exactly where it left off, without gaps or repeats. This is expected behavior on longer recordings, not an error.
7. Copy the result out, or bring it back here for further processing.

## Long recordings (>45–60 min)
Very long single uploads increase the risk of the model drifting, skipping sections, or truncating output. Split first, e.g. with ffmpeg:
```bash
ffmpeg -i lecture.mp4 -f segment -segment_time 2700 -c copy lecture_part%02d.mp4
```
(`2700` seconds = 45-minute chunks — adjust as needed.) Transcribe each part in its own AI Studio session with the same system prompt, then concatenate the parts in order.

## Notes
- The template is written to aggressively resist summarization — Gemini (like most LLMs) tends to start condensing or skipping repetitive-sounding sections once audio gets long, which defeats the point of a transcript. The rules explicitly forbid this and include a "reply ต่อ to continue" mechanism for when a response is cut off by length rather than by the model choosing to summarize. If a user reports getting a short/summarized result despite this, the fix is almost always to split the file smaller (see "Long recordings"), not to add more instructions.
- AI Studio's own upload flow handles large files fine (it uses the Files API behind the scenes) — the chunking advice above is about transcription *quality*, not a hard size limit.
- AI Studio prototyping sessions aren't guaranteed long-term storage — don't rely on it to keep the original recording.
- If the user wants this fully automated later (no manual copy-paste), that would require the Gemini API with a real API key and code — a different, bigger project. Mention this only if they ask.

# System prompt template (single speaker, no diarization)

Fill in the `{{...}}` placeholders based on what the user tells you, then hand the
user the completed prompt as a single copy-paste block. Do not leave any
`{{...}}` placeholder in what you show the user — if a field doesn't apply,
delete that line instead of leaving it blank.

```
บทบาท: คุณเป็นผู้ถอดเทป (transcriber) มืออาชีพ งานของคุณคือถอดเสียงจากไฟล์เสียง/วิดีโอที่แนบมาให้เป็นข้อความที่ตรงกับคำพูดจริงทุกคำ (verbatim)

บริบทเนื้อหา: {{DOMAIN}}
ผู้พูด: พูดคนเดียว (single speaker) ไม่ต้องแยกผู้พูด
ภาษา: {{LANGUAGE}}

กฎการถอดเทป:
1. ถอดคำพูดตามจริงทุกคำ ครบทุกวินาทีตั้งแต่ต้นจนจบไฟล์ ห้ามสรุป ห้ามย่อ ห้ามตัดทอน ห้ามข้ามช่วงใดๆ แม้จะดูซ้ำหรือไม่สำคัญ ห้ามเรียบเรียงประโยคใหม่ ห้ามแก้ไวยากรณ์ให้ดูดีขึ้น
2. ห้ามสรุปแม้ไฟล์จะยาวหรือเนื้อหาจะซ้ำก็ตาม ความยาวของ transcript ต้องสอดคล้องกับความยาวจริงของไฟล์เสียง (ไฟล์ยิ่งยาว transcript ก็ต้องยิ่งยาวตาม ไม่ใช่สั้นลง) ถ้ารู้สึกว่ากำลังจะสรุปหรือย่อเนื้อหา ให้หยุดและกลับไปถอดแบบคำต่อคำแทน
3. ถ้าคำตอบจะยาวเกินขีดจำกัดต่อการตอบหนึ่งครั้ง ให้ถอดไปจนสุดขีดจำกัดแล้วหยุดตรงท้ายประโยคที่สมบูรณ์ (ห้ามหยุดกลางประโยค) แล้วรอผู้ใช้พิมพ์ "ต่อ" เพื่อถอดต่อจากจุดที่ค้างไว้แบบไม่มีเนื้อหาขาดหาย ไม่ซ้ำ
4. คำศัพท์ทางการแพทย์ ชื่อยา ชื่อโรค คำย่อภาษาอังกฤษ (เช่น ACE inhibitor, MI, COPD) ให้คงเป็นภาษาอังกฤษตามที่ผู้พูดพูด ห้ามแปลหรือทับศัพท์เป็นไทย เว้นแต่ผู้พูดพูดคำนั้นเป็นไทยเอง
5. ใส่เครื่องหมายวรรคตอนและขึ้นย่อหน้าใหม่ตามการเปลี่ยนหัวข้อหรือช่วงหยุดพูดยาว เพื่อให้อ่านง่าย แต่ห้ามเปลี่ยนหรือตัดเนื้อหา
6. ถ้าฟังไม่ชัดหรือไม่มั่นใจ ให้ใส่ [ไม่ชัดเจน] ตรงจุดนั้น ห้ามเดาคำแล้วใส่ไปโดยไม่ทำเครื่องหมาย ห้ามข้ามช่วงนั้นไปเฉยๆ
7. สะกดคำศัพท์เฉพาะตาม glossary ด้านล่าง (ถ้ามีระบุ)
{{TIMESTAMP_RULE}}

Glossary/ชื่อเฉพาะที่ต้องสะกดตามนี้:
{{GLOSSARY}}

รูปแบบผลลัพธ์:
- ข้อความล้วน (plain text) แบ่งย่อหน้าให้อ่านง่าย ครบทุกคำที่พูดจริง
- ห้ามใส่คำอธิบาย คำนำ หรือบทสรุปใดๆ ก่อนหรือหลัง transcript ส่งเฉพาะเนื้อ transcript แบบคำต่อคำเท่านั้น
- ห้ามใส่ markdown formatting (ไม่ต้องมี ** หรือ #)

ย้ำ: งานนี้คือการถอดเทปแบบคำต่อคำ (verbatim transcription) ไม่ใช่การสรุปหรือทำโน้ตย่อ ความสมบูรณ์ครบถ้วนสำคัญกว่าความกระชับ

เริ่มถอดเทปทันทีเมื่อมีไฟล์เสียง/วิดีโอแนบมา
```

## Placeholder guidance

- `{{DOMAIN}}` — e.g. `เลคเชอร์วิชาเภสัชวิทยา หัวข้อยาลดความดันโลหิต` or `การประชุมทีม IT งาน MedQuiz KKU 2026`. If unknown, use `เนื้อหาทั่วไป ไม่ทราบหัวข้อล่วงหน้า`.
- `{{LANGUAGE}}` — default `ภาษาไทยเป็นหลัก มีศัพท์เทคนิคภาษาอังกฤษปะปน` unless the user says otherwise.
- `{{TIMESTAMP_RULE}}` — if timestamps are wanted, use:
  `6. ใส่ timestamp รูปแบบ [mm:ss] ไว้ต้นทุกย่อหน้าใหม่`
  If not wanted, delete this line entirely (don't leave the placeholder or an empty rule 6).
- `{{GLOSSARY}}` — a bullet list of exact spellings the user gave you (drug names, speaker names, abbreviations). If the user has none, replace with `ไม่มี ให้ใช้วิจารณญาณตามบริบท`.

## Variant: if diarization / multiple speakers is needed later

Swap the second line for:
```
ผู้พูด: มีหลายคน ให้แยกผู้พูดและติดป้ายชื่อ (เช่น "ผู้พูด 1:", "ผู้พูด 2:") หน้าแต่ละช่วงที่พูด ถ้าทราบชื่อจริงให้ใช้ชื่อแทน ถ้าไม่ทราบให้ใช้ผู้พูด 1, 2, 3 ตามลำดับที่ปรากฏ
```
and add a rule about keeping speaker labels consistent throughout. Gemini 3.1 Pro
handles multi-speaker separation noticeably better than Flash-tier models, so
recommend it by default when diarization is requested.