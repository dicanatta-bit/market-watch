import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const fmtDate = (d) => {
  const dt = new Date(d + 'T00:00:00')
  return dt.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
}

const fmtTooltip = (d) => {
  const dt = new Date(d + 'T00:00:00')
  return dt.toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

export default function PriceChart({ history, komoditas, isArchive, onClose }) {
  const data = history.filter(h => Number.isFinite(h.harga_low) && Number.isFinite(h.harga_high)).map(h => ({
    date: h.date,
    price: Math.round((h.harga_low + h.harga_high) / 2),
  }))

  return (
    <div className="fixed inset-0 z-[5000] bg-black/50 flex items-center justify-center p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div><h3 className="font-bold text-base text-navy dark:text-blue-300">{komoditas}</h3><p className="text-xs text-slate-500 mt-1">{data.length ? `Riwayat ${fmtDate(data[0].date)}–${fmtDate(data[data.length - 1].date)}` : 'Riwayat harga'} · {isArchive ? 'rata-rata harga eceran pasar' : 'ringkasan konsumen'} Jawa Timur</p></div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-2xl leading-none">&times;</button>
        </div>
        <div className="p-6">
          {data.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-12">Belum ada observasi harga terverifikasi untuk periode ini.</p>
          ) : (
            <>
            {data.length === 1 && <p className="text-sm text-slate-600 mb-4">Baru ada 1 observasi pada {fmtTooltip(data[0].date)}. Titik harga ditampilkan; tren akan muncul setelah sinkronisasi periode berikutnya.</p>}
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={data} margin={{ top: 5, right: 15, left: 10, bottom: 5 }}>
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={fmtDate} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `Rp${(v/1000).toFixed(1)}k`} width={68} tickCount={4} domain={data.length === 1 ? [data[0].price * 0.9, data[0].price * 1.1] : ['auto', 'auto']} />
                <Tooltip
                  formatter={value => [`Rp ${value.toLocaleString('id-ID')}/kg`, isArchive ? 'Rata-rata eceran pasar' : 'Ringkasan konsumen']}
                  labelFormatter={fmtTooltip}
                />
                <Line type="linear" dataKey="price" stroke="#235d86" strokeWidth={2.5} dot={{ r: 5, fill: '#235d86' }} activeDot={{ r: 7 }} />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-xs text-slate-500 mt-3">{isArchive ? 'Tiap titik adalah rata-rata pasar yang tersedia pada minggu tersebut. Minggu berjalan bisa berubah saat pasar lain melapor.' : 'Tiap titik adalah periode ringkasan dari sumber.'} Minggu tanpa data tidak diisi otomatis. <a href={isArchive ? 'https://fishinfojatim.net/HargaPedagang' : 'https://fishinfojatim.net/'} target="_blank" rel="noreferrer" className="underline">Lihat sumber ↗</a></p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
