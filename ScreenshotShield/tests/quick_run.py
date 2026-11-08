import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from analyzer import analyze_image
d = os.path.join(os.path.dirname(__file__), "samples")
for n in sorted(os.listdir(d)):
    if not n[0].isdigit(): continue
    r = analyze_image(os.path.join(d, n), n, "/tmp/out_" + n)
    c = {x["id"]: (x["status"], x["subscore"]) for x in r["risk"]["components"]}
    print(f"{n:34s} score={r['risk']['score']:3d} {r['risk']['category']:6s} raw={r['risk']['raw_score']:5.1f} t={r['duration_s']}s")
    print("   comps:", c)
    print("   ela clusters:", r["ela"].get("clusters", [])[:2], "diffuse", r["ela"].get("diffuse"), "| noise clusters:", r["noise"].get("clusters", [])[:2], "diffuse", r["noise"].get("diffuse"))
    print("   ocr words:", r["ocr"].get("word_count"), "anoms:", [(a["word"], a["type"], a["weight"]) for a in r["ocr"].get("anomalies", [])][:6])
    for g in r["regions"]["regions"]:
        print("   region", g["id"], g["bbox"], g["score"], g["confidence"], [i["key"] for i in g["indicators"]])
