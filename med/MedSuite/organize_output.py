"""
organize_output.py
------------------
Groups output/<stem>/ folders by whether they contain "require_img" questions.

After running:
  output/require_img/<stem>/   — folders with ≥1 require_img question
  output/<stem>/               — folders with no require_img questions

Also re-checks folders already inside output/require_img/ and moves them back
if their questions no longer contain require_img (e.g. after re-conversion).

Usage:
  python organize_output.py                  # all folders
  python organize_output.py MD47 PSYCHIAYRY  # filter by partial name
"""

import json
import shutil
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
REQUIRE_IMG_DIR = OUTPUT_DIR / "require_img"


def count_require_img(stem_dir: Path) -> tuple[int, int]:
    stem = stem_dir.name
    json_path = stem_dir / f"{stem}.json"
    if not json_path.exists():
        return 0, 0
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    questions = raw.get("questions", [])
    req = sum(1 for q in questions if q.get("img") == "require_img")
    return req, len(questions)


def collect_folders(filters: list[str]) -> list[Path]:
    """Return all stem folders from both output/ and output/require_img/."""
    folders = []
    for d in OUTPUT_DIR.iterdir():
        if d.is_dir() and d.name not in ("require_img",) and not d.name.startswith("."):
            folders.append(d)
    if REQUIRE_IMG_DIR.exists():
        for d in REQUIRE_IMG_DIR.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                folders.append(d)
    if filters:
        folders = [d for d in folders if any(f in d.name.upper() for f in filters)]
    return sorted(folders, key=lambda d: d.name)


def main():
    filters = [a.upper() for a in sys.argv[1:]]
    folders = collect_folders(filters)

    if not folders:
        print("No matching output folders found.")
        return

    REQUIRE_IMG_DIR.mkdir(exist_ok=True)

    moved_in  = []
    moved_out = []
    stayed    = []

    print(f"{'Folder':<35} {'Total':>6} {'require_img':>12}  Action")
    print("-" * 70)

    for folder in folders:
        req, total = count_require_img(folder)
        currently_inside = folder.parent == REQUIRE_IMG_DIR

        if req > 0 and not currently_inside:
            dest = REQUIRE_IMG_DIR / folder.name
            shutil.move(str(folder), str(dest))
            moved_in.append(folder.name)
            action = f"[MOVED] -> require_img/ ({req} need image)"
        elif req == 0 and currently_inside:
            dest = OUTPUT_DIR / folder.name
            shutil.move(str(folder), str(dest))
            moved_out.append(folder.name)
            action = "[MOVED] <- back to output/ (no longer needs images)"
        else:
            stayed.append(folder.name)
            loc = "require_img/" if currently_inside else "output/"
            action = f"stays in {loc}"

        print(f"{folder.name:<35} {total:>6} {req:>12}  {action}")

    print("-" * 70)
    print(f"Moved to require_img/: {len(moved_in)}  |  Moved back: {len(moved_out)}  |  Unchanged: {len(stayed)}")

    if moved_in:
        print()
        print("Folders needing image uploads:")
        for name in moved_in:
            print(f"  output/require_img/{name}/")


if __name__ == "__main__":
    main()
