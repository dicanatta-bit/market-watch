export default function CommodityCard({ item }) {
  const isFish = /tuna|cakalang|kakap|kerapu|cumi|lobster/i.test(item.komoditas)
  const lo = (item.harga_tambak_low || 0).toLocaleString('id')
  const hi = (item.harga_tambak_high || 0).toLocaleString('id')
  const ekspor = item.harga_ekspor_low ? `$${item.harga_ekspor_low.toFixed(2)}` : '—'

  return (
    <div className={`bg-white rounded-xl p-4 shadow-sm border-t-[3px] ${isFish ? 'border-t-emerald-700' : 'border-t-navy'} hover:-translate-y-1 hover:shadow-md transition cursor-default`}>
      <div className="flex justify-between items-start mb-2">
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${isFish ? 'bg-emerald-50 text-emerald-700' : 'bg-blue-50 text-blue-700'}`}>
          {isFish ? 'Tangkap' : 'Budidaya'}
        </span>
      </div>
      <h3 className="text-sm font-bold text-navy leading-tight">{item.komoditas}</h3>
      <p className="text-[11px] text-slate-400 mt-0.5">{item.size}</p>
      <p className="text-lg font-extrabold text-slate-800 mt-2">
        Rp {lo} – {hi}<span className="text-[11px] font-normal text-slate-400">/kg</span>
      </p>
      <p className="text-[11px] text-slate-500 mt-1">Ekspor: USD {ekspor}/kg</p>
      <p className="text-[9px] text-slate-300 mt-auto pt-3 truncate">{item.sumber}</p>
    </div>
  )
}
