# ScreenshotShield — *Don't Trust the Screenshot. Verify It.*

AI-assisted screenshot verification for payment confirmations, bank messages, chats and e-mails. Runs fully locally (no API keys, no paid services). It shows **evidence and uncertainty**; it never declares an image "genuine" or "fake".

**Stack:** React + Vite + Tailwind + Lucide + Recharts · FastAPI · OpenCV · Pillow · NumPy · Tesseract OCR · ReportLab

## Quick start

Requirements: Python 3.10+, Node 18+, and the **Tesseract OCR** binary (`sudo apt install tesseract-ocr` / `brew install tesseract` / Windows installer from UB Mannheim, then add to PATH). Without Tesseract the app still works; text analysis is marked *unavailable*.

### Option A - one command (demo mode, http://localhost:8000)
```bash
./run.sh
```

### Option B - development mode (hot reload)
```bash
# terminal 1
cd backend && pip install -r requirements.txt && uvicorn main:app --port 8000
# terminal 2
cd frontend && npm install && npm run dev      # http://localhost:5173
```

### Tests
```bash
python -m pytest tests -q            # 15 tests: modules, API validation, full upload->analyze->PDF flow
python tests/run_evaluation.py       # regenerates docs/TEST_RESULTS.md from the synthetic samples
```
Sample images are in `tests/samples/` (regenerate with `python tests/make_samples.py`).

## Hackathon demo script (3-4 min)
1. **Landing page** - say the tagline; stress "evidence, not verdicts".
2. **Analyze** - drag in `tests/samples/01_normal.jpg` -> Low priority, no regions (no false alarm).
3. Upload `03_modified_image_region.jpg` -> watch the live progress, then the **Results** page: gauge, score breakdown, region #1 over the replaced logo (toggle Heatmap / ELA / Noise), click the region card to see which indicators fired and why.
4. Upload `05_no_exif.png` -> ELA shows **unavailable** (not suspicious) and missing EXIF is **inconclusive**.
5. **Download PDF** and open the Report page.
6. Close with `docs/TEST_RESULTS.md`: be upfront that `02_modified_text.jpg` is a **false negative**; that honesty is the selling point.

## API
`POST /api/upload` (multipart `file`) -> `{upload_id}` · `POST /api/analyze {upload_id}` -> `202 {analysis_id}` · `GET /api/results/{id}` -> progress or full JSON · `GET /api/results/{id}/image/{name}` · `GET /api/report/{id}` (PDF) · `DELETE /api/results/{id}` · `GET /api/health`

Limits: JPEG/PNG/WebP, 10 MB (`SHIELD_MAX_MB`), 25 MP, auto-delete after 60 min (`SHIELD_TTL_MIN`).

## Docs
- `docs/ARCHITECTURE.md` - architecture and how each detection method works
- `docs/TEST_RESULTS.md` - measured results, successes and failures

## Limitations
Heuristic only; not validated on real-world data; ELA needs JPEG; screenshots re-saved after editing can hide traces; re-rendered fake screenshots (rebuilt in HTML) cannot be detected. Always verify with the bank/platform.
