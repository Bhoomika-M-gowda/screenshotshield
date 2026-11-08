import { Link, useLocation } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'

export default function Navbar() {
  const { pathname } = useLocation()
  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-ink/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-electric to-violet shadow-[0_0_20px_rgba(99,102,241,.6)]"><ShieldCheck size={20} /></span>
          <span className="text-lg font-bold tracking-tight">Screenshot<span className="h-grad">Shield</span></span>
        </Link>
        <nav className="flex items-center gap-2 text-sm">
          <Link to="/" className={`hidden rounded-lg px-3 py-2 sm:block ${pathname === '/' ? 'text-white' : 'text-slate-400 hover:text-white'}`}>Home</Link>
          <Link to="/analyze" className="btn-primary !px-4 !py-2">Analyze</Link>
        </nav>
      </div>
    </header>
  )
}
