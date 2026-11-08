"""Module 5 - OCR (Tesseract) and text-layout analysis. Layout differences are weak, reviewable hints only."""
import numpy as np
import cv2

try:
    import pytesseract
    from pytesseract import Output
except Exception:  # pragma: no cover
    pytesseract = None


def ocr_available():
    if pytesseract is None:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _ink_and_bg(bgr, x, y, w, h):
    H, W = bgr.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    roi = bgr[y0:y1, x0:x1]
    if roi.size == 0:
        return None, None
    p = 3  # background = median of a thin ring just outside the word box (text itself is excluded)
    ring = bgr[max(y0 - p, 0):min(y1 + p, H), max(x0 - p, 0):min(x1 + p, W)].copy()
    mask = np.ones(ring.shape[:2], bool)
    mask[y0 - max(y0 - p, 0):y0 - max(y0 - p, 0) + (y1 - y0), x0 - max(x0 - p, 0):x0 - max(x0 - p, 0) + (x1 - x0)] = False
    px = roi.reshape(-1, 3).astype(np.float32)
    bg = np.median(ring[mask].astype(np.float32), axis=0) if mask.any() else np.median(px, axis=0)
    d = np.linalg.norm(px - bg, axis=1)
    k = max(int(len(d) * 0.1), 1)
    ink = px[np.argsort(d)[-k:]].mean(axis=0)
    return ink, bg


