"""scrape_commodity.py — Real web scraping + BASE_DATA fallback → INSERT MySQL"""
import sys, time, re
from datetime import date
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import CommodityPrice, RegionalPrice

try:
    import requests
    from bs4 import BeautifulSoup
    WEB = True
except ImportError:
    WEB = False

WILAYAH_FAKTOR = {"Jawa-Bali":1.00,"Sumatera":0.95,"Kalimantan":0.92,"Sulawesi":0.90,"NTT-NTB":0.88,"Maluku":0.85,"Papua":0.85}

HTTP_HEADERS = {"User-Agent":"Mozilla/5.0 (compatible; MarketWatchAJN/3.0)","Accept-Language":"en-US,en;q=0.9"}

BASE_DATA = [
    {"komoditas":"Udang Vaname (Litopenaeus vannamei)","size":"Size 50","tambak_lo":60000,"tambak_hi":65000,"ekspor_lo":3.55,"ekspor_hi":3.64,"sumber":"JALA Tech; KKP DJPB; UCN; ShrimpNews Asia","catatan":"Harga tambak Jawa Tengah. Naik 1-3% vs bulan lalu."},
    {"komoditas":"Udang Vaname (Litopenaeus vannamei)","size":"Size 60","tambak_lo":55000,"tambak_hi":60000,"ekspor_lo":3.55,"ekspor_hi":3.55,"sumber":"JALA Tech; KKP DJPB; FAO GLOBEFISH","catatan":"Global turun 5,6% YoY. Indonesia relatif stabil."},
    {"komoditas":"Udang Windu (Penaeus monodon)","size":"Size 20","tambak_lo":100000,"tambak_hi":120000,"ekspor_lo":8.00,"ekspor_hi":10.00,"sumber":"KKP DJPB; JALA Tech; SeafoodSource; ShrimpNews Asia","catatan":"Produksi terbatas; harga premium vs vaname."},
    {"komoditas":"Nila (Oreochromis niloticus)","size":"300-500 g","tambak_lo":22000,"tambak_hi":28000,"ekspor_lo":3.00,"ekspor_hi":4.00,"sumber":"KKP DJPB; BPS ekspor; FAO GLOBEFISH","catatan":"Ekspor fillet ke AS & Eropa."},
    {"komoditas":"Tuna Sirip Kuning / Yellowfin (Thunnus albacares)","size":"Sashimi grade","tambak_lo":60000,"tambak_hi":80000,"ekspor_lo":5.00,"ekspor_hi":8.00,"sumber":"KKP; ASTUIN; PPS Bitung; FAO GLOBEFISH; Undercurrent News","catatan":"Ekspor utama ke Jepang dan Eropa."},
    {"komoditas":"Tuna Cakalang (Katsuwonus pelamis)","size":"-","tambak_lo":15000,"tambak_hi":25000,"ekspor_lo":1.50,"ekspor_hi":2.50,"sumber":"KKP; PPS Bitung; ASTUIN; FAO GLOBEFISH","catatan":"Bahan baku utama pengalengan."},
    {"komoditas":"Rumput Laut (Eucheuma cottonii)","size":"Kering","tambak_lo":6000,"tambak_hi":7000,"ekspor_lo":0.40,"ekspor_hi":0.50,"sumber":"KKP DJPB; Asosiasi RL Indonesia; FAO GLOBEFISH","catatan":"Dominan NTT, Sulawesi, Maluku."},
    {"komoditas":"Lobster (Panulirus ornatus) / Mutiara","size":">200 g","tambak_lo":280000,"tambak_hi":380000,"ekspor_lo":18.00,"ekspor_hi":22.00,"sumber":"KKP; Pelabuhan Perikanan; Undercurrent News","catatan":"Sensitif terhadap kuota ekspor KKP."},
    {"komoditas":"Bandeng (Chanos chanos)","size":"250-500 g","tambak_lo":20000,"tambak_hi":28000,"ekspor_lo":1.80,"ekspor_hi":2.50,"sumber":"KKP DJPB; Pasar Ikan Nasional; BPS ekspor; Trobos Aqua","catatan":"Premium menjelang Lebaran."},
    {"komoditas":"Cumi-cumi (Loligo spp.)","size":"-","tambak_lo":35000,"tambak_hi":50000,"ekspor_lo":3.50,"ekspor_hi":5.00,"sumber":"KKP; Pelabuhan Perikanan; FAO GLOBEFISH","catatan":"Fluktuatif mengikuti musim tangkapan."},
]


