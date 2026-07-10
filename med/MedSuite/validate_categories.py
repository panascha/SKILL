#!/usr/bin/env python3
"""
validate_categories.py
----------------------
ตรวจสอบ ส่งออกข้อสอบที่มีปัญหาเพื่อให้ AI ช่วยตั้งหมวดหมู่ 
และนำเข้าข้อสอบที่แก้ไขแล้วเพื่ออัปเดตระบบอัตโนมัติ
"""

import json
import re
import difflib
from pathlib import Path

# กำหนด Path
BASE_DIR = Path(__file__).parent
COURSES_DIR = BASE_DIR / "courses"
OUTPUT_DIR = BASE_DIR / "output"
QUIZDATA_PATH = OUTPUT_DIR / "quizdata.js"
PROMPT_OUT_PATH = BASE_DIR / "prompt_for_ai.txt"
CORRECTED_IN_PATH = BASE_DIR / "corrected_questions.json"


def load_courses():
    """โหลดข้อมูลหลักสูตรทั้งหมดจาก courses/"""
    courses = {}
    if not COURSES_DIR.exists():
        print(f"❌ ไม่พบโฟลเดอร์ courses ที่ตำแหน่ง: {COURSES_DIR}")
        return courses

    for f in COURSES_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sub_code = data.get("subject_code", "").upper()
            if sub_code:
                courses[sub_code] = data
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลดไฟล์วิชา {f.name} ได้: {e}")
    return courses


def load_quizdata():
    """ดึงข้อมูล JSON จาก quizdata.js"""
    if not QUIZDATA_PATH.exists():
        print(f"❌ ไม่พบไฟล์รวมผลลัพธ์ที่ตำแหน่ง: {QUIZDATA_PATH}")
        return None, None

    content = QUIZDATA_PATH.read_text(encoding="utf-8").strip()
    m = re.search(r'var\s+quizdata\s*=\s*(\{[\s\S]+?\})(?:\s*;?\s*)$', content)
    if not m:
        m = re.search(r'var\s+quizdata\s*=\s*(\{[\s\S]+\})', content)

    if m:
        try:
            json_str = m.group(1).strip()
            if json_str.endswith(';'):
                json_str = json_str[:-1].strip()
            return json.loads(json_str), content
        except Exception as e:
            print(f"❌ โครงสร้าง JSON ใน quizdata.js ผิดพลาด: {e}")
    else:
        print("❌ ไม่พบตัวแปร var quizdata ในไฟล์ quizdata.js")
    return None, None


def split_category(category_str):
    """แยกข้อมูล Category จากรูปแบบ Subject_Subgroup_Topic"""
    parts = category_str.split('_', 2)
    subject = parts[0] if len(parts) > 0 else ""
    subgroup = parts[1] if len(parts) > 1 else ""
    topic = parts[2] if len(parts) > 2 else ""
    return subject, subgroup, topic


def get_valid_options(course_data):
    """ดึงข้อมูลหัวข้อและ Subgroup ที่อนุญาตจาก Course Preset"""
    valid_map = {}  # {topic_name: subgroup_suffix}
    subgroup_mode = course_data.get("subgroup")
    topics = course_data.get("topics", [])

    if subgroup_mode == "MAPPED":
        for t in topics:
            if isinstance(t, dict):
                valid_map[t.get("topic")] = t.get("subgroup")
    elif subgroup_mode == "LEC":
        for t in topics:
            if isinstance(t, str):
                valid_map[t] = "LEC"
    elif isinstance(subgroup_mode, list):
        for g in subgroup_mode:
            valid_map[f"Any Topic Under {g}"] = g
    return valid_map


def scan_problematic_questions(courses, quizdata):
    """สแกนค้นหาข้อสอบที่หมวดหมู่ไม่ตรงกับหลักสูตร"""
    problems = []
    subjects_in_problems = set()

    for exam_key, questions in quizdata.items():
        for q in questions:
            if "category" in q and len(q["category"]) > 1:
                cat_val = q["category"][1]
                subject, subgroup, topic = split_category(cat_val)
                
                # ถ้าไม่พบวิชา หรือหัวข้อไม่ตรงกับไฟล์ Preset
                if subject not in courses:
                    problems.append(q)
                    subjects_in_problems.add(subject)
                    continue

                valid_options = get_valid_options(courses[subject])
                if topic not in valid_options or valid_options[topic] != subgroup:
                    problems.append(q)
                    subjects_in_problems.add(subject)

    return problems, subjects_in_problems


