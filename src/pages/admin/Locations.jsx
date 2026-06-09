import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchKnmp } from '../../api/client.js'

export default function Locations() {
  const [locations, setLocations] = useState([])
  const [search, setSearch] = useState('')
  const [prov, setProv] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => { fetchKnmp().then(setLocations) }, [])

  const provs = [...new Set(locations.map(l => l.provinsi).filter(Boolean))].sort()

  const filtered = locations.filter(l => {
    if (prov && l.provinsi !== prov) return false
    if (status && l.status_knmp !== status) return false
    if (search && !`${l.nama_kampung} ${l.kabupaten} ${l.penyedia || ''}`.toLowerCase().includes(search.toLowerCase())) return false
    return true
  }).slice(0, 200)

  return (
    <div>
      <div className="bg-white rounded-xl shadow-sm p-4 mb-4 flex flex-wrap gap-3 items-end">
        <div><label className="block text-[11px] text-slate-500 mb-1">Provinsi</label><select value={prov} onChange={e => setProv(e.target.value)} className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white"><option value="">Semua</option>{provs.map(p => <option key={p} value={p}>{p}</option>)}</select></div>
        <div><label className="block text-[11px] text-slate-500 mb-1">Status</label><select value={status} onChange={e => setStatus(e.target.value)} className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg bg-white"><option value="">Semua</option><option value="HUB">HUB</option><option value="PENYANGGA">Penyangga</option></select></div>
        <div className="flex-1"><label className="block text-[11px] text-slate-500 mb-1">Cari</label><input type="text" value={search} onChange={e => setSearch(e.target.value)} className="w-full px-3 py-1.5 text-xs border border-slate-200 rounded-lg" placeholder="Nama, kab, penyedia..." /></div>
        <div className="flex gap-2"><button onClick={() => { setProv(''); setStatus(''); setSearch('') }} className="px-4 py-1.5 text-xs font-semibold bg-white border border-navy text-navy rounded-lg">Reset</button></div>
      </div>

      <div className="bg-white rounded-xl shadow-sm overflow-x-auto">
        <table className="w-full text-xs">
          <thead><tr className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wide">
            <th className="p-2.5 text-left">ID</th><th className="p-2.5 text-left">Nama</th><th className="p-2.5 text-left">Provinsi</th><th className="p-2.5 text-left">Kabupaten</th><th className="p-2.5 text-left">Status</th><th className="p-2.5 text-left">Progress</th><th></th>
          </tr></thead>
          <tbody>
            {filtered.map(l => {
              const p = l.progress_kumulatif
              const color = p != null && p >= 100 ? 'text-emerald-700 bg-emerald-50' : p != null && p > 0 ? 'text-amber-700 bg-amber-50' : 'text-blue-700 bg-blue-50'
              return (
                <tr key={l.id_lokasi} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="p-2.5">{l.id_lokasi}</td>
                  <td className="p-2.5 font-semibold">{l.nama_kampung}</td>
                  <td className="p-2.5">{l.provinsi}</td>
                  <td className="p-2.5">{l.kabupaten}</td>
                  <td className="p-2.5"><span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${l.status_knmp === 'HUB' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{l.status_knmp}</span></td>
                  <td className="p-2.5"><span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${color}`}>{p != null ? p + '%' : '—'}</span></td>
                  <td className="p-2.5"><Link to={`/admin/locations/${l.id_lokasi}`} className="text-navy font-semibold hover:underline text-[11px]">Detail →</Link></td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