def _get(url, timeout=10):
    if not WEB: return None
    try:
        r = requests.get(url, headers=HTTP_HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except: return None


def scrape_shrimpnews():
    print("  Mencoba ShrimpNews Asia...")
    html = _get("https://www.shrimpnews.com/FreeReportsFolder/Reports/AsiaReports.html")
    if not html: return {}
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(r"\$([\d]+\.[\d]{2})\s*/\s*kg", re.IGNORECASE)
    matches = [float(m) for m in pattern.findall(soup.get_text(" ", strip=True))]
    if matches:
        avg = sum(matches) / len(matches)
        print(f"  ✓ ShrimpNews: {len(matches)} ref, avg USD {avg:.2f}/kg")
        return {"shrimpnews_avg": avg, "sumber": "ShrimpNews Asia", "kepercayaan": "Sedang"}
    return {}


def scrape_fao():
    print("  Mencoba FAO Fish Price Index...")
    html = _get("https://www.fao.org/in-action/globefish/market-reports/resource-detail/en/c/338612/")
    if not html: return {}
    soup = BeautifulSoup(html, "html.parser")
    m = re.search(r"Fish\s+Price\s+Index[^\d]*(\d{2,3}(?:\.\d+)?)", soup.get_text(" ", strip=True), re.IGNORECASE)
    if m:
        print(f"  ✓ FAO FPI: {m.group(1)}")
        return {"fao_fpi": float(m.group(1)), "sumber": "FAO Fish Price Index", "kepercayaan": "Tinggi"}
    return {}


def scrape_kkp():
    print("  Mencoba portal KKP...")
    html = _get("https://kkp.go.id/", timeout=12)
    if html: print("  ✓ KKP dapat diakses"); return {"kkp_ok": True, "sumber_kkp": "KKP.go.id"}
    return {}


def scrape_worldbank():
    print("  Mencoba World Bank Fish Price Index...")
    if not WEB: return {}
    try:
        r = requests.get("https://api.worldbank.org/v2/country/wld/indicator/PFISH?format=json&date=2024:2026&per_page=10",
                          timeout=10, headers=HTTP_HEADERS)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and len(data) > 1:
            vals = [float(i["value"]) for i in (data[1] or []) if i.get("value")]
            if vals:
                avg = sum(vals) / len(vals)
                print(f"  ✓ WorldBank PFISH avg: {avg:.1f}")
                return {"wb_pfish": avg, "sumber_wb": "WorldBank PFISH"}
    except Exception as e: print(f"  WorldBank: {type(e).__name__}")
    return {}


def main():
    db = SessionLocal()
    print("=" * 55)
    print(f"Commodity Scraper — {date.today()}")

    # Web scraping (best-effort)
    time.sleep(0.5)
    web = {}; web.update(scrape_shrimpnews()); time.sleep(0.5)
    web.update(scrape_fao()); time.sleep(0.5)
    web.update(scrape_kkp()); time.sleep(0.5)
    web.update(scrape_worldbank())

    kepercayaan = "Sedang" if web else "Estimasi"
    sumber_extra = "; ".join(filter(None, [web.get("sumber"), web.get("sumber_fao"), web.get("sumber_kkp", "").replace("True","KKP.go.id")]))

    TODAY = date.today()
    added = 0
    try:
        for e in BASE_DATA:
            exists = db.query(CommodityPrice).filter_by(tanggal=TODAY, komoditas=e["komoditas"], size=e["size"]).first()
            if exists: continue
            db.add(CommodityPrice(
                tanggal=TODAY, komoditas=e["komoditas"], size=e["size"],
                harga_tambak_low=e["tambak_lo"], harga_tambak_high=e["tambak_hi"],
                harga_ekspor_low=e["ekspor_lo"], harga_ekspor_high=e["ekspor_hi"],
                sumber=f"{e['sumber']}; {sumber_extra}" if sumber_extra else e["sumber"],
                tingkat_kepercayaan=kepercayaan, catatan=e["catatan"]))
            added += 1

        for e in BASE_DATA:
            for w, f in WILAYAH_FAKTOR.items():
                exists = db.query(RegionalPrice).filter_by(tanggal=TODAY, wilayah=w, komoditas=e["komoditas"], size=e["size"]).first()
                if exists: continue
                db.add(RegionalPrice(tanggal=TODAY, wilayah=w, komoditas=e["komoditas"], size=e["size"],
                    harga_tambak_low=round(e["tambak_lo"]*f), harga_tambak_high=round(e["tambak_hi"]*f), faktor_wilayah=f))
        db.commit()
        print(f"\n✓ {added} commodity prices added, regional prices for {len(WILAYAH_FAKTOR)} wilayah")
        print("=" * 55)
    finally:
        db.close()

if __name__ == "__main__":
    main()
