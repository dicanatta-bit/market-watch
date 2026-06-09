import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { fetchKnmp } from '../../api/client.js'

export default function LocDashboard() {
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
      <h2 className="text-base font-bold text-navy mb-1">{loc.nama_kampung}</h2>
      <div className="flex flex-wrap gap-2 mb-4 text-xs">
        <span className="text-slate-500">{loc.provinsi} · {loc.kabupaten}</span>
        <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${loc.status_knmp === 'HUB' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{loc.status_knmp}</span>
        <span className="text-slate-400">Nelayan {loc.jumlah_nelayan || 0} · Kapal {loc.jumlah_kapal || 0}</span>
      </div>

      {/* Progress Kumulatif */}
      <div className="bg-white rounded-xl shadow-sm p-5 mb-4">
        <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">Progress Kumulatif</h3>
        <div className="h-4 bg-slate-100 rounded-full overflow-hidden mb-3">
          <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${Math.min(p || 0, 100)}%` }} />
        </div>
        <div className="flex justify-between text-xs text-slate-600">
          <span><strong>{p != null ? p + '%' : '0%'}</strong> kumulatif</span>
          <span>Fisik: <strong>{loc.realisasi_fisik != null ? loc.realisasi_fisik + '%' : '—'}</strong></span>
          <span>Keuangan: <strong>{loc.realisasi_keuangan != null ? loc.realisasi_keuangan + '%' : '—'}</strong></span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Item Pembangunan */}
        <div className="bg-white rounded-xl shadow-sm p-5">
          <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">Item Pembangunan</h3>
          {['Bangunan TPI', 'Dermaga', 'Cold Storage'].map((item, i) => (
            <div key={i} className="py-2.5 border-b border-slate-100 last:border-0">
              <div className="flex justify-between items-center mb-1">
                <strong className="text-xs">{item}</strong>
                <button className="text-[10px] font-semibold bg-white border border-navy text-navy px-2 py-0.5 rounded hover:bg-slate-50">Update</button>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-amber-400 rounded-full" style={{ width: `${Math.min(i * 30 + 10, 100)}%` }} />
              </div>
            </div>
          ))}
          <p className="text-[11px] text-slate-400 mt-3">Login via admin_lokasi untuk update real-time</p>
        </div>

        {/* Harga TPI + Kendala */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm p-5">
            <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">Harga TPI</h3>
            <div className="flex gap-2 mb-3">
              <input type="text" placeholder="Komoditas" className="flex-1 px-2 py-1.5 text-xs border border-slate-200 rounded-lg" />
              <input type="text" placeholder="TPI" className="w-24 px-2 py-1.5 text-xs border border-slate-200 rounded-lg" />
              <input type="number" placeholder="Harga" className="w-20 px-2 py-1.5 text-xs border border-slate-200 rounded-lg" />
              <button className="px-3 py-1.5 text-xs font-bold bg-navy text-white rounded-lg hover:bg-navy-dark">+</button>
            </div>
            <p className="text-[11px] text-slate-400">Belum ada data harga. Input harga pertama!</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-5">
            <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">⚠️ Kendala & Tindak Lanjut</h3>
            <textarea rows={2} placeholder="Deskripsi kendala..." className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg mb-2 resize-none" />
            <textarea rows={2} placeholder="Rencana tindak lanjut..." className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg mb-2 resize-none" />
            <button className="px-4 py-1.5 text-xs font-semibold bg-white border border-navy text-navy rounded-lg hover:bg-slate-50">Simpan</button>
          </div>
        </div>
      </div>

      {/* CCTV */}
      <div className="bg-white rounded-xl shadow-sm p-5 mt-4">
        <h3 className="text-sm font-bold text-navy mb-3 pb-2 border-b-2 border-gold">📹 CCTV Monitoring</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {['CCTV Depan TPI', 'CCTV Dermaga'].map((label, i) => (
            <div key={i} className="bg-slate-900 rounded-lg p-10 flex items-center justify-center text-slate-600 text-xs text-center min-h-[150px]">
              <div><div className="text-3xl mb-1">📹</div>{label}<br /><span className="text-[10px]">Stream tersedia setelah integrasi CCTV</span></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
