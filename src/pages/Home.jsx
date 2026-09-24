import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, CalendarDays, Database, Fish, MapPinned, RefreshCw, ShieldCheck, TriangleAlert } from 'lucide-react'
import CommodityCard from '../components/cards/CommodityCard.jsx'
import PriceChart from '../components/charts/PriceChart.jsx'
import api from '../api/client.js'

const isCapture = name => /tuna|tongkol|cakalang|kembung|cumi|kepiting/i.test(name)
const formatDate = value => value ? new Date(`${value}T12:00:00`).toLocaleDateString('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }) : 'Belum tersedia'

export default function Home() {
  const [prices, setPrices] = useState([])
  const [meta, setMeta] = useState(null)
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [modalItem, setModalItem] = useState(null)
  const [historyData, setHistoryData] = useState([])

  const load = async () => {
    setLoading(true)
    setError('')
    const [priceResult, statsResult] = await Promise.allSettled([api.get('/api/prices'), api.get('/api/stats')])
    if (priceResult.status === 'fulfilled') {
      setPrices(priceResult.value.data.data || [])
      setMeta(priceResult.value.data)
    } else setError('Koneksi ke data harga gagal. Coba lagi beberapa saat.')
    if (statsResult.status === 'fulfilled') setStats(statsResult.value.data.data || {})
    else setError(previous => previous || 'Koneksi ke data KNMP gagal. Coba lagi beberapa saat.')
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const openHistory = async item => {
    try {
      const response = await api.get('/api/prices/history', { params: { komoditas: item.komoditas, size: item.size } })
      setHistoryData(response.data.data || [])
      setModalItem(item)
    } catch { setError('Riwayat harga belum dapat dimuat.') }
  }

  const filtered = prices.filter(item => filter === 'all' || (filter === 'capture' ? isCapture(item.komoditas) : !isCapture(item.komoditas)))
  const status = !meta?.latest_date ? 'Belum tersedia' : meta.fresh ? 'Data sumber aktif' : 'Data perlu diperbarui'

  return (
    <div className="mw-home">
      <section className="mw-hero">
        <div className="mw-hero-orb" aria-hidden="true" />
        <div className="mw-hero-content">
          <div className="mw-eyebrow"><span className="mw-live-dot" /> MARKET WATCH / AGRINAS JALADRI</div>
          <h1>Pantau pasar perikanan.<br/><em>Berbasis data yang jelas.</em></h1>
          <p>Informasi harga bersumber resmi dan sebaran Kampung Nelayan Merah Putih, tersaji dalam satu ruang kerja.</p>
          <div className="mw-hero-actions"><Link className="mw-action-primary" to="/peta">Jelajahi Peta KNMP <ArrowUpRight size={16}/></Link><a className="mw-action-secondary" href="#harga">Lihat harga ↓</a></div>
        </div>
        <div className="mw-hero-meta"><span>AJN / MARKET WATCH</span><span>01 — 02</span></div>
      </section>

      <section className="mw-metrics" aria-label="Ringkasan data">
        <div className="mw-metric"><Fish size={19}/><span>Harga terverifikasi</span><strong>{loading ? '—' : prices.length}</strong><small>komoditas · Jawa Timur</small></div>
        <div className="mw-metric"><MapPinned size={19}/><span>Sebaran KNMP</span><strong>{stats?.total_lokasi?.toLocaleString('id-ID') ?? '—'}</strong><small>lokasi terdata</small></div>
        <div className="mw-metric"><CalendarDays size={19}/><span>Periode harga</span><strong className="mw-metric-date">{formatDate(meta?.latest_date)}</strong><small>tanggal awal periode sumber</small></div>
        <div className="mw-metric"><Database size={19}/><span>Status sumber</span><strong className="mw-metric-date">{status}</strong><small>FishInfo Jatim · DKP Jatim</small></div>
      </section>

      <section id="harga" className="mw-section">
        <div className="mw-section-heading"><div><span className="mw-kicker">01 / PRICE SIGNAL</span><h2>Harga komoditas</h2><p>{meta?.series === 'retail_market_mean' ? 'Rata-rata sederhana harga eceran dari pasar yang tersedia di Jawa Timur (olah AJN), bukan harga tambak, TPI, ekspor, atau nasional.' : 'Rata-rata konsumen Provinsi Jawa Timur, bukan harga tambak, TPI, ekspor, atau nasional.'}</p></div><button className="mw-refresh" onClick={load} disabled={loading}><RefreshCw size={15} className={loading ? 'animate-spin' : ''}/> Muat ulang</button></div>
        {error && <div className="mw-notice mw-notice-error"><TriangleAlert size={18}/>{error}</div>}
        {meta && !meta.fresh && <div className="mw-notice mw-notice-warn"><TriangleAlert size={18}/>{meta.latest_date ? `Data terakhir ${formatDate(meta.latest_date)}. Sumber belum memberi periode baru atau sinkronisasi gagal.` : 'Belum ada harga terverifikasi. Estimasi historis tidak ditampilkan sebagai harga aktual.'}</div>}
        <div className="mw-source-line"><ShieldCheck size={16}/><span>Sumber: <a href={prices[0]?.source_url || 'https://fishinfojatim.net/'} target="_blank" rel="noreferrer">FishInfo Jatim — Dinas Kelautan dan Perikanan Jawa Timur ↗</a></span><span className="mw-source-separator">·</span><span>{formatDate(meta?.latest_date)}</span></div>
        <div className="mw-source-register" aria-label="Keterangan sumber data">
          <div><span>Harga komoditas</span><strong>FishInfo Jatim · DKP Jawa Timur</strong><small>Harga eceran pasar yang tersedia di Jawa Timur; dirata-ratakan AJN per periode.</small></div>
          <div><span>Sebaran KNMP</span><strong>eKNMP · Kementerian Kelautan dan Perikanan</strong><small>Lokasi, status program, nelayan, kapal, dan koordinat Kampung Nelayan Merah Putih.</small></div>
          <div><span>Catatan cakupan</span><strong>Basis data tidak digabung</strong><small>Harga bukan harga tambak, TPI, ekspor, atau indikator nasional.</small></div>
        </div>
        <div className="mw-filter" role="group" aria-label="Filter komoditas">{[['all','Semua'],['culture','Budidaya'],['capture','Tangkap']].map(([key,label]) => <button key={key} className={filter === key ? 'active' : ''} onClick={() => setFilter(key)}>{label}</button>)}</div>
        {loading ? <div className="mw-card-grid">{Array.from({ length: 6 }, (_, i) => <div className="mw-price-skeleton" key={i}/>)}</div> : filtered.length ? <div className="mw-card-grid">{filtered.map(item => <button key={`${item.komoditas}-${item.size}`} className="mw-card-button" onClick={() => openHistory(item)}><CommodityCard item={item}/></button>)}</div> : <div className="mw-empty">{prices.length ? 'Tidak ada komoditas pada kategori ini.' : 'Belum ada harga terverifikasi. Data akan tampil setelah sumber berhasil disinkronkan.'}</div>}
      </section>

      <section className="mw-bottom-note"><div><span className="mw-kicker">02 / GEOGRAPHIC VIEW</span><h2>Lihat cerita di balik titik-titiknya.</h2><p>Peta KNMP menampilkan lokasi dan status program. Harga regional tidak ditampilkan sebelum ada observasi yang valid.</p></div><Link to="/peta">Buka peta interaktif <ArrowUpRight size={17}/></Link></section>
      {modalItem && <PriceChart history={historyData} komoditas={modalItem.komoditas} isArchive={meta?.series === 'retail_market_mean'} onClose={() => { setModalItem(null); setHistoryData([]) }} />}
    </div>
  )
}
