import { useState } from 'react'
import { Outlet, Link, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import DarkToggle from '../ui/DarkToggle.jsx'
import { Button } from '../ui/Button.jsx'
import { LayoutDashboard, MapPin, Users, Download, Globe, LogOut } from 'lucide-react'

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)

  if (!user) return <Navigate to="/login" replace />

  const isSuper = user.role === 'superadmin'
  const items = isSuper ? [
    { to: '/admin', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/admin/locations', icon: MapPin, label: 'Lokasi KNMP' },
    { to: '/admin/users', icon: Users, label: 'User' },
  ] : [
    { to: `/loc/${user.id_lokasi}`, icon: LayoutDashboard, label: 'Dashboard' },
  ]

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-40 w-60 bg-card border-r transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-4 border-b">
          <h2 className="text-sm font-bold text-[#C9A84C]">Market Watch AJN</h2>
          <p className="text-[10px] text-muted-foreground">{isSuper ? 'Superadmin' : `#${user.id_lokasi}`}</p>
        </div>
        <nav className="p-3 space-y-0.5">
          {items.map(n => (
            <Link key={n.to} to={n.to} onClick={() => setOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 text-xs rounded-md transition ${pathname === n.to ? 'bg-primary/10 text-primary font-semibold' : 'text-muted-foreground hover:bg-accent'}`}>
              <n.icon className="h-4 w-4" /> {n.label}
            </Link>
          ))}
          <hr className="my-2" />
          <Link to="/" className="flex items-center gap-3 px-3 py-2.5 text-xs text-muted-foreground hover:bg-accent rounded-md"><Globe className="h-4 w-4" /> Website</Link>
        </nav>
      </aside>
      {open && <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setOpen(false)} />}

      {/* Main */}
      <div className="flex-1 lg:ml-60">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b bg-card/80 backdrop-blur px-4 gap-4">
          <div className="flex items-center gap-3">
            <button onClick={() => setOpen(!open)} className="lg:hidden"><LayoutDashboard className="h-5 w-5" /></button>
            <span className="text-xs text-muted-foreground font-medium">{isSuper ? 'Superadmin' : `KNMP #${user.id_lokasi}`}</span>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <DarkToggle />
            <span className="text-muted-foreground">{user.username}</span>
            <button onClick={logout} className="text-destructive hover:underline font-semibold">Logout</button>
          </div>
        </header>
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