def export_to_ai_prompt(problems, subjects_in_problems, courses):
    """สร้างไฟล์ prompt_for_ai.txt สำหรับนำไปส่งให้ AI"""
    if not problems:
        print("✅ ไม่พบข้อสอบที่มีปัญหา ไม่จำเป็นต้องส่งออกไฟล์")
        return

    # สร้างข้อมูลหลักสูตรที่ถูกต้องประกอบใน Prompt
    courses_info = []
    for sub in subjects_in_problems:
        if sub in courses:
            courses_info.append(f"\n--- รายชื่อวิชาและหัวข้อที่ถูกต้องของวิชา {sub} ---")
            course_data = courses[sub]
            valid_options = get_valid_options(course_data)
            for topic, subg in valid_options.items():
                courses_info.append(f"- [{subg}] {topic}")
        else:
            courses_info.append(f"\n--- ⚠️ ไม่พบข้อมูล Preset สำหรับวิชา {sub} ในโฟลเดอร์ courses/ ---")

    courses_text = "\n".join(courses_info)

    # กรองเอาเฉพาะข้อมูลฟิลด์สำคัญเพื่อประหยัด Token และป้องกัน AI แก้ไขส่วนอื่น
    compact_questions = []
    for q in problems:
        compact_questions.append({
            "problem": q.get("problem"),
            "choices": q.get("choices"),
            "answer": q.get("answer"),
            "category": q.get("category")
        })

    prompt_content = f"""คุณคือผู้เชี่ยวชาญการจำแนกหมวดหมู่ข้อสอบแพทย์ (Medical MCQ Categorizer)

หน้าที่ของคุณ:
1. อ่านคำถาม (problem) และตัวเลือก (choices) ของข้อสอบแต่ละข้อด้านล่าง
2. พิจารณาเลือกหัวข้อและกลุ่มวิชาที่ "ถูกต้องตรงกันทุกตัวอักษร" จากรายการหลักสูตรที่กำหนดให้เท่านั้น
3. ปรับเปลี่ยนข้อมูลเฉพาะในฟิลด์ category[1] ให้ถูกต้องตามรูปแบบ: SubjectCode_SubGroupSuffix_TopicLabel
   - เช่น ถ้าคำถามสอดคล้องกับหัวข้อ "Mechanics of breathing" ของวิชา "RS" ซึ่งมีรหัสกลุ่มวิชาคือ "PHYSIO" ให้แก้ไขค่า category[1] เป็น "RS_PHYSIO_Mechanics of breathing"
   - ห้ามแก้ไขข้อมูลใน category[0]

⚠️ ข้อกำหนดสำคัญ:
- ส่งคำตอบกลับมาเฉพาะในรูปแบบ JSON Array ของคำถามที่แก้ไขฟิลด์ category[1] แล้วเท่านั้น
- ห้ามแก้ไขฟิลด์ problem, choices, answer หรือฟิลด์อื่นๆ โดยเด็ดขาด
- ห้ามใส่คำอธิบายเพิ่มเติมใดๆ นอกเหนือจาก JSON Array

{courses_text}

--- รายการข้อสอบที่มีปัญหา (Problematic Questions JSON) ---
{json.dumps(compact_questions, ensure_ascii=False, indent=2)}
"""

    PROMPT_OUT_PATH.write_text(prompt_content, encoding="utf-8")
    print(f"\n✅ ส่งออกข้อมูลสำเร็จ!")
    print(f"📍 ไฟล์คำสั่ง: {PROMPT_OUT_PATH.relative_to(BASE_DIR)}")
    print(f"👉 กรุณาเปิดไฟล์ คัดลอกเนื้อหาทั้งหมดส่งให้ AI และบันทึกคำตอบของ AI ลงในไฟล์ '{CORRECTED_IN_PATH.name}'")


