"""Module 4 - Canny edge detection and block edge-density analysis."""
import numpy as np
import cv2
from utils import block_mean, robust_z, cluster_score


def run_edges(bgr, block):
    gray = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), (3, 3), 0)
    edges = cv2.Canny(gray, 60, 160)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0); gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    grad = block_mean(np.sqrt(gx * gx + gy * gy), block)
    ycc = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb).astype(np.float32)
    cg = np.zeros(gray.shape, np.float32)
    for ch in (1, 2):
        cx = cv2.Sobel(ycc[..., ch], cv2.CV_32F, 1, 0); cy = cv2.Sobel(ycc[..., ch], cv2.CV_32F, 0, 1)
        cg = np.maximum(cg, np.sqrt(cx * cx + cy * cy))
    chroma = block_mean(cg, block)
    density = block_mean((edges > 0).astype(np.float64), block)
    valid = density > 0.005
    z, st = robust_z(density, valid, floor=0.03)
    z = np.maximum(z, 0)  # only abnormally dense boundaries are interesting
    cs = cluster_score(z, valid, thresh=5.0)
    vis = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    vis[edges > 0] = (255, 160, 60)
    res = {"status": "ok", "edge_pixel_fraction": round(float((edges > 0).mean()), 4),
           "block_density_median": round(float(np.median(density[valid])), 4) if valid.any() else 0.0, **cs}
    res.pop("subscore", None)  # edges are a supporting signal for region detection only
    return res, {"vis": vis, "mask": edges, "density": density, "grad": grad, "chroma": chroma, "z": z, "valid": valid}
