import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Tooltip, Popup } from 'react-leaflet'
import { Link } from 'react-router-dom'
import { fetchKnmp } from '../api/client.js'
import { Button } from '../components/ui/Button.jsx'
import { Input } from '../components/ui/Input.jsx'
import { Badge } from '../components/ui/Badge.jsx'

const ST = { selesai: '#10B981', berjalan: '#F59E0B', siap: '#3B82F6', penyangga: '#94A3B8' }

function popupHTML(m) {
  const p = m.progress_kumulatif, sts = p != null && p >= 100 ? 'selesai' : p != null && p > 0 ? 'berjalan' : 'siap'
  const sc = ST[sts], lb = sts === 'selesai' ? 'Selesai' : 'Berjalan'
  return `<div style="font-family:system-ui;min-width:260px"><div style="padding:10px 13px;font-weight:700;font-size:13px;color:#C9A84C;background:linear-gradient(135deg,#1B3A6B,#0d2244)">#${m.id_lokasi} · ${m.nama_kampung||'?'}</div>${p!=null?`<div style="height:4px;background:#e2e8f0"><div style="height:100%;width:${Math.min(p,100)}%;background:${sc}"></div></div>`:''}<div style="padding:4px 11px;display:flex;gap:4px;flex-wrap:wrap"><span style="padding:1px 7px;border-radius:8px;font-size:10px;font-weight:700;color:#fff;background:${sc}">${lb}${p>0?' '+p+'%':''}</span>${m.status_knmp?`<span style="padding:1px 7px;border-radius:8px;font-size:10px;font-weight:700;background:${m.status_knmp==='HUB'?'#D1FAE5':'#F1F5F9'};color:${m.status_knmp==='HUB'?'#065F46':'#475569'}">${m.status_knmp}</span>`:''}${m.tahun?`<span style="padding:1px 7px;border-radius:8px;font-size:10px;font-weight:700;background:#F1F5F9;color:#475569">${m.tahun}</span>`:''}</div><table style="width:100%;border-collapse:collapse;font-size:12px"><tbody><tr><td style="padding:3px 11px;color:#475569;width:90px;font-weight:600">Provinsi</td><td style="padding:3px 11px;color:#1e293b"><b>${m.provinsi||''}</b></td></tr><tr><td style="padding:3px 11px;color:#475569;font-weight:600">Kabupaten</td><td style="padding:3px 11px;color:#1e293b"><b>${m.kabupaten||''}</b></td></tr>${m.kecamatan?`<tr><td style="padding:3px 11px;color:#475569;font-weight:600">Kec</td><td style="padding:3px 11px;color:#1e293b"><b>${m.kecamatan}</b></td></tr>`:''}<tr><td style="padding:3px 11px;color:#475569;font-weight:600">Nelayan</td><td style="padding:3px 11px;color:#1e293b"><b>${(m.jumlah_nelayan||0).toLocaleString('id')} org</b></td></tr><tr><td style="padding:3px 11px;color:#475569;font-weight:600">Kapal</td><td style="padding:3px 11px;color:#1e293b"><b>${m.jumlah_kapal||0} unit</b></td></tr>${m.penyedia?`<tr><td style="padding:3px 11px;color:#475569;font-weight:600">Penyedia</td><td style="padding:3px 11px;color:#1e293b"><b>${m.penyedia}</b></td></tr>`:''}</tbody></table><div style="padding:6px 11px;background:#F0FDF4;border-top:1px solid #BBF7D0;font-size:11px">🏗️ Fisik <b>${m.realisasi_fisik!=null?m.realisasi_fisik+'%':'—'}</b> &nbsp; 💰 Keu <b>${m.realisasi_keuangan!=null?m.realisasi_keuangan+'%':'—'}</b></div><div style="padding:4px 11px;text-align:center;font-size:9px;color:#94a3b8;border-top:1px solid #f1f5f9">⏱️ ${m.snapshot_date||'—'} · <a href="/login" style="color:#3B82F6">🔒 Login</a></div></div>`
}

