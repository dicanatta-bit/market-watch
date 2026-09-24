"""Seed a disposable SQLite database from public read-only sources for local UI smoke tests.

Run: python -m tests.local_smoke_seed /private/tmp/market-watch-smoke.db
The target must not exist. This never connects to the production database.
"""
import argparse
from pathlib import Path

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import CommodityPrice, KnmpLocation
from app.scrapers.commodity import SOURCE_NAME, SOURCE_URL, parse_page

KNMP_URL = "https://portal.agrinasjaladri.co.id/market-watch/api/knmp"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db", type=Path, help="new disposable SQLite database path")
    args = parser.parse_args()
    target = args.db.resolve()
    if target.exists():
        parser.error(f"Refusing to overwrite existing file: {target}")
    price_response = requests.get(SOURCE_URL, timeout=30)
    price_response.raise_for_status()
    period_start, period_end, prices = parse_page(price_response.text)
    locations_response = requests.get(KNMP_URL, timeout=40)
    locations_response.raise_for_status()
    locations = locations_response.json().get("data", [])
    if not isinstance(locations, list) or len(locations) < 100:
        raise ValueError("KNMP API returned too few locations; refusing to seed")
    engine = create_engine(f"sqlite:///{target}")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        for name, value in prices.items():
            db.add(CommodityPrice(tanggal=period_start, komoditas=name,
                                  size="Rata-rata konsumen", harga_tambak_low=value,
                                  harga_tambak_high=value, sumber=SOURCE_NAME,
                                  tingkat_kepercayaan="Sumber resmi",
                                  catatan=f"Periode sumber {period_start} s.d. {period_end}; {SOURCE_URL}"))
        for item in locations:
            db.add(KnmpLocation(**{key: item.get(key) for key in (
                "id_lokasi", "nama_kampung", "provinsi", "kabupaten", "kecamatan",
                "desa", "lat", "lon", "tahun", "status_knmp", "jumlah_nelayan",
                "jumlah_kapal") if key in item}))
        db.commit()
    print(f"Local-only smoke DB: {target}; {len(prices)} prices, {len(locations)} KNMP locations")


if __name__ == "__main__":
    main()
