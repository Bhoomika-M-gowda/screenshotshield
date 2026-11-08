"""PDF forensic report (ReportLab)."""
import os
from datetime import datetime
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, KeepTogether
from PIL import Image as PILImage

NAVY, BLUE, PURPLE = colors.HexColor("#0b1330"), colors.HexColor("#3b82f6"), colors.HexColor("#8b5cf6")
CAT_COL = {"Low": colors.HexColor("#16a34a"), "Medium": colors.HexColor("#d97706"), "High": colors.HexColor("#dc2626")}


def _img(path, max_w=16.5 * cm, max_h=9 * cm):
    if not os.path.exists(path):
        return None
    w, h = PILImage.open(path).size
    s = min(max_w / w, max_h / h)
    return RLImage(path, width=w * s, height=h * s)


def _p(text, st):
    return Paragraph(escape(str(text)), st)


def build_report(res, analysis_dir, out_path):
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("s", parent=body, fontSize=8, leading=10, textColor=colors.HexColor("#555555"))
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], textColor=NAVY, fontSize=18, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=BLUE, fontSize=12.5, spaceBefore=10, spaceAfter=4)
    risk = res["risk"]

    def footer(c, d):
        c.saveState()
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        c.drawString(2 * cm, 1.2 * cm, "ScreenshotShield - Automated screenshot analysis. Heuristic output, not legal proof.")
        c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {d.page}")
        c.restoreState()

    def header(c, d):
        c.saveState()
        c.setFillColor(NAVY)
        c.rect(0, A4[1] - 2.2 * cm, A4[0], 2.2 * cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 17)
        c.drawString(2 * cm, A4[1] - 1.35 * cm, "ScreenshotShield")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#93c5fd"))
        c.drawString(2 * cm, A4[1] - 1.85 * cm, "Forensic Analysis Report  |  Don't Trust the Screenshot. Verify It.")
        c.restoreState()
        footer(c, d)

    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=3 * cm, bottomMargin=2 * cm,
                            title="ScreenshotShield Report", author="ScreenshotShield")
    S = []
    im = res["image"]
    S.append(Paragraph("Analysis Summary", h1))
    info = [["Screenshot file", res["filename"]], ["Analysis ID", res["analysis_id"]], ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M")],
            ["Dimensions", f"{im['width']} x {im['height']} px"], ["Format", f"{im['format']} ({im['mode']})"],
            ["File size", f"{im['size_bytes'] / 1024:.1f} KB"]]
    t = Table([[_p(a, body), _p(b, body)] for a, b in info], colWidths=[4 * cm, 13 * cm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2ff"))]))
    S += [t, Spacer(1, 10)]

    badge = Table([[Paragraph(f"<font size=26 color='white'><b>{risk['score']}</b></font><font size=10 color='white'> / 100</font>", body),
                    Paragraph(f"<font size=15 color='white'><b>{risk['category']} review priority</b></font><br/><font size=8 color='white'>Heuristic risk indicator - not a probability of forgery</font>", body)]],
                  colWidths=[4 * cm, 13 * cm])
    badge.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CAT_COL[risk["category"]]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    S += [badge, Spacer(1, 8)]
    rows = [["Check", "Status", "Weight", "Sub-score", "Points"]]
    for c in risk["components"]:
        rows.append([c["name"], c["status"], c["weight"], f"{c['subscore']:.2f}" if c["status"] != "unavailable" else "n/a", c["points"] if c["points"] is not None else "n/a"])
    t = Table(rows, colWidths=[6 * cm, 3.2 * cm, 2.5 * cm, 2.8 * cm, 2.5 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 9),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])]))
    S += [t, Spacer(1, 4), _p(risk["formula"], small), _p(risk["disclaimer"], small)]

    S.append(Paragraph("Suspicious Regions", h2))
    regs = res["regions"]["regions"]
    pic = _img(os.path.join(analysis_dir, "regions.png"))
    if pic:
        S.append(pic)
    if regs:
        rows = [["#", "x, y", "w x h", "Score", "Confidence", "Indicators"]]
        for r in regs:
            b = r["bbox"]
            rows.append([r["id"], f"{b['x']}, {b['y']}", f"{b['w']} x {b['h']}", r["score"], r["confidence"], ", ".join(i["name"] for i in r["indicators"])])
        t = Table(rows, colWidths=[1 * cm, 2.6 * cm, 2.8 * cm, 1.8 * cm, 2.4 * cm, 6.4 * cm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PURPLE), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                               ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1"))]))
        S += [Spacer(1, 6), t, Spacer(1, 4)]
        for r in regs:
            S.append(_p(r["explanation"], body)); S.append(Spacer(1, 3))
    else:
        S.append(_p("No region met the evidence threshold. This does not rule out manipulation.", body))
    S.append(_p(f"Coordinates are in pixels from the top-left corner of the original image and follow a {im['block_size']} px analysis grid.", small))

    S.append(PageBreak())
    S.append(Paragraph("Metadata Analysis", h2))
    m = res["metadata"]
    for f in m["findings"]:
        S.append(_p(f"[{f['severity'].upper()}] {f['text']}", body))
    if m["exif"]:
        S.append(Spacer(1, 4))
        t = Table([[_p(k, small), _p(v, small)] for k, v in list(m["exif"].items())[:18]], colWidths=[5 * cm, 12 * cm])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0"))]))
        S.append(t)

    S.append(Paragraph("Error Level Analysis (ELA)", h2))
    e = res["ela"]
    if e["status"] == "unavailable":
        S.append(_p(e["reason"], body))
    else:
        S.append(_p(f"Re-encoded at JPEG quality {e['recompress_quality']}. Estimated source quality: {e['estimated_quality']}. Mean error level {e['mean_ela']}, 99th percentile {e['p99_ela']}, "
                    f"localized outlier clusters: {e['n_clusters']}{' (diffuse)' if e['diffuse'] else ''}.", body))
        p = _img(os.path.join(analysis_dir, "ela.png"), max_h=7 * cm)
        if p: S.append(p)
        for n in e.get("notes", []): S.append(_p(n, small))
    S.append(Paragraph("Noise Analysis", h2))
    n_ = res["noise"]
    if n_["status"] == "unavailable":
        S.append(_p(n_["reason"], body))
    else:
        S.append(_p(f"Median local noise {n_['median_noise']} (scale {n_['noise_scale']}); {n_['testable_blocks']} of {n_['total_blocks']} blocks testable; localized outlier clusters: {n_['n_clusters']}.", body))
        p = _img(os.path.join(analysis_dir, "noise.png"), max_h=7 * cm)
        if p: S.append(p)
    S.append(Paragraph("Edge Analysis", h2))
    S.append(_p(f"Canny edge pixels: {res['edges']['edge_pixel_fraction'] * 100:.1f}% of the image. Edge density is used only as a supporting signal and never highlights a region on its own.", body))

    S.append(Paragraph("OCR Text Analysis", h2))
    o = res["ocr"]
    if o["status"] == "unavailable":
        S.append(_p(o["reason"], body))
    else:
        S.append(_p(f"{o.get('word_count', 0)} words recognised, average confidence {o.get('avg_confidence', 0)}%.", body))
        if o.get("text"):
            S.append(Paragraph(escape(o["text"][:1500]).replace("\n", "<br/>"), ParagraphStyle("mono", parent=small, fontName="Courier", fontSize=8, backColor=colors.HexColor("#f1f5f9"), borderPadding=4)))
        for a in o.get("anomalies", [])[:8]:
            S.append(_p(f"- '{a['word']}' at ({a['bbox']['x']}, {a['bbox']['y']}): {a['detail']}", small))

    S.append(Paragraph("Technical Explanation", h2))
    for ex in res["explanations"]:
        S.append(_p(f"{ex['module']}: {ex['text']}", body)); S.append(Spacer(1, 2))
    S.append(Paragraph("Limitations", h2))
    for l in res["limitations"]:
        S.append(_p(f"- {l}", body))
    S.append(Paragraph("Recommendations", h2))
    for l in res["recommendations"]:
        S.append(_p(f"- {l}", body))
    S.append(Paragraph("Final Assessment", h2))
    S.append(_p(f"Based on the automated checks that could be run ({sum(1 for c in risk['components'] if c['status'] != 'unavailable')} of {len(risk['components'])}), "
                f"this screenshot receives a {risk['category'].upper()} review priority (indicator {risk['score']}/100). "
                "This outcome means the listed areas should be inspected by a person; it is neither a certificate of authenticity nor proof of forgery.", body))
    doc.build(S, onFirstPage=header, onLaterPages=header)
    return out_path