export default function MapPage() {
  const [markers, setMarkers] = useState([])
  const [search, setSearch] = useState('')
  const [selectedProv, setSelectedProv] = useState('')
  const [statFilter, setStatFilter] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => { fetchKnmp().then(setMarkers) }, [])

  const filtered = markers.filter(m => {
    if (m.lat == null || m.lon == null) return false
    if (selectedProv && (m.provinsi||'').toUpperCase() !== selectedProv.toUpperCase()) return false
    if (statFilter === 'selesai' && (m.progress_kumulatif||0) < 100) return false
    if (statFilter === 'berjalan' && !((m.progress_kumulatif||0) > 0 && (m.progress_kumulatif||0) < 100)) return false
    if (statFilter === 'siap' && (m.progress_kumulatif||0) > 0) return false
    if (statFilter === 'HUB' && m.status_knmp !== 'HUB') return false
    if (statFilter === 'PENYANGGA' && m.status_knmp !== 'PENYANGGA') return false
    if (search && ![(m.nama_kampung||''),(m.kabupaten||''),(m.penyedia||'')].some(v => v.toLowerCase().includes(search.toLowerCase()))) return false
    return true
  })

  const total = markers.length
  const selesai = markers.filter(m => (m.progress_kumulatif||0)>=100).length
  const berjalan = markers.filter(m => (m.progress_kumulatif||0)>0&&(m.progress_kumulatif||0)<100).length

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-100 dark:bg-slate-950">
      <header className="flex-shrink-0 h-12 border-b bg-card/90 backdrop-blur flex items-center justify-between px-3 gap-3 z-30 shadow-sm">
        <div className="flex items-center gap-2 min-w-0">
          <button onClick={()=>setSidebarOpen(!sidebarOpen)} className="p-1 rounded-md hover:bg-accent">☰</button>
          <div className="min-w-0"><h1 className="text-sm font-bold text-foreground truncate">Peta KNMP Nasional</h1></div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Badge variant="outline" className="text-[10px]">{total} Lokasi</Badge>
          <Link to="/"><Button variant="ghost" size="xs">📊</Button></Link>
          <Link to="/login"><Button variant="gold" size="xs">🔒 Login</Button></Link>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className={`${sidebarOpen?'w-64':'w-0'} transition-all overflow-hidden lg:w-64 bg-card border-r flex-shrink-0 z-10`}>
          <div className="p-3 space-y-3 overflow-y-auto h-full">
            <div className="grid grid-cols-2 gap-2">
              {[[total,'Total'],[selesai,'Selesai'],[berjalan,'Berjalan'],[total-selesai-berjalan,'Siap']].map(([v,l],i)=>(
                <div key={i} className="bg-muted rounded-lg p-2.5 text-center border"><div className="text-lg font-extrabold text-foreground">{v}</div><div className="text-[10px] text-muted-foreground">{l}</div></div>
              ))}
            </div>
            <Input placeholder="Cari lokasi..." value={search} onChange={e=>setSearch(e.target.value)} className="h-8 text-xs"/>
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground mb-1">Provinsi</label>
              <select value={selectedProv} onChange={e => setSelectedProv(e.target.value)} className="w-full h-8 text-xs border rounded-md bg-background px-2">
                <option value="">Semua Provinsi</option>
                {[...new Set(markers.map(m=>m.provinsi).filter(Boolean))].sort().map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-muted-foreground mb-1">Status</label>
              <select value={statFilter} onChange={e=>setStatFilter(e.target.value)} className="w-full h-8 text-xs border rounded-md bg-background px-2">
                <option value="">Semua Status</option><option value="selesai">Selesai (100%)</option><option value="berjalan">Berjalan</option><option value="siap">Siap Dibangun</option><option value="HUB">HUB</option><option value="PENYANGGA">Penyangga</option>
              </select>
            </div>
            <Button variant="outline" size="xs" className="w-full" onClick={()=>{setSearch('');setSelectedProv('');setStatFilter('')}}>↺ Reset</Button>
            <div className="border-t pt-2 text-[11px] space-y-1">
              <div className="text-[10px] font-bold text-muted-foreground uppercase mb-1">Legenda</div>
              {[['🟢 Selesai',selesai],['🟡 Berjalan',berjalan],['🔵 Siap',total-selesai-berjalan]].map(([l,v],i)=>(<div key={i} className="flex justify-between text-muted-foreground"><span>{l}</span><span className="font-semibold">{v}</span></div>))}
              <div className="flex justify-between text-muted-foreground"><span>⭐ HUB</span><span className="font-semibold">{markers.filter(m=>m.status_knmp==='HUB').length}</span></div>
              <div className="flex justify-between text-muted-foreground"><span>◆ Penyangga</span><span className="font-semibold">{markers.filter(m=>m.status_knmp==='PENYANGGA').length}</span></div>
            </div>
          </div>
        </div>

        <div className="flex-1 relative">
          {markers.length === 0 ? (
            <div className="w-full h-full flex items-center justify-center bg-muted/30">
              <div className="text-center space-y-3">
                <div className="animate-spin w-10 h-10 border-4 border-muted border-t-primary rounded-full mx-auto"/>
                <p className="text-sm text-muted-foreground">Memuat peta KNMP...</p>
              </div>
            </div>
          ) : (
            <MapContainer center={[-2.5,118]} zoom={5} className="w-full h-full" preferCanvas>
              <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" attribution="&copy; OSM &copy; CARTO" subdomains="abcd" maxZoom={19}/>
              {filtered.map(m => {
                const p = m.progress_kumulatif, sts = p!=null&&p>=100?'selesai':p!=null&&p>0?'berjalan':m.status_knmp==='PENYANGGA'?'penyangga':'siap'
                return (
                  <CircleMarker key={m.id_lokasi} center={[m.lat,m.lon]} radius={m.status_knmp==='HUB'?7:5} fillColor={ST[sts]} pathOptions={{color:'#fff',weight:1.5}} fillOpacity={0.9}>
                    <Popup maxWidth={300}><div dangerouslySetInnerHTML={{__html:popupHTML(m)}}/></Popup>
                    <Tooltip direction="top" offset={[0,-12]}><b>{m.nama_kampung}</b><br/>{m.status_knmp} · {p!=null?p+'%':'—'}</Tooltip>
                  </CircleMarker>
                )
              })}
            </MapContainer>
          )}
          {total > 0 && (
            <div className="absolute bottom-3 left-3 right-3 z-[1000]">
              <div className="bg-card/90 backdrop-blur rounded-lg shadow border px-4 py-2.5 flex items-center gap-4 text-xs flex-wrap">
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden min-w-[150px]"><div className="h-full bg-emerald-500 rounded-full" style={{width:`${(selesai/total*100).toFixed(0)}%`}}/></div>
                <span className="font-bold text-emerald-700 dark:text-emerald-400">{selesai} Selesai</span><span className="text-muted-foreground">|</span>
                <span className="font-bold text-amber-700 dark:text-amber-400">{berjalan} Berjalan</span><span className="text-muted-foreground">|</span>
                <span className="text-muted-foreground">{total-selesai-berjalan} Siap</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
