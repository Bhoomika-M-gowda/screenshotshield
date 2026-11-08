"""Orchestrates all forensic modules and writes visualisations + structured results."""
import os
import time
import cv2
import numpy as np
from PIL import Image

from metadata import analyze_metadata
from ela import run_ela
from edges import run_edges
from noise_analysis import run_noise
from text_analysis import run_text
from region_detection import detect_regions, render_heatmap, render_regions
from risk_engine import assess
from explain import explain_all, LIMITATIONS, RECOMMENDATIONS


def pick_block(h, w):
    return int(np.clip(round(min(h, w) / 45 / 4) * 4, 12, 32))


def analyze_image(path, filename, out_dir, progress=lambda stage, pct: None):
    t0 = time.time()
    src = Image.open(path)
    src.load()
    rgb = src.convert("RGB")
    bgr = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    block = pick_block(h, w)
    timings = {}

    def step(name, pct, fn):
        progress(name, pct)
        t = time.time()
        r = fn()
        timings[name] = round(time.time() - t, 2)
        return r

    meta = step("Reading metadata", 8, lambda: analyze_metadata(path, filename, src))
    edges, edge_arr = step("Detecting edges", 20, lambda: run_edges(bgr, block))
    ela, ela_arr = step("Error level analysis", 38, lambda: run_ela(rgb, src.format, block, edge_arr["grad"], edge_arr["chroma"], src))
    noise, noise_arr = step("Analysing noise", 55, lambda: run_noise(bgr, block, edge_arr["mask"]))
    ocr = step("Reading text (OCR)", 72, lambda: run_text(bgr, ela_arr.get("px"), edge_arr["chroma"], block))
    regions, combined = step("Locating suspicious regions", 88, lambda: detect_regions(bgr, block, ela_arr, noise_arr, edge_arr, ocr, ela, noise))

    progress("Scoring and rendering", 94)
    reg_sub = 0.0
    if regions["regions"]:
        top = regions["regions"][0]
        reg_sub = min(1.0, top["score"] / 60.0) * (1.0 if len(top["indicators"]) >= 2 else 0.6)
    regions_part = {"status": "ok" if (ela["status"] != "unavailable" or noise["status"] != "unavailable" or ocr["status"] != "unavailable") else "unavailable",
                    "subscore": round(reg_sub, 3)}
    risk = assess({"metadata": meta, "ela": ela, "noise": noise, "text": ocr, "regions": regions_part})

    os.makedirs(out_dir, exist_ok=True)
    imgs = {"original": bgr, "edges": edge_arr["vis"], "heatmap": render_heatmap(bgr, combined, block),
            "regions": render_regions(bgr, regions["regions"])}
    if "vis" in ela_arr:
        imgs["ela"] = ela_arr["vis"]
    if "vis" in noise_arr:
        imgs["noise"] = noise_arr["vis"]
    for name, im in imgs.items():
        cv2.imwrite(os.path.join(out_dir, f"{name}.png"), im)

    result = {
        "filename": filename,
        "image": {"width": w, "height": h, "format": src.format, "mode": src.mode, "size_bytes": meta["file_size_bytes"], "block_size": block},
        "risk": risk, "metadata": meta, "ela": ela, "noise": noise, "edges": edges,
        "ocr": ocr, "regions": regions, "images_available": sorted(imgs.keys()),
        "limitations": LIMITATIONS, "recommendations": RECOMMENDATIONS, "timings": timings,
    }
    result["explanations"] = explain_all(result)
    result["duration_s"] = round(time.time() - t0, 2)
    progress("Complete", 100)
    return result
