import { useState, useEffect } from 'react'
import StatCard from '../components/cards/StatCard.jsx'
import CommodityCard from '../components/cards/CommodityCard.jsx'
import { fetchPrices, fetchRegionalPrices, fetchStats } from '../api/client.js'

export default function Home() {
  const [prices, setPrices] = useState([])
  const [regional, setRegional] = useState({})
  const [stats, setStats] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    fetchPrices().then(setPrices)
    fetchRegionalPrices().then(setRegional)
    fetchStats().then(setStats)
  }, [])

  const isFish = /tuna|cakalang|kakap|kerapu|cumi|lobster/i
  const budidaya = prices.filter(p => !isFish.test(p.komoditas))
  const tangkap = prices.filter(p => isFish.test(p.komoditas))
  const filtered = filter === 'all' ? prices : filter === 'b' ? budidaya : tangkap

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <StatCard value={prices.length} label="Komoditas Dipantau" />
        <StatCard value={0} label="Alert Aktif" color="gold" />
        <StatCard value={stats?.total_lokasi || 723} label="Lokasi KNMP" color="blue" />
        <StatCard value="63.1%" label="Progress Nasional" color="green" />
      </div>

      <h2 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-gold" /> Harga Tambak — 09 Juni 2026
      </h2>

      <div className="flex gap-2 mb-4">
        {['all','b','t'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-4 py-1.5 text-xs font-bold rounded-full border-2 transition ${filter === f ? 'bg-navy text-white border-navy' : 'bg-white text-slate-500 border-slate-200 hover:border-navy'}`}>
            {f === 'all' ? 'Semua' : f === 'b' ? 'Budidaya' : 'Tangkap'}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
        {filtered.map((p, i) => <CommodityCard key={i} item={p} />)}
      </div>

      <h2 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-gold" /> Harga per Wilayah
      </h2>
      <div className="bg-white rounded-xl shadow-sm overflow-x-auto mb-6">
        <table className="w-full text-xs">
          <thead><tr className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wide">
            <th className="p-2.5 text-left">Wilayah</th><th className="p-2.5 text-left">Komoditas</th><th className="p-2.5 text-left">Size</th><th className="p-2.5 text-right">Harga Tambak</th>
          </tr></thead>
          <tbody>
            {Object.entries(regional).slice(0, 10).map(([wil, items]) =>
              items.slice(0, 2).map((p, i) => (
                <tr key={`${wil}-${i}`} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="p-2.5">{i === 0 ? <strong>{wil}</strong> : ''}</td>
                  <td className="p-2.5">{p.komoditas}</td>
                  <td className="p-2.5">{p.size}</td>
                  <td className="p-2.5 text-right font-bold">Rp {(p.harga_low || 0).toLocaleString('id')} – {(p.harga_high || 0).toLocaleString('id')}/kg</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