def import_corrected_questions():
    """นำเข้าข้อสอบที่แก้ไขโดย AI จาก corrected_questions.json และอัปเดตไฟล์ทั้งระบบ"""
    if not CORRECTED_IN_PATH.exists():
        print(f"❌ ไม่พบไฟล์นำเข้าที่ตำแหน่ง: {CORRECTED_IN_PATH}")
        print(f"💡 กรุณาส่งออกข้อสอบที่มีปัญหาให้ AI และนำคำตอบมาเซฟไว้ที่ไฟล์ {CORRECTED_IN_PATH.name} ก่อนรันคำสั่งนี้")
        return

    try:
        corrected_data = json.loads(CORRECTED_IN_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ รูปแบบไฟล์ {CORRECTED_IN_PATH.name} ไม่ใช่ JSON ที่ถูกต้อง: {e}")
        return

    if not isinstance(corrected_data, list):
        print(f"❌ ข้อมูลในไฟล์ {CORRECTED_IN_PATH.name} ต้องอยู่ในรูปแบบ JSON Array (รายการคำถาม)")
        return

    # สร้างแผนผังจับคู่การเปลี่ยนแปลง {problem_text: new_category_array}
    update_map = {}
    for q in corrected_data:
        if isinstance(q, dict) and "problem" in q and "category" in q:
            update_map[q["problem"].strip()] = q["category"]

    if not update_map:
        print("⚠️ ไม่พบข้อมูลคำถามที่ระบุการแก้ไข category ในไฟล์")
        return

    print(f"\n📬 ตรวจพบข้อสอบที่ได้รับการแก้ไขจากไฟล์นำเข้า: {len(update_map)} ข้อ")

    # 1. ค้นหาและอัปเดตไฟล์ .json รายรายวิชาในโฟลเดอร์ output/ และ require_img/
    updated_files_count = 0
    updated_questions_count = 0

    all_json_files = list(OUTPUT_DIR.glob("**/*.json"))
    for json_file in all_json_files:
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            changed = False
            for q in data.get("questions", []):
                prob_text = q.get("problem", "").strip()
                if prob_text in update_map:
                    q["category"] = update_map[prob_text]
                    changed = True
                    updated_questions_count += 1
            if changed:
                json_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                updated_files_count += 1
                print(f"  - อัปเดตไฟล์: {json_file.relative_to(BASE_DIR)}")
        except Exception as e:
            print(f"  ⚠️ เกิดข้อผิดพลาดขณะเขียนไฟล์ {json_file.name}: {e}")

    # 2. ปรับปรุงไฟล์รวมย่อย output/quizdata.js
    quiz_data, _ = load_quizdata()
    if quiz_data:
        for exam_key, questions in quiz_data.items():
            for q in questions:
                prob_text = q.get("problem", "").strip()
                if prob_text in update_map:
                    q["category"] = update_map[prob_text]
        
        try:
            js_content = (
                "// Auto-generated Combined MCQ Quiz Data\n"
                f"var quizdata = {json.dumps(quiz_data, ensure_ascii=False, indent=2)};\n"
            )
            QUIZDATA_PATH.write_text(js_content, encoding="utf-8")
            print("  - อัปเดตไฟล์ภาพรวมระบบ: output/quizdata.js สำเร็จ!")
        except Exception as e:
            print(f"  ❌ ไม่สามารถเขียนทับไฟล์ quizdata.js: {e}")

    print(f"\n✨ ปรับปรุงข้อมูลเสร็จสิ้น!")
    print(f"  - อัปเดตไฟล์คำถามย่อยทั้งหมด: {updated_files_count} ไฟล์")
    print(f"  - อัปเดตคำถามทั้งระบบ: {updated_questions_count} ข้อ")


def main():
    print("=" * 60)
    print("   🏥 ระบบตรวจสอบและส่งออก/นำเข้า Category ด้วย AI")
    print("=" * 60)
    print("เลือกเมนูการดำเนินงาน:")
    print(" [1] สแกนตรวจหาข้อสอบที่มีปัญหา (Scan Categories)")
    print(" [2] ส่งออกข้อสอบที่มีปัญหาไปยัง prompt_for_ai.txt เพื่อไปถาม AI")
    print(" [3] นำเข้าคำตอบของ AI จาก corrected_questions.json เข้าสู่ระบบ")
    print(" [q] ออกจากโปรแกรม")
    print("-" * 60)

    choice = input("👉 เลือกเมนู (1/2/3/q): ").strip().lower()

    if choice == '1':
        courses = load_courses()
        quizdata, _ = load_quizdata()
        if not courses or not quizdata:
            return
        problems, _ = scan_problematic_questions(courses, quizdata)
        if problems:
            print(f"\n❌ พบข้อสอบที่หมวดหมู่สะกดผิดหรือไม่ตรงกับหลักสูตร: {len(problems)} ข้อ")
            print("💡 แนะนำให้เลือกเมนู [2] เพื่อส่งออกข้อสอบส่งให้ AI ช่วยแก้ไข")
        else:
            print("\n✅ ยินดีด้วยครับ! หมวดหมู่ข้อสอบทั้งหมดตรงกับโครงสร้างหลักสูตร 100%")

    elif choice == '2':
        courses = load_courses()
        quizdata, _ = load_quizdata()
        if not courses or not quizdata:
            return
        problems, subjects = scan_problematic_questions(courses, quizdata)
        export_to_ai_prompt(problems, subjects, courses)

    elif choice == '3':
        import_corrected_questions()

    else:
        print("\nออกจากโปรแกรม")


if __name__ == "__main__":
    main()