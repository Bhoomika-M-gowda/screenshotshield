import { useEffect, useState } from 'react'

const BASE = import.meta.env.VITE_API_BASE || ''

async function parse(res) {
  let data = null
  try { data = await res.json() } catch { /* non-JSON */ }
  if (!res.ok) throw new Error(data?.detail || data?.error || `Request failed (${res.status})`)
  return data
}

export const api = {
  health: () => fetch(`${BASE}/api/health`).then(parse),
  upload: (file) => { const f = new FormData(); f.append('file', file); return fetch(`${BASE}/api/upload`, { method: 'POST', body: f }).then(parse) },
  analyze: (upload_id) => fetch(`${BASE}/api/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ upload_id }) }).then(parse),
  results: (id) => fetch(`${BASE}/api/results/${id}`).then(parse),
  reportUrl: (id) => `${BASE}/api/report/${id}`,
  imageUrl: (id, name) => `${BASE}/api/results/${id}/image/${name}`,
  remove: (id) => fetch(`${BASE}/api/results/${id}`, { method: 'DELETE' }).then(parse),
}

/** Loads (and polls while processing) an analysis result. */
export function useResult(id) {
  const [state, setState] = useState({ loading: true, data: null, error: null, progress: null })
  useEffect(() => {
    let stop = false, timer
    const tick = async () => {
      try {
        const d = await api.results(id)
        if (stop) return
        if (d.status === 'complete') setState({ loading: false, data: d, error: null, progress: null })
        else { setState((s) => ({ ...s, progress: d })); timer = setTimeout(tick, 600) }
      } catch (e) { if (!stop) setState({ loading: false, data: null, error: e.message, progress: null }) }
    }
    tick()
    return () => { stop = true; clearTimeout(timer) }
  }, [id])
  return state
}
