"""Import observed consumer prices from official FishInfo Jatim.

An unavailable or stale source fails the job; estimates never get a fresh date.
"""
import re
from datetime import date, timedelta
from zoneinfo import ZoneInfo
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from app.database import SessionLocal
from app.models import CommodityPrice

SOURCE_URL = "https://fishinfojatim.net/"
SOURCE_NAME = "FishInfo Jatim (DKP Jawa Timur) — rata-rata konsumen"
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6,
          "jul": 7, "agu": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12}
NAME_MAP = {name.lower(): name for name in (
    "Udang Vaname", "Cumi-cumi", "Gurami", "Bandeng", "Tongkol",
    "Kepiting", "Nila", "Kembung", "Tuna", "Lele")}


def parse_page(html, today=None):
    today = today or datetime.now(ZoneInfo("Asia/Jakarta")).date()
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.select_one("#tableHead h5")
    table = soup.select_one("#tabel-harga tbody")
    if not heading or not table:
        raise ValueError("Struktur tabel harga FishInfo berubah atau kosong")
    period = re.search(r"(\d{1,2})(?:\s+([A-Za-z]+))?\s*[-–]\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", heading.get_text(" ", strip=True))
    if not period:
        raise ValueError("Periode FishInfo tidak terbaca")
    day_start, start_month_name, day_end, end_month_name, year = period.groups()
    end_month = MONTHS.get(end_month_name.lower()[:3])
    start_month = MONTHS.get((start_month_name or end_month_name).lower()[:3])
    if not start_month or not end_month:
        raise ValueError(f"Bulan FishInfo tidak dikenal: {heading.get_text(' ', strip=True)}")
    end = date(int(year), end_month, int(day_end))
    start_year = int(year) - (1 if start_month > end_month else 0)
    start = date(start_year, start_month, int(day_start))
    if not start <= today <= end + timedelta(days=1):
        raise ValueError(f"Periode sumber {start} s.d. {end} tidak mencakup {today}")
    prices = {}
    for row in table.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        name = cells[0].get_text(" ", strip=True).lower()
        number = re.search(r"Rp\s*([\d.]+)", cells[1].get_text(" ", strip=True), re.I)
        if name in NAME_MAP and number:
            value = int(number.group(1).replace(".", ""))
            if 1000 <= value <= 1_000_000:
                prices[NAME_MAP[name]] = value
    if len(prices) < 6:
        raise ValueError(f"Hanya {len(prices)} harga valid; impor dibatalkan")
    return start, end, prices


def main():
    response = requests.get(SOURCE_URL, headers={"User-Agent": "MarketWatchAJN/3.0"}, timeout=25)
    response.raise_for_status()
    start, end, prices = parse_page(response.text)
    db = SessionLocal()
    try:
        added = 0
        for name, value in prices.items():
            existing = db.query(CommodityPrice).filter_by(tanggal=start, komoditas=name, size="Rata-rata konsumen").first()
            if existing:
                existing.harga_tambak_low = value
                existing.harga_tambak_high = value
                existing.harga_ekspor_low = None
                existing.harga_ekspor_high = None
                existing.sumber = SOURCE_NAME
                existing.catatan = f"Periode sumber {start} s.d. {end}; {SOURCE_URL}"
                existing.tingkat_kepercayaan = "Sumber resmi"
            else:
                db.add(CommodityPrice(
                    tanggal=start, komoditas=name, size="Rata-rata konsumen",
                    harga_tambak_low=value, harga_tambak_high=value,
                    harga_ekspor_low=None, harga_ekspor_high=None,
                    sumber=SOURCE_NAME, tingkat_kepercayaan="Sumber resmi",
                    catatan=f"Periode sumber {start} s.d. {end}; {SOURCE_URL}"))
                added += 1
        db.commit()
        print(f"FishInfo Jatim {start}–{end}: {len(prices)} harga valid, {added} baru")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()



if __name__ == "__main__":
    main()
