import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import api from '../api/client.js'
import '../styles/admin.css'

const islands = ['Jawa-Bali', 'Sumatera', 'Kalimantan', 'Sulawesi', 'NTT-NTB', 'Maluku', 'Papua']
const number = value => Number(value || 0).toLocaleString('id-ID')
const stamp = value => value ? new Intl.DateTimeFormat('id-ID', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : 'Belum ada'

function Health({ label, value, detail, healthy }) {
  const text = healthy === true ? 'Sehat' : healthy === false ? 'Perlu perhatian' : 'Belum tersedia'
  return <article className="admin-health"><div><span>{label}</span><b className={healthy === true ? 'good' : healthy === false ? 'bad' : ''}>{text}</b></div><strong>{value}</strong><small>{detail}</small></article>
}

export default function Admin() {
  const { user, logout } = useAuth()
  const [prices, setPrices] = useState([]); const [stats, setStats] = useState({}); const [visitors, setVisitors] = useState({}); const [monitor, setMonitor] = useState(null)
  const [pulau, setPulau] = useState(''); const [running, setRunning] = useState(false); const [exporting, setExporting] = useState(''); const [log, setLog] = useState(''); const [notice, setNotice] = useState('')
  const refresh = useCallback(async () => {
    const results = await Promise.allSettled([api.get('/api/prices'), api.get('/api/stats'), api.get('/api/visitor/stats'), api.get('/api/admin/monitoring')])
    if (results[0].status === 'fulfilled') setPrices(results[0].value.data.data || [])
    if (results[1].status === 'fulfilled') setStats(results[1].value.data.data || {})
    if (results[2].status === 'fulfilled') setVisitors(results[2].value.data.data || {})
    if (results[3].status === 'fulfilled') setMonitor(results[3].value.data.data || results[3].value.data)
  }, [])
  useEffect(() => { refresh() }, [refresh])
  const sync = async () => {
    setRunning(true); setNotice(''); setLog('Menjalankan pipeline sinkronisasi…')
    try { const { data } = await api.post('/api/scrape/trigger'); setLog(data.log || data.message || 'Sinkronisasi selesai.'); setNotice('Sinkronisasi selesai. Ringkasan dimuat ulang.'); await refresh() }
    catch (error) { const detail = error.response?.data?.detail; setLog(`Gagal: ${typeof detail === 'object' ? detail.message : detail || error.message}${typeof detail === 'object' && detail.log ? `\n\n${detail.log}` : ''}`) }
    finally { setRunning(false) }
  }
  const download = async format => {
    setExporting(format); setNotice('')
    try {
      const response = await api.get(`/api/export/${format}`, { params: pulau ? { pulau } : {}, responseType: 'blob' }); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); const fromHeader = response.headers['content-disposition']?.match(/filename=\"?([^\";]+)\"?/)?.[1]
      link.href = url; link.download = fromHeader || `KNMP_${pulau || 'Semua'}.${format === 'excel' ? 'xlsx' : 'pdf'}`; document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); setNotice(`Export ${format.toUpperCase()} berhasil disiapkan.`)
    } catch (error) { setNotice(`Export gagal: ${error.response?.data?.detail || error.message}`) } finally { setExporting('') }
  }
  const price = monitor?.price || {}; const knmp = monitor?.knmp || {}; const pipeline = monitor?.pipeline || {}
  return <div className="admin-shell">
    <header className="admin-header"><Link className="admin-brand" to="/"><span>AJN</span><div>Market Watch<small>internal console</small></div></Link><nav><Link to="/">Beranda</Link><Link to="/peta">Peta KNMP</Link><span>{user?.username || 'Admin'}</span><button onClick={logout}>Keluar</button></nav></header>
    <main className="admin-main"><section className="admin-hero"><div><p>OPERASIONAL DATA</p><h1>Kontrol Market Watch</h1><span>Amati kesegaran data, jalankan sinkronisasi yang terkunci, dan ambil laporan KNMP dari satu tempat.</span></div><button onClick={refresh}>↻ Muat ulang status</button></section>{notice && <div className="admin-notice">{notice}</div>}
      <section className="admin-health-grid"><Health label="Harga pasar" value={price.latest_date || '—'} detail={`${number(price.observations)} observasi · ${price.age_days ?? '—'} hari lalu`} healthy={price.healthy}/><Health label="Sebaran KNMP" value={`${number(knmp.locations)} lokasi`} detail={knmp.last_updated ? `diperbarui ${knmp.age_days} hari lalu` : 'belum ada waktu pembaruan'} healthy={knmp.healthy}/><Health label="Pipeline terakhir" value={pipeline.status || 'Belum ada run'} detail={pipeline.finished_at ? stamp(pipeline.finished_at) : 'Belum ada catatan eksekusi'} healthy={pipeline.healthy}/></section>
      <section className="admin-grid"><article className="admin-panel"><p>SINKRONISASI</p><h2>Jalankan update manual</h2><span>Tombol ini menjalankan pipeline yang sama dengan cron: eKNMP, arsip harga FishInfo Jatim, lalu alert. Dua proses tidak dapat berjalan bersamaan.</span><button className="primary" onClick={sync} disabled={running}>{running ? 'Sinkronisasi berjalan…' : 'Mulai sinkronisasi'}</button>{log && <pre>{log}</pre>}</article><article className="admin-panel"><p>LAPORAN</p><h2>Export sebaran KNMP</h2><span>Pilih cakupan. File berasal dari data KNMP yang sama dengan peta publik.</span><label>Cakupan wilayah<select value={pulau} onChange={event => setPulau(event.target.value)}><option value="">Seluruh Indonesia</option>{islands.map(item => <option key={item}>{item}</option>)}</select></label><div className="export"><button onClick={() => download('excel')} disabled={!!exporting}>{exporting === 'excel' ? 'Menyiapkan…' : 'Excel (.xlsx)'}</button><button onClick={() => download('pdf')} disabled={!!exporting}>{exporting === 'pdf' ? 'Menyiapkan…' : 'PDF (.pdf)'}</button></div></article></section>
      <section className="admin-metrics"><article><strong>{number(stats.total_lokasi)}</strong><span>Lokasi KNMP</span></article><article><strong>{number(stats.total_nelayan)}</strong><span>Nelayan tercatat</span></article><article><strong>{number(stats.total_kapal)}</strong><span>Kapal tercatat</span></article><article><strong>{number(visitors.today)}</strong><span>Kunjungan hari ini</span></article></section>
      <section className="admin-grid"><article className="admin-panel"><p>ALERT TERBARU</p><h2>Perubahan yang perlu dibaca</h2>{monitor?.alerts?.length ? <ul>{monitor.alerts.map((alert, index) => <li key={`${alert.date}-${index}`}><i className={alert.level || ''}/><div><strong>{alert.commodity || 'Alert data'}</strong><small>{alert.message || alert.date || 'Tanpa keterangan'}</small></div></li>)}</ul> : <em>Belum ada alert aktif dari pipeline terakhir.</em>}</article><article className="admin-panel"><p>RIWAYAT PIPELINE</p><h2>Eksekusi terakhir</h2><dl><div><dt>Pemicu</dt><dd>{pipeline.trigger || '—'}</dd></div><div><dt>Mulai</dt><dd>{stamp(pipeline.started_at)}</dd></div><div><dt>Selesai</dt><dd>{stamp(pipeline.finished_at)}</dd></div></dl>{pipeline.log && <details><summary>Lihat log pipeline</summary><pre>{pipeline.log}</pre></details>}</article></section>
      <section className="admin-panel prices"><p>HARGA TERKINI</p><h2>Rata-rata eceran pasar Jawa Timur</h2><div className="table"><table><thead><tr><th>Komoditas</th><th>Ukuran</th><th>Harga rata-rata/kg</th><th>Sumber</th></tr></thead><tbody>{prices.length ? prices.map((item, index) => <tr key={`${item.komoditas}-${index}`}><td>{item.komoditas}</td><td>{item.size || '—'}</td><td>Rp {number(item.harga_tambak_low)}</td><td>{item.sumber || '—'}</td></tr>) : <tr><td colSpan="4"><em>Data harga belum tersedia.</em></td></tr>}</tbody></table></div></section>
    </main></div>
}
