import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchKnmp } from '../../api/client.js'
import { Button } from '../../components/ui/Button.jsx'
import { Input } from '../../components/ui/Input.jsx'
import { Select } from '../../components/ui/Select.jsx'
import { Badge } from '../../components/ui/Badge.jsx'
import { Card } from '../../components/ui/Card.jsx'
import { Skeleton } from '../../components/ui/Skeleton.jsx'
import { Table, TableBody, TableRow, TableCell, TableHead, TableHeader } from '../../components/ui/Table.jsx'

export default function Locations() {
  const [locations, setLocations] = useState(null)
  const [search, setSearch] = useState('')
  const [prov, setProv] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => { fetchKnmp().then(setLocations) }, [])

  if (!locations) return <Card><div className="p-6 space-y-2">{[1,2,3,4,5].map(i=> <Skeleton key={i} className="h-8 w-full rounded" />)}</div></Card>

  const provs = [...new Set(locations.map(l => l.provinsi).filter(Boolean))].sort()
  const filtered = locations.filter(l => {
    if (prov && l.provinsi !== prov) return false
    if (status && l.status_knmp !== status) return false
    if (search && !`${l.nama_kampung} ${l.kabupaten} ${l.penyedia||''}`.toLowerCase().includes(search.toLowerCase())) return false
    return true
  }).slice(0, 200)

  return (
    <div>
      <Card className="p-4 mb-4 flex flex-wrap gap-3 items-end">
        <div><label className="block text-[11px] text-muted-foreground mb-1">Provinsi</label><Select value={prov} onChange={e=>setProv(e.target.value)}><option value="">Semua</option>{provs.map(p=><option key={p} value={p}>{p}</option>)}</Select></div>
        <div><label className="block text-[11px] text-muted-foreground mb-1">Status</label><Select value={status} onChange={e=>setStatus(e.target.value)}><option value="">Semua</option><option value="HUB">HUB</option><option value="PENYANGGA">Penyangga</option></Select></div>
        <div className="flex-1"><label className="block text-[11px] text-muted-foreground mb-1">Cari</label><Input placeholder="Nama, kab, penyedia..." value={search} onChange={e=>setSearch(e.target.value)} className="h-9 text-xs" /></div>
        <Button variant="outline" size="sm" onClick={()=>{setProv('');setStatus('');setSearch('')}}>Reset</Button>
      </Card>

      <Card className="overflow-hidden">
        <Table>
          <TableHeader><TableRow><TableHead>ID</TableHead><TableHead>Nama</TableHead><TableHead>Provinsi</TableHead><TableHead>Kabupaten</TableHead><TableHead>Status</TableHead><TableHead>Progress</TableHead><TableHead></TableHead></TableRow></TableHeader>
          <TableBody>
            {filtered.map(l => {
              const p = l.progress_kumulatif
              return (
                <TableRow key={l.id_lokasi}>
                  <TableCell className="text-xs">{l.id_lokasi}</TableCell>
                  <TableCell className="font-semibold text-xs">{l.nama_kampung}</TableCell>
                  <TableCell className="text-xs">{l.provinsi}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{l.kabupaten}</TableCell>
                  <TableCell><Badge variant={l.status_knmp==='HUB'?'success':'secondary'} className="text-[10px]">{l.status_knmp}</Badge></TableCell>
                  <TableCell><Badge variant={p!=null&&p>=100?'success':p!=null&&p>0?'warning':'info'} className="text-[10px]">{p!=null?p+'%':'—'}</Badge></TableCell>
                  <TableCell><Link to={`/admin/locations/${l.id_lokasi}`}><Button variant="outline" size="xs">Detail</Button></Link></TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
