import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Card } from '../components/ui/Card.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Input } from '../components/ui/Input.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { fetchPrices, fetchStats, fetchKnmp } from '../api/client.js'

export default function Admin() {
  const { user, logout } = useAuth()
  const [prices, setPrices] = useState([])
  const [stats, setStats] = useState(null)

  useEffect(() => { fetchPrices().then(setPrices); fetchStats().then(setStats) }, [])

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-navy text-white flex items-center justify-between px-6 h-12">
        <h1 className="text-sm font-bold text-gold">Market Watch AJN · Admin</h1>
        <div className="flex items-center gap-4 text-xs">
          <a href="/" className="text-slate-400 hover:text-white">← Website</a>
          <span>{user?.username}</span>
          <button onClick={logout} className="text-red-400 hover:text-red-300 font-semibold">Logout</button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto p-6">
        <h2 className="text-base font-bold text-navy mb-4">Commodity Prices</h2>
        <Card className="overflow-hidden mb-6">
          <table className="w-full text-xs">
            <thead><tr className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wide">
              <th className="p-2.5 text-left">Komoditas</th><th className="p-2.5 text-left">Size</th>
              <th className="p-2.5 text-right">Tambak (Rp/kg)</th><th className="p-2.5 text-right">Ekspor (USD/kg)</th>
            </tr></thead>
            <tbody>
              {prices.map((p,i) => (
                <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="p-2.5 font-semibold">{p.komoditas}</td><td className="p-2.5">{p.size}</td>
                  <td className="p-2.5 text-right">{(p.harga_tambak_low||0).toLocaleString('id')} – {(p.harga_tambak_high||0).toLocaleString('id')}</td>
                  <td className="p-2.5 text-right">{p.harga_ekspor_low ? `$${p.harga_ekspor_low.toFixed(2)}` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <h2 className="text-base font-bold text-navy mb-4">Statistik</h2>
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-navy">{stats?.total_lokasi||723}</div><div className="text-[11px] text-slate-500">Lokasi KNMP</div></Card>
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-emerald-700">{stats?.selesai||0}</div><div className="text-[11px] text-slate-500">Selesai</div></Card>
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-amber-700">{stats?.berjalan||0}</div><div className="text-[11px] text-slate-500">Berjalan</div></Card>
        </div>

        <div className="flex gap-3">
          <a href="/api/export/excel"><Button variant="outline" size="sm">📥 Export Excel</Button></a>
        </div>
      </div>
    </div>
  )
}
