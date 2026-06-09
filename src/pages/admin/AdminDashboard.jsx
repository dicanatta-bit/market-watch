import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchStats, fetchPrices } from '../../api/client.js'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  useEffect(() => { fetchStats().then(setStats) }, [])

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[
          [stats?.total_lokasi || 723, 'Total Lokasi', 'navy'],
          [stats?.selesai || 63, 'Selesai', 'green'],
          [stats?.berjalan || 36, 'Berjalan', 'gold'],
          [724, 'Total User', 'blue'],
        ].map(([v, l, c], i) => (
          <div key={i} className={`bg-white rounded-xl p-4 shadow-sm border-l-4 ${c === 'green' ? 'border-l-emerald-500' : c === 'gold' ? 'border-l-gold' : c === 'blue' ? 'border-l-blue-500' : 'border-l-navy'}`}>
            <div className={`text-xl font-extrabold ${c === 'green' ? 'text-emerald-700' : c === 'gold' ? 'text-amber-700' : c === 'blue' ? 'text-blue-700' : 'text-navy'}`}>{v}</div>
            <div className="text-[11px] text-slate-500 mt-1">{l}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm p-5">
          <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">Quick Links</h3>
          <Link to="/admin/locations" className="block w-full text-left px-4 py-2.5 text-xs font-semibold bg-navy text-white rounded-lg mb-2 hover:bg-navy-dark transition text-center">📍 Manage Locations</Link>
          <Link to="/admin/users" className="block w-full text-left px-4 py-2.5 text-xs font-semibold bg-white text-navy border border-navy rounded-lg mb-2 hover:bg-slate-50 transition text-center">👥 Manage Users</Link>
          <a href="/api/export/excel" className="block w-full text-left px-4 py-2.5 text-xs font-semibold bg-gold text-white rounded-lg mb-2 hover:bg-amber-600 transition text-center">📥 Export Excel</a>
          <a href="/api/export/pdf" className="block w-full text-left px-4 py-2.5 text-xs font-semibold bg-white text-navy border border-navy rounded-lg hover:bg-slate-50 transition text-center">📄 Export PDF</a>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-5">
          <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">Link Publik</h3>
          <a href="/" target="_blank" className="block w-full text-left px-4 py-2.5 text-xs font-semibold bg-white text-navy border border-navy rounded-lg mb-2 hover:bg-slate-50 transition text-center">📊 Dashboard Harga</a>
          <a href="/peta" target="_blank" className="block w-full text-left px-4 py-2.5 text-xs font-semibold bg-white text-navy border border-navy rounded-lg hover:bg-slate-50 transition text-center">🗺️ Peta KNMP</a>
        </div>
      </div>
    </div>
  )
}
