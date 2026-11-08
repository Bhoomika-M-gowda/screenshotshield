"""Module 1 - Metadata analysis (Pillow). Missing metadata is INCONCLUSIVE, never proof."""
import os
from datetime import datetime
from PIL import ExifTags

EDITOR_KEYWORDS = ["photoshop", "adobe", "gimp", "canva", "pixlr", "snapseed", "lightroom", "affinity",
                   "paint.net", "photopea", "picsart", "fotor", "acdsee", "krita", "inkscape", "illustrator"]
EXT_FORMAT = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def _clean(v):
    if isinstance(v, bytes):
        try:
            v = v.decode("utf-8", "ignore")
        except Exception:
            return f"<{len(v)} bytes>"
    return str(v).strip("\x00 ")[:120]


def _parse_dt(s):
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:19], fmt)
        except Exception:
            pass
    return None


def analyze_metadata(path, filename, img):
    findings, exif_out, subs = [], {}, [0.0]
    fmt = img.format
    ext = os.path.splitext(filename)[1].lower()
    exif = img.getexif()
    tags = {}
    for k, v in exif.items():
        tags[ExifTags.TAGS.get(k, str(k))] = v
    try:
        for k, v in exif.get_ifd(0x8769).items():
            tags[ExifTags.TAGS.get(k, str(k))] = v
    except Exception:
        pass
    gps_present = bool(exif.get(0x8825))
    for k, v in tags.items():
        if k in ("MakerNote", "UserComment", "PrintImageMatching", "ComponentsConfiguration", "ExifVersion"):
            continue
        exif_out[k] = _clean(v)
        if len(exif_out) >= 40:
            break

    software = _clean(tags.get("Software") or img.info.get("Software") or "")
    if not tags and not software:
        findings.append({"severity": "info", "text": "No EXIF metadata found. Screenshots, messaging apps and social platforms routinely strip metadata, so this is inconclusive."})
    else:
        findings.append({"severity": "info", "text": f"{len(tags)} EXIF field(s) present."})
    if gps_present:
        findings.append({"severity": "info", "text": "GPS data is embedded in the file (coordinates are intentionally not displayed or stored in the report)."})
    if software:
        hit = [k for k in EDITOR_KEYWORDS if k in software.lower()]
        if hit:
            findings.append({"severity": "warning", "text": f"Software tag '{software}' names an image editor. The file was saved by editing software at some point, which is not proof of tampering but warrants review."})
            subs.append(0.6)
        else:
            findings.append({"severity": "info", "text": f"Software tag: '{software}'."})
    dt_o, dt_m = _parse_dt(_clean(tags.get("DateTimeOriginal", ""))), _parse_dt(_clean(tags.get("DateTime", "")))
    if dt_o and dt_m and abs((dt_m - dt_o).total_seconds()) > 60:
        findings.append({"severity": "notice", "text": f"Modification time ({dt_m}) differs from capture time ({dt_o}). Files are legitimately re-saved, so this is only a weak indicator."})
        subs.append(0.3)
    if ext in EXT_FORMAT and fmt and EXT_FORMAT[ext] != fmt:
        findings.append({"severity": "notice", "text": f"File extension '{ext}' does not match the real image format ({fmt}). This can happen when files are renamed or converted."})
        subs.append(0.2)
    if img.info.get("icc_profile"):
        findings.append({"severity": "info", "text": "An embedded ICC colour profile is present."})
    has_flag = any(f["severity"] in ("warning", "notice") for f in findings)
    return {
        "status": "ok" if (has_flag or tags) else "inconclusive",
        "width": img.width, "height": img.height, "format": fmt, "mode": img.mode,
        "file_size_bytes": os.path.getsize(path),
        "has_exif": bool(tags), "software": software or None, "gps_present": gps_present,
        "exif": exif_out, "findings": findings, "subscore": round(max(subs), 3),
    }
