import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Landing from './pages/Landing.jsx'
import Analyze from './pages/Analyze.jsx'
import Results from './pages/Results.jsx'
import Report from './pages/Report.jsx'

export default function App() {
  return (
    <HashRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/results/:id" element={<Results />} />
        <Route path="/report/:id" element={<Report />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <footer className="mx-auto mt-16 max-w-6xl px-5 pb-10 text-center text-xs text-slate-500">
        ScreenshotShield — heuristic forensic aid for manual review. Results are not proof of authenticity or forgery. Uploads are kept temporarily and auto-deleted.
      </footer>
    </HashRouter>
  )
}
