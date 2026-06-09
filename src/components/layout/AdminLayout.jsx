import { useState } from 'react'
import { Outlet, Link, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'

const superNav = [
  { to: '/admin', label: '📊', text: 'Dashboard' },
  { to: '/admin/locations', label: '📍', text: 'Lokasi KNMP' },
  { to: '/admin/users', label: '👥', text: 'Kelola User' },
]

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  if (!user) return <Navigate to="/login" replace />

  const isSuper = user.role === 'superadmin'
  const navItems = isSuper ? superNav : [
    { to: `/loc/${user.id_lokasi}`, label: '📊', text: 'Dashboard Lokasi' }
  ]

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-40 w-60 bg-gradient-to-b from-slate-900 to-navy text-white sidebar-transition lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-4 border-b border-white/10">
          <h2 className="text-gold font-bold text-sm">Market Watch AJN</h2>
          <p className="text-[10px] text-slate-500">{isSuper ? 'Superadmin' : `KNMP #${user.id_lokasi}`}</p>
        </div>
        <nav className="p-3 space-y-0.5">
          {navItems.map(n => (
            <Link key={n.to} to={n.to}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 text-xs rounded-lg transition ${pathname === n.to || (n.to !== '/admin' && pathname.startsWith(n.to)) ? 'bg-gold/10 text-gold border-l-2 border-gold' : 'text-slate-400 hover:text-white hover:bg-white/5 border-l-2 border-transparent'}`}>
              <span className="text-sm">{n.label}</span> {n.text}
            </Link>
          ))}
          <div className="border-t border-white/10 my-2" />
          <Link to="/" className="flex items-center gap-3 px-3 py-2.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg border-l-2 border-transparent">
            <span>🌐</span> Lihat Website
          </Link>
        </nav>
      </aside>

      {/* Overlay */}
      {sidebarOpen && <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setSidebarOpen(false)} />}

      {/* Main */}
      <div className="flex-1 lg:ml-60">
        <header className="sticky top-0 z-20 bg-white border-b border-slate-200 shadow-sm flex items-center justify-between px-4 lg:px-6 h-14">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden text-navy text-xl">☰</button>
            <span className="text-xs text-slate-500 font-medium">{isSuper ? 'Superadmin Dashboard' : `KNMP #${user.id_lokasi}`}</span>
          </div>
          <div className="flex items-center gap-4 text-xs">
            <Link to="/change-password" className="text-navy hover:underline">Ganti PW</Link>
            <span className="text-slate-400">{user.username}</span>
            <button onClick={logout} className="text-red-600 hover:underline font-semibold">Logout</button>
          </div>
        </header>
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
