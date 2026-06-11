import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function PriceChart({ history, komoditas, onClose }) {
  const data = history.map(h => ({
    date: h.date,
    low: h.harga_low,
    high: h.harga_high,
    avg: Math.round((h.harga_low + h.harga_high) / 2),
  }))

  return (
    <div className="fixed inset-0 z-[5000] bg-black/50 flex items-center justify-center p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200 dark:border-slate-700">
          <h3 className="font-bold text-sm text-navy dark:text-blue-300">{komoditas}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none">&times;</button>
        </div>
        <div className="p-5">
          {data.length < 2 ? (
            <p className="text-sm text-slate-500 text-center py-8">Belum cukup data untuk grafik (min 2 minggu)</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.02}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={v => v.substring(5)} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `Rp${(v/1000).toFixed(0)}k`} width={60} />
                <Tooltip
                  formatter={(value, name) => {
                    const label = name === 'low' ? 'Rendah' : name === 'high' ? 'Tinggi' : 'Rata-rata'
                    return [`Rp ${value.toLocaleString('id')}/kg`, label]
                  }}
                  labelFormatter={label => `Tanggal: ${label}`}
                />
                <Area type="monotone" dataKey="high" stroke="#3B82F6" fill="none" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="avg" stroke="#1d4ed8" strokeWidth={1.5} dot={{ r: 3 }} fill="url(#colorPrice)" />
                <Area type="monotone" dataKey="low" stroke="#93c5fd" fill="none" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
