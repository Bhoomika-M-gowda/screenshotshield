import { Link, useParams } from 'react-router-dom'
import { Download, ArrowLeft, Loader2, AlertTriangle } from 'lucide-react'
import { CAT } from '../components/RiskGauge.jsx'
import Section from '../components/Section.jsx'
import { api, useResult } from '../services/api.js'

export default function Report() {
  const { id } = useParams()
  const { loading, data, error } = useResult(id)
  if (error) return <main className="mx-auto max-w-xl px-5 py-20 text-center"><AlertTriangle className="mx-auto mb-3 text-amber-400" size={36} /><p className="text-slate-300">{error}</p><Link to="/analyze" className="btn-primary mt-6">New analysis</Link></main>
  if (loading || !data) return <main className="py-24 text-center"><Loader2 className="mx-auto animate-spin text-sky-300" size={36} /></main>
  const { risk, regions, image } = data
  const c = CAT[risk.category]
  return (
    <main className="mx-auto max-w-4xl space-y-5 px-5 py-8">
      <div className="reveal flex flex-wrap items-center justify-between gap-3">
        <div><Link to={`/results/${id}`} className="mb-1 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-white"><ArrowLeft size={14} /> Back to results</Link><h1 className="text-2xl font-bold sm:text-3xl">Forensic report</h1></div>
        <a href={api.reportUrl(id)} className="btn-primary"><Download size={16} /> Download PDF report</a>
      </div>
      <Section title="Analysis summary">
        <dl className="grid grid-cols-[auto,1fr] gap-x-6 gap-y-1.5 text-sm"><dt className="text-slate-400">File</dt><dd>{data.filename}</dd><dt className="text-slate-400">Dimensions</dt><dd>{image.width} × {image.height} px</dd><dt className="text-slate-400">Format</dt><dd>{image.format} ({image.mode})</dd><dt className="text-slate-400">Risk indicator</dt><dd className={`font-semibold ${c.text}`}>{risk.score}/100 · {risk.category} review priority</dd></dl>
        <table className="mt-4 w-full text-left text-sm"><thead className="text-xs uppercase text-slate-400"><tr><th className="py-1">Check</th><th>Status</th><th>Weight</th><th>Sub-score</th></tr></thead>
          <tbody>{risk.components.map((x) => <tr key={x.id} className="border-t border-white/5"><td className="py-1.5">{x.name}</td><td className="text-slate-400">{x.status}</td><td>{x.weight}</td><td>{x.status === 'unavailable' ? 'n/a' : x.subscore.toFixed(2)}</td></tr>)}</tbody></table>
        <p className="mt-3 text-xs text-slate-500">{risk.disclaimer}</p>
      </Section>
      <Section title="Suspicious region coordinates">
        {regions.regions.length === 0 ? <p className="text-sm text-slate-300">No region met the evidence threshold.</p> : (
          <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase text-slate-400"><tr><th className="py-1">#</th><th>x</th><th>y</th><th>w</th><th>h</th><th>Score</th><th>Confidence</th><th>Indicators</th></tr></thead>
            <tbody>{regions.regions.map((r) => <tr key={r.id} className="border-t border-white/5 font-mono text-xs"><td className="py-1.5">{r.id}</td><td>{r.bbox.x}</td><td>{r.bbox.y}</td><td>{r.bbox.w}</td><td>{r.bbox.h}</td><td>{r.score}</td><td>{r.confidence}</td><td className="font-sans">{r.indicators.map((i) => i.name).join(', ')}</td></tr>)}</tbody></table></div>)}
        <img src={api.imageUrl(id, 'regions')} alt="Regions" className="mx-auto mt-4 max-h-96 rounded-xl border border-white/10" />
      </Section>
      <Section title="Detection explanations"><ul className="space-y-2 text-sm text-slate-300">{data.explanations.map((e, i) => <li key={i}><span className="mr-2 text-xs font-semibold uppercase text-slate-500">{e.module}</span>{e.text}</li>)}</ul></Section>
      <div className="grid gap-5 md:grid-cols-2">
        <Section title="Limitations"><ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-300">{data.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul></Section>
        <Section title="Recommendations"><ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-300">{data.recommendations.map((l, i) => <li key={i}>{l}</li>)}</ul></Section>
      </div>
    </main>
  )
}
