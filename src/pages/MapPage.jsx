import { useEffect, useMemo, useState } from 'react'
import { MapContainer, CircleMarker, Popup, Tooltip, useMap } from 'react-leaflet'
import { maplibreGL } from '@maplibre/maplibre-gl-leaflet'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Link } from 'react-router-dom'
import { ArrowLeft, FilterX, Layers3, MapPinned, Menu, Search, X } from 'lucide-react'
import api from '../api/client.js'

const statusOf = value => (value || '').toUpperCase()
const colors = { HUB: '#17699b', PENYANGGA: '#e8a84b' }

function VectorBasemap() {
  const map = useMap()
  useEffect(() => {
    const layer = maplibreGL({ style: 'https://tiles.openfreemap.org/styles/positron' }).addTo(map)
    return () => map.removeLayer(layer)
  }, [map])
  return null
}

function LocationPopup({ item }) {
  const rows = [['Provinsi', item.provinsi], ['Kabupaten', item.kabupaten], ['Kecamatan', item.kecamatan], ['Desa', item.desa], ['Nelayan', item.jumlah_nelayan != null ? `${item.jumlah_nelayan} orang` : null], ['Kapal', item.jumlah_kapal != null ? `${item.jumlah_kapal} unit` : null]]
  return <div className="mw-popup"><div className="mw-popup-top"><span>KNMP / {item.id_lokasi}</span><h3>{item.nama_kampung || 'Lokasi tanpa nama'}</h3><div>{statusOf(item.status_knmp) || 'Belum diklasifikasi'} {item.tahun ? `· ${item.tahun}` : ''}</div></div><div className="mw-popup-rows">{rows.filter(([,value]) => value != null && value !== '').map(([label,value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div><p>Lokasi berdasarkan data eKNMP. Harga regional belum terverifikasi.</p></div>
}

export default function MapPage() {
  const [markers, setMarkers] = useState([])
  const [lastUpdate, setLastUpdate] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [province, setProvince] = useState('')
  const [status, setStatus] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    Promise.all([api.get('/api/knmp'), api.get('/api/stats')]).then(([locations, summary]) => {
      setMarkers(locations.data.data || [])
      setLastUpdate(summary.data.data?.latest_knmp_update || null)
    }).catch(() => setError('Data peta tidak dapat dimuat. Periksa koneksi atau layanan API.')).finally(() => setLoading(false))
  }, [])

  const provinces = useMemo(() => [...new Set(markers.map(item => item.provinsi).filter(Boolean))].sort(), [markers])
  const filtered = useMemo(() => markers.filter(item => {
    const lat = Number(item.lat), lon = Number(item.lon)
    return Number.isFinite(lat) && Number.isFinite(lon) && lat >= -12 && lat <= 7 && lon >= 94 && lon <= 142 &&
      (!province || item.provinsi === province) && (!status || statusOf(item.status_knmp) === status) &&
      (!search || `${item.nama_kampung || ''} ${item.kabupaten || ''} ${item.provinsi || ''}`.toLowerCase().includes(search.toLowerCase()))
  }), [markers, province, status, search])
  const hub = markers.filter(item => statusOf(item.status_knmp) === 'HUB').length
  const support = markers.filter(item => statusOf(item.status_knmp) === 'PENYANGGA').length
  const reset = () => { setSearch(''); setProvince(''); setStatus('') }

  return <div className="mw-map-page">
    <header className="mw-map-header"><div className="mw-map-header-left"><button className="mw-icon-button" onClick={() => setSidebarOpen(value => !value)} aria-label={sidebarOpen ? 'Tutup filter' : 'Buka filter'}><Menu size={19}/></button><Link to="/" className="mw-map-back"><ArrowLeft size={16}/> Market Watch</Link><span className="mw-map-divider"/><strong>Peta Sebaran KNMP</strong></div><div className="mw-map-header-right"><span className="mw-map-live"><span/> DATA eKNMP</span><span className="mw-map-total">{markers.length.toLocaleString('id-ID')} lokasi</span></div></header>
    <div className="mw-map-body">
      <aside className={`mw-map-sidebar ${sidebarOpen ? 'open' : ''}`}><div className="mw-map-sidebar-inner"><div className="mw-map-sidebar-title"><div><span className="mw-kicker">EXPLORE / INDONESIA</span><h1>Jelajahi sebaran.</h1></div><button className="mw-icon-button mw-map-close" onClick={() => setSidebarOpen(false)} aria-label="Tutup filter"><X size={18}/></button></div><p className="mw-map-intro">Titik lokasi Kampung Nelayan Merah Putih, diperbarui dari eKNMP.</p><div className="mw-map-counts"><div><MapPinned size={17}/><strong>{markers.length.toLocaleString('id-ID')}</strong><span>Total lokasi</span></div><div><span className="mw-dot hub"/><strong>{hub.toLocaleString('id-ID')}</strong><span>HUB</span></div><div><span className="mw-dot support"/><strong>{support.toLocaleString('id-ID')}</strong><span>Penyangga</span></div></div><div className="mw-map-controls"><label htmlFor="mw-map-search">Cari lokasi</label><div className="mw-map-search"><Search size={16}/><input id="mw-map-search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Kampung, kabupaten..."/></div><label htmlFor="mw-map-province">Provinsi</label><select id="mw-map-province" value={province} onChange={event => setProvince(event.target.value)}><option value="">Semua provinsi</option>{provinces.map(value => <option key={value} value={value}>{value}</option>)}</select><label htmlFor="mw-map-status">Status</label><select id="mw-map-status" value={status} onChange={event => setStatus(event.target.value)}><option value="">Semua status</option><option value="HUB">HUB</option><option value="PENYANGGA">Penyangga</option></select><button className="mw-map-reset" onClick={reset}><FilterX size={15}/> Atur ulang filter</button></div><div className="mw-map-sidebar-foot"><Layers3 size={16}/><span>{filtered.length.toLocaleString('id-ID')} titik tampil di peta</span></div></div></aside>
      <div className="mw-map-canvas">{loading || error ? <div className="mw-map-message">{error || 'Memuat lokasi KNMP...'}</div> : <MapContainer center={[-2.5, 118]} zoom={5} minZoom={2} maxZoom={18} className="mw-map-leaflet" preferCanvas><VectorBasemap/>{filtered.map(item => { const type = statusOf(item.status_knmp); const color = colors[type] || '#8296a8'; return <CircleMarker key={item.id_lokasi} center={[Number(item.lat), Number(item.lon)]} radius={type === 'HUB' ? 6 : 4} pathOptions={{ color: '#ffffff', weight: 1.5, fillColor: color, fillOpacity: .9 }}><Popup maxWidth={330}><LocationPopup item={item}/></Popup><Tooltip direction="top" offset={[0, -8]}>{item.nama_kampung || 'Lokasi KNMP'}</Tooltip></CircleMarker> })}</MapContainer>}<div className="mw-map-overlay"><div><span className="mw-dot hub"/> HUB <span className="mw-dot support"/> PENYANGGA <span className="mw-dot other"/> LAINNYA</div><small>{lastUpdate ? `Sinkronisasi lokasi: ${new Date(lastUpdate).toLocaleDateString('id-ID')}` : 'Tanggal sinkronisasi belum tersedia'}</small></div></div>
    </div>
  </div>
}
