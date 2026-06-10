"""scrape_sihi.py — Scrape SIHI KKP harga ikan per TPI → INSERT tpi_prices"""
import sys, time, re, requests
from datetime import date
from bs4 import BeautifulSoup
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import TpiPrice

SIHI_URL = "https://sihi.kkp.go.id"
PIPP_URL = "https://pipp.kkp.go.id"
HTTP_HEADERS = {"User-Agent":"Mozilla/5.0 (compatible; MarketWatchAJN/3.0)","Accept":"application/json, text/html"}


def scrape_sihi():
    """Best-effort scrape dari SIHI / PIPP KKP."""
    items = []
    try:
        r = requests.get(f"{SIHI_URL}/harga-ikan/data", params={"draw":1,"start":0,"length":100,"tanggal":date.today().strftime("%Y-%m-%d")},
                         headers=HTTP_HEADERS, timeout=15)
        if r.status_code == 200 and r.headers.get("content-type","").startswith("application/json"):
            data = r.json()
            if isinstance(data, dict) and "data" in data:
                for row in data["data"]:
                    if isinstance(row, (list,tuple)):
                        items.append({"nama_tpi": str(row[0]) if len(row)>0 else "", "komoditas": str(row[3]) if len(row)>3 else "", "harga": _parse_harga(str(row[4])) if len(row)>4 else 0})
    except Exception as e:
        print(f"  SIHI: {type(e).__name__}")

    if not items:
        try:
            r = requests.get(f"{PIPP_URL}/rata-rata-harga", params={"tanggal": date.today().strftime("%Y-%m-%d")},
                             headers=HTTP_HEADERS, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for table in soup.find_all("table"):
                    for tr in table.find_all("tr")[1:]:
                        cells = tr.find_all(["td","th"])
                        if len(cells) >= 3:
                            items.append({"nama_tpi": cells[0].get_text(strip=True), "komoditas": cells[1].get_text(strip=True), "harga": _parse_harga(cells[2].get_text(strip=True))})
        except Exception as e:
            print(f"  PIPP: {type(e).__name__}")

    return items


def _parse_harga(s):
    s = re.sub(r"[Rp\s]", "", str(s or ""))
    s = re.sub(r"[.,](\d{3})", r"\1", s)
    s = re.sub(r"[.,]", "", s)
    s = re.sub(r"[^\d]", "", s)
    try: return float(s) if s else 0
    except: return 0


def main():
    print("=" * 55)
    print(f"SIHI Scraper — {date.today()}")

    items = scrape_sihi()
    if not items:
        print("  ❌ No data from SIHI/PIPP — servers may be unreachable outside Indonesia")
        print("=" * 55)
        return

    TODAY = date.today()
    db = SessionLocal()
    added = 0
    try:
        for item in items[:200]:  # limit to 200 per run
            if item.get("harga") and item["harga"] > 0:
                db.add(TpiPrice(nama_tpi=item.get("nama_tpi",""), komoditas=item.get("komoditas",""),
                                harga=item["harga"], tanggal=TODAY))
                added += 1
        db.commit()
        print(f"  ✓ {added} TPI prices inserted")
    finally:
        db.close()
    print("=" * 55)


if __name__ == "__main__":
    main()
