import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Tooltip, Popup } from 'react-leaflet'
import { Link } from 'react-router-dom'
import api from '../api/client.js'
import { Button } from '../components/ui/Button.jsx'
import { Input } from '../components/ui/Input.jsx'
import { Badge } from '../components/ui/Badge.jsx'

// Normalize status_knmp: 'penyangga' or 'Penyangga' or 'PENYANGGA' → 'PENYANGGA'
function normStatus(s) {
  if (!s) return ''
  const u = s.toUpperCase()
  if (u === 'HUB') return 'HUB'
  if (u === 'PENYANGGA') return 'PENYANGGA'
  return u
}

const WILAYAH_PROV = {
  "ACEH":"Sumatera","SUMATERA UTARA":"Sumatera","SUMATRA UTARA":"Sumatera",
  "SUMATERA BARAT":"Sumatera","SUMATRA BARAT":"Sumatera","RIAU":"Sumatera",
  "KEPULAUAN RIAU":"Sumatera","JAMBI":"Sumatera","BENGKULU":"Sumatera",
  "SUMATERA SELATAN":"Sumatera","SUMATRA SELATAN":"Sumatera","LAMPUNG":"Sumatera",
  "KEPULAUAN BANGKA BELITUNG":"Sumatera","BANGKA BELITUNG":"Sumatera",
  "BANTEN":"Jawa-Bali","DKI JAKARTA":"Jawa-Bali","JAKARTA":"Jawa-Bali",
  "JAWA BARAT":"Jawa-Bali","JAWA TENGAH":"Jawa-Bali","JAWA TIMUR":"Jawa-Bali",
  "DI YOGYAKARTA":"Jawa-Bali","BALI":"Jawa-Bali",
  "KALIMANTAN BARAT":"Kalimantan","KALIMANTAN TENGAH":"Kalimantan",
  "KALIMANTAN SELATAN":"Kalimantan","KALIMANTAN TIMUR":"Kalimantan","KALIMANTAN UTARA":"Kalimantan",
  "SULAWESI UTARA":"Sulawesi","SULAWESI TENGAH":"Sulawesi","SULAWESI SELATAN":"Sulawesi",
  "SULAWESI TENGGARA":"Sulawesi","GORONTALO":"Sulawesi","SULAWESI BARAT":"Sulawesi",
  "NUSA TENGGARA BARAT":"NTT-NTB","NTB":"NTT-NTB",
  "NUSA TENGGARA TIMUR":"NTT-NTB","NTT":"NTT-NTB",
  "MALUKU":"Maluku","MALUKU UTARA":"Maluku",
  "PAPUA":"Papua","PAPUA BARAT":"Papua","PAPUA SELATAN":"Papua","PAPUA TENGAH":"Papua",
  "PAPUA PEGUNUNGAN":"Papua","PAPUA BARAT DAYA":"Papua",
}

