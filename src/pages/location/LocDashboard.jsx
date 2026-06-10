import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { fetchKnmp } from '../../api/client.js'
import { Button } from '../../components/ui/Button.jsx'
import { Input } from '../../components/ui/Input.jsx'
import { Textarea } from '../../components/ui/Textarea.jsx'
import { Badge } from '../../components/ui/Badge.jsx'
import { Card, CardHeader, CardContent, CardTitle } from '../../components/ui/Card.jsx'
import { Progress } from '../../components/ui/Progress.jsx'
import { Skeleton } from '../../components/ui/Skeleton.jsx'

export default function LocDashboard() {
  const { id } = useParams()
  const [loc, setLoc] = useState(null)

  useEffect(() => { fetchKnmp().then(data => setLoc(data.find(l => l.id_lokasi === parseInt(id)))) }, [id])

  if (!loc) return <div className="space-y-4">{[1,2,3].map(i=><Skeleton key={i} className="h-40 rounded-xl"/>)}</div>

  const p = loc.progress_kumulatif

  return (
    <div>
      <h2 className="text-base font-bold text-foreground mb-1">{loc.nama_kampung}</h2>
      <div className="flex flex-wrap gap-2 mb-4 text-xs">
        <span className="text-muted-foreground">{loc.provinsi} · {loc.kabupaten}</span>
        <Badge variant={loc.status_knmp==='HUB'?'success':'secondary'} className="text-[10px]">{loc.status_knmp}</Badge>
        <span className="text-muted-foreground">Nelayan {loc.jumlah_nelayan||0} · Kapal {loc.jumlah_kapal||0}</span>
      </div>

      {/* Progress Kumulatif */}
      <Card className="mb-4">
        <CardHeader><CardTitle>Progress Kumulatif</CardTitle></CardHeader>
        <CardContent>
          <Progress value={p||0} className="h-4 mb-3" indicatorClassName={p!=null&&p>=100?'bg-emerald-500':p!=null&&p>0?'bg-amber-500':'bg-blue-500'} />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span><strong>{p!=null?p+'%':'0%'}</strong> kumulatif</span>
            <span>Fisik: <strong>{loc.realisasi_fisik!=null?loc.realisasi_fisik+'%':'—'}</strong></span>
            <span>Keuangan: <strong>{loc.realisasi_keuangan!=null?loc.realisasi_keuangan+'%':'—'}</strong></span>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Item Pembangunan */}
        <Card>
          <CardHeader><CardTitle>Item Pembangunan</CardTitle></CardHeader>
          <CardContent>
            {['Bangunan TPI','Dermaga','Cold Storage'].map((item,i)=>(
              <div key={i} className="py-2.5 border-b border-border last:border-0">
                <div className="flex justify-between items-center mb-1">
                  <strong className="text-xs">{item}</strong>
                  <Button variant="outline" size="xs">Update</Button>
                </div>
                <Progress value={Math.min(i*30+10,100)} className="h-2" indicatorClassName="bg-amber-400" />
              </div>
            ))}
            <p className="text-[11px] text-muted-foreground mt-3">Login via admin_lokasi untuk update real-time</p>
          </CardContent>
        </Card>

        {/* Harga TPI + Kendala */}
        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Harga TPI</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-2 mb-3">
                <Input placeholder="Komoditas" className="h-8 text-xs" />
                <Input placeholder="TPI" className="h-8 text-xs w-24" />
                <Input type="number" placeholder="Harga" className="h-8 text-xs w-20" />
                <Button size="xs">+</Button>
              </div>
              <p className="text-[11px] text-muted-foreground">Belum ada data harga. Input harga pertama!</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>⚠️ Kendala & Tindak Lanjut</CardTitle></CardHeader>
            <CardContent>
              <Textarea rows={2} placeholder="Deskripsi kendala..." className="mb-2 text-xs" />
              <Textarea rows={2} placeholder="Rencana tindak lanjut..." className="mb-3 text-xs" />
              <Button variant="outline" size="xs">Simpan</Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* CCTV */}
      <Card className="mt-4">
        <CardHeader><CardTitle>📹 CCTV Monitoring</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {['CCTV Depan TPI','CCTV Dermaga'].map((label,i)=>(
              <div key={i} className="bg-muted rounded-lg p-10 flex items-center justify-center text-xs text-muted-foreground text-center min-h-[150px]">
                <div><div className="text-3xl mb-1">📹</div>{label}<br/><span className="text-[10px]">Stream tersedia setelah integrasi CCTV</span></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
