import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const fmtDate = (d) => {
  const dt = new Date(d + 'T00:00:00')
  return dt.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
}

const fmtTooltip = (d) => {
  const dt = new Date(d + 'T00:00:00')
  return dt.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

export default function PriceChart({ history, komoditas, onClose }) {
  const data = history.map(h => ({
    date: h.date,
    low: h.harga_low,
    high: h.harga_high,
    avg: Math.round((h.harga_low + h.harga_high) / 2),
  }))

  return (
    <div className="fixed inset-0 z-[5000] bg-black/50 flex items-center justify-center p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <h3 className="font-bold text-base text-navy dark:text-blue-300">{komoditas}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
        </div>
        <div className="p-6">
          {data.length < 2 ? (
            <p className="text-sm text-slate-500 text-center py-12">Belum cukup data untuk grafik (min 2 minggu)</p>
          ) : (
            <ResponsiveContainer width="100%" height={360}>
              <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
                <defs>
                  <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.02}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={fmtDate} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `Rp${(v/1000).toFixed(0)}k`} width={60} />
                <Tooltip
                  formatter={(value, name) => {
                    const label = name === 'low' ? 'Rendah' : name === 'high' ? 'Tinggi' : 'Rata-rata'
                    return [`Rp ${value.toLocaleString('id')}/kg`, label]
                  }}
                  labelFormatter={fmtTooltip}
                />
                <Area type="linear" dataKey="high" stroke="#3B82F6" fill="none" strokeWidth={2} dot={false} />
                <Area type="linear" dataKey="avg" stroke="#1d4ed8" strokeWidth={1.5} dot={{ r: 3 }} fill="url(#colorPrice)" />
                <Area type="linear" dataKey="low" stroke="#93c5fd" fill="none" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
