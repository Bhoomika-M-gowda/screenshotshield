# Architecture & detection methods

```
React (Vite, Tailwind, Recharts)  --REST/JSON-->  FastAPI
  Landing / Analyze / Results / Report              POST /api/upload   validate type, size, pixels; store privately
                                                    POST /api/analyze  start background analysis (returns analysis_id)
  polls /api/results/{id} for progress              GET  /api/results/{id}  progress, then full JSON
                                                    GET  /api/results/{id}/image/{name}  ela|noise|edges|heatmap|regions|original
                                                    GET  /api/report/{id}   PDF (ReportLab)
                                                    GET  /api/health
                              analyzer.py  ->  metadata -> edges -> ela -> noise -> text(OCR) -> regions -> risk -> explain
```
Storage: `uploads/u_<uuid>` then `uploads/a_<uuid>`; 128-bit random IDs, never listed, `Cache-Control: no-store`, CORS limited to the dev origin, auto-deleted after 60 min (`SHIELD_TTL_MIN`) and on `DELETE /api/results/{id}`.

## Modules
1. **Metadata (Pillow)** - EXIF tags, Software/editor names, DateTime vs DateTimeOriginal, extension/format mismatch. Missing EXIF = *inconclusive* (sub-score 0). GPS is detected but never displayed.
2. **ELA (JPEG only)** - recompress at quality 90, take the per-pixel maximum channel difference, average per block. Blocks are compared only with *similar* blocks (grouped by gradient strength and by presence of coloured edges, because chroma subsampling makes coloured edges naturally bright). Robust z-score (median/MAD) with floors; clusters of strong outliers raise the sub-score; diffuse (>25% of blocks) patterns and low-quality sources are down-weighted. PNG/WebP: *unavailable*.
3. **Noise (OpenCV)** - residual of a 3x3 median filter, measured only on pixels away from edges; per-block robust z-score. Blocks dominated by text/edges are marked untestable (dimmed in the visualisation).
4. **Edges** - Canny, block density, z-score of unusually dense blocks. A supporting signal only: it can never create a region alone.
5. **OCR (Tesseract)** - words and boxes, grouped into lines; hints for glyph height, baseline offset, background colour mismatch (measured on a ring around the word) and word-level ELA outliers. Layout-only hints are capped at 0.5 of the text sub-score.
6. **Regions** - per-block evidence in [0,1] from ELA, noise, text and edges, combined with weights 0.35/0.25/0.30/0.10. Connected blocks form a region; it is kept only if two signals agree, or one strong signal is localised (>= 2 blocks, or a text hint). Confidence = number of agreeing signals (1 low, 2 medium, 3+ high). Heatmap = smoothed combined evidence.

## Risk engine (rule-based, transparent)
`score = 100 * sum(w_i * s_i) / sum(w_i of available checks)`, weights: metadata 10, ELA 25, noise 20, text 20, region consensus 25. Unavailable checks are removed from both sums. Low < 30, Medium 30-59, High >= 60, and **High needs >= 2 components with sub-score >= 0.4** (otherwise capped at 59). This is a review-priority heuristic, **not** a probability of forgery.

## Explanations
`explain.py` fills sentence templates with measured values only (no generative model, no API keys), so it works offline and cannot invent findings.
