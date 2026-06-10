import { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, CircleMarker, useMap } from 'react-leaflet'
import { Link } from 'react-router-dom'
import L from 'leaflet'
import 'leaflet.markercluster'
import { fetchKnmp } from '../api/client.js'
import { Button } from '../components/ui/Button.jsx'
import { Input } from '../components/ui/Input.jsx'
import { Badge } from '../components/ui/Badge.jsx'

const STATUS_COLOR = {
  selesai: '#10B981', berjalan: '#F59E0B', siap: '#3B82F6', penyangga: '#94A3B8'
}

function popupHTML(m) {
  const p = m.progress_kumulatif
  const sts = p != null && p >= 100 ? 'selesai' : p != null && p > 0 ? 'berjalan' : 'siap'
  const sc = STATUS_COLOR[sts]
  const lb = sts === 'selesai' ? 'Selesai' : sts === 'berjalan' ? 'Berjalan' : 'Siap Dibangun'

  return `<div style="min-width:240px;font-family:system-ui,sans-serif">
    <div style="padding:10px 12px;font-weight:700;font-size:13px;color:#1B3A6B;background:#f8fafc;border-bottom:1px solid #e2e8f0">${m.nama_kampung||''}</div>
    ${p!=null?`<div style="height:4px;background:#e2e8f0"><div style="height:100%;width:${Math.min(p,100)}%;background:${sc}"></div></div>`:''}
    <div style="padding:3px 12px"><span style="display:inline-block;padding:1px 6px;border-radius:6px;font-size:10px;font-weight:700;background:${sc}20;color:${sc}">${lb}${p>0?' '+p+'%':''}</span> ${m.status_knmp?`<span style="display:inline-block;padding:1px 6px;border-radius:6px;font-size:10px;font-weight:700;background:${m.status_knmp==='HUB'?'#D1FAE5':'#F1F5F9'};color:${m.status_knmp==='HUB'?'#065F46':'#475569'}">${m.status_knmp}</span>`:''}</div>
    <div style="padding:6px 12px;font-size:12px;color:#1e293b">
      <div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Provinsi</span><b>${m.provinsi||''}</b></div>
      <div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Kabupaten</span><b>${m.kabupaten||''}</b></div>
      ${m.kecamatan?`<div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Kecamatan</span><b>${m.kecamatan}</b></div>`:''}
      ${(m.jumlah_nelayan||m.jumlah_kapal)?`<div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Nelayan/Kapal</span><b>${m.jumlah_nelayan||0} / ${m.jumlah_kapal||0}</b></div>`:''}
      ${m.penyedia?`<div style="display:flex;justify-content:space-between;padding:2px 0"><span style="color:#64748b">Penyedia</span><b>${m.penyedia}</b></div>`:''}
    </div>
    <div style="padding:4px 12px;text-align:center;font-size:10px;color:#94a3b8;border-top:1px solid #f1f5f9"><a href="/login" style="color:#3B82F6">🔒 Login</a> untuk update progress</div>
  </div>`
}

