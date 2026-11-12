"""Shared validation for teacher edits, imports and the command-line QA tool."""
import re

ID = re.compile(r"^[a-z][a-z0-9-]{1,79}$")
STATUSES = {"missing", "unreadable", "review", "draft", "available", "published"}
ORIGINS = {"textbook", "adaptation", "supplementary"}


def _validate_curriculum(data):
    errors = []
    if not isinstance(data, dict) or data.get("schemaVersion") != 1:
        return ["schemaVersion must be 1."]
    lessons = data.get("lessons", [])
    if not isinstance(lessons, list) or len(lessons) != 20:
        errors.append("Exactly 20 numbered textbook lesson records are required.")
    if [l.get("number") for l in lessons if isinstance(l, dict)] != list(range(1, 21)):
        errors.append("Textbook lesson numbers must be 1–20, in order, without gaps or duplicates.")
    ids = set()
    criteria = {c.get("id") for c in data.get("criteria", []) if isinstance(c, dict)}
    if not criteria:
        errors.append("Assessment criteria are required.")
    for lesson in lessons + data.get("supplementary", []):
        if not isinstance(lesson, dict):
            errors.append("Every lesson must be an object.")
            continue
        label = lesson.get("id", "unknown")
        def check_id(obj):
            value = obj.get("id", "")
            if not isinstance(value, str) or not ID.fullmatch(value):
                errors.append(f"{label}: invalid identifier {value!r}.")
            elif value in ids:
                errors.append(f"Duplicate identifier: {value}.")
            ids.add(value)
        check_id(lesson)
        if lesson.get("kind") not in {"textbook", "supplementary"}:
            errors.append(f"{label}: invalid lesson kind.")
        if lesson.get("status") not in STATUSES:
            errors.append(f"{label}: invalid status.")
        if not isinstance(lesson.get("title"), str) or not lesson["title"].strip():
            errors.append(f"{label}: title is required.")
        if lesson.get("origin") not in ORIGINS:
            errors.append(f"{label}: invalid origin.")
        slides = lesson.get("sourceSlides", [])
        slide_ids = {s.get("id") for s in slides if isinstance(s, dict)}
        if len(slide_ids) != len(slides):
            errors.append(f"{label}: duplicate slide identifiers.")
        def refs(obj):
            for ref in obj.get("sourceRefs", []):
                if ref not in slide_ids:
                    errors.append(f"{label}: broken source reference {ref!r}.")
            if lesson.get("kind") == "textbook" and obj.get("origin") in {"textbook", "adaptation"} and not obj.get("sourceRefs"):
                errors.append(f"{label}: textbook content and adaptations need slide references.")
        refs(lesson) if lesson.get("status") == "published" else None
        for slide in slides:
            if not isinstance(slide, dict) or not isinstance(slide.get("number"), int) or slide["number"] < 1:
                errors.append(f"{label}: slide numbers must be positive integers.")
                continue
            if not isinstance(slide.get("text"), str):
                errors.append(f"{label}: slide text must be a string.")
        for field in ["vocabulary", "readings", "patterns", "questions", "tasks", "culturalNotes"]:
            if not isinstance(lesson.get(field), list):
                errors.append(f"{label}: {field} must be an array.")
                continue
            for obj in lesson[field]:
                if not isinstance(obj, dict):
                    errors.append(f"{label}: {field} entries must be objects.")
                    continue
                check_id(obj)
                if obj.get("origin") not in ORIGINS:
                    errors.append(f"{label}/{obj.get('id')}: specify textbook, adaptation or supplementary origin.")
                refs(obj)
        for v in lesson.get("vocabulary", []):
            for key in ["chinese", "pinyin", "meaning", "example"]:
                if not isinstance(v.get(key), str) or not v[key].strip():
                    errors.append(f"{label}/{v.get('id')}: vocabulary {key} is required.")
        reading_ids = {r.get("id") for r in lesson.get("readings", [])}
        for r in lesson.get("readings", []):
            if not r.get("title") or not isinstance(r.get("body"), list) or not r["body"] or not all(isinstance(p, str) and p.strip() for p in r["body"]):
                errors.append(f"{label}: readings need a title and nonempty text paragraphs.")
        for p in lesson.get("patterns", []):
            if not p.get("title") or not p.get("explanation") or not isinstance(p.get("examples"), list) or not p["examples"]:
                errors.append(f"{label}: language patterns need title, explanation and examples.")
        for q in lesson.get("questions", []):
            if q.get("type") not in {"choice", "text"} or not q.get("prompt") or not q.get("explanation"):
                errors.append(f"{label}: questions need type, prompt and explanation.")
            if q.get("skill") not in criteria or q.get("layer") not in {"understand", "communicate", "apply"}:
                errors.append(f"{label}/{q.get('id')}: invalid skill or learning layer.")
            if q.get("readingId") and q["readingId"] not in reading_ids:
                errors.append(f"{label}/{q.get('id')}: broken reading reference.")
            if q.get("type") == "choice":
                options = q.get("options", [])
                option_ids = [o.get("id") for o in options if isinstance(o, dict)]
                if len(options) < 2 or len(option_ids) != len(set(option_ids)) or q.get("answer") not in option_ids or any(not o.get("text") for o in options):
                    errors.append(f"{label}/{q.get('id')}: invalid choice options or answer key.")
            elif q.get("type") == "text" and (not isinstance(q.get("acceptedAnswers"), list) or not q["acceptedAnswers"] or not all(isinstance(x, str) and x.strip() for x in q["acceptedAnswers"])):
                errors.append(f"{label}/{q.get('id')}: nonempty accepted answers required.")
        for t in lesson.get("tasks", []):
            if t.get("type") not in {"writing", "roleplay", "project"} or not t.get("prompt") or not t.get("title") or not t.get("model"):
                errors.append(f"{label}: tasks need type, title, prompt and a labeled model.")
            if not t.get("criteria") or not set(t["criteria"]).issubset(criteria):
                errors.append(f"{label}/{t.get('id')}: invalid assessment criteria.")
            if not isinstance(t.get("minCharacters"), int) or not 0 <= t["minCharacters"] <= 2000:
                errors.append(f"{label}: task character guidance must be 0–2000.")
        if lesson.get("kind") == "textbook" and lesson.get("status") == "published":
            if not lesson.get("originalTitle") or not slides or not lesson.get("objectives") or not lesson.get("goals") or not lesson.get("minutes"):
                errors.append(f"{label}: publishing needs original title, slides, objectives, goals and estimated time.")
            if lesson.get("approval") != "teacher_approved":
                errors.append(f"{label}: teacher approval required before publishing source curriculum.")
            if any(s.get("reviewStatus") != "verified" for s in slides):
                errors.append(f"{label}: every source slide must be verified before publishing.")
            if not lesson.get("readings") or not lesson.get("questions") or not lesson.get("tasks"):
                errors.append(f"{label}: publishing needs reading, formative questions and a communication task.")
            if lesson.get("processing", {}).get("status") in {"missing", "unreadable"}:
                errors.append(f"{label}: cannot publish missing or unreadable source content.")
    return errors


