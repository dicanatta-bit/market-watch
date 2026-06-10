import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { fetchKnmp } from '../../api/client.js'
import { Card } from '../../components/ui/Card.jsx'
import { Badge } from '../../components/ui/Badge.jsx'
import { Progress } from '../../components/ui/Progress.jsx'
import { Skeleton } from '../../components/ui/Skeleton.jsx'

export default function LocationDetail() {
  const { id } = useParams()
  const [loc, setLoc] = useState(null)

  useEffect(() => { fetchKnmp().then(data => setLoc(data.find(l => l.id_lokasi === parseInt(id)))) }, [id])

  if (!loc) return <div className="space-y-4">{[1,2,3].map(i=><Skeleton key={i} className="h-40 rounded-xl"/>)}</div>

  const p = loc.progress_kumulatif

  return (
    <div>
      <h2 className="text-base font-bold text-foreground mb-1">KNMP #{loc.id_lokasi} — {loc.nama_kampung}</h2>
      <p className="text-xs text-muted-foreground mb-4">{loc.provinsi} · {loc.kabupaten} · {loc.kecamatan || '—'}</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="p-5">
          <h3 className="text-sm font-bold text-foreground mb-3 pb-2 border-b-2 border-gold">Info Lokasi</h3>
          <div className="space-y-2 text-xs">
            {[
              ['Status', <Badge variant={loc.status_knmp==='HUB'?'success':'secondary'} className="text-[10px]">{loc.status_knmp}</Badge>],
              ['Progress', p!=null?p+'%':'—'],
              ['Tahun', loc.tahun||'—'],
              ['Penyedia', loc.penyedia||'—'],
              ['Nelayan', loc.jumlah_nelayan||'—'],
              ['Kapal', loc.jumlah_kapal||'—'],
              ['Fisik', loc.realisasi_fisik!=null?loc.realisasi_fisik+'%':'—'],
              ['Keuangan', loc.realisasi_keuangan!=null?loc.realisasi_keuangan+'%':'—'],
            ].map(([l,v],i)=>(
              <div key={i} className="flex justify-between py-1.5 border-b border-border"><span className="text-muted-foreground w-28">{l}</span><span className="font-semibold">{v}</span></div>
            ))}
          </div>
        </Card>
        <Card className="p-5">
          <h3 className="text-sm font-bold text-foreground mb-3 pb-2 border-b-2 border-gold">Progress</h3>
          <Progress value={p||0} className="h-3 mb-3" indicatorClassName={p!=null&&p>=100?'bg-emerald-500':p!=null&&p>0?'bg-amber-500':'bg-blue-500'} />
          <p className="text-xs text-muted-foreground">Progress kumulatif: <strong>{p!=null?p+'%':'Belum ada data'}</strong></p>
          <p className="text-xs text-muted-foreground mt-2">Snapshot: {loc.snapshot_date||'—'}</p>
        </Card>
      </div>
    </div>
  )
}