function popupHTML(m, hargaWilayah) {
  const st = normStatus(m.status_knmp)
  const wil = WILAYAH_PROV[m.provinsi] || null
  const harga = wil && hargaWilayah && hargaWilayah[wil] ? hargaWilayah[wil].slice(0, 3) : []
  const badgeBg = st === 'HUB' ? '#DBEAFE' : '#FEF3C7'
  const badgeClr = st === 'HUB' ? '#1E40AF' : '#92400E'
  const row = (l, v, w) => `<tr${w ? ' style="background:#f1f5f9"' : ''}><td style="padding:3px 11px;color:#475569;width:80px;font-weight:600;white-space:nowrap">${l}</td><td style="padding:3px 11px;color:#1e293b"><b>${v||'—'}</b></td></tr>`
  const rows = [['Provinsi', m.provinsi],['Kabupaten', m.kabupaten]]
  if (m.kecamatan) rows.push(['Kecamatan', m.kecamatan])
  if (m.desa) rows.push(['Desa', m.desa])
  rows.push(['Nelayan', (m.jumlah_nelayan||0)+' org'],['Kapal', (m.jumlah_kapal||0)+' unit'])
  if (m.tahun) rows.push(['Tahun', m.tahun])

  return `<div style="font-family:system-ui;min-width:260px;max-width:340px">
    <div style="padding:9px 13px;font-weight:700;font-size:13px;color:#C9A84C;background:linear-gradient(135deg,#1B3A6B,#0d2244)">#${m.id_lokasi} · ${m.nama_kampung||'?'}</div>
    <div style="padding:4px 11px"><span style="display:inline-block;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:700;background:${badgeBg};color:${badgeClr}">${st||'—'}</span>${m.tahun?`<span style="display:inline-block;padding:1px 7px;border-radius:8px;font-size:10px;font-weight:700;background:#F1F5F9;color:#475569;margin-left:4px">${m.tahun}</span>`:''}</div>
    <table style="width:100%;border-collapse:collapse;font-size:12px">${rows.map((r,i)=>row(r[0],r[1],i%2!==0)).join('')}</table>
    ${harga.length?`<div style="background:#f0f7ff;border-top:1px solid #dbeafe;border-bottom:1px solid #dbeafe"><div style="padding:6px 11px 2px;font-size:11px;font-weight:700;color:#1B3A6B;text-transform:uppercase;letter-spacing:.4px">&#128722; Harga Komoditas — ${wil}</div>${harga.map(h=>`<div style="display:flex;justify-content:space-between;padding:2px 11px;font-size:12px!important"><span style="color:#475569">${h.komoditas} <em style="color:#94a3b8;font-style:normal">${h.size}</em></span><span style="color:#1B3A6B;font-weight:700">Rp ${(h.harga_low||0).toLocaleString('id')} – ${(h.harga_high||0).toLocaleString('id')}/kg</span></div>`).join('<div style="border-bottom:1px dotted #e2e8f0"/>')}<div style="padding:2px 11px 6px;font-size:9px;color:#94a3b8">Per hari ini · Estimasi tingkat nelayan/tambak</div></div>`:''}
    <div style="padding:4px 11px;text-align:center;font-size:9px;color:#94a3b8;border-top:1px solid #f1f5f9"><a href="/login" style="color:#3B82F6">🔒 Login</a> untuk detail</div>
  </div>`
}

export default function MapPage() {
  const [markers, setMarkers] = useState([])
  const [hargaWilayah, setHargaWilayah] = useState({})
  const [search, setSearch] = useState('')
  const [selectedProv, setSelectedProv] = useState('')
  const [statFilter, setStatFilter] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    api.get('/api/knmp').then(r => setMarkers(r.data.data||[])).catch(() => {})
    api.get('/api/prices/regional').then(r => setHargaWilayah(r.data.data||{})).catch(() => {})
  }, [])

  const filtered = markers.filter(m => {
    if (m.lat == null || m.lon == null) return false
    if (selectedProv && (m.provinsi||'').toUpperCase() !== selectedProv.toUpperCase()) return false
    if (statFilter === 'HUB' && normStatus(m.status_knmp) !== 'HUB') return false
    if (statFilter === 'PENYANGGA' && normStatus(m.status_knmp) !== 'PENYANGGA') return false
    if (search && ![(m.nama_kampung||''),(m.kabupaten||'')].some(v => v.toLowerCase().includes(search.toLowerCase()))) return false
    return true
  })

  const total = markers.length
  const hub = markers.filter(m => normStatus(m.status_knmp) === 'HUB').length
  const penyangga = markers.filter(m => normStatus(m.status_knmp) === 'PENYANGGA').length
  const provs = [...new Set(markers.map(m => m.provinsi).filter(Boolean))].sort()

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
              {[[total,'Total'],[hub,'HUB'],[penyangga,'Penyangga'],[total-hub-penyangga,'Lain']].map(([v,l],i)=>(
                <div key={i} className="bg-muted rounded-lg p-2.5 text-center border"><div className="text-lg font-extrabold text-foreground">{v}</div><div className="text-[10px] text-muted-foreground">{l}</div></div>
              ))}
            </div>
            <Input placeholder="Cari lokasi..." value={search} onChange={e=>setSearch(e.target.value)} className="h-8 text-xs"/>
            <div><label className="block text-[11px] font-semibold text-muted-foreground mb-1">Provinsi</label>
              <select value={selectedProv} onChange={e=>setSelectedProv(e.target.value)} className="w-full h-8 text-xs border rounded-md bg-background px-2"><option value="">Semua Provinsi</option>{provs.map(p=><option key={p} value={p}>{p}</option>)}</select>
            </div>
            <div><label className="block text-[11px] font-semibold text-muted-foreground mb-1">Status</label>
              <select value={statFilter} onChange={e=>setStatFilter(e.target.value)} className="w-full h-8 text-xs border rounded-md bg-background px-2">
                <option value="">Semua</option><option value="HUB">HUB</option><option value="PENYANGGA">Penyangga</option>
              </select>
            </div>
            <Button variant="outline" size="xs" className="w-full" onClick={()=>{setSearch('');setSelectedProv('');setStatFilter('')}}>↺ Reset</Button>
            <div className="border-t pt-2 text-[11px] space-y-1">
              <div className="text-[10px] font-bold text-muted-foreground uppercase mb-1">Legenda</div>
              <div className="flex justify-between text-muted-foreground"><span><span className="text-[#3B82F6]">⬤</span> HUB</span><span className="font-semibold">{hub}</span></div>
              <div className="flex justify-between text-muted-foreground"><span><span className="text-[#C9A84C]">⬤</span> Penyangga</span><span className="font-semibold">{penyangga}</span></div>
              <div className="flex justify-between text-muted-foreground"><span><span className="text-[#60A5FA]">⬤</span> Lain</span><span className="font-semibold">{total-hub-penyangga}</span></div>
            </div>
          </div>
        </div>

        <div className="flex-1 relative">
          {markers.length === 0 ? (
            <div className="w-full h-full flex items-center justify-center bg-muted/30">
              <div className="text-center space-y-3">
                <div className="animate-spin w-10 h-10 border-4 border-muted border-t-primary rounded-full mx-auto"/>
                <p className="text-sm text-muted-foreground">Memuat peta KNMP... {markers.length} markers</p>
              </div>
            </div>
          ) : (
            <MapContainer center={[-2.5,118]} zoom={5} className="w-full h-full" preferCanvas>
              <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" attribution="&copy; OSM &copy; CARTO" subdomains="abcd" maxZoom={19}/>
              {filtered.map(m => {
                const st = normStatus(m.status_knmp)
                const color = st === 'PENYANGGA' ? '#C9A84C' : st === 'HUB' ? '#3B82F6' : '#60A5FA'
                return (
                  <CircleMarker key={m.id_lokasi} center={[m.lat,m.lon]}
                    radius={st === 'HUB' ? 7 : 5} fillColor={color} pathOptions={{color:'#fff',weight:1.5}} fillOpacity={0.9}>
                    <Popup maxWidth={320}><div dangerouslySetInnerHTML={{__html:popupHTML(m, hargaWilayah)}}/></Popup>
                    <Tooltip direction="top" offset={[0,-12]}><b>{m.nama_kampung}</b><br/>{st}</Tooltip>
                  </CircleMarker>
                )
              })}
            </MapContainer>
          )}
          {total > 0 && (
            <div className="absolute bottom-3 left-3 right-3 z-[1000]">
              <div className="bg-card/90 backdrop-blur rounded-lg shadow border px-4 py-2.5 flex items-center gap-4 text-xs flex-wrap">
                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden min-w-[150px]"><div className="h-full bg-blue-500 rounded-full" style={{width:`${(hub/total*100).toFixed(0)}%`}}/></div>
                <span className="font-bold text-blue-700 dark:text-blue-400">{hub} HUB</span>
                <span className="text-muted-foreground">|</span>
                <span className="font-bold text-amber-700 dark:text-amber-400">{penyangga} Penyangga</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
