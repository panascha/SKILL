#!/usr/bin/env python3
"""
validate_format.py
------------------
ตรวจสอบรูปแบบผลลัพธ์ของ Convert (MCQ converter) และ Generate (quiz generator)
ว่าตรงตาม MDKKU schema หรือไม่

    python validate_format.py                # ตรวจทุกไฟล์ใน output/
    python validate_format.py CVS PHARM      # ตรวจเฉพาะชื่อที่ตรงบางส่วน
    python validate_format.py --self-test    # ตรวจตัวสคริปต์เองด้วย fixture

exit code 0 = ไม่พบ ERROR, 1 = พบ ERROR
"""

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
QUIZDATA_PATH = OUTPUT_DIR / "quizdata.js"

REQUIRED_KEYS = {"problem", "img", "choices", "answer", "select", "explain", "category", "state"}
# รูปแบบ CategoryID ที่ระบบอัปโหลดต้องการ: <Subject>_by AI_<SubGroup>_<Topic Label>
SEP = "_by AI_"
SUBGROUPS = {"LEC", "ANA", "BIOCHEM", "PHYSIO", "MICRO", "PARASITO", "PATHO", "PHARM", "RADIO", "CLINICAL"}


def has_thai(text: str) -> bool:
    # ช่วง Thai Unicode block U+0E00 - U+0E7F
    return any("฀" <= c <= "๿" for c in text)


def check_question(q, where):
    """คืน list ของ (severity, message) สำหรับคำถาม 1 ข้อ"""
    issues = []
    err = lambda m: issues.append(("ERROR", f"{where}: {m}"))
    warn = lambda m: issues.append(("WARN", f"{where}: {m}"))

    if not isinstance(q, dict):
        err(f"ไม่ใช่ object (เป็น {type(q).__name__})")
        return issues

    keys = set(q.keys())
    missing = REQUIRED_KEYS - keys
    extra = keys - REQUIRED_KEYS
    if missing:
        err(f"ขาดฟิลด์ {sorted(missing)}")
    if extra:
        err(f"มีฟิลด์เกิน {sorted(extra)}")

    problem = q.get("problem")
    if not isinstance(problem, str) or not problem.strip():
        err("problem ว่างหรือไม่ใช่ string")

    choices = q.get("choices")
    if not isinstance(choices, str):
        err("choices ไม่ใช่ string")
    else:
        parts = choices.split("///")
        if len(parts) != 5:
            err(f"choices มี {len(parts)} ตัวเลือก (ต้อง 5)")
        if any(not p.strip() for p in parts):
            err("choices มีตัวเลือกว่าง")
        if any(p != p.strip() for p in parts):
            err("choices มีช่องว่างหน้า/หลังตัวคั่น ///")

        answer = q.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            err("answer ว่างหรือไม่ใช่ string")
        elif answer not in parts:
            err(f"answer ไม่ตรงกับตัวเลือกใดเลย: {answer[:60]!r}")

    if q.get("select") != "":
        err(f"select ต้องเป็น \"\" (พบ {q.get('select')!r})")

    if q.get("state") is not False:
        err(f"state ต้องเป็น boolean false (พบ {q.get('state')!r})")

    img = q.get("img")
    if not isinstance(img, str):
        err("img ไม่ใช่ string")
    elif img not in ("", "require_img") and not img.startswith(("http://", "https://")):
        err(f"img ต้องเป็น \"\" | \"require_img\" | URL (พบ {img[:40]!r})")

    explain = q.get("explain")
    if not isinstance(explain, str) or not explain.strip():
        err("explain ว่างหรือไม่ใช่ string")
    elif not has_thai(explain):
        warn("explain ไม่มีตัวอักษรไทยเลย (ต้องเป็นภาษาไทย + ศัพท์แพทย์อังกฤษ)")

    cat = q.get("category")
    if not isinstance(cat, str) or not cat.strip():
        err("category ว่างหรือไม่ใช่ string (schema ปัจจุบันเป็น single string)")
    else:
        if cat != cat.strip() or "  " in cat:
            err(f"category มีช่องว่างหน้า/หลัง หรือเว้นวรรคซ้อน: {cat!r}")
        n = cat.count(SEP)
        if n == 0:
            err(f"category ไม่มี {SEP!r}: {cat!r}")
        elif n > 1:
            err(f"category ซ้ำ {SEP!r} {n} ครั้ง (prefix ซ้อน): {cat!r}")
        else:
            tail = cat.split(SEP, 1)[1]
            head = tail.split("_", 1)[0].upper()
            if head not in SUBGROUPS:
                warn(f"category ไม่มี SubGroup ที่รู้จักตามหลัง {SEP!r} ({head}) — โหมด LEC ถือว่าปกติ")

    return issues


