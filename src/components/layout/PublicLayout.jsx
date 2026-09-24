import { useEffect } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { LogIn, MapPinned, TrendingUp } from 'lucide-react'
import api from '../../api/client.js'

export default function PublicLayout() {
  const { pathname } = useLocation()
  useEffect(() => { api.post('/api/visitor/log').catch(() => {}) }, [])
  return <div className="mw-shell"><header className="mw-header"><div className="mw-header-inner"><Link to="/" className="mw-brand"><span className="mw-brand-symbol">A<span>✳</span></span><span><strong>MARKET WATCH</strong><small>AGRINAS JALADRI NUSANTARA</small></span></Link><nav className="mw-nav"><Link to="/" className={pathname === '/' ? 'active' : ''}><TrendingUp size={16}/> Harga</Link><Link to="/peta" className={pathname === '/peta' ? 'active' : ''}><MapPinned size={16}/> Peta KNMP</Link><Link to="/login" className="mw-nav-login"><LogIn size={16}/> Login</Link></nav></div></header><main className="mw-main"><Outlet /></main><footer className="mw-footer"><span>© {new Date().getFullYear()} PT Agrinas Jaladri Nusantara</span><span>BUILT FOR BETTER DECISIONS / MARKET WATCH</span></footer></div>
}
