import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from '../components/Sidebar.jsx'
import Navbar from '../components/Navbar.jsx'

export default function DashboardLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="relative flex min-h-screen bg-slate-50/90 text-ink-900 transition-colors dark:bg-[#0b0f19] dark:text-ink-100">
      {/* Ambient background glow */}
      <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_0%,rgba(99,102,241,0.08),rgba(255,255,255,0))] dark:bg-[radial-gradient(ellipse_70%_50%_at_50%_0%,rgba(99,102,241,0.14),rgba(11,15,25,0))]" />

      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <Navbar onMenuClick={() => setMobileOpen(true)} />
        <main key={location.pathname} className="mx-auto w-full max-w-7xl flex-1 animate-fade-in p-4 sm:p-6 lg:p-7">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
