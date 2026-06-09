import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'

export default function PublicLayout() {
  const { pathname } = useLocation()
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-gradient-to-r from-navy to-navy-dark text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between flex-wrap gap-2">
          <div>
            <h1 className="text-lg font-bold text-gold tracking-wide">Market Watch AJN</h1>
            <p className="text-[10px] sm:text-xs text-slate-400">PT Agrinas Jaladri Nusantara (Persero)</p>
          </div>
          <div className="flex items-center gap-3">
            {user ? (
              <span className="text-xs bg-gold/20 border border-gold/40 text-gold px-3 py-1 rounded-full">
                {user.role === 'superadmin' ? 'Superadmin' : `KNMP #${user.id_lokasi}`}
              </span>
            ) : (
              <Link to="/login" className="bg-gold hover:bg-amber-600 text-navy-dark font-bold text-xs sm:text-sm px-4 py-1.5 rounded-lg transition">
                🔒 Login
              </Link>
            )}
          </div>
        </div>
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 flex border-t border-white/10">
          <Link to="/" className={`px-5 py-2.5 text-xs sm:text-sm font-semibold border-b-2 transition ${pathname === '/' ? 'border-gold text-gold' : 'border-transparent text-slate-400 hover:text-white'}`}>
            📊 Harga Komoditas
          </Link>
          <Link to="/peta" className={`px-5 py-2.5 text-xs sm:text-sm font-semibold border-b-2 transition ${pathname === '/peta' ? 'border-gold text-gold' : 'border-transparent text-slate-400 hover:text-white'}`}>
            🗺️ Peta KNMP
          </Link>
        </nav>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <Outlet />
      </main>
      <footer className="max-w-7xl mx-auto px-4 sm:px-6 py-4 text-center text-[11px] text-slate-400 border-t border-slate-200">
        Market Watch AJN &copy; 2026 — PT Agrinas Jaladri Nusantara (Persero)
      </footer>
    </div>
  )
}
