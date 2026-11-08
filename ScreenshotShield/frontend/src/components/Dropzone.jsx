import { useRef, useState } from 'react'
import { UploadCloud } from 'lucide-react'

export default function Dropzone({ onFile, disabled }) {
  const input = useRef(null)
  const [over, setOver] = useState(false)
  return (
    <div
      onClick={() => !disabled && input.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setOver(true) }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); const f = e.dataTransfer.files?.[0]; if (f && !disabled) onFile(f) }}
      className={`glass group flex cursor-pointer flex-col items-center justify-center gap-3 border-2 border-dashed px-6 py-14 text-center transition ${over ? 'border-electric bg-electric/10' : 'border-white/15 hover:border-violet/60'}`}
      role="button" tabIndex={0} aria-label="Upload a screenshot"
    >
      <span className="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-electric/30 to-violet/30 text-sky-300 transition group-hover:scale-110"><UploadCloud size={30} /></span>
      <div className="text-lg font-semibold">Drag & drop a screenshot here</div>
      <div className="text-sm text-slate-400">or click to browse — JPEG, PNG or WebP, up to 10 MB</div>
      <input ref={input} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); e.target.value = '' }} />
    </div>
  )
}
