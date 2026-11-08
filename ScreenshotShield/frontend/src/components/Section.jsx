export default function Section({ icon: Icon, title, badge, children }) {
  return (
    <section className="glass reveal p-5 sm:p-6">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {Icon && <Icon size={18} className="text-violet-300" />}<h2 className="text-lg font-semibold">{title}</h2>{badge}
      </div>
      {children}
    </section>
  )
}
export function StatusChip({ status }) {
  const m = { ok: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300', inconclusive: 'border-slate-500/40 bg-slate-500/10 text-slate-300', unavailable: 'border-slate-500/40 bg-slate-500/10 text-slate-400' }
  return <span className={`chip ${m[status] || m.ok}`}>{status}</span>
}
