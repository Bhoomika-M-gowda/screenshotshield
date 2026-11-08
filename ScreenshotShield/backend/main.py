"""ScreenshotShield FastAPI backend."""
import asyncio
import json
import os
import re
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from analyzer import analyze_image
from report import build_report
from text_analysis import ocr_available

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STORE = os.environ.get("SHIELD_STORE", os.path.join(ROOT, "uploads"))
MAX_BYTES = int(os.environ.get("SHIELD_MAX_MB", "10")) * 1024 * 1024
MAX_PIXELS = 25_000_000
TTL_SECONDS = int(os.environ.get("SHIELD_TTL_MIN", "60")) * 60
ALLOWED = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
ID_RE = re.compile(r"^[0-9a-f]{32}$")
IMG_NAMES = {"original", "ela", "noise", "edges", "heatmap", "regions"}
Image.MAX_IMAGE_PIXELS = MAX_PIXELS
os.makedirs(STORE, exist_ok=True)


def _dir(kind, id_):
    if not ID_RE.match(id_ or ""):
        raise HTTPException(400, "Invalid id.")
    return os.path.join(STORE, f"{kind}_{id_}")


def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    os.replace(tmp, path)


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def cleanup_expired():
    now = time.time()
    for name in os.listdir(STORE):
        p = os.path.join(STORE, name)
        if os.path.isdir(p) and name[:2] in ("u_", "a_") and now - os.path.getmtime(p) > TTL_SECONDS:
            shutil.rmtree(p, ignore_errors=True)


@asynccontextmanager
async def lifespan(app):
    cleanup_expired()

    async def loop():
        while True:
            await asyncio.sleep(300)
            try:
                cleanup_expired()
            except Exception:
                pass
    task = asyncio.create_task(loop())
    yield
    task.cancel()


app = FastAPI(title="ScreenshotShield API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("SHIELD_CORS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
                   allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": app.version, "ocr_available": ocr_available(), "max_upload_mb": MAX_BYTES // 1024 // 1024,
            "retention_minutes": TTL_SECONDS // 60}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"File too large. Maximum size is {MAX_BYTES // 1024 // 1024} MB.")
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    uid = uuid.uuid4().hex
    d = _dir("u", uid)
    os.makedirs(d)
    tmp = os.path.join(d, "incoming.bin")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        try:
            with Image.open(tmp) as im:
                fmt = im.format
                im.verify()
            with Image.open(tmp) as im:
                w, h = im.size
        except Exception:
            raise HTTPException(400, "This file is not a valid image or is corrupted. Please upload a JPEG, PNG or WebP screenshot.")
        if fmt not in ALLOWED:
            raise HTTPException(415, f"Unsupported image type '{fmt}'. Allowed types: JPEG, PNG, WebP.")
        if w * h > MAX_PIXELS:
            raise HTTPException(413, "Image resolution is too large (limit 25 megapixels).")
        if w < 64 or h < 64:
            raise HTTPException(400, "Image is too small to analyse (minimum 64x64 px).")
        path = os.path.join(d, "source" + ALLOWED[fmt])
        os.replace(tmp, path)
        name = re.sub(r"[^\w.\- ]", "_", os.path.basename(file.filename or "screenshot"))[:120]
        _write_json(os.path.join(d, "meta.json"), {"filename": name, "format": fmt, "path": path, "size": len(data), "width": w, "height": h})
        return {"upload_id": uid, "filename": name, "format": fmt, "width": w, "height": h, "size_bytes": len(data)}
    except HTTPException:
        shutil.rmtree(d, ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(d, ignore_errors=True)
        raise HTTPException(500, "Upload failed unexpectedly.")


class AnalyzeReq(BaseModel):
    upload_id: str


def _run(aid):
    d = _dir("a", aid)
    status_path = os.path.join(d, "status.json")
    meta = _read_json(os.path.join(d, "meta.json"))

    def progress(stage, pct):
        _write_json(status_path, {"status": "processing", "stage": stage, "progress": pct})

    try:
        res = analyze_image(os.path.join(d, os.path.basename(meta["path"])), meta["filename"], d, progress)
        res["analysis_id"] = aid
        res["created_at"] = datetime.now(timezone.utc).isoformat()
        _write_json(os.path.join(d, "results.json"), res)
        _write_json(status_path, {"status": "complete", "stage": "Complete", "progress": 100})
    except Exception as e:  # keep the app alive and report a meaningful message
        _write_json(status_path, {"status": "failed", "stage": "Failed", "progress": 100, "error": f"Analysis failed: {type(e).__name__}: {e}"})


@app.post("/api/analyze", status_code=202)
def analyze(req: AnalyzeReq, bg: BackgroundTasks):
    src = _dir("u", req.upload_id)
    if not os.path.isdir(src):
        raise HTTPException(404, "Upload not found or expired. Please upload the screenshot again.")
    aid = uuid.uuid4().hex
    dst = _dir("a", aid)
    os.replace(src, dst)
    _write_json(os.path.join(dst, "status.json"), {"status": "processing", "stage": "Queued", "progress": 2})
    bg.add_task(_run, aid)
    return {"analysis_id": aid, "status": "processing"}


@app.get("/api/results/{analysis_id}")
def results(analysis_id: str):
    d = _dir("a", analysis_id)
    if not os.path.isdir(d):
        raise HTTPException(404, "Analysis not found or expired.")
    st = _read_json(os.path.join(d, "status.json"))
    if st["status"] == "complete":
        res = _read_json(os.path.join(d, "results.json"))
        res["status"] = "complete"
        res["image_urls"] = {n: f"/api/results/{analysis_id}/image/{n}" for n in res["images_available"]}
        return JSONResponse(res, headers={"Cache-Control": "no-store"})
    if st["status"] == "failed":
        return JSONResponse(st, status_code=500)
    return JSONResponse(st, headers={"Cache-Control": "no-store"})


@app.get("/api/results/{analysis_id}/image/{name}")
def result_image(analysis_id: str, name: str):
    d = _dir("a", analysis_id)
    p = os.path.join(d, f"{name}.png")
    if name not in IMG_NAMES or not os.path.exists(p):
        raise HTTPException(404, "Image not available.")
    return FileResponse(p, media_type="image/png", headers={"Cache-Control": "no-store"})


@app.get("/api/report/{analysis_id}")
def report(analysis_id: str):
    d = _dir("a", analysis_id)
    rp = os.path.join(d, "results.json")
    if not os.path.exists(rp):
        raise HTTPException(404, "Results not ready or expired.")
    pdf = os.path.join(d, "report.pdf")
    if not os.path.exists(pdf):
        build_report(_read_json(rp), d, pdf)
    return FileResponse(pdf, media_type="application/pdf", filename=f"ScreenshotShield_Report_{analysis_id[:8]}.pdf",
                        headers={"Cache-Control": "no-store"})


@app.delete("/api/results/{analysis_id}")
def delete(analysis_id: str):
    d = _dir("a", analysis_id)
    if not os.path.isdir(d):
        raise HTTPException(404, "Analysis not found.")
    shutil.rmtree(d, ignore_errors=True)
    return {"deleted": True}


_dist = os.path.join(ROOT, "frontend", "dist")
if os.path.isdir(_dist):  # single-process demo mode: serve the built frontend (HashRouter, so no SPA fallback needed)
    app.mount("/", StaticFiles(directory=_dist, html=True), name="web")
