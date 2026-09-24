"""Backfill observed weekly retail-market prices from FishInfo Jatim.

Each point is the arithmetic mean of the market prices shown by FishInfo for
that exact date range. Missing weeks/commodities are never interpolated.
"""
import argparse
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from app.database import SessionLocal
from app.models import CommodityPrice

SOURCE_URL = "https://fishinfojatim.net/dashboard/dashharga"
SOURCE_NAME = "FishInfo Jatim (DKP Jawa Timur) — eceran pasar, olah AJN"
SERIES_SIZE = "Rata-rata eceran pasar"
BACKFILL_START = date(2026, 5, 20)  # Week containing the last successful May sync.
FISH_IDS = {
    "Bandeng": 613, "Cumi-cumi": 166, "Gurami": 616,
    "Kembung": 20, "Kepiting": 25, "Lele": 619,
    "Nila": 621, "Tongkol": 161, "Tuna": 75,
    "Udang Vaname": 610,
}


def jakarta_today():
    return datetime.now(ZoneInfo("Asia/Jakarta")).date()


def week_starts(first, last):
    """Wednesday-start weekly buckets, including the partial current week."""
    cursor = first
    while cursor <= last:
        yield cursor, min(cursor + timedelta(days=6), last)
        cursor += timedelta(days=7)


def parse_archive_page(html, name, start, end):
    soup = BeautifulSoup(html, "html.parser")
    section = soup.select_one("#tab-tabel")
    table = soup.select_one("#tb_harga tbody")
    if section is None or table is None:
        raise ValueError("Tabel historis FishInfo tidak ditemukan")
    heading = section.select_one("center")
    title = heading.get_text(" ", strip=True) if heading else ""
    normalized = " ".join(title.split()).casefold()
    if f"eceran ikan {name}".casefold() not in normalized or "jawa timur" not in normalized:
        raise ValueError(f"Filter komoditas tidak cocok: {title}")
    period = re.search(r"(\d{1,2} [A-Za-z]+ \d{4})\s*-\s*(\d{1,2} [A-Za-z]+ \d{4})", title)
    if not period:
        raise ValueError(f"Periode historis tidak terbaca: {title}")
    actual_start = datetime.strptime(period.group(1), "%d %B %Y").date()
    actual_end = datetime.strptime(period.group(2), "%d %B %Y").date()
    if (actual_start, actual_end) != (start, end):
        raise ValueError(f"Periode historis salah: {actual_start}–{actual_end}")

    prices = []
    for row in table.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 4 or cells[1].get_text(" ", strip=True).casefold() != name.casefold():
            continue
        amount = re.search(r"([\d.]+,\d{2})", cells[3].get_text(" ", strip=True))
        if not amount:
            continue
        value = float(amount.group(1).replace(".", "").replace(",", "."))
        if 1000 <= value <= 1_000_000:
            prices.append(value)
    if not prices:
        return None
    return round(statistics.mean(prices)), len(prices)


def fetch_week(name, fish_id, start, end):
    params = {"tgl1": start.isoformat(), "tgl2": end.isoformat(),
              "ikan": str(fish_id), "pasar": "all", "jenis": "0", "kota": "all"}
    for attempt in range(3):
        try:
            response = requests.get(SOURCE_URL, params=params,
                                    headers={"User-Agent": "MarketWatchAJN/3.0"}, timeout=35)
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            if attempt == 2 or (isinstance(exc, requests.HTTPError)
                                and response.status_code < 500):
                raise
            time.sleep(0.5 * (2 ** attempt))
    result = parse_archive_page(response.text, name, start, end)
    return result, response.url


def sync_history(first=BACKFILL_START, last=None, dry_run=False):
    last = last or jakarta_today()
    if first > last:
        raise ValueError("Tanggal awal backfill melebihi tanggal akhir")
    db = SessionLocal()
    total = 0
    try:
        for start, end in week_starts(first, last):
            # Revisit recent weeks for late source corrections. Older complete
            # weeks are skipped; missing fish are retried.
            existing = {
                p.komoditas: p for p in db.query(CommodityPrice).filter_by(
                    tanggal=start, size=SERIES_SIZE).all()
                if p.sumber == SOURCE_NAME
            }
            names = list(FISH_IDS) if end >= last - timedelta(days=14) else [
                n for n in FISH_IDS if n not in existing]
            if not names:
                continue
            results = {}
            errors = []
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {pool.submit(fetch_week, name, FISH_IDS[name], start, end): name for name in names}
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        results[name] = future.result()
                    except Exception as exc:
                        errors.append(f"{name}: {exc}")
            if errors:
                raise RuntimeError(f"FishInfo {start}–{end}: " + "; ".join(errors))
            for name, (observation, url) in results.items():
                if observation is None:
                    continue
                value, count = observation
                total += 1
                if dry_run:
                    continue
                row = existing.get(name)
                if row is None:
                    row = CommodityPrice(tanggal=start, komoditas=name, size=SERIES_SIZE)
                    db.add(row)
                row.harga_tambak_low = value
                row.harga_tambak_high = value
                row.harga_ekspor_low = None
                row.harga_ekspor_high = None
                row.sumber = SOURCE_NAME
                row.tingkat_kepercayaan = "Observasi resmi; rata-rata olahan AJN"
                row.catatan = f"Periode {start} s.d. {end}; {count} harga pasar; {url}"
            if not dry_run:
                db.commit()  # A completed week survives a later network failure.
            print(f"FishInfo historis {start}–{end}: {len(results)} respons, "
                  f"{sum(value[0] is not None for value in results.values())} komoditas berdata")
        return total
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Backfill harga eceran mingguan FishInfo Jatim")
    parser.add_argument("--from", dest="first", type=date.fromisoformat, default=BACKFILL_START)
    parser.add_argument("--until", type=date.fromisoformat, default=jakarta_today())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    count = sync_history(args.first, args.until, args.dry_run)
    print(f"Total {count} observasi komoditas diproses")


if __name__ == "__main__":
    main()
