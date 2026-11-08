"""Shared helpers: block-grid maths, robust statistics, cluster scoring."""
import numpy as np
import cv2


def n_blocks(h, w, b):
    return -(-h // b), -(-w // b)


def block_sum(a, b):
    h, w = a.shape[:2]
    nh, nw = n_blocks(h, w, b)
    pad = np.zeros((nh * b, nw * b), dtype=np.float64)
    pad[:h, :w] = a
    return pad.reshape(nh, b, nw, b).sum(axis=(1, 3))


def block_mean(a, b):
    ones = np.ones(a.shape[:2], dtype=np.float64)
    return block_sum(a, b) / np.maximum(block_sum(ones, b), 1)


def robust_z(values, valid, floor):
    """(v - median) / max(1.4826*MAD, floor) over valid cells; invalid -> 0."""
    z = np.zeros_like(values, dtype=np.float64)
    v = values[valid]
    if v.size < 8:
        return z, None
    med = float(np.median(v))
    mad = 1.4826 * float(np.median(np.abs(v - med)))
    scale = max(mad, floor)
    z[valid] = (values[valid] - med) / scale
    return z, {"median": med, "scale": scale}


def structure_residual_z(y, x, valid, floor):
    """Robust linear fit y ~ a*x + b (x = local edge density); returns z of residuals.
    Removes the expected dependence of ELA/noise on image structure (text, borders)."""
    yv, xv = y[valid], x[valid]
    if yv.size < 12:
        return None, None
    keep = np.ones(yv.size, bool)
    a, b, med, s = 0.0, float(np.median(yv)), 0.0, floor
    for _ in range(3):
        if keep.sum() < 8:
            break
        if np.ptp(xv[keep]) > 1e-6:
            a, b = np.polyfit(xv[keep], yv[keep], 1)
        else:
            a, b = 0.0, float(np.median(yv[keep]))
        r = yv - (a * xv + b)
        med = float(np.median(r[keep]))
        mad = 1.4826 * float(np.median(np.abs(r[keep] - med)))
        s = max(mad, floor)
        keep = np.abs(r - med) < 3.5 * s
    z = (y - (a * x + b) - med) / s
    z[~valid] = 0
    return z, {"slope": float(a), "intercept": float(b), "scale": float(s)}


def cluster_score(z_abs, valid, thresh=4.5, diffuse_frac=0.25):
    """Summarise localized outliers in a block map of |z| values."""
    flagged = (z_abs >= thresh) & valid
    n_valid = max(int(valid.sum()), 1)
    frac = float(flagged.sum()) / n_valid
    n, lab, stats, _ = cv2.connectedComponentsWithStats(flagged.astype(np.uint8), connectivity=8)
    clusters = []
    for i in range(1, n):
        m = lab == i
        clusters.append({"blocks": int(m.sum()), "peak_z": float(z_abs[m].max())})
    clusters.sort(key=lambda c: (c["peak_z"] * min(c["blocks"], 3)), reverse=True)
    diffuse = frac > diffuse_frac
    sub = 0.0
    if clusters:
        best = clusters[0]
        base = float(np.clip((best["peak_z"] - 4.0) / 8.0, 0, 1))
        size_f = 1.0 if best["blocks"] >= 3 else (0.6 if best["blocks"] == 2 else 0.35)
        sub = min(1.0, base * size_f + 0.05 * min(len(clusters) - 1, 3))
        if diffuse:
            sub = min(sub, 0.25)
    return {
        "flagged_blocks": int(flagged.sum()),
        "flagged_fraction": round(frac, 4),
        "clusters": clusters[:8],
        "n_clusters": len(clusters),
        "max_abs_z": float(z_abs[valid].max()) if valid.any() else 0.0,
        "diffuse": bool(diffuse),
        "subscore": round(float(sub), 3),
    }


def norm_to_u8(a, lo=None, hi=None):
    lo = float(np.min(a)) if lo is None else lo
    hi = float(np.max(a)) if hi is None else hi
    if hi - lo < 1e-9:
        return np.zeros(a.shape, np.uint8)
    return np.clip((a - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)


def binned_residual_z(y, x, valid, floor, max_bins=6, min_per_bin=15, rel_floor=0.15, group=None):
    """Peer comparison: group blocks by local structure x (gradient strength) into quantile bins and
    compute a robust z of y inside each bin. A block is only judged against blocks that look similar."""
    if group is not None:
        # structure groups (e.g. coloured-edge vs luminance-only blocks) are analysed independently
        z = np.zeros_like(y, dtype=np.float64)
        infos = []
        for g in np.unique(group[valid]):
            m = valid & (group == g)
            if m.sum() < 12:
                continue
            zg, ig = binned_residual_z(y, x, m, floor, max_bins, min_per_bin, rel_floor)
            if zg is not None:
                z[m] = zg[m]
                infos.append({"group": int(g), **ig})
        return z, {"groups": infos}
    yv, xv = y[valid], x[valid]
    if yv.size < 12:
        return None, None
    edges = np.unique(np.quantile(xv, np.linspace(0, 1, max_bins + 1)))
    if edges.size < 2:
        edges = np.array([xv.min(), xv.max() + 1e-9])
    edges[-1] += 1e-9
    idx = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(edges) - 2)
    nb = len(edges) - 1
    # merge sparse bins into the previous one
    remap = list(range(nb))
    for b in range(1, nb):
        if (idx[valid] == b).sum() < min_per_bin:
            remap[b] = remap[b - 1]
    idx = np.array(remap)[idx]
    z = np.zeros_like(y, dtype=np.float64)
    info = []
    for b in np.unique(idx[valid]):
        m = valid & (idx == b)
        v = y[m]
        med = float(np.median(v))
        mad = 1.4826 * float(np.median(np.abs(v - med)))
        scale = max(mad, floor, rel_floor * abs(med))
        z[m] = (y[m] - med) / scale
        info.append({"blocks": int(m.sum()), "median": round(med, 3), "scale": round(scale, 3)})
    return z, {"bins": info}
