"""Transparent rule-based risk engine. The score is a REVIEW-PRIORITY HEURISTIC, not a probability of forgery."""

COMPONENTS = [
    ("metadata", "Metadata", 10),
    ("ela", "Compression (ELA)", 25),
    ("noise", "Noise consistency", 20),
    ("text", "Text layout (OCR)", 20),
    ("regions", "Region consensus", 25),
]
LOW_MAX, MED_MAX = 30, 60


def assess(parts):
    """parts: dict id -> {status, subscore}. Unavailable checks are excluded, never counted as suspicious."""
    comps, total_w, acc = [], 0.0, 0.0
    for cid, name, wt in COMPONENTS:
        p = parts.get(cid, {"status": "unavailable", "subscore": 0.0})
        avail = p.get("status") != "unavailable"
        sub = float(p.get("subscore", 0.0)) if avail else 0.0
        comps.append({"id": cid, "name": name, "weight": wt, "status": p.get("status", "unavailable"),
                      "subscore": round(sub, 3), "points": round(sub * wt, 1) if avail else None})
        if avail:
            total_w += wt
            acc += sub * wt
    raw = 100.0 * acc / total_w if total_w else 0.0
    agreeing = sum(1 for c in comps if c["status"] != "unavailable" and c["subscore"] >= 0.4)
    capped = False
    score = raw
    if agreeing < 2 and score > MED_MAX - 1:
        score, capped = MED_MAX - 1, True  # High priority requires at least two independent indicators
    score = int(round(score))
    cat = "Low" if score < LOW_MAX else ("Medium" if score < MED_MAX else "High")
    return {
        "score": score, "category": cat, "raw_score": round(raw, 1), "capped": capped,
        "agreeing_indicators": agreeing, "available_weight": total_w, "components": comps,
        "formula": "score = 100 x sum(weight_i x subscore_i) / sum(weight_i of available checks). Unavailable checks are removed from both sums. "
                   "A score of 60+ (High) requires at least two components with subscore >= 0.4.",
        "thresholds": {"low": f"< {LOW_MAX}", "medium": f"{LOW_MAX}-{MED_MAX - 1}", "high": f">= {MED_MAX}"},
        "disclaimer": "This is a heuristic review-priority indicator. It is NOT a statistically validated probability that the image is forged or genuine.",
    }
