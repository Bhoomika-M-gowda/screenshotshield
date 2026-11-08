import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ScanSearch, X, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'
import Dropzone from '../components/Dropzone.jsx'
import { api } from '../services/api.js'

const TYPES = ['image/jpeg', 'image/png', 'image/webp']
const STAGES = ['Reading metadata', 'Detecting edges', 'Error level analysis', 'Analysing noise', 'Reading text (OCR)', 'Locating suspicious regions', 'Scoring and rendering']

export default function Analyze() {
  const nav = useNavigate()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [prog, setProg] = useState({ stage: '', progress: 0 })
  const [health, setHealth] = useState(null)

  useEffect(() => { api.health().then(setHealth).catch(() => setHealth(false)) }, [])
  useEffect(() => { if (!file) { setPreview(null); return } const u = URL.createObjectURL(file); setPreview(u); return () => URL.revokeObjectURL(u) }, [file])

  const pick = (f) => {
    setError('')
    if (!TYPES.includes(f.type)) return setError('Unsupported file type. Please upload a JPEG, PNG or WebP image.')
    if (f.size > 10 * 1024 * 1024) return setError('File is larger than 10 MB.')
    setFile(f)
  }

  const run = async () => {
    setBusy(true); setError(''); setProg({ stage: 'Uploading', progress: 3 })
    try {
      const up = await api.upload(file)
      const { analysis_id } = await api.analyze(up.upload_id)
      for (;;) {
        const r = await api.results(analysis_id)
        if (r.status === 'complete') return nav(`/results/${analysis_id}`)
        setProg({ stage: r.stage, progress: r.progress })
        await new Promise((res) => setTimeout(res, 500))
      }
    } catch (e) { setError(e.message || 'Analysis failed.'); setBusy(false) }
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <div className="reveal mb-6">
        <h1 className="text-3xl font-bold">Analysis dashboard</h1>
        <p className="mt-1 text-sm text-slate-400">Upload a screenshot. Analysis runs on your local ScreenshotShield server; files are deleted automatically.</p>
      </div>
      {health === false && (
        <div className="glass mb-4 flex items-start gap-3 border-red-500/40 p-4 text-sm text-red-200"><AlertTriangle size={18} className="mt-0.5 shrink-0" />The backend is not reachable. Start it with <code className="rounded bg-black/40 px-1.5">uvicorn main:app --port 8000</code> inside the backend folder.</div>
      )}
      {health && !health.ocr_available && (
        <div className="glass mb-4 flex items-start gap-3 border-amber-500/40 p-4 text-sm text-amber-200"><AlertTriangle size={18} className="mt-0.5 shrink-0" />Tesseract OCR is not installed — text analysis will be marked unavailable. Everything else still works.</div>
      )}
      {!file ? <Dropzone onFile={pick} disabled={busy} /> : (
        <div className="glass reveal p-5">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0"><div className="truncate font-semibold">{file.name}</div><div className="text-xs text-slate-400">{file.type} · {(file.size / 1024).toFixed(1)} KB</div></div>
            {!busy && <button className="btn-ghost !px-3 !py-2" onClick={() => setFile(null)} aria-label="Remove file"><X size={16} /></button>}
          </div>
          <div className="relative mt-4 overflow-hidden rounded-xl border border-white/10 bg-black/40">
            <img src={preview} alt="Preview" className="mx-auto max-h-[55vh] object-contain" />
            {busy && <div className="pointer-events-none absolute left-0 h-0.5 w-full animate-scan bg-gradient-to-r from-transparent via-electric to-transparent shadow-[0_0_16px_#3b82f6]" />}
          </div>
          {busy ? (
            <div className="mt-5">
              <div className="mb-2 flex items-center justify-between text-sm"><span className="flex items-center gap-2"><Loader2 size={16} className="animate-spin text-sky-300" />{prog.stage || 'Working'}…</span><span className="tabular-nums text-slate-400">{prog.progress}%</span></div>
              <div className="h-2 overflow-hidden rounded-full bg-white/10"><div className="h-full rounded-full bg-gradient-to-r from-electric to-violet transition-all duration-500" style={{ width: `${prog.progress}%` }} /></div>
              <ul className="mt-4 grid gap-1.5 text-xs text-slate-400 sm:grid-cols-2">
                {STAGES.map((s) => { const done = STAGES.indexOf(prog.stage) > STAGES.indexOf(s) || prog.progress >= 94 && s !== prog.stage; return (
                  <li key={s} className={`flex items-center gap-2 ${s === prog.stage ? 'text-white' : ''}`}>{done ? <CheckCircle2 size={14} className="text-emerald-400" /> : <span className="h-3.5 w-3.5 rounded-full border border-white/20" />}{s}</li>) })}
              </ul>
            </div>
          ) : <button className="btn-primary mt-5 w-full" onClick={run}><ScanSearch size={18} /> Analyze Screenshot</button>}
        </div>
      )}
      {error && <div className="glass mt-4 flex items-start gap-3 border-red-500/40 p-4 text-sm text-red-200"><AlertTriangle size={18} className="mt-0.5 shrink-0" />{error}</div>}
    </main>
  )
}
