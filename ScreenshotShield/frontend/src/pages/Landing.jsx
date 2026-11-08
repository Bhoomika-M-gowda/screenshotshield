import { Link } from 'react-router-dom'
import { ShieldCheck, UploadCloud, ScanSearch, FileText, Layers, Waves, ScanText, Fingerprint, MapPinned, ArrowRight } from 'lucide-react'

const features = [
  [Fingerprint, 'Metadata inspection', 'EXIF, editing-software tags and timestamps — missing data is flagged as inconclusive, never as proof.'],
  [Layers, 'Error Level Analysis', 'Re-compression analysis that exposes areas saved with a different JPEG history.'],
  [Waves, 'Noise consistency', 'Compares local noise patterns across the image to find pasted or regenerated areas.'],
  [ScanText, 'OCR text analysis', 'Reads the text, then checks alignment, spacing, background and compression of each word.'],
  [MapPinned, 'Suspicious regions', 'Combines independent signals into numbered boxes and a heatmap, with the evidence behind each.'],
  [FileText, 'Forensic PDF report', 'Download findings, coordinates, explanations and limitations in one professional report.'],
]
const steps = [
  [UploadCloud, 'Upload', 'Drop a payment, bank, chat or e-mail screenshot.'],
  [ScanSearch, 'Analyze', 'Five independent forensic modules run locally on the server.'],
  [ShieldCheck, 'Review', 'Inspect highlighted regions, explanations and the transparent risk score.'],
]

export default function Landing() {
  return (
    <main>
      <section className="relative mx-auto max-w-6xl px-5 pb-16 pt-16 text-center sm:pt-24">
        <div className="reveal mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs text-sky-200">
          <span className="h-2 w-2 animate-glow rounded-full bg-emerald-400" /> AI-assisted digital image forensics · runs fully local
        </div>
        <h1 className="reveal text-4xl font-extrabold leading-tight tracking-tight sm:text-6xl">
          Don’t Trust the Screenshot.<br /><span className="h-grad">Verify It.</span>
        </h1>
        <p className="reveal mx-auto mt-6 max-w-2xl text-base text-slate-300 sm:text-lg" style={{ animationDelay: '.1s' }}>
          ScreenshotShield analyses payment confirmations, bank messages, chats and e-mails for signs of manipulation, highlights
          the regions that deserve a closer look, and explains every finding — with honest uncertainty.
        </p>
        <div className="reveal mt-9 flex flex-wrap justify-center gap-3" style={{ animationDelay: '.2s' }}>
          <Link to="/analyze" className="btn-primary"><UploadCloud size={18} /> Upload Screenshot</Link>
          <a href="#how" className="btn-ghost">How it works <ArrowRight size={16} /></a>
        </div>
        <div className="reveal relative mx-auto mt-14 max-w-sm" style={{ animationDelay: '.3s' }}>
          <div className="glass overflow-hidden p-4 text-left">
            <div className="mb-3 flex items-center justify-between text-xs text-slate-400"><span>payment_receipt.jpg</span><span className="chip border-amber-500/40 bg-amber-500/10 text-amber-300">Region #1</span></div>
            <div className="relative space-y-2 rounded-lg bg-slate-900/80 p-4">
              <div className="h-3 w-1/2 rounded bg-slate-700" /><div className="h-8 w-2/3 rounded border-2 border-dashed border-amber-400 bg-amber-400/10" />
              <div className="h-3 w-3/4 rounded bg-slate-700" /><div className="h-3 w-1/3 rounded bg-slate-700" />
              <div className="absolute left-0 h-0.5 w-full animate-scan bg-gradient-to-r from-transparent via-electric to-transparent shadow-[0_0_14px_#3b82f6]" />
            </div>
          </div>
        </div>
      </section>

      <section id="how" className="mx-auto max-w-6xl px-5 py-12">
        <h2 className="mb-8 text-center text-2xl font-bold sm:text-3xl">How it works</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {steps.map(([Icon, t, d], i) => (
            <div key={t} className="glass reveal p-6" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="mb-4 flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-xl bg-electric/15 text-sky-300"><Icon size={22} /></span><span className="text-sm font-semibold text-violet-300">Step {i + 1}</span></div>
              <h3 className="text-lg font-semibold">{t}</h3><p className="mt-1 text-sm text-slate-400">{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-12">
        <h2 className="mb-8 text-center text-2xl font-bold sm:text-3xl">Key features</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(([Icon, t, d]) => (
            <div key={t} className="glass p-6 transition hover:-translate-y-1 hover:border-violet/40">
              <Icon className="mb-3 text-violet-300" size={24} /><h3 className="font-semibold">{t}</h3><p className="mt-1 text-sm text-slate-400">{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-4xl px-5 py-10">
        <div className="glass border-electric/30 p-7 text-center">
          <h3 className="text-xl font-bold">Evidence, not verdicts</h3>
          <p className="mx-auto mt-2 max-w-2xl text-sm text-slate-300">The risk indicator is a transparent, rule-based review-priority score — not a probability of forgery. No single signal can mark an image as fake, and checks that cannot run are marked unavailable instead of suspicious.</p>
          <Link to="/analyze" className="btn-primary mt-5">Start analysis <ArrowRight size={16} /></Link>
        </div>
      </section>
    </main>
  )
}
