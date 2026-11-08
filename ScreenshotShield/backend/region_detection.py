"""Module 6 - Suspicious region detection by combining independent signals on a block grid."""
import numpy as np
import cv2

WEIGHTS = {"ela": 0.35, "noise": 0.25, "text": 0.30, "edges": 0.10}
LABEL = {"ela": "Compression (ELA)", "noise": "Noise", "text": "Text layout", "edges": "Edge density"}
Z0 = {"ela": 3.5, "noise": 3.5, "edges": 4.0}
Z1 = {"ela": 9.0, "noise": 9.0, "edges": 10.0}


def _ev(z, k):
    return np.clip((np.abs(z) - Z0[k]) / (Z1[k] - Z0[k]), 0, 1)


def detect_regions(bgr, block, ela_arr, noise_arr, edge_arr, text_res, ela_res, noise_res, max_regions=6):
    h, w = bgr.shape[:2]
    nh, nw = -(-h // block), -(-w // block)
    ev, signed = {}, {}
    ignored = []
    for k, arr, res in (("ela", ela_arr, ela_res), ("noise", noise_arr, noise_res)):
        if arr and "z" in arr:
            if res.get("diffuse"):
                ignored.append(k)
                continue
            ev[k] = _ev(arr["z"], k)
            signed[k] = arr["z"]
    if edge_arr and "z" in edge_arr:
        ev["edges"] = _ev(edge_arr["z"], "edges")
        signed["edges"] = edge_arr["z"]
    if text_res.get("status") == "ok":
        tm = np.zeros((nh, nw))
        for a in text_res.get("anomalies", []):
            b = a["bbox"]
            y0, y1 = max(b["y"], 0) // block, min(b["y"] + b["h"], h - 1) // block
            x0, x1 = max(b["x"], 0) // block, min(b["x"] + b["w"], w - 1) // block
            tm[y0:y1 + 1, x0:x1 + 1] = np.maximum(tm[y0:y1 + 1, x0:x1 + 1], a["weight"])
        ev["text"] = np.clip(tm / 0.5, 0, 1)
    if not ev:
        return {"regions": [], "ignored": ignored}, np.zeros((nh, nw))
    wsum = sum(WEIGHTS[k] for k in ev)
    combined = sum(WEIGHTS[k] * ev[k] for k in ev) / wsum
    cand = np.zeros((nh, nw), bool)
    for k in ev:
        cand |= ev[k] >= 0.3
    grown = cv2.dilate(cand.astype(np.uint8), np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(grown, connectivity=8)
    regions = []
    for i in range(1, n):
        m = (lab == i) & cand
        if not m.any():
            continue
        peaks = {k: float(ev[k][m].max()) for k in ev}
        active = [k for k in ev if peaks[k] >= 0.3]
        nblocks = int(m.sum())
        strong = max(peaks.values())
        ok = len(active) >= 2 or (strong >= 0.5 and (active[0] == "text" or nblocks >= 2))
        if active == ["edges"]:
            ok = False  # edges alone never justify a region
        if not ok:
            continue
        ys, xs = np.where(m)
        x0, x1 = int(xs.min()) * block, min((int(xs.max()) + 1) * block, w)
        y0, y1 = int(ys.min()) * block, min((int(ys.max()) + 1) * block, h)
        score = int(round(100 * sum(WEIGHTS[k] * peaks[k] for k in ev) / wsum))
        conf = "high" if len(active) >= 3 else ("medium" if len(active) == 2 else "low")
        inds = []
        for k in active:
            if k == "text":
                words = [a for a in text_res["anomalies"] if x0 - block <= a["bbox"]["x"] <= x1 and y0 - block <= a["bbox"]["y"] <= y1]
                inds.append({"name": LABEL[k], "key": k, "strength": round(peaks[k], 2),
                             "detail": "; ".join(f"'{a['word']}': {a['detail']}" for a in words[:3]) or "Text-layout anomaly nearby."})
            else:
                zz = signed[k][m]
                zmax = float(zz[np.argmax(np.abs(zz))])
                d = {"ela": "ELA error level is {} than the image's typical level for this kind of structure (robust z = {:+.1f}).",
                     "noise": "Local noise is {} than the rest of the image (robust z = {:+.1f}).",
                     "edges": "Edge density is {} than typical (robust z = {:+.1f})."}[k]
                inds.append({"name": LABEL[k], "key": k, "strength": round(peaks[k], 2),
                             "detail": d.format("higher" if zmax > 0 else "lower", zmax)})
        regions.append({"bbox": {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}, "score": score,
                        "confidence": conf, "n_blocks": nblocks, "indicators": inds})
    regions.sort(key=lambda r: (-r["score"], -len(r["indicators"])))
    regions = regions[:max_regions]
    for i, r in enumerate(regions, 1):
        r["id"] = i
    return {"regions": regions, "ignored": ignored, "block_size": block}, combined


def render_heatmap(bgr, combined, block):
    h, w = bgr.shape[:2]
    heat = cv2.resize(combined.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    heat = cv2.GaussianBlur(heat, (0, 0), max(block / 2, 3))
    u8 = np.clip(heat / max(heat.max(), 0.35) * 255, 0, 255).astype(np.uint8)
    col = cv2.applyColorMap(u8, cv2.COLORMAP_JET)
    alpha = (np.clip(heat / 0.35, 0, 1) * 0.6)[..., None]
    alpha[heat < 0.03] = 0
    return (bgr * (1 - alpha) + col * alpha).astype(np.uint8)


def render_regions(bgr, regions):
    out = bgr.copy()
    th = max(2, round(min(bgr.shape[:2]) / 400))
    colors = {"high": (60, 60, 255), "medium": (0, 165, 255), "low": (255, 200, 60)}
    for r in regions:
        b = r["bbox"]
        c = colors[r["confidence"]]
        cv2.rectangle(out, (b["x"], b["y"]), (b["x"] + b["w"], b["y"] + b["h"]), c, th)
        lab = f"#{r['id']}"
        fs = max(0.5, min(bgr.shape[:2]) / 900)
        (tw, tht), _ = cv2.getTextSize(lab, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
        y = max(b["y"], tht + 6)
        cv2.rectangle(out, (b["x"], y - tht - 6), (b["x"] + tw + 8, y), c, -1)
        cv2.putText(out, lab, (b["x"] + 4, y - 4), cv2.FONT_HERSHEY_SIMPLEX, fs, (0, 0, 0), 2)
    return out
