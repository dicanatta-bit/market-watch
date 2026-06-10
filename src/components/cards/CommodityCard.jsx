import { Card } from '../ui/Card.jsx'
import { Badge } from '../ui/Badge.jsx'

export default function CommodityCard({ item }) {
  const isFish = /tuna|cakalang|kakap|kerapu|cumi|lobster/i.test(item.komoditas)
  const lo = (item.harga_tambak_low || 0).toLocaleString('id')
  const hi = (item.harga_tambak_high || 0).toLocaleString('id')
  const ekspor = item.harga_ekspor_low ? `$${item.harga_ekspor_low.toFixed(2)}` : '—'

  return (
    <Card className={`p-4 border-t-[3px] ${isFish ? 'border-t-emerald-600' : 'border-t-navy'} hover:-translate-y-1 hover:shadow-md transition cursor-default`}>
      <div className="flex justify-between items-start mb-2">
        <Badge variant={isFish ? 'success' : 'info'} className="text-[10px]">{isFish ? 'Tangkap' : 'Budidaya'}</Badge>
      </div>
      <h3 className="text-sm font-bold text-foreground leading-tight">{item.komoditas}</h3>
      <p className="text-[11px] text-muted-foreground mt-0.5">{item.size}</p>
      <p className="text-lg font-extrabold text-foreground mt-2">Rp {lo} – {hi}<span className="text-[11px] font-normal text-muted-foreground">/kg</span></p>
      <p className="text-[11px] text-muted-foreground mt-1">Ekspor: USD {ekspor}/kg</p>
      <p className="text-[9px] text-muted-foreground/50 mt-auto pt-3 truncate">{item.sumber}</p>
    </Card>
  )
}