function KnmpLayer({ markers }) {
  const map = useMap()

  useEffect(() => {
    if (!markers.length) return
    const mcg = L.markerClusterGroup({
      chunkedLoading: true, maxClusterRadius: 55, disableClusteringAtZoom: 16,
      iconCreateFunction: function(cluster) {
        const count = cluster.getChildCount()
        const s = count < 30 ? 34 : count < 80 ? 42 : count < 200 ? 50 : 58
        return L.divIcon({
          html: `<div style="background:#1B3A6B;border:2.5px solid #C9A84C;border-radius:50%;width:${s}px;height:${s}px;display:flex;align-items:center;justify-content:center;color:#C9A84C;font-size:${s<42?11:13}px;font-weight:800;box-shadow:0 2px 8px rgba(0,0,0,.3)">${count}</div>`,
          className: '', iconSize: [s, s], iconAnchor: [s/2, s/2]
        })
      }
    })

    let idx = 0
    const BATCH = 120
    function addBatch() {
      const chunk = markers.slice(idx, idx + BATCH)
      chunk.forEach(m => {
        const p = m.progress_kumulatif
        const sts = p != null && p >= 100 ? 'selesai' : p != null && p > 0 ? 'berjalan' : m.status_knmp === 'PENYANGGA' ? 'penyangga' : 'siap'
        const c = L.circleMarker([m.lat || 0, m.lon || 0], {
          radius: m.status_knmp === 'HUB' ? 7 : 5, fillColor: STATUS_COLOR[sts],
          color: '#fff', weight: 1.5, fillOpacity: 0.9
        })
        c.bindPopup(popupHTML(m), { maxWidth: 320 })
        c.bindTooltip(`<b>${m.nama_kampung||''}</b><br>${m.status_knmp||''} · ${p!=null?p+'%':'—'}`, { direction: 'top' })
        mcg.addLayer(c)
      })
      idx += BATCH
      if (idx < markers.length) requestAnimationFrame(addBatch)
      else map.addLayer(mcg)
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

  useEffect(() => {
    const t0 = performance.now()
    fetchKnmp().then(data => {
      setMarkers(data)
      console.log(`${data.length} markers in ${Math.round(performance.now()-t0)}ms`)
    })
  }, [])

  const filtered = markers.filter(m => {
    if (provFilter && m.provinsi !== provFilter) return false
    if (statFilter === 'HUB' && m.status_knmp !== 'HUB') return false
    if (statFilter === 'PENYANGGA' && m.status_knmp !== 'PENYANGGA') return false
    if (search && !`${m.nama_kampung||''} ${m.kabupaten||''} ${m.penyedia||''}`.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const provs = [...new Set(markers.map(m => m.provinsi).filter(Boolean))].sort()
  const selesai = markers.filter(m => (m.progress_kumulatif || 0) >= 100).length
  const berjalan = markers.filter(m => (m.progress_kumulatif || 0) > 0 && (m.progress_kumulatif || 0) < 100).length

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-100 dark:bg-slate-950">
      {/* Top bar — shadcn styled */}
      <header className="flex-shrink-0 h-12 border-b bg-card/90 backdrop-blur flex items-center justify-between px-3 gap-3 z-30 shadow-sm">
        <div className="flex items-center gap-2 min-w-0">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 rounded-md hover:bg-accent">☰</button>
          <div className="min-w-0">
            <h1 className="text-sm font-bold text-foreground truncate">Peta KNMP Nasional</h1>
            <p className="text-[9px] text-muted-foreground hidden sm:block">PT Agrinas Jaladri Nusantara</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Badge variant="outline" className="text-[10px]">{markers.length} Lokasi</Badge>
          <Link to="/"><Button variant="ghost" size="xs">📊</Button></Link>
          <Link to="/login"><Button variant="gold" size="xs">🔒 Login</Button></Link>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className={`${sidebarOpen ? 'w-60' : 'w-0'} transition-all overflow-hidden lg:w-60 bg-card border-r flex-shrink-0 z-10`}>
          <div className="p-3 space-y-3 overflow-y-auto h-full">
            <div className="grid grid-cols-2 gap-2">
              {[[markers.length,'Total'],[markers.length,'Live'],[selesai,'Selesai'],[berjalan,'Berjalan']].map(([v,l],i) => (
                <div key={i} className="bg-muted rounded-lg p-2.5 text-center border">
                  <div className="text-lg font-extrabold text-foreground">{v}</div>
                  <div className="text-[10px] text-muted-foreground">{l}</div>
                </div>
              ))}
            </div>

            <Input placeholder="Cari nama, kab, penyedia…" value={search} onChange={e => setSearch(e.target.value)} className="h-8 text-xs" />

            <select value={provFilter} onChange={e => setProvFilter(e.target.value)} className="w-full h-8 text-xs border rounded-md bg-background px-2">
              <option value="">Semua Provinsi</option>
              {provs.map(p => <option key={p} value={p}>{p}</option>)}
            </select>

            <select value={statFilter} onChange={e => setStatFilter(e.target.value)} className="w-full h-8 text-xs border rounded-md bg-background px-2">
              <option value="">Semua Status</option>
              <option value="HUB">HUB</option>
              <option value="PENYANGGA">Penyangga</option>
            </select>

            <Button variant="outline" size="xs" className="w-full" onClick={() => { setSearch(''); setProvFilter(''); setStatFilter('') }}>↺ Reset</Button>

            <div className="border-t pt-2 text-[11px] space-y-1">
              {[['🟢 Selesai', selesai], ['🟡 Berjalan', berjalan], ['🔵 Siap', markers.length-selesai-berjalan]].map(([l,v],i) => (
                <div key={i} className="flex justify-between text-muted-foreground"><span>{l}</span><span className="font-semibold">{v}</span></div>
              ))}
            </div>
          </div>
        </div>

        {/* Map area */}
        <div className="flex-1 relative">
          <MapContainer center={[-2.5, 118]} zoom={5} className="w-full h-full" preferCanvas>
            <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
              attribution='&copy; OSM &copy; CARTO' subdomains="abcd" maxZoom={19} />
            <KnmpLayer markers={filtered} />
          </MapContainer>

          {/* Bottom progress bar */}
          {markers.length > 0 && (
            <div className="absolute bottom-3 left-3 right-3 z-10">
              <div className="bg-card/90 backdrop-blur rounded-lg shadow border px-4 py-2.5 flex items-center gap-4 text-xs flex-wrap">
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden min-w-[150px]">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${(selesai/markers.length*100).toFixed(0)}%` }} />
                </div>
                <span className="font-bold text-emerald-700 dark:text-emerald-400">{selesai} Selesai</span>
                <span className="text-muted-foreground">|</span>
                <span className="font-bold text-amber-700 dark:text-amber-400">{berjalan} Berjalan</span>
                <span className="text-muted-foreground">|</span>
                <span className="text-muted-foreground">{markers.length - selesai - berjalan} Siap</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
