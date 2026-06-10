import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { Card } from '../components/ui/Card.jsx'
import { Button } from '../components/ui/Button.jsx'
import { fetchPrices, fetchStats } from '../api/client.js'

const PULAU_LIST = ["Jawa-Bali", "Sumatera", "Kalimantan", "Sulawesi", "NTT-NTB", "Maluku", "Papua"]

export default function Admin() {
  const { user, logout } = useAuth()
  const [prices, setPrices] = useState([])
  const [stats, setStats] = useState(null)
  const [pulau, setPulau] = useState('')

  useEffect(() => { fetchPrices().then(setPrices); fetchStats().then(setStats) }, [])

  const exportURL = pulau ? `/api/export/excel?pulau=${encodeURIComponent(pulau)}` : '/api/export/excel'

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
        {/* Export */}
        <Card className="p-5 mb-6">
          <h2 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">📥 Export Excel</h2>
          <div className="flex flex-wrap items-end gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Filter Pulau</label>
              <select value={pulau} onChange={e => setPulau(e.target.value)} className="px-3 py-1.5 text-sm border rounded-lg bg-white">
                <option value="">Semua Lokasi</option>
                {PULAU_LIST.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <a href={exportURL} download>
              <Button variant="gold">📥 Export {pulau || 'Semua'} → Excel</Button>
            </a>
          </div>
          <p className="text-xs text-slate-400 mt-3">
            Akses via API: <code className="bg-slate-100 px-1 rounded">/api/export/excel?pulau=Jawa-Bali</code> · Swagger: <a href="/api/docs" className="text-blue-600 hover:underline">/api/docs</a>
          </p>
        </Card>

        {/* Commodity Prices */}
        <h2 className="text-sm font-bold text-navy mb-3">Harga Komoditas</h2>
        <Card className="overflow-hidden mb-6">
          <table className="w-full text-xs">
            <thead><tr className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wide">
              <th className="p-2.5 text-left">Komoditas</th><th className="p-2.5 text-left">Size</th><th className="p-2.5 text-right">Tambak</th><th className="p-2.5 text-right">Ekspor</th>
            </tr></thead>
            <tbody>
              {prices.map((p,i) => (
                <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="p-2.5 font-semibold">{p.komoditas}</td><td className="p-2.5">{p.size}</td>
                  <td className="p-2.5 text-right">Rp {(p.harga_tambak_low||0).toLocaleString('id')} – {(p.harga_tambak_high||0).toLocaleString('id')}</td>
                  <td className="p-2.5 text-right">{p.harga_ekspor_low ? `$${p.harga_ekspor_low.toFixed(2)}` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {/* Stats */}
        <h2 className="text-sm font-bold text-navy mb-3">Statistik</h2>
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-navy">{stats?.total_lokasi||723}</div><div className="text-[11px] text-slate-500">Lokasi KNMP</div></Card>
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-slate-600">{stats?.total_nelayan?.toLocaleString('id')||'—'}</div><div className="text-[11px] text-slate-500">Nelayan</div></Card>
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-slate-600">{stats?.total_kapal?.toLocaleString('id')||'—'}</div><div className="text-[11px] text-slate-500">Kapal</div></Card>
        </div>
      </div>
    </div>
  )
}
