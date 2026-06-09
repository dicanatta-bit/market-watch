import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { fetchKnmp } from '../../api/client.js'

export default function LocationDetail() {
  const { id } = useParams()
  const [loc, setLoc] = useState(null)

  useEffect(() => {
    fetchKnmp().then(data => setLoc(data.find(l => l.id_lokasi === parseInt(id))))
  }, [id])

  if (!loc) return <div className="text-slate-400 text-sm">Loading...</div>

  const p = loc.progress_kumulatif
  const color = p != null && p >= 100 ? 'bg-emerald-500' : p != null && p > 0 ? 'bg-amber-500' : 'bg-blue-500'

  return (
    <div>
      <h2 className="text-base font-bold text-navy mb-1">KNMP #{loc.id_lokasi} — {loc.nama_kampung}</h2>
      <p className="text-xs text-slate-500 mb-4">{loc.provinsi} · {loc.kabupaten} · {loc.kecamatan || '—'}</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm p-5">
          <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">Info Lokasi</h3>
          <table className="w-full text-xs">
            <tbody>
              {[
                ['Status KNMP', <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${loc.status_knmp === 'HUB' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{loc.status_knmp}</span>],
                ['Progress', `${p != null ? p + '%' : '—'}`],
                ['Tahun', loc.tahun],
                ['Penyedia', loc.penyedia || '—'],
                ['Nelayan', loc.jumlah_nelayan || '—'],
                ['Kapal', loc.jumlah_kapal || '—'],
                ['Realisasi Fisik', loc.realisasi_fisik != null ? loc.realisasi_fisik + '%' : '—'],
                ['Realisasi Keuangan', loc.realisasi_keuangan != null ? loc.realisasi_keuangan + '%' : '—'],
                ['Koordinat', `${loc.lat}, ${loc.lon}`],
              ].map(([l, v], i) => (
                <tr key={i} className="border-b border-slate-50"><td className="py-2 pr-4 text-slate-500 w-32">{l}</td><td className="py-2 font-semibold">{v}</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-5">
          <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">Progress Bar</h3>
          <div className="h-3 bg-slate-100 rounded-full overflow-hidden mb-4">
            <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${Math.min(p || 0, 100)}%` }} />
          </div>
          <p className="text-xs text-slate-500">Progress kumulatif: <strong>{p != null ? p + '%' : 'Belum ada data'}</strong></p>
          <p className="text-xs text-slate-400 mt-2">Snapshot terakhir: {loc.snapshot_date || '—'}</p>
        </div>
      </div>
    </div>
  )
}
