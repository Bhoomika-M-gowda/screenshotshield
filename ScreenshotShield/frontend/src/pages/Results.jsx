import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Download, FileText, Fingerprint, Layers, Waves, ScanText, MapPinned, Info, AlertTriangle, Loader2, RotateCcw } from 'lucide-react'
import RiskGauge, { CAT } from '../components/RiskGauge.jsx'
import ImageViewer from '../components/ImageViewer.jsx'
import Section, { StatusChip } from '../components/Section.jsx'
import { api, useResult } from '../services/api.js'

const LEVEL = { high: 'border-red-500/40 text-red-300', medium: 'border-amber-500/40 text-amber-300', low: 'border-sky-500/40 text-sky-300', info: 'border-white/10 text-slate-400' }
const CONF = { high: 'border-red-500/40 bg-red-500/10 text-red-300', medium: 'border-amber-500/40 bg-amber-500/10 text-amber-300', low: 'border-sky-500/40 bg-sky-500/10 text-sky-300' }

export default function Results() {
  const { id } = useParams()
  const { loading, data, error, progress } = useResult(id)
  const [active, setActive] = useState(null)

  if (error) return (
    <main className="mx-auto max-w-xl px-5 py-20 text-center">
      <AlertTriangle className="mx-auto mb-3 text-amber-400" size={36} /><h1 className="text-xl font-bold">Results unavailable</h1>
      <p className="mt-2 text-sm text-slate-400">{error}</p><Link to="/analyze" className="btn-primary mt-6">Analyze a new screenshot</Link>
    </main>)
  if (loading || !data) return (
    <main className="mx-auto max-w-xl px-5 py-24 text-center"><Loader2 className="mx-auto animate-spin text-sky-300" size={36} /><p className="mt-3 text-sm text-slate-400">{progress?.stage || 'Loading'}…</p></main>)

  const { risk, metadata: m, ela, noise, ocr, regions } = data
  const c = CAT[risk.category]
  const chart = risk.components.filter((x) => x.status !== 'unavailable').map((x) => ({ name: x.name, pct: Math.round(x.subscore * 100) }))
  const unavailable = risk.components.filter((x) => x.status === 'unavailable')

  return (
    <main className="mx-auto max-w-6xl space-y-5 px-5 py-8">
      <div className="reveal flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-2xl font-bold sm:text-3xl">Analysis results</h1><p className="text-sm text-slate-400">{data.filename} · {data.image.width}×{data.image.height} · {data.image.format} · {data.duration_s}s</p></div>
        <div className="flex flex-wrap gap-2">
          <Link to="/analyze" className="btn-ghost"><RotateCcw size={16} /> New analysis</Link>
          <Link to={`/report/${id}`} className="btn-ghost"><FileText size={16} /> Report page</Link>
          <a href={api.reportUrl(id)} className="btn-primary"><Download size={16} /> Download PDF</a>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Section title="Overall risk indicator">
          <RiskGauge score={risk.score} category={risk.category} />
          <div className="mt-2 text-center"><span className={`chip text-sm ${c.chip}`}>{risk.category} review priority</span></div>
          <p className="mt-3 text-center text-xs text-slate-400">{risk.disclaimer}</p>
          {risk.capped && <p className="mt-2 text-center text-xs text-amber-300">Capped below High: fewer than two independent indicators agreed.</p>}
        </Section>
        <div className="lg:col-span-2"><Section title="Score breakdown" icon={Layers}>
          <div className="h-56"><ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart} layout="vertical" margin={{ left: 10, right: 20 }}>
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 11 }} unit="%" /><YAxis type="category" dataKey="name" width={130} tick={{ fill: '#cbd5e1', fontSize: 12 }} />
              <Tooltip cursor={{ fill: 'rgba(255,255,255,.04)' }} contentStyle={{ background: '#0b1330', border: '1px solid rgba(255,255,255,.1)', borderRadius: 12 }} formatter={(v) => [`${v}% of component weight`, 'Sub-score']} />
              <Bar dataKey="pct" radius={[0, 8, 8, 0]}>{chart.map((d, i) => <Cell key={i} fill={d.pct >= 60 ? '#ef4444' : d.pct >= 30 ? '#f59e0b' : '#3b82f6'} />)}</Bar>
            </BarChart></ResponsiveContainer></div>
          {unavailable.length > 0 && <p className="text-xs text-slate-400">Not run (excluded from the score, not treated as suspicious): {unavailable.map((u) => u.name).join(', ')}.</p>}
          <p className="mt-2 text-xs text-slate-500">{risk.formula}</p>
        </Section></div>
      </div>

      <ImageViewer data={data} active={active} setActive={setActive} />

      <Section icon={MapPinned} title="Suspicious regions" badge={<span className="chip border-white/10 text-slate-300">{regions.regions.length} flagged</span>}>
        {regions.regions.length === 0 ? <p className="text-sm text-slate-300">No area met the evidence threshold. This does not rule out manipulation.</p> : (
          <div className="space-y-3">
            {regions.regions.map((r) => (
              <div key={r.id} onClick={() => setActive(r.id)} className={`cursor-pointer rounded-xl border p-4 transition ${active === r.id ? 'border-violet bg-violet/10' : 'border-white/10 hover:border-white/25'}`}>
                <div className="flex flex-wrap items-center gap-2"><span className="font-semibold">Region #{r.id}</span><span className={`chip ${CONF[r.confidence]}`}>{r.confidence} confidence</span><span className="chip border-white/10 text-slate-300">score {r.score}</span>
                  <span className="ml-auto font-mono text-xs text-slate-400">x={r.bbox.x} y={r.bbox.y} w={r.bbox.w} h={r.bbox.h}</span></div>
                <div className="mt-2 flex flex-wrap gap-1.5">{r.indicators.map((i) => <span key={i.key} className="chip border-violet/30 bg-violet/10 text-violet-200">{i.name} · {Math.round(i.strength * 100)}%</span>)}</div>
                <p className="mt-2 text-sm text-slate-300">{r.explanation}</p>
              </div>))}
          </div>)}
        <p className="mt-3 text-xs text-slate-500">Boxes follow a {data.image.block_size}px analysis grid: they show where to look, not the exact edited pixels.</p>
      </Section>

      <div className="grid gap-5 md:grid-cols-2">
        <Section icon={Fingerprint} title="Metadata analysis" badge={<StatusChip status={m.status} />}>
          <ul className="space-y-2 text-sm">{m.findings.map((f, i) => <li key={i} className={`rounded-lg border-l-2 bg-white/[0.03] px-3 py-2 ${f.severity === 'warning' ? 'border-amber-400 text-amber-100' : f.severity === 'notice' ? 'border-sky-400' : 'border-white/15 text-slate-300'}`}>{f.text}</li>)}</ul>
          <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-400"><span>Format</span><span className="text-slate-200">{m.format}</span><span>Dimensions</span><span className="text-slate-200">{m.width}×{m.height}</span><span>Mode</span><span className="text-slate-200">{m.mode}</span><span>File size</span><span className="text-slate-200">{(m.file_size_bytes / 1024).toFixed(1)} KB</span></div>
          {Object.keys(m.exif).length > 0 && <details className="mt-3 text-xs text-slate-400"><summary className="cursor-pointer">EXIF fields ({Object.keys(m.exif).length})</summary><dl className="mt-2 grid grid-cols-2 gap-1">{Object.entries(m.exif).map(([k, v]) => <><dt key={k}>{k}</dt><dd className="truncate text-slate-200">{v}</dd></>)}</dl></details>}
        </Section>
        <Section icon={Layers} title="Image consistency" badge={<StatusChip status={ela.status} />}>
          <div className="space-y-3 text-sm text-slate-300">
            <div><div className="font-medium text-white">Error level analysis</div>{ela.status === 'unavailable' ? <p className="text-slate-400">{ela.reason}</p> : <p>Re-saved at quality {ela.recompress_quality}; estimated source quality {ela.estimated_quality ?? 'n/a'}. Mean error {ela.mean_ela}, {ela.n_clusters} localized outlier cluster(s){ela.diffuse ? ' (diffuse)' : ''}.</p>}{(ela.notes || []).map((n, i) => <p key={i} className="text-xs text-amber-200/80">{n}</p>)}</div>
            <div><div className="flex items-center gap-2 font-medium text-white"><Waves size={14} />Noise analysis <StatusChip status={noise.status} /></div>{noise.status === 'unavailable' ? <p className="text-slate-400">{noise.reason}</p> : <p>{noise.testable_blocks}/{noise.total_blocks} blocks testable; median noise {noise.median_noise}; {noise.n_clusters} localized outlier cluster(s).</p>}</div>
            <div><div className="font-medium text-white">Edge detection</div><p>{(data.edges.edge_pixel_fraction * 100).toFixed(1)}% edge pixels — used as a supporting signal only.</p></div>
          </div>
        </Section>
      </div>

      <Section icon={ScanText} title="OCR text analysis" badge={<StatusChip status={ocr.status} />}>
        {ocr.status === 'unavailable' ? <p className="text-sm text-slate-400">{ocr.reason}</p> : (
          <div className="grid gap-4 md:grid-cols-2">
            <div><div className="mb-1 text-xs text-slate-400">{ocr.word_count} words · average confidence {ocr.avg_confidence}%</div><pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-xl border border-white/10 bg-black/40 p-3 font-mono text-xs text-slate-200">{ocr.text || '(no text detected)'}</pre></div>
            <div><div className="mb-1 text-xs text-slate-400">Text-layout and compression hints</div>
              {ocr.anomalies.length === 0 ? <p className="text-sm text-slate-300">No unusual text regions found.</p> : <ul className="max-h-64 space-y-2 overflow-auto text-xs">{ocr.anomalies.slice(0, 12).map((a, i) => <li key={i} className="rounded-lg bg-white/[0.04] p-2"><span className="font-semibold text-white">“{a.word}”</span> <span className="font-mono text-slate-500">({a.bbox.x},{a.bbox.y})</span><br /><span className="text-slate-300">{a.detail}</span></li>)}</ul>}
              <p className="mt-2 text-xs text-slate-500">{(ocr.notes || [])[0]}</p></div>
          </div>)}
      </Section>

      <Section icon={Info} title="Detailed explanations">
        <ul className="space-y-2 text-sm">{data.explanations.map((e, i) => <li key={i} className={`rounded-lg border-l-2 bg-white/[0.03] px-3 py-2 ${LEVEL[e.level] || LEVEL.info}`}><span className="mr-2 text-xs font-semibold uppercase tracking-wider text-slate-400">{e.module}</span><span className="text-slate-200">{e.text}</span></li>)}</ul>
        <h3 className="mt-5 text-sm font-semibold text-white">Limitations</h3>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-xs text-slate-400">{data.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul>
      </Section>
    </main>
  )
}
