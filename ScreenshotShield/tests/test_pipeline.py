import os, sys, time, shutil, tempfile, io
import pytest
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "backend"))
sys.path.insert(0, HERE)
os.environ["SHIELD_STORE"] = tempfile.mkdtemp(prefix="shield_test_")
from fastapi.testclient import TestClient
from PIL import Image
import make_samples
from analyzer import analyze_image
import main

SAMPLES = os.path.join(HERE, "samples")


@pytest.fixture(scope="session")
def samples():
    return make_samples.generate(SAMPLES)


@pytest.fixture(scope="session")
def results(samples, tmp_path_factory):
    out = {}
    for n, p in samples.items():
        out[n] = analyze_image(p, n, str(tmp_path_factory.mktemp(n)))
    return out


def overlaps(box, region):
    b = region["bbox"]
    return not (b["x"] + b["w"] < box[0] or b["x"] > box[2] or b["y"] + b["h"] < box[1] or b["y"] > box[3])


def test_normal_is_low(results):
    assert results["01_normal.jpg"]["risk"]["category"] == "Low"
    assert results["01_normal.jpg"]["regions"]["regions"] == []


def test_png_ela_unavailable_not_suspicious(results):
    r = results["05_no_exif.png"]
    assert r["ela"]["status"] == "unavailable"
    assert r["risk"]["category"] == "Low"
    assert [c for c in r["risk"]["components"] if c["id"] == "ela"][0]["points"] is None


def test_missing_exif_inconclusive(results):
    assert results["05_no_exif.png"]["metadata"]["status"] == "inconclusive"
    assert results["05_no_exif.png"]["metadata"]["subscore"] == 0


def test_editor_tag_flagged(results):
    m = results["06_modified_text_editor_tag.jpg"]["metadata"]
    assert m["subscore"] >= 0.6 and any(f["severity"] == "warning" for f in m["findings"])


def test_pasted_region_localised(results):
    r = results["03_modified_image_region.jpg"]
    assert r["risk"]["category"] in ("Medium", "High")
    top = r["regions"]["regions"][0]
    assert overlaps(make_samples.LOGO_BOX, top) and len(top["indicators"]) >= 2


def test_compressed_not_high(results):
    assert results["04_compressed.jpg"]["risk"]["category"] != "High"


def test_no_high_with_single_indicator(results):
    for r in results.values():
        if r["risk"]["category"] == "High":
            assert r["risk"]["agreeing_indicators"] >= 2


def test_ocr_reads_text(results):
    assert "Payment Successful" in results["01_normal.jpg"]["ocr"]["text"]


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def _upload(client, path, name=None, ctype="image/jpeg"):
    with open(path, "rb") as f:
        return client.post("/api/upload", files={"file": (name or os.path.basename(path), f, ctype)})


def test_health(client):
    j = client.get("/api/health").json()
    assert j["status"] == "ok" and j["ocr_available"] is True


def test_rejects_non_image(client):
    r = client.post("/api/upload", files={"file": ("x.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400


def test_rejects_unsupported_type(client):
    buf = io.BytesIO(); Image.new("RGB", (100, 100)).save(buf, "GIF")
    r = client.post("/api/upload", files={"file": ("x.gif", buf.getvalue(), "image/gif")})
    assert r.status_code == 415


def test_rejects_large(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_BYTES", 1000)
    r = client.post("/api/upload", files={"file": ("big.jpg", b"0" * 5000, "image/jpeg")})
    assert r.status_code == 413


def test_rejects_bad_ids(client):
    assert client.get("/api/results/../../etc/passwd").status_code in (400, 404)
    assert client.get("/api/results/" + "z" * 32).status_code == 400
    assert client.get("/api/results/" + "a" * 32).status_code == 404


def test_full_flow_and_pdf(client, samples):
    up = _upload(client, samples["03_modified_image_region.jpg"]).json()
    r = client.post("/api/analyze", json={"upload_id": up["upload_id"]})
    assert r.status_code == 202
    aid = r.json()["analysis_id"]
    for _ in range(60):
        j = client.get(f"/api/results/{aid}").json()
        if j["status"] != "processing":
            break
        time.sleep(0.5)
    assert j["status"] == "complete" and j["risk"]["score"] > 0
    assert client.get(j["image_urls"]["heatmap"]).headers["content-type"] == "image/png"
    pdf = client.get(f"/api/report/{aid}")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF" and len(pdf.content) > 5000
    assert client.delete(f"/api/results/{aid}").json()["deleted"]
    assert client.get(f"/api/results/{aid}").status_code == 404


def test_cleanup_expired(client, monkeypatch):
    d = os.path.join(main.STORE, "u_" + "b" * 32)
    os.makedirs(d)
    old = time.time() - 99999
    os.utime(d, (old, old))
    main.cleanup_expired()
    assert not os.path.exists(d)
