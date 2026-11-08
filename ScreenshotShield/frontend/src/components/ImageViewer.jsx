import { useState } from 'react'
import { api } from '../services/api.js'

const LAYERS = [
  ['regions', 'Suspicious regions'], ['heatmap', 'Heatmap'], ['ela', 'ELA'], ['noise', 'Noise'], ['edges', 'Edges'], ['original', 'Original'],
]
const BOX = { high: '#ef4444', medium: '#f59e0b', low: '#38bdf8' }

export default function ImageViewer({ data, active, setActive }) {
  const avail = data.images_available
  const [layer, setLayer] = useState('original')
  const [boxes, setBoxes] = useState(true)
  const { width, height } = data.image
  const showLayer = layer === 'regions' ? 'original' : layer // regions layer is drawn as interactive overlay
  return (
    <div className="glass p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {LAYERS.filter(([k]) => k === 'regions' || avail.includes(k)).map(([k, label]) => (
          <button key={k} onClick={() => { setLayer(k); if (k === 'regions') setBoxes(true) }}
            className={`chip cursor-pointer transition ${layer === k ? 'border-electric bg-electric/20 text-white' : 'border-white/10 text-slate-400 hover:text-white'}`}>{label}</button>
        ))}
        {layer !== 'regions' && (
          <label className="ml-auto flex cursor-pointer items-center gap-2 text-xs text-slate-400">
            <input type="checkbox" checked={boxes} onChange={(e) => setBoxes(e.target.checked)} className="accent-violet-500" /> Show region boxes
          </label>
        )}
      </div>
      <div className="relative mx-auto max-h-[70vh] overflow-auto rounded-xl border border-white/10 bg-black/40">
        <div className="relative mx-auto" style={{ maxWidth: Math.min(width, 640) }}>
          <img src={api.imageUrl(data.analysis_id, showLayer)} alt={showLayer} className="block w-full" />
          {boxes && (
            <svg viewBox={`0 0 ${width} ${height}`} className="absolute inset-0 h-full w-full">
              {data.regions.regions.map((r) => {
                const b = r.bbox, sel = active === r.id, col = BOX[r.confidence]
                const fs = Math.max(14, width / 40)
                return (
                  <g key={r.id} onClick={() => setActive(r.id)} className="cursor-pointer">
                    <rect x={b.x} y={b.y} width={b.w} height={b.h} fill={sel ? `${col}33` : 'transparent'} stroke={col} strokeWidth={sel ? Math.max(4, width / 160) : Math.max(2, width / 300)} rx="3" />
                    <rect x={b.x} y={Math.max(b.y - fs * 1.5, 0)} width={fs * 2.2} height={fs * 1.5} fill={col} rx="3" />
                    <text x={b.x + fs * 0.5} y={Math.max(b.y - fs * 1.5, 0) + fs * 1.1} fontSize={fs} fontWeight="700" fill="#000">#{r.id}</text>
                  </g>
                )
              })}
            </svg>
          )}
        </div>
      </div>
      <p className="mt-2 text-xs text-slate-500">
        {{ regions: 'Boxes mark areas worth manual inspection (colour = confidence). Click a box for details.', heatmap: 'Warmer colours = more indicators agree.',
          ela: 'Brighter = larger difference after JPEG recompression. Natural edges also glow; look for isolated bright areas.', noise: 'Local noise level. Dimmed blocks were not testable.',
          edges: 'Canny edge map (supporting signal only).', original: 'Uploaded image.' }[layer]}
      </p>
    </div>
  )
}
