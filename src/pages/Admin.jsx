import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { Card } from '../components/ui/Card.jsx'
import { Button } from '../components/ui/Button.jsx'
import api from '../api/client.js'

  const PULAU_LIST = ["Jawa-Bali", "Sumatera", "Kalimantan", "Sulawesi", "NTT-NTB", "Maluku", "Papua"]
  const [visitorStats, setVisitorStats] = useState(null)

  useEffect(() => { api.get('/api/prices').then(r => setPrices(r.data.data||[])).catch(() => {}); api.get('/api/stats').then(r => setStats(r.data.data||{})).catch(() => {}); api.get('/api/visitor/stats').then(r => setVisitorStats(r.data.data||{})).catch(() => {}) }, [])

  const triggerScrape = async () => {
    setScraping(true)
    setScrapeLog('Menjalankan scraper...')
    try {
      const { data } = await api.post('/api/scrape/trigger')
      setScrapeLog(data.logs?.join('\n\n') || 'Selesai')
      // Refresh data
      fetchPrices().then(setPrices)
      fetchStats().then(setStats)
    } catch (e) {
      setScrapeLog('Gagal: ' + (e.response?.data?.detail || e.message))
    } finally { setScraping(false) }
  }

  const exportURL = pulau ? `/market-watch/api/export/excel?pulau=${encodeURIComponent(pulau)}` : '/market-watch/api/export/excel'

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-navy text-white flex items-center justify-between px-6 h-12">
        <h1 className="text-sm font-bold text-gold">Market Watch AJN · Admin</h1>
        <div className="flex items-center gap-4 text-xs">
          <Link to="/" className="text-slate-400 hover:text-white">← Website</Link>
          <Link to="/peta" className="text-slate-400 hover:text-white">🗺️ Peta</Link>
          <span>{user?.username}</span>
          <button onClick={logout} className="text-red-400 hover:text-red-300 font-semibold">Logout</button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto p-6">

        {/* Manual Scrape */}
        <Card className="p-5 mb-6">
          <h2 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">🔄 Manual Scrape</h2>
          <p className="text-xs text-slate-500 mb-3">Jalankan scraper untuk update data eKNMP, harga komoditas, SIHI, dan alert.</p>
          <Button variant="gold" onClick={triggerScrape} disabled={scraping}>
            {scraping ? '⏳ Scraping...' : '🔄 Scrape Sekarang'}
          </Button>
          {scrapeLog && (
            <pre className="mt-3 p-3 bg-slate-900 text-green-400 text-[11px] rounded-lg overflow-auto max-h-60 whitespace-pre-wrap">{scrapeLog}</pre>
          )}
        </Card>

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
            <a href={exportURL}><Button variant="outline">📥 Export {pulau || 'Semua'}</Button></a>
          </div>
          <p className="text-xs text-slate-400 mt-3">API: <code className="bg-slate-100 px-1 rounded">/api/export/excel?pulau=Jawa-Bali</code> · <a href="/market-watch/docs" className="text-blue-600 hover:underline" target="_blank">Swagger /docs</a></p>
        </Card>

        {/* Stats */}
        <h2 className="text-sm font-bold text-navy mb-3">Statistik</h2>
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-navy">{stats?.total_lokasi||723}</div><div className="text-[11px] text-slate-500">Lokasi KNMP</div></Card>
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-emerald-700">{stats?.total_nelayan?.toLocaleString('id')||'—'}</div><div className="text-[11px] text-slate-500">Nelayan</div></Card>
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-amber-700">{stats?.total_kapal?.toLocaleString('id')||'—'}</div><div className="text-[11px] text-slate-500">Kapal</div></Card>
        </div>

        {/* Visitor Stats */}
        <h2 className="text-sm font-bold text-navy mb-3">👁️ Visitor</h2>
        <div className="grid grid-cols-3 gap-3 mb-6">
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-navy">{visitorStats?.total||0}</div><div className="text-[11px] text-slate-500">Total Kunjungan</div></Card>
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-emerald-700">{visitorStats?.today||0}</div><div className="text-[11px] text-slate-500">Hari Ini</div></Card>
          <Card className="p-4 text-center"><div className="text-2xl font-extrabold text-amber-700">{visitorStats?.unique_ips||0}</div><div className="text-[11px] text-slate-500">IP Unik</div></Card>
        </div>

        {visitorStats?.recent_logs?.length > 0 && (
          <Card className="overflow-hidden mb-6">
            <table className="w-full text-xs">
              <thead><tr className="bg-slate-50 font-semibold uppercase tracking-wide">
                <th className="p-2.5 text-left text-slate-500">IP</th><th className="p-2.5 text-left text-slate-500">Halaman</th><th className="p-2.5 text-left text-slate-500">User Agent</th><th className="p-2.5 text-left text-slate-500">Waktu</th>
              </tr></thead>
              <tbody>
                {visitorStats.recent_logs.slice(0, 20).map((v, i) => (
                  <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="p-2.5 font-mono text-[10px]">{v.ip}</td>
                    <td className="p-2.5">{v.page}</td>
                    <td className="p-2.5 text-[10px] text-slate-500">{v.ua}</td>
                    <td className="p-2.5 text-slate-500">{v.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}

        {/* Prices */}
        <h2 className="text-sm font-bold text-navy mb-3">Harga Komoditas</h2>
        <Card className="overflow-hidden mb-6">
          <table className="w-full text-xs">
            <thead><tr className="bg-slate-50 font-semibold uppercase tracking-wide">
              <th className="p-2.5 text-left text-slate-500">Komoditas</th><th className="p-2.5 text-left text-slate-500">Size</th><th className="p-2.5 text-right text-slate-500">Tambak</th><th className="p-2.5 text-right text-slate-500">Ekspor</th>
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
      </div>
    </div>
  )
}
