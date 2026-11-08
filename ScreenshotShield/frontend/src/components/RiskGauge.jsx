import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts'

export const CAT = {
  Low: { color: '#22c55e', text: 'text-green-400', chip: 'border-green-500/40 bg-green-500/10 text-green-300' },
  Medium: { color: '#f59e0b', text: 'text-amber-400', chip: 'border-amber-500/40 bg-amber-500/10 text-amber-300' },
  High: { color: '#ef4444', text: 'text-red-400', chip: 'border-red-500/40 bg-red-500/10 text-red-300' },
}

export default function RiskGauge({ score, category }) {
  const c = CAT[category]
  return (
    <div className="relative mx-auto h-56 w-56">
      <RadialBarChart width={224} height={224} innerRadius="78%" outerRadius="100%" data={[{ v: score, fill: c.color }]} startAngle={225} endAngle={-45}>
        <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
        <RadialBar dataKey="v" cornerRadius={12} background={{ fill: 'rgba(255,255,255,.06)' }} isAnimationActive />
      </RadialBarChart>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className={`text-5xl font-extrabold tabular-nums ${c.text}`}>{score}</div>
          <div className="text-xs uppercase tracking-widest text-slate-400">of 100</div>
        </div>
      </div>
    </div>
  )
}
