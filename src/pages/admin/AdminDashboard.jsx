import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchStats } from '../../api/client.js'
import { Card } from '../../components/ui/Card.jsx'
import { Button } from '../../components/ui/Button.jsx'
import { Skeleton } from '../../components/ui/Skeleton.jsx'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  useEffect(() => { fetchStats().then(setStats) }, [])

  if (!stats) return <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">{[1,2,3,4].map(i=><Skeleton key={i} className="h-24 rounded-xl"/>)}</div>

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {[[stats.total_lokasi,'Total Lokasi','navy'],[stats.selesai,'Selesai','green'],[stats.berjalan,'Berjalan','gold'],[724,'Total User','blue']].map(([v,l,c],i)=>(
          <Card key={i} className={`p-4 border-l-4 ${c==='green'?'border-l-emerald-500':c==='gold'?'border-l-gold':c==='blue'?'border-l-blue-500':'border-l-navy'}`}>
            <div className={`text-xl font-extrabold ${c==='green'?'text-emerald-700 dark:text-emerald-400':c==='gold'?'text-amber-700 dark:text-amber-400':c==='blue'?'text-blue-700 dark:text-blue-400':'text-navy'}`}>{v}</div>
            <div className="text-[11px] text-muted-foreground mt-1">{l}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="p-5">
          <h3 className="text-sm font-bold text-foreground mb-3 pb-2 border-b-2 border-gold">Quick Links</h3>
          <Link to="/admin/locations"><Button variant="default" className="w-full mb-2">📍 Manage Locations</Button></Link>
          <Link to="/admin/users"><Button variant="outline" className="w-full mb-2">👥 Manage Users</Button></Link>
          <a href="/api/export/excel"><Button variant="gold" className="w-full mb-2">📥 Export Excel</Button></a>
          <a href="/api/export/pdf"><Button variant="outline" className="w-full">📄 Export PDF</Button></a>
        </Card>
        <Card className="p-5">
          <h3 className="text-sm font-bold text-foreground mb-3 pb-2 border-b-2 border-gold">Link Publik</h3>
          <a href="/" target="_blank"><Button variant="outline" className="w-full mb-2">📊 Dashboard Harga</Button></a>
          <a href="/peta" target="_blank"><Button variant="outline" className="w-full">🗺️ Peta KNMP</Button></a>
        </Card>
      </div>
    </div>
  )
}
