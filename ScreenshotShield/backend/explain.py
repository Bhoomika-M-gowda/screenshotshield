"""Template-based explanation engine. Every sentence is generated from measured values; nothing is invented."""


def explain_all(r):
    ex, risk = [], r["risk"]
    ela, noise, txt, meta = r["ela"], r["noise"], r["ocr"], r["metadata"]

    ex.append({"module": "Overall", "level": risk["category"].lower(),
               "text": f"Review priority: {risk['category']} (indicator {risk['score']}/100, based on {sum(1 for c in risk['components'] if c['status'] != 'unavailable')} of {len(risk['components'])} available checks). "
                       "This is a heuristic that tells you where to look first; it does not prove that the image is genuine or edited."
                       + (" The score was capped below High because fewer than two independent indicators agreed." if risk["capped"] else "")})
    for f in meta["findings"]:
        if f["severity"] in ("warning", "notice"):
            ex.append({"module": "Metadata", "level": "medium" if f["severity"] == "warning" else "low", "text": f["text"]})
    if not meta["has_exif"]:
        ex.append({"module": "Metadata", "level": "info", "text": "No EXIF metadata is available. This is inconclusive: screenshots and files forwarded through messaging apps normally have none."})

    if ela["status"] == "unavailable":
        ex.append({"module": "ELA", "level": "info", "text": ela["reason"]})
    else:
        if ela["n_clusters"] and not ela["diffuse"]:
            c = ela["clusters"][0]
            ex.append({"module": "ELA", "level": "medium" if ela["subscore"] >= 0.4 else "low",
                       "text": f"{ela['n_clusters']} localized area(s) show an unusual compression error level compared with similar image structure (strongest deviation z = {c['peak_z']:.1f}, {c['blocks']} block(s)). "
                               "This may indicate that the area was processed or saved differently from its surroundings. However, resizing, re-saving and normal image compression can produce similar patterns."})
        elif ela["diffuse"]:
            ex.append({"module": "ELA", "level": "info", "text": "Compression differences are spread across much of the image rather than concentrated in one area. This usually reflects uniform or repeated compression and is not treated as localized evidence."})
        else:
            ex.append({"module": "ELA", "level": "info", "text": "No localized compression anomalies were found. ELA can miss edits that were saved at the same quality as the rest of the image."})
        for n in ela.get("notes", []):
            ex.append({"module": "ELA", "level": "info", "text": n})
    if noise["status"] == "unavailable":
        ex.append({"module": "Noise", "level": "info", "text": noise["reason"]})
    else:
        if noise["n_clusters"] and not noise["diffuse"]:
            c = noise["clusters"][0]
            ex.append({"module": "Noise", "level": "medium" if noise["subscore"] >= 0.4 else "low",
                       "text": f"{noise['n_clusters']} area(s) have a local noise level that differs from the rest of the image (strongest z = {c['peak_z']:.1f}). Content pasted from another source often carries a different noise signature, but graphics, photos and gradients inside a screenshot can also differ naturally."})
        else:
            ex.append({"module": "Noise", "level": "info", "text": f"Local noise was consistent across the {noise['testable_blocks']} testable blocks."})
    if txt["status"] == "unavailable":
        ex.append({"module": "OCR", "level": "info", "text": txt["reason"]})
    else:
        ex.append({"module": "OCR", "level": "info", "text": f"{txt.get('word_count', 0)} word(s) recognised (average confidence {txt.get('avg_confidence', 0)}%)."})
        for a in txt.get("anomalies", [])[:5]:
            ex.append({"module": "OCR", "level": "low", "text": f"Word '{a['word']}' at ({a['bbox']['x']},{a['bbox']['y']}): {a['detail']} Different fonts or alignment do not by themselves indicate manipulation."})
    for reg in r["regions"]["regions"]:
        names = ", ".join(i["name"] for i in reg["indicators"])
        b = reg["bbox"]
        reg["explanation"] = (f"Region #{reg['id']} at x={b['x']}, y={b['y']}, {b['w']}x{b['h']} px was flagged by {len(reg['indicators'])} indicator(s): {names} "
                              f"({reg['confidence']} confidence). " + " ".join(i["detail"] for i in reg["indicators"])
                              + " Inspect this area manually; similar patterns can arise from resizing or normal compression.")
    if r["regions"]["ignored"]:
        ex.append({"module": "Regions", "level": "info", "text": "The following signals were excluded from region highlighting because they were spread across the whole image: " + ", ".join(r["regions"]["ignored"]) + "."})
    if not r["regions"]["regions"]:
        ex.append({"module": "Regions", "level": "info", "text": "No area met the evidence threshold, so nothing is highlighted. This does not rule out manipulation."})
    return ex


LIMITATIONS = [
    "The risk indicator is a transparent heuristic, not a statistically validated probability of forgery.",
    "ELA only works on JPEG files and is unreliable on low-quality, resized or repeatedly compressed images; it can produce false positives.",
    "Edits that were exported at the same quality as the original, or whole-image recompression after editing, can hide traces (false negatives).",
    "Screenshots routinely lack EXIF metadata; missing metadata is inconclusive.",
    "OCR can misread text, and font/alignment differences are common in genuine screenshots.",
    "Highlighted regions use a coarse block grid; they show where to look, not the exact edited pixels.",
    "Fully synthetic or carefully re-rendered screenshots (e.g. rebuilt in HTML) leave no pixel-level traces and cannot be detected by these methods.",
]
RECOMMENDATIONS = [
    "Review each highlighted region manually at full size against the original image evidence.",
    "Ask the sender for the original file, or verify the transaction directly with the bank, payment provider or platform.",
    "Cross-check transaction IDs, amounts, dates and account details against an official statement.",
    "Do not make a decision based on this tool alone.",
]