def validate_curriculum(data):
    """Reject malformed teacher edits without saving a model the UI cannot render."""
    try:
        errors = _validate_curriculum(data)
        for lesson in data.get("lessons", []) + data.get("supplementary", []):
            if lesson.get("adaptationVersion") != 2:
                continue
            label = lesson["id"]
            slides = {s["id"] for s in lesson["sourceSlides"]}
            def strings(value):
                return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)
            def source_refs(item):
                if not strings(item.get("sourceRefs")) or not set(item["sourceRefs"]).issubset(slides):
                    errors.append(label + ": teaching item needs valid source references.")
            p = lesson.get("pedagogy", {})
            if any(not isinstance(p.get(k), str) or not p[k].strip() for k in ["profile", "diagnostic", "multilingual", "reflection"]):
                errors.append(label + ": incomplete personalized teaching brief.")
            seq = p.get("sequence", [])
            if not isinstance(seq, list) or len(seq) != 3 or any(not x.get("stage") or not x.get("activity") or type(x.get("minutes")) != int or x["minutes"] <= 0 for x in seq):
                errors.append(label + ": three timed learning stages are required.")
            elif sum(x["minutes"] for x in seq) != lesson.get("minutes"):
                errors.append(label + ": teaching stage times must match lesson duration.")
            decisions = p.get("decisions", [])
            if {x.get("action") for x in decisions} != {"retain", "extend", "scaffold", "interactive"}:
                errors.append(label + ": all four source adaptation decisions are required.")
            for decision in decisions:
                source_refs(decision)
                if not decision.get("content"): errors.append(label + ": empty adaptation decision.")
            for reading in lesson["readings"]:
                if not isinstance(reading.get("discussion"), list) or not reading["discussion"]:
                    errors.append(label + ": reading needs source-specific discussion.")
                for discussion in reading.get("discussion", []):
                    if not discussion.get("prompt") or not discussion.get("guide"):
                        errors.append(label + ": discussion prompt and reasoning guide required.")
            for pattern in lesson["patterns"]:
                if not pattern.get("pitfall") or not pattern.get("application") or not strings(pattern.get("examples")):
                    errors.append(label + ": language pattern needs examples, distinction and application.")
            for v in lesson["vocabulary"]:
                if not isinstance(v.get("collocations"), list) or any(not isinstance(x, str) for x in v["collocations"]) or not isinstance(v.get("gloss"), dict):
                    errors.append(label + ": invalid vocabulary chunks or language glosses.")
            for t in lesson["tasks"]:
                if not strings(t.get("scaffold")) or not strings(t.get("successCriteria")) or not isinstance(t.get("challenge"), str) or not t["challenge"].strip():
                    errors.append(label + ": tasks need scaffolds, success criteria and an extension.")
            live = lesson.get("liveListening", {})
            source_refs(live)
            if not strings(live.get("instructions")) or not live.get("focus") or live.get("questionId") not in {q["id"] for q in lesson["questions"]}:
                errors.append(label + ": live listening needs instructions and a valid focus question.")
        return errors
    except (TypeError, AttributeError, KeyError, ValueError):
        return ["Invalid curriculum field type. Preserve the documented object, array, string and numeric fields."]
