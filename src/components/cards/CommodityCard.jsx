import { ArrowUpRight } from 'lucide-react'

export default function CommodityCard({ item }) {
  const capture = /tuna|tongkol|cakalang|kembung|cumi|kepiting/i.test(item.komoditas)
  return <div className="mw-price-card"><div className="mw-price-card-top"><span className={`mw-price-category ${capture ? 'capture' : 'culture'}`}>{capture ? 'TANGKAP' : 'BUDIDAYA'}</span><ArrowUpRight size={17}/></div><div><h3>{item.komoditas}</h3><p>{item.size}</p></div><div className="mw-price-value"><span>Rp</span><strong>{Number(item.harga_tambak_low).toLocaleString('id-ID')}</strong><span>/ kg</span></div><div className="mw-price-foot"><span>{item.market_count ? `${item.market_count} harga pasar · Jawa Timur` : 'Rata-rata konsumen · Jawa Timur'}</span><span>Lihat riwayat →</span></div></div>
}
