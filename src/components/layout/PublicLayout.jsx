import { useState, useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import DarkToggle from '../ui/DarkToggle.jsx'
import { Button } from '../ui/Button.jsx'
import api from '../../api/client.js'

export default function PublicLayout() {
  const { pathname } = useLocation()
  const { user } = useAuth()
  const [visitorCount, setVisitorCount] = useState(null)

  useEffect(() => {
    api.post('/api/visitor/log').then(r => setVisitorCount(r.data)).catch(() => {})
  }, [])

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="sticky top-0 z-30 border-b bg-card/80 backdrop-blur supports-[backdrop-filter]:bg-card/60">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-sm font-bold tracking-tight text-[#C9A84C]">Market Watch AJN</h1>
              <p className="text-[9px] text-muted-foreground hidden sm:block">PT Agrinas Jaladri Nusantara</p>
            </div>
            <nav className="flex items-center gap-1 ml-4">
              <Link to="/" className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${pathname === '/' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>📊 Harga</Link>
              <Link to="/peta" className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${pathname === '/peta' ? 'bg-primary text-white' : 'text-muted-foreground hover:text-foreground'}`}>🗺️ Peta</Link>
            </nav>
          </div>
          <div className="flex items-center gap-2">
            {visitorCount && <span className="text-[10px] text-muted-foreground">Today Visitor : {visitorCount.today}</span>}
            <DarkToggle />
            {user ? (
              <Link to="/admin"><Button variant="gold" size="xs">{user.nama || 'Admin'} →</Button></Link>
            ) : (
              <Link to="/login"><Button variant="gold" size="xs">🔒 Login</Button></Link>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 container py-6">
        <Outlet />
      </main>
      <footer className="border-t py-4 text-center text-[11px] text-muted-foreground flex-shrink-0">
        Market Watch AJN © 2026 — PT Agrinas Jaladri Nusantara (Persero)
      </footer>
    </div>
  )
}
