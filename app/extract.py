"""Offline OOXML extraction; no guessed curriculum and no silent visual-content loss."""
from pathlib import Path, PurePosixPath
import hashlib
import posixpath
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main", "a": "http://schemas.openxmlformats.org/drawingml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships", "c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SAFE_IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_UNCOMPRESSED = 240 * 1024 * 1024


def relationships(archive, part):
    path = str(PurePosixPath(part).parent / "_rels" / (PurePosixPath(part).name + ".rels"))
    if path not in archive.namelist():
        return {}
    result = {}
    for rel in ET.fromstring(archive.read(path)).findall("{" + REL_NS + "}Relationship"):
        if rel.get("TargetMode") == "External":
            continue
        target = posixpath.normpath(posixpath.join(posixpath.dirname(part), rel.get("Target", "")))
        if not target.startswith("../") and not target.startswith("/"):
            result[rel.get("Id")] = {"target": target, "type": rel.get("Type", "")}
    return result


def paragraphs(root):
    return ["".join(p.itertext()).strip() if False else "".join(t.text or "" for t in p.findall(".//a:t", NS)).strip() for p in root.findall(".//a:p", NS)]


def extract_pptx(path, lesson_number, assets_dir):
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    prefix = f"zt-{lesson_number:02d}"
    out = Path(assets_dir) / digest[:16]
    slides, issues = [], []
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        if len(infos) > 12000 or sum(x.file_size for x in infos) > MAX_UNCOMPRESSED:
            raise ValueError("Presentation exceeds the safe archive expansion limit.")
        if any(x.flag_bits & 1 for x in infos):
            raise ValueError("Encrypted slides cannot be read; provide an unlocked copy.")
        root = ET.fromstring(z.read("ppt/presentation.xml"))
        rels = relationships(z, "ppt/presentation.xml")
        ordered = root.findall(".//p:sldIdLst/p:sldId", NS)
        if not ordered:
            raise ValueError("No slides found in the presentation order.")
        if len(ordered) > 500:
            raise ValueError("More than 500 slides; split the source for review.")
        for i, s in enumerate(ordered, 1):
            rel = rels.get(s.get("{" + NS["r"] + "}id"))
            if not rel:
                raise ValueError(f"Slide {i} has a broken presentation relationship.")
            part = rel["target"]
            slide_root = ET.fromstring(z.read(part))
            slide_rels = relationships(z, part)
            texts = [p for p in paragraphs(slide_root) if p]
            notes, visuals, charts, tables = [], [], [], []
            flags = ["Verify text order and visual layout against the original slide before approving."]
            for table in slide_root.findall(".//a:tbl", NS):
                tables.append([["\n".join(p for p in paragraphs(cell) if p) for cell in row.findall("a:tc", NS)] for row in table.findall("a:tr", NS)])
            for pic in slide_root.findall(".//p:pic", NS):
                blip = pic.find(".//a:blip", NS)
                props = pic.find(".//p:cNvPr", NS)
                target = slide_rels.get(blip.get("{" + NS["r"] + "}embed")) if blip is not None else None
                if not target or target["target"] not in z.namelist():
                    flags.append("Linked or missing visual; inspect the original file.")
                    continue
                media = target["target"]
                suffix = PurePosixPath(media).suffix.lower()
                item = {"originalPart": media, "alt": props.get("descr", "") if props is not None else "", "name": props.get("name", "") if props is not None else "", "url": None}
                if suffix in SAFE_IMAGES:
                    out.mkdir(parents=True, exist_ok=True)
                    name = hashlib.sha256(media.encode()).hexdigest()[:10] + suffix
                    (out / name).write_bytes(z.read(media))
                    item["url"] = "/assets/source/" + digest[:16] + "/" + name
                else:
                    flags.append(f"Visual format {suffix or 'unknown'} retained in original but not rendered; teacher review required.")
                visuals.append(item)
            for value in slide_rels.values():
                target = value["target"]
                if "notesSlide" in value["type"] and target in z.namelist():
                    notes.extend(p for p in paragraphs(ET.fromstring(z.read(target))) if p)
                if value["type"].endswith("/chart") and target in z.namelist():
                    chart = ET.fromstring(z.read(target))
                    charts.append({"part": target, "text": [t.text or "" for t in chart.findall(".//a:t", NS)], "cachedValues": [v.text or "" for v in chart.findall(".//c:v", NS)]})
                    flags.append("Chart values extracted; verify series, axes, labels and units in the original.")
                if "audio" in value["type"] or "video" in value["type"]:
                    flags.append("Embedded media retained in the original; playback/transcription is not implemented.")
            if visuals:
                flags.append("Images may contain text, maps or cultural information. No OCR or visual interpretation has been assumed.")
            if not texts:
                flags.append("No selectable text: image-only or empty slide. Teacher transcription required; do not infer content.")
            if slide_root.find(".//p:graphicFrame", NS) is not None:
                flags.append("Check tables, diagrams and SmartArt in the original; text extraction may not preserve relationships.")
            slides.append({"id": f"{prefix}-slide-{i:03d}", "number": i, "fileHash": digest, "originalPart": part, "text": "\n".join(texts), "notes": "\n".join(notes), "tables": tables, "charts": charts, "visuals": visuals, "issues": list(dict.fromkeys(flags)), "reviewStatus": "pending", "reviewNotes": "", "hidden": slide_root.get("show") == "0"})
    issues.append("Extraction is a draft, not a completed lesson adaptation. Every slide requires teacher verification, including visuals, exercises and answer keys.")
    return {"slides": slides, "issues": issues, "sha256": digest}


def find_soffice():
    return shutil.which("soffice") or shutil.which("libreoffice")


def extract_file(path, lesson_number, assets_dir):
    path = Path(path)
    if path.suffix.lower() == ".pptx":
        return extract_pptx(path, lesson_number, assets_dir)
    if path.suffix.lower() != ".ppt":
        raise ValueError("Only PPT and PPTX sources are accepted.")
    executable = find_soffice()
    if not executable:
        raise ValueError("Legacy .ppt needs LibreOffice/soffice. Convert to .pptx and upload again. The original is retained for review.")
    with tempfile.TemporaryDirectory(prefix="emmalyne-convert-") as td:
        folder = Path(td)
        profile = (folder / "profile").as_uri()
        result = subprocess.run([executable, "-env:UserInstallation=" + profile, "--headless", "--convert-to", "pptx", "--outdir", str(folder), str(path.resolve())], capture_output=True, timeout=90)
        converted = folder / (path.stem + ".pptx")
        if result.returncode or not converted.exists():
            raise ValueError("Legacy conversion failed. Convert the file to .pptx in PowerPoint and try again; original retained.")
        extracted = extract_pptx(converted, lesson_number, assets_dir)
        extracted["issues"].append("Converted from legacy PPT using LibreOffice. Verify formatting and all content against the original PPT.")
        extracted["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return extracted
