"""Module 3 - Local noise consistency (OpenCV)."""
import numpy as np
import cv2
from utils import block_sum, robust_z, cluster_score, norm_to_u8


def run_noise(bgr, block, edge_mask):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    resid = np.abs(gray.astype(np.float32) - cv2.medianBlur(gray, 3).astype(np.float32))
    near_edge = cv2.dilate((edge_mask > 0).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    ok = (~near_edge).astype(np.float64)
    cnt = block_sum(ok, block)
    full = block_sum(np.ones_like(ok), block)
    noise = block_sum(resid * ok, block) / np.maximum(cnt, 1)
    valid = (cnt / np.maximum(full, 1)) >= 0.35
    if valid.sum() < 12:
        return {"status": "unavailable", "subscore": 0.0, "reason": "Too little edge-free image area to estimate local noise reliably."}, {}
    z, st = robust_z(noise, valid, floor=0.25)
    zabs = np.abs(z)
    cs = cluster_score(zabs, valid)
    vis = cv2.applyColorMap(norm_to_u8(np.where(valid, noise, 0), 0, max(float(np.percentile(noise[valid], 99.5)), 1.0)), cv2.COLORMAP_VIRIDIS)
    vis = cv2.resize(vis, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_NEAREST)
    nv = cv2.resize((~valid).astype(np.uint8), (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    vis[nv] = (vis[nv] * 0.25).astype(np.uint8)  # dim blocks that could not be tested
    res = {"status": "ok", "median_noise": round(st["median"], 3), "noise_scale": round(st["scale"], 3),
           "testable_blocks": int(valid.sum()), "total_blocks": int(valid.size),
           "notes": (["Many blocks were excluded because they are dominated by edges/text."] if valid.mean() < 0.5 else []), **cs}
    return res, {"vis": vis, "z": z, "valid": valid}
