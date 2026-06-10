"""alert_engine.py — Detect price changes >5% → INSERT alert_log"""
import sys
from datetime import date, timedelta
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import CommodityPrice, AlertLog


def main():
    db = SessionLocal()
    TODAY = date.today()
    WEEK_AGO = TODAY - timedelta(days=7)

    try:
        latest = db.query(CommodityPrice).filter(CommodityPrice.tanggal == TODAY).all()
        if not latest:
            prev_date = db.query(CommodityPrice.tanggal).order_by(CommodityPrice.tanggal.desc()).first()
            if not prev_date:
                print("No price data"); return
            latest = db.query(CommodityPrice).filter(CommodityPrice.tanggal == prev_date[0]).all()

        prev = {}
        for p in db.query(CommodityPrice).filter(CommodityPrice.tanggal <= WEEK_AGO).order_by(CommodityPrice.tanggal.desc()).all():
            key = f"{p.komoditas}|{p.size}"
            if key not in prev: prev[key] = p

        added = 0
        for p in latest:
            key = f"{p.komoditas}|{p.size}"
            old = prev.get(key)
            if not old or not old.harga_tambak_low or not p.harga_tambak_low: continue

            mid_old = (old.harga_tambak_low + (old.harga_tambak_high or old.harga_tambak_low)) / 2
            mid_new = (p.harga_tambak_low + (p.harga_tambak_high or p.harga_tambak_low)) / 2
            if mid_old == 0: continue

            pct = (mid_new - mid_old) / mid_old * 100
            if abs(pct) >= 5:
                alert_type = "MERAH" if abs(pct) >= 10 else "KUNING" if abs(pct) >= 7 else "BIRU"
                short = p.komoditas.split("(")[0].strip()
                pesan = f"{short} {p.size}: {'naik' if pct>0 else 'turun'} {abs(pct):.1f}% vs minggu lalu"
                rekomendasi = "Pantau pergerakan harga" if abs(pct) < 7 else "Pertimbangkan penyesuaian stok" if abs(pct) < 15 else "Evaluasi strategi pembelian"
                existing = db.query(AlertLog).filter_by(tanggal=TODAY, komoditas=p.komoditas, size=p.size).first()
                if not existing:
                    db.add(AlertLog(tanggal=TODAY, alert_type=alert_type, komoditas=p.komoditas, size=p.size, pesan=pesan, rekomendasi=rekomendasi))
                    added += 1

        db.commit()
        print(f"Alert engine: {added} alerts generated")
    finally:
        db.close()

if __name__ == "__main__":
    main()