def check_question_list(questions, label, key_must_match=None):
    """ตรวจทั้งชุด: แต่ละข้อ + duplicate problem + key ตรงกับ category"""
    issues = []
    seen = {}
    for i, q in enumerate(questions):
        issues += check_question(q, f"{label}[{i}]")
        if isinstance(q, dict):
            p = q.get("problem")
            if isinstance(p, str) and p.strip():
                if p in seen:
                    issues.append(("WARN", f"{label}[{i}]: problem ซ้ำกับข้อ [{seen[p]}]"))
                else:
                    seen[p] = i
            if key_must_match is not None and q.get("category") != key_must_match:
                issues.append(("ERROR", f"{label}[{i}]: category ไม่ตรงกับ key ของ quizdata.js "
                                        f"({q.get('category')!r} != {key_must_match!r})"))
    return issues


def load_quizdata(path: Path):
    content = path.read_text(encoding="utf-8")
    m = re.search(r"var\s+quizdata\s*=\s*(\{[\s\S]*\})\s*;?\s*$", content.strip())
    if not m:
        raise ValueError("ไม่พบ pattern 'var quizdata = {...}'")
    return json.loads(m.group(1))


def validate_run_file(path: Path):
    """ไฟล์ผลลัพธ์ต่อรอบ: {meta: {...}, questions: [...]} (ใช้ทั้ง Convert และ Generate)"""
    issues = []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "questions" not in data:
        return [("ERROR", f"{path.name}: ไม่มีคีย์ 'questions' ที่ระดับบนสุด")], 0
    questions = data["questions"]
    if not isinstance(questions, list):
        return [("ERROR", f"{path.name}: 'questions' ไม่ใช่ list")], 0

    meta = data.get("meta")
    if not isinstance(meta, dict):
        issues.append(("WARN", f"{path.name}: ไม่มี meta block"))
    else:
        found = set(meta.get("categories_found") or [])
        actual = {q.get("category") for q in questions if isinstance(q, dict)}
        if found and found != actual:
            issues.append(("WARN", f"{path.name}: meta.categories_found ไม่ตรงกับ category จริง "
                                   f"(meta={sorted(found)}, actual={sorted(str(a) for a in actual)})"))
        if isinstance(meta.get("converted"), int) and meta["converted"] != len(questions):
            issues.append(("WARN", f"{path.name}: meta.converted={meta['converted']} "
                                   f"แต่มีคำถามจริง {len(questions)} ข้อ"))

    issues += check_question_list(questions, path.name)
    return issues, len(questions)


def collapse(messages):
    """ยุบข้อความที่ต่างกันแค่เลขข้อ ให้เหลือบรรทัดเดียว + จำนวนครั้ง"""
    groups = {}
    for m in messages:
        key = re.sub(r"\[\d+\]", "[*]", m)
        groups.setdefault(key, []).append(m)
    out = []
    for key, items in groups.items():
        out.append(items[0] if len(items) == 1 else f"{key}  (x{len(items)})")
    return out


def report(title, issues, count):
    errors = [m for s, m in issues if s == "ERROR"]
    warns = [m for s, m in issues if s == "WARN"]
    status = "[FAIL]" if errors else ("[WARN]" if warns else "[OK]")
    print(f"{status} {title}  ({count} questions, {len(errors)} errors, {len(warns)} warnings)")
    for m in collapse(errors)[:15]:
        print(f"    [ERROR] {m}")
    for m in collapse(warns)[:10]:
        print(f"    [WARN]  {m}")
    return len(errors), len(warns)


GOOD_FIXTURE = {
    "problem": "1. ผู้ป่วยชายอายุ 45 ปี มาด้วยอาการเจ็บหน้าอก ข้อใดถูกต้อง?",
    "img": "",
    "choices": "Choice A///Choice B///Choice C///Choice D///Choice E",
    "answer": "Choice A",
    "select": "",
    "explain": "คำตอบคือ Choice A เพราะ myocardial ischemia ทำให้เกิด ST elevation",
    "category": "RS_by AI_PHARM_Antiasthmatic drugs",
    "state": False,
}