def run_text(bgr, ela_px=None, chroma=None, block=16):
    if not ocr_available():
        return {"status": "unavailable", "subscore": 0.0, "words": [], "anomalies": [], "text": "",
                "reason": "Tesseract OCR is not installed or not on PATH, so text analysis was skipped (not treated as suspicious)."}
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    data = pytesseract.image_to_data(rgb, output_type=Output.DICT, config="--psm 11")
    words = []
    for i, t in enumerate(data["text"]):
        t = (t or "").strip()
        try:
            conf = float(data["conf"][i])
        except Exception:
            conf = -1
        if not t or conf < 40:
            continue
        words.append({"text": t, "conf": round(conf, 1), "x": int(data["left"][i]), "y": int(data["top"][i]),
                      "w": int(data["width"][i]), "h": int(data["height"][i]),
                      "line_key": (data["block_num"][i], data["par_num"][i], data["line_num"][i])})
    if not words:
        return {"status": "ok", "subscore": 0.0, "words": [], "anomalies": [], "text": "", "word_count": 0,
                "avg_confidence": 0.0, "notes": ["No readable text detected."]}

    # group words into visual lines (tesseract line ids are unreliable with psm 11): cluster by vertical centre
    ws = sorted(words, key=lambda w: w["y"] + w["h"] / 2)
    lines, cur = [], [ws[0]]
    for w in ws[1:]:
        c = np.mean([a["y"] + a["h"] / 2 for a in cur])
        mh = np.median([a["h"] for a in cur])
        if abs((w["y"] + w["h"] / 2) - c) <= 0.6 * mh:
            cur.append(w)
        else:
            lines.append(cur); cur = [w]
    lines.append(cur)

    anomalies = []
    for li, ln in enumerate(lines):
        ln.sort(key=lambda w: w["x"])
        for w in ln:
            w["ink"], w["bg"] = _ink_and_bg(bgr, w["x"], w["y"], w["w"], w["h"])
        if len(ln) < 3:
            continue
        H = float(np.median([w["h"] for w in ln]))
        CY = float(np.median([w["y"] + w["h"] / 2 for w in ln]))
        bgs = np.array([w["bg"] for w in ln if w["bg"] is not None])
        inks = np.array([w["ink"] for w in ln if w["ink"] is not None])
        bg_med = np.median(bgs, axis=0) if len(bgs) else None
        ink_med = np.median(inks, axis=0) if len(inks) else None
        for w in ln:
            box = {"x": w["x"], "y": w["y"], "w": w["w"], "h": w["h"]}
            ratio = w["h"] / H if H else 1
            if len(w["text"]) >= 3 and (ratio > 1.6 or ratio < 0.55):
                anomalies.append({"type": "height", "word": w["text"], "bbox": box, "weight": 0.30, "line": li,
                                  "detail": f"Glyph height is {ratio:.2f}x the median of other words on the same line."})
            off = ((w["y"] + w["h"] / 2) - CY) / H if H else 0
            if abs(off) > 0.35 and len(w["text"]) >= 2:
                anomalies.append({"type": "baseline", "word": w["text"], "bbox": box, "weight": 0.30, "line": li,
                                  "detail": f"Vertical position is offset by {abs(off):.2f} text-heights from the rest of the line."})
            if bg_med is not None and w["bg"] is not None and np.linalg.norm(w["bg"] - bg_med) > 25:
                anomalies.append({"type": "background", "word": w["text"], "bbox": box, "weight": 0.35, "line": li,
                                  "detail": "Local background colour differs from neighbouring words on the same line (could be a highlight, badge or patched area)."})
    # word-level compression consistency: a word whose ELA level differs strongly from comparable words
    if ela_px is not None and chroma is not None:
        H, W = ela_px.shape
        rows = []
        for w in words:
            x0, y0, x1, y1 = max(w["x"], 0), max(w["y"], 0), min(w["x"] + w["w"], W), min(w["y"] + w["h"], H)
            if x1 - x0 < 4 or y1 - y0 < 4:
                continue
            ch = chroma[y0 // block:y1 // block + 1, x0 // block:x1 // block + 1].mean()
            rows.append((w, float(ela_px[y0:y1, x0:x1].mean()), int(ch > 4.0)))
        for g in (0, 1):
            grp = [r for r in rows if r[2] == g]
            if len(grp) < 8:
                continue
            v = np.array([r[1] for r in grp])
            med = float(np.median(v))
            scale = max(1.4826 * float(np.median(np.abs(v - med))), 0.3, 0.3 * med)
            for wd, m, _ in grp:
                z = (m - med) / scale
                if z >= 4.0 and m >= 0.6:
                    anomalies.append({"type": "compression", "word": wd["text"], "weight": 0.5, "line": -1,
                                      "bbox": {"x": wd["x"], "y": wd["y"], "w": wd["w"], "h": wd["h"]},
                                      "detail": f"Compression error level inside this word is {m:.1f} versus a typical {med:.1f} for comparable text (robust z = {z:.1f})."})
    # keep per-word strongest/aggregated
    agg = {}
    for a in anomalies:
        k = (a["bbox"]["x"], a["bbox"]["y"])
        if k in agg:
            agg[k]["weight"] = min(0.8, agg[k]["weight"] + a["weight"] * 0.7)
            agg[k]["detail"] += " " + a["detail"]
            agg[k]["type"] += "+" + a["type"]
        else:
            agg[k] = dict(a)
    anomalies = sorted(agg.values(), key=lambda a: -a["weight"])[:30]
    layout_w = sum(a["weight"] for a in anomalies if a["type"] != "compression")
    comp_w = sum(a["weight"] for a in anomalies if a["type"] == "compression")
    sub = float(np.clip(min(layout_w / 3.0, 0.5) + min(comp_w / 1.5, 0.6), 0, 1))  # layout alone never exceeds 0.5
    if len(words) < 6:
        sub = min(sub, 0.3)
    full_text = "\n".join(" ".join(w["text"] for w in ln) for ln in lines)
    out_words = [{k: w[k] for k in ("text", "conf", "x", "y", "w", "h")} for w in words]
    return {"status": "ok", "subscore": round(sub, 3), "word_count": len(words), "line_count": len(lines),
            "avg_confidence": round(float(np.mean([w["conf"] for w in words])), 1),
            "text": full_text, "words": out_words, "anomalies": anomalies,
            "notes": ["Font, colour or alignment differences are common in genuine screenshots (mixed fonts, badges, links); they are reported as hints only."]}
