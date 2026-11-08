"""Module 2 - Error Level Analysis (JPEG only)."""
import io
import numpy as np
import cv2
from PIL import Image
from utils import block_mean, binned_residual_z, cluster_score, norm_to_u8

RECOMPRESS_Q = 90


def estimate_jpeg_quality(img):
    """Best-matching libjpeg quality from the luminance quantisation table (None if unavailable)."""
    q = getattr(img, "quantization", None)
    if not q or 0 not in q:
        return None, False
    tbl = list(q[0])
    best = None
    for quality in range(1, 101):
        buf = io.BytesIO()
        Image.new("L", (8, 8)).save(buf, "JPEG", quality=quality)
        buf.seek(0)
        ref = list(Image.open(buf).quantization[0])
        d = sum(abs(a - b) for a, b in zip(tbl, ref))
        if best is None or d < best[0]:
            best = (d, quality)
    return best[1], best[0] == 0


def run_ela(img_rgb, fmt, block, grad, chroma, source_img=None):
    if fmt != "JPEG":
        return {"status": "unavailable", "subscore": 0.0,
                "reason": f"ELA is only meaningful for JPEG files; this file is {fmt}. PNG/WebP are not re-compressed in a comparable way, so the check was skipped (not treated as suspicious)."}, {}
    est_q, exact = estimate_jpeg_quality(source_img) if source_img is not None else (None, False)
    buf = io.BytesIO()
    img_rgb.save(buf, "JPEG", quality=RECOMPRESS_Q)
    buf.seek(0)
    re = np.asarray(Image.open(buf).convert("RGB"), dtype=np.int16)
    orig = np.asarray(img_rgb, dtype=np.int16)
    ela = np.abs(orig - re).max(axis=2).astype(np.float64)

    bm = block_mean(ela, block)
    valid = np.ones(bm.shape, bool)
    group = (chroma > 4.0).astype(int)  # coloured edges behave differently from luminance-only edges (chroma subsampling)
    z, fit = binned_residual_z(bm, grad, valid, floor=0.3, group=group)
    if z is None:
        return {"status": "unavailable", "subscore": 0.0, "reason": "Image too small for a reliable block analysis."}, {}
    zabs = np.abs(z)
    cs = cluster_score(zabs, valid)

    vis = norm_to_u8(ela, 0, max(float(np.percentile(ela, 99.7)), 3.0))
    vis = cv2.applyColorMap(vis, cv2.COLORMAP_INFERNO)
    low_q = est_q is not None and est_q < 70
    notes = []
    if low_q:
        notes.append(f"The file appears to be saved at low JPEG quality (~{est_q}); heavy compression makes ELA noisy and less reliable.")
    if cs["diffuse"]:
        notes.append("Differences are spread over a large part of the image (diffuse), which is typical of uniform or repeated compression rather than a localized edit.")
    res = {
        "status": "ok", "recompress_quality": RECOMPRESS_Q,
        "estimated_quality": est_q, "standard_tables": exact,
        "mean_ela": round(float(ela.mean()), 3), "p99_ela": round(float(np.percentile(ela, 99)), 3),
        "max_ela": int(ela.max()), "fit": fit, "notes": notes, **cs,
    }
    if low_q:
        res["subscore"] = round(min(res["subscore"], 0.4), 3)
    return res, {"vis": vis, "z": z, "valid": valid, "px": ela.astype(np.float32)}
