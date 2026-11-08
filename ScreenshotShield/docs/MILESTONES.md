# ScreenshotShield - Milestones

| # | Milestone | Deliverables | Status | How to verify |
|---|---|---|---|---|
| M1 | Environment & skeleton | Folder structure, `requirements.txt`, `.gitignore`, Tesseract check | Done | `python -c "import cv2, PIL, pytesseract"` |
| M2 | Forensic engine | `metadata.py`, `ela.py`, `noise_analysis.py`, `edges.py`, `text_analysis.py` | Done | `python tests/quick_run.py` |
| M3 | Regions + risk + explanations | `region_detection.py` (boxes, heatmap, coordinates), `risk_engine.py`, `explain.py`, `analyzer.py` | Done | Results JSON has `risk`, `regions`, `explanations` |
| M4 | Backend API + PDF | `main.py` (upload, analyze, results, report, health, delete), `report.py`, private temp storage, auto-cleanup | Done | `pytest tests -q` (15 pass) |
| M5 | Frontend | Landing, Analyze (drag-drop, live progress), Results (gauge, charts, region viewer), Report pages | Done | `cd frontend && npm run build` |
| M6 | Integration | Frontend <-> API, polling progress, PDF download, error states | Done | Playwright run: upload -> results -> PDF, 0 console errors |
| M7 | Testing & evaluation | Synthetic samples, `run_evaluation.py`, `TEST_RESULTS.md` | Done | `python tests/run_evaluation.py` |
| M8 | Docs & demo | `README.md`, `ARCHITECTURE.md`, demo script, `run.sh` | Done | `./run.sh` -> http://localhost:8000 |

## Next milestones (post-hackathon)
| # | Milestone | Goal |
|---|---|---|
| M9 | Close known false negatives | Multi-quality ELA ("JPEG ghost") and double-compression detection without raising false alarms (samples 02, 06) |
| M10 | Real-data validation | Test on real screenshots; compute precision/recall; tune thresholds on a held-out set |
| M11 | OCR upgrade | Optional EasyOCR backend, character-level font checks for amounts and IDs |
| M12 | Deployment | Docker, auth, rate limiting, HTTPS |
