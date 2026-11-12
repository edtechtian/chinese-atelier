#!/usr/bin/env python3
"""Inventory and extract actual files. Never auto-publish inferred lesson content."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.storage import Store
from app.extract import extract_file


def import_folder(folder, store):
    results = []
    for original in sorted(Path(folder).rglob("*")):
        if not original.is_file() or original.suffix.lower() not in {".ppt", ".pptx"}:
            continue
        match = re.search(r"第\s*(\d+)\s*课", original.name)
        number = int(match[1]) if match else None
        sha = hashlib.sha256(original.read_bytes()).hexdigest()
        previous = next((f for f in store.curriculum["fileInventory"] if f["sha256"] == sha), None)
        if previous:
            results.append({"file": original.name, "status": "already_imported", "lesson": previous["lessonNumber"]})
            continue
        record = {"id": "file-" + sha[:20], "filename": original.name, "sha256": sha, "bytes": original.stat().st_size, "lessonNumber": number, "status": "unassigned", "issues": [], "importedAt": datetime.now(timezone.utc).isoformat()}
        if number not in range(1, 21):
            record["issues"].append("Cannot determine lesson 1–20 from filename. Teacher must assign the source.")
        else:
            lesson = store.curriculum["lessons"][number - 1]
            if lesson["sourceSlides"]:
                record["status"] = "duplicate_lesson"
                record["issues"].append("Another file is assigned to this lesson; retained in inventory without replacing it.")
            else:
                destination = ROOT / "sources" / (sha[:16] + original.suffix.lower())
                shutil.copy2(original, destination)
                record["storedName"] = destination.name
                try:
                    extracted = extract_file(destination, number, ROOT / "public/assets/source")
                    lesson["sourceSlides"] = extracted["slides"]
                    lesson["sourceRefs"] = [s["id"] for s in extracted["slides"]]
                    title = re.sub(r"^第\s*\d+\s*课\s*", "", original.stem).replace("PPTX", "").strip()
                    lesson.update({"title": title, "originalTitle": title, "status": "review", "approval": "pending_review"})
                    lesson["processing"] = {"status": "extracted", "files": [record["id"]], "issues": extracted["issues"], "inspectedAt": datetime.now(timezone.utc).isoformat()}
                    record.update({"status": "extracted", "slides": len(extracted["slides"]), "issues": extracted["issues"]})
                except Exception as e:
                    record.update({"status": "unreadable", "issues": [str(e)]})
                    lesson["status"] = "unreadable"
                    lesson["processing"] = {"status": "unreadable", "files": [record["id"]], "issues": [str(e)]}
        store.curriculum["fileInventory"].append(record)
        store.save_curriculum()
        results.append({"file": original.name, "lesson": number, "status": record["status"], "slides": record.get("slides", 0), "issues": record["issues"] if record["status"] != "extracted" else []})
    return results


def reports(store):
    rows = ["# Source inventory", "", "Original course: 《走遍泰国》 — Prince of Songkla University Phuket Confucius Institute.", "", "Extraction does not imply teacher approval. Text order, images, maps, charts, cultural claims and answer keys require verification. Supplementary activities are separately identified.", "", "| Lesson | Original file | Slides | Status |", "|---|---|---:|---|"]
    for lesson in store.curriculum["lessons"]:
        files = [f["filename"] for f in store.curriculum["fileInventory"] if f.get("id") in lesson["processing"]["files"]]
        rows.append(f"| {lesson['number']:02d} | {', '.join(files) or 'Not supplied'} | {len(lesson['sourceSlides'])} | {lesson['processing']['status']} |")
    (ROOT / "docs/source-inventory.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    for lesson in store.curriculum["lessons"]:
        out = [f"# {lesson['number']:02d} {lesson['title']}"]
        for s in lesson["sourceSlides"]:
            out += [f"\n## Slide {s['number']} [{s['id']}]", s["text"], "Notes: " + s["notes"] if s["notes"] else "", "Visuals: " + str(len(s["visuals"])), "Charts: " + str(len(s["charts"]))]
        (ROOT / "data" / f"source-{lesson['number']:02d}.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    store = Store(ROOT)
    print(json.dumps(import_folder(args.folder, store), ensure_ascii=False, indent=2))
    reports(store)
