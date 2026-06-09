import { useEffect, useRef, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.markercluster'
import { fetchKnmp } from '../api/client.js'

function KnmpLayer({ markers }) {
  const map = useMap()

  useEffect(() => {
    if (!markers.length) return
    // Use MarkerCluster via L.markerClusterGroup
    const mcg = L.markerClusterGroup({ chunkedLoading: true, maxClusterRadius: 55 })

    const batchSize = 100
    let idx = 0
    const allCircleMarkers = []

    function addBatch() {
      const chunk = markers.slice(idx, idx + batchSize)
      chunk.forEach(m => {
        const p = m.progress_kumulatif
        const color = p != null && p >= 100 ? '#10B981' : p != null && p > 0 ? '#F59E0B' : m.status_knmp === 'PENYANGGA' ? '#94A3B8' : '#3B82F6'
        const radius = m.status_knmp === 'HUB' ? 7 : 5

        const circle = L.circleMarker([m.lat || 0, m.lon || 0], {
          radius, fillColor: color, color: '#fff', weight: 1.5, fillOpacity: 0.9
        })

        const popContent = `<div style="min-width:240px">
          <div style="background:#f8fafc;padding:8px 12px;font-weight:700;color:#1B3A6B;border-bottom:1px solid #e2e8f0">${m.nama_kampung}</div>
          <div style="padding:6px 12px;font-size:12px">
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Provinsi</span><b>${m.provinsi}</b></div>
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Kabupaten</span><b>${m.kabupaten}</b></div>
            ${m.kecamatan ? `<div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Kecamatan</span><b>${m.kecamatan}</b></div>` : ''}
            ${m.jumlah_nelayan || m.jumlah_kapal ? `<div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Nelayan/Kapal</span><b>${m.jumlah_nelayan || 0} / ${m.jumlah_kapal || 0}</b></div>` : ''}
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Status</span><b>${m.status_knmp}</b></div>
            <div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Progress</span><b>${p != null ? p + '%' : '—'}</b></div>
          </div>
          ${p != null ? `<div style="height:4px;background:#e2e8f0;margin:0"><div style="height:100%;width:${Math.min(p, 100)}%;background:${color}"></div></div>` : ''}
          <div style="padding:4px 12px;text-align:center;font-size:10px;color:#94a3b8"><a href="/login" style="color:#3B82F6">🔒 Login</a> untuk update progress</div>
        </div>`

        circle.bindPopup(popContent, { maxWidth: 320 })
        circle.bindTooltip(`<b>${m.nama_kampung}</b><br>${m.status_knmp} · ${p != null ? p + '%' : '—'}`, { direction: 'top' })

        allCircleMarkers.push(circle)
      })
      mcg.addLayers(allCircleMarkers.slice(-chunk.length))
      idx += batchSize
      if (idx < markers.length) {
        requestAnimationFrame(addBatch)
      } else {
        map.addLayer(mcg)
      }
    }

    addBatch()
    return () => { map.removeLayer(mcg) }
  }, [markers, map])

  return null
}

export default function MapPage() {
  const [markers, setMarkers] = useState([])
  const [search, setSearch] = useState('')
  const [provFilter, setProvFilter] = useState('')
  const [statFilter, setStatFilter] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => { fetchKnmp().then(setMarkers) }, [])

  const filtered = markers.filter(m => {
    if (provFilter && m.provinsi !== provFilter) return false
    const p = m.progress_kumulatif
    if (statFilter === 'HUB' && m.status_knmp !== 'HUB') return false
    if (statFilter === 'PENYANGGA' && m.status_knmp !== 'PENYANGGA') return false
    if (statFilter === 'selesai' && (p == null || p < 100)) return false
    if (statFilter === 'berjalan' && (p == null || p <= 0 || p >= 100)) return false
    if (search && !`${m.nama_kampung} ${m.kabupaten} ${m.penyedia || ''}`.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const provs = [...new Set(markers.map(m => m.provinsi).filter(Boolean))].sort()
  const selesai = markers.filter(m => (m.progress_kumulatif || 0) >= 100).length
  const berjalan = markers.filter(m => (m.progress_kumulatif || 0) > 0 && (m.progress_kumulatif || 0) < 100).length

  return (
    <div className="-mx-4 sm:-mx-6 -my-6 fixed inset-0 top-[81px] flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-60' : 'w-0'} transition-all overflow-hidden lg:w-60 bg-white border-r border-slate-200 flex-shrink-0 z-10`}>
        <div className="p-3 space-y-3 overflow-y-auto h-full">
          <div className="grid grid-cols-2 gap-2">
            {[
              [markers.length, 'Total'], [markers.length, 'Live eKNMP'], [selesai, 'Selesai'], [berjalan, 'Berjalan']
            ].map(([v, l], i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-2.5 text-center border border-slate-100">
                <div className="text-lg font-extrabold text-navy">{v}</div>
                <div className="text-[10px] text-slate-500">{l}</div>
              </div>
            ))}
          </div>

          <input type="text" placeholder="Cari nama, kab, penyedia…" value={search} onChange={e => setSearch(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:border-gold focus:ring-1 focus:ring-gold outline-none" />

          <div>
            <label className="block text-[11px] text-slate-500 mb-1">Provinsi</label>
            <select value={provFilter} onChange={e => setProvFilter(e.target.value)} className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-lg bg-white">
              <option value="">Semua</option>
              {provs.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-[11px] text-slate-500 mb-1">Status</label>
            <select value={statFilter} onChange={e => setStatFilter(e.target.value)} className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded-lg bg-white">
              <option value="">Semua</option>
              <option value="HUB">HUB</option>
              <option value="PENYANGGA">Penyangga</option>
              <option value="selesai">Selesai</option>
              <option value="berjalan">Berjalan</option>
            </select>
          </div>
          <button onClick={() => { setSearch(''); setProvFilter(''); setStatFilter('') }} className="w-full py-1.5 text-xs font-semibold bg-slate-100 text-navy rounded-lg hover:bg-slate-200">↺ Reset</button>

          <div className="border-t pt-2 text-[11px] text-slate-400 space-y-1">
            <div className="flex justify-between"><span>🟢 Selesai</span><span>{selesai}</span></div>
            <div className="flex justify-between"><span>🟡 Berjalan</span><span>{berjalan}</span></div>
            <div className="flex justify-between"><span>🔵 Siap</span><span>{markers.length - selesai - berjalan}</span></div>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="absolute top-2 left-2 z-20 bg-white shadow px-2 py-1 text-sm rounded lg:hidden">
          {sidebarOpen ? '✕' : '☰'}
        </button>
        <MapContainer center={[-2.5, 118]} zoom={5} className="w-full h-full" preferCanvas>
          <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            attribution='&copy; OSM &copy; CARTO' subdomains="abcd" maxZoom={19} />
          <KnmpLayer markers={filtered} />
        </MapContainer>
      </div>
    </div>
  )
}
