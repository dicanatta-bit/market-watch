import { useState, useEffect } from 'react'
import StatCard from '../components/cards/StatCard.jsx'
import CommodityCard from '../components/cards/CommodityCard.jsx'
import PriceChart from '../components/charts/PriceChart.jsx'
import { Button } from '../components/ui/Button.jsx'
import { Card, CardHeader, CardContent, CardTitle } from '../components/ui/Card.jsx'
import { Badge } from '../components/ui/Badge.jsx'
import { Skeleton } from '../components/ui/Skeleton.jsx'
import { Table, TableBody, TableRow, TableCell, TableHead, TableHeader } from '../components/ui/Table.jsx'
import api from '../api/client.js'

export default function Home() {
  const [prices, setPrices] = useState(null)
  const [regional, setRegional] = useState(null)
  const [stats, setStats] = useState(null)
  const [lastUpdate, setLastUpdate] = useState('')
  const [filter, setFilter] = useState('all')
  const [modalItem, setModalItem] = useState(null)
  const [historyData, setHistoryData] = useState([])

  useEffect(() => {
    api.get('/api/prices').then(r => {
      setPrices(r.data.data||[])
      if (r.data.latest_date) setLastUpdate(r.data.latest_date)
    }).catch(() => {})
    api.get('/api/prices/regional').then(r => setRegional(r.data.data||{})).catch(() => {})
    api.get('/api/stats').then(r => setStats(r.data.data||{})).catch(() => {})
  }, [])

  const fetchHistory = (komoditas, size) => {
    api.get(`/api/prices/history?komoditas=${encodeURIComponent(komoditas)}&size=${encodeURIComponent(size)}`)
      .then(r => {
        setHistoryData(r.data.data || [])
        setModalItem({ komoditas, size })
      })
      .catch(() => {})
  }

  const loading = !prices || !regional || !stats
  const isFish = /tuna|cakalang|kakap|kerapu|cumi|lobster/i
  const budidaya = (prices || []).filter(p => !isFish.test(p.komoditas))
  const tangkap = (prices || []).filter(p => isFish.test(p.komoditas))
  const filtered = filter === 'all' ? (prices || []) : filter === 'b' ? budidaya : tangkap

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
        <Skeleton className="h-8 w-40" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[1,2,3,4,5,6].map(i => <Skeleton key={i} className="h-44 rounded-xl" />)}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <StatCard value={prices.length} label="Komoditas Dipantau" />
        <StatCard value={0} label="Alert Aktif" color="gold" />
        <StatCard value={stats.total_lokasi} label="Lokasi KNMP" color="blue" />
        <StatCard value={`${((stats.selesai / stats.total_lokasi) * 100).toFixed(1)}%`} label="Progress Nasional" color="green" />
      </div>

      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-gold" /> Harga Komoditas — <strong>{lastUpdate ? new Date(lastUpdate).toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : 'memuat...'}</strong>
        </h2>
        <div className="flex gap-1.5 ml-auto">
          {[{key:'all',label:'Semua'},{key:'b',label:'Budidaya'},{key:'t',label:'Tangkap'}].map(({key,label}) => (
            <Button key={key} variant={filter === key ? 'default' : 'outline'} size="xs" onClick={() => setFilter(key)}>{label}</Button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
        {filtered.map((p, i) => (
          <div key={i} onClick={() => fetchHistory(p.komoditas, p.size)} className="cursor-pointer">
            <CommodityCard item={p} />
          </div>
        ))}
      </div>

      <h2 className="text-sm font-bold text-foreground flex items-center gap-2 mb-3">
        <span className="w-2 h-2 rounded-full bg-gold" /> Harga per Wilayah
      </h2>
      <Card className="mb-6 overflow-hidden">
        <Table>
          <TableHeader><TableRow><TableHead>Wilayah</TableHead><TableHead>Komoditas</TableHead><TableHead>Size</TableHead><TableHead className="text-right">Harga Tambak</TableHead></TableRow></TableHeader>
          <TableBody>
            {Object.entries(regional).slice(0, 12).flatMap(([wil, items]) =>
              items.slice(0, 2).map((p, i) => (
                <TableRow key={`${wil}-${i}`} className="border-t">
                  <TableCell className="font-semibold">{i === 0 ? wil : ''}</TableCell>
                  <TableCell className="text-muted-foreground">{p.komoditas}</TableCell>
                  <TableCell className="text-muted-foreground">{p.size}</TableCell>
                  <TableCell className="text-right font-bold">Rp {(p.harga_low || 0).toLocaleString('id')} – {(p.harga_high || 0).toLocaleString('id')}/kg</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <h2 className="text-sm font-bold text-foreground flex items-center gap-2 mb-3">
        <span className="w-2 h-2 rounded-full bg-gold" /> Alert & Pergerakan Harga
      </h2>
      <Card>
        <CardContent className="pt-4 text-center text-muted-foreground text-sm">Belum ada alert. Sistem pemantauan berjalan normal.</CardContent>
      </Card>

      {modalItem && (
        <PriceChart
          history={historyData}
          komoditas={`${modalItem.komoditas.split('(')[0].trim()} ${modalItem.size}`}
          onClose={() => { setModalItem(null); setHistoryData([]) }}
        />
      )}
    </div>
  )
}