def self_test():
    """พิสูจน์ว่าไม่ false-positive: fixture ที่ถูกต้องต้องผ่าน 0 issue"""
    ok = True
    issues = check_question(GOOD_FIXTURE, "fixture")
    if issues:
        ok = False
        print("[FAIL] self-test: fixture ที่ถูกต้องกลับถูกจับผิด")
        for s, m in issues:
            print(f"    [{s}] {m}")
    else:
        print("[OK] self-test: fixture ถูกต้อง -> 0 issues")

    bad_cases = {
        "4 choices": {"choices": "A///B///C///D", "answer": "A"},
        "answer mismatch": {"answer": "Choice Z"},
        "state string": {"state": "false"},
        "doubled separator": {"category": "CONCEPT_by AI_RADIO_RS_by AI_RADIO_Topic"},
        "underscore separator": {"category": "RS_by_AI_PHARM_Antiasthmatic_drugs"},
        "select not empty": {"select": "A"},
        "bad img": {"img": "images/page_001.png"},
    }
    for name, patch in bad_cases.items():
        q = dict(GOOD_FIXTURE, **patch)
        if not any(s == "ERROR" for s, _ in check_question(q, "fixture")):
            ok = False
            print(f"[FAIL] self-test: ไม่จับ error กรณี '{name}'")
    if ok:
        print(f"[OK] self-test: จับ error ครบทั้ง {len(bad_cases)} กรณีผิดรูปแบบ")

    # ตรวจระดับชุด: problem ซ้ำ + category ไม่ตรง key
    dup = check_question_list([GOOD_FIXTURE, dict(GOOD_FIXTURE)], "dup")
    if not any(s == "WARN" and "ซ้ำ" in m for s, m in dup):
        ok = False
        print("[FAIL] self-test: ไม่จับ problem ซ้ำ")
    mismatch = check_question_list([GOOD_FIXTURE], "key", key_must_match="OTHER_KEY")
    if not any(s == "ERROR" and "ไม่ตรงกับ key" in m for s, m in mismatch):
        ok = False
        print("[FAIL] self-test: ไม่จับ category ไม่ตรงกับ key")
    if not check_question_list([GOOD_FIXTURE], "ok", key_must_match=GOOD_FIXTURE["category"]):
        print("[OK] self-test: การตรวจระดับชุด (problem ซ้ำ / key mismatch) ทำงานถูกต้อง")
    else:
        ok = False
        print("[FAIL] self-test: การตรวจระดับชุดจับผิดทั้งที่ข้อมูลถูกต้อง")
    return ok


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run_self_test = "--self-test" in sys.argv

    if run_self_test and not self_test():
        return 1
    if run_self_test:
        print()

    if not OUTPUT_DIR.exists():
        print(f"[FAIL] ไม่พบโฟลเดอร์ output/ ที่ {OUTPUT_DIR}")
        return 1

    total_err = total_warn = total_q = 0
    checked = 0

    # 1) ไฟล์ผลลัพธ์ต่อรอบ (Convert + Generate มีรูปแบบเดียวกัน)
    # รวม output/require_img/<stem>/ ที่ organize_output.py ย้ายไป (ลึกอีก 1 ชั้น)
    run_files = sorted(set(OUTPUT_DIR.glob("*/*.json")) | set(OUTPUT_DIR.glob("require_img/*/*.json")))
    for path in run_files:
        if args and not any(a.lower() in path.parent.name.lower() for a in args):
            continue
        checked += 1
        try:
            issues, count = validate_run_file(path)
        except Exception as e:
            print(f"[FAIL] {path.parent.name}/{path.name}: อ่านไม่ได้ - {e}")
            total_err += 1
            continue
        e, w = report(f"{path.parent.name}/{path.name}", issues, count)
        total_err += e
        total_warn += w
        total_q += count

    # 2) ไฟล์รวมสะสม quizdata.js
    if QUIZDATA_PATH.exists() and not args:
        try:
            data = load_quizdata(QUIZDATA_PATH)
        except Exception as e:
            print(f"[FAIL] quizdata.js: อ่านไม่ได้ - {e}")
            total_err += 1
        else:
            checked += 1
            issues = []
            count = 0
            for key, questions in data.items():
                if not isinstance(questions, list):
                    issues.append(("ERROR", f"key {key!r}: ค่าไม่ใช่ list"))
                    continue
                count += len(questions)
                issues += check_question_list(questions, f"{key}", key_must_match=key)
            e, w = report("output/quizdata.js", issues, count)
            total_err += e
            total_warn += w

    print("-" * 70)
    if checked == 0:
        print("ไม่พบไฟล์ที่ตรงกับเงื่อนไข")
        return 0
    print(f"ตรวจ {checked} ไฟล์ | {total_q} คำถาม | {total_err} errors | {total_warn} warnings")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
