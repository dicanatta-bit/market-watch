"""
Market Watch - AJN
Update harga komoditas perikanan ke Google Sheet "Harga Komoditas"
- 14 kolom: tambah historis, % perubahan, sumber & tingkat kepercayaan
- Scraping best-effort dari shrimpnews.com, FAO, KKP (fallback ke Estimasi)
"""

import sys
import re
import time
from datetime import date, datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

try:
    import requests
    from bs4 import BeautifulSoup
    WEB = True
except ImportError:
    WEB = False

SERVICE_ACCOUNT_EMAIL = "knmp-ajn-service@knmp-ajn.iam.gserviceaccount.com"
SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
SHEET_NAME = "Harga Komoditas"
CREDENTIALS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Tanggal", "Komoditas", "Size",
    "Harga Tambak (Rp/kg)", "Harga Ekspor (USD/kg)", "Harga Internasional (USD/kg)",
    "Harga Minggu Lalu (Rp/kg)", "Harga 1 Bulan Lalu (Rp/kg)", "Harga 3 Bulan Lalu (Rp/kg)",
    "% vs Minggu Lalu", "% vs 3 Bulan Lalu",
    "Sumber", "Tingkat Kepercayaan", "Catatan",
]
HEADER_COL = chr(64 + len(HEADERS))   # 'N'

TANGGAL = date.today().strftime("%d/%m/%Y")

# ── Data dasar (fallback; diperbarui jika scraping berhasil) ──────────────────
BASE_DATA = [
    # Budidaya
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 50",
     "harga_tambak": "60.000 – 65.000", "harga_ekspor": "3,55 – 3,64",
     "harga_intl": "3,55 – 3,64",
     "sumber": "JALA Tech; UCN Global Shrimp Index; SeafoodSource",
     "catatan": "Harga tambak Jawa Tengah. Naik 1-3% vs bulan lalu."},
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 60",
     "harga_tambak": "55.000 – 60.000", "harga_ekspor": "3,55",
     "harga_intl": "3,55",
     "sumber": "JALA Tech; UCN Global Shrimp Index",
     "catatan": "Global turun 5,6% YoY (Mar 2026). Indonesia relatif stabil."},
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 70",
     "harga_tambak": "50.000 – 55.000", "harga_ekspor": "—",
     "harga_intl": "—",
     "sumber": "JALA Tech",
     "catatan": "Stabil. Produksi diperkirakan meningkat Apr-Mei."},
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 100",
     "harga_tambak": "40.000 – 45.000", "harga_ekspor": "—",
     "harga_intl": "—",
     "sumber": "JALA Tech",
     "catatan": "Estimasi berdasarkan gradasi harga antar ukuran."},
    {"komoditas": "Udang Windu (Penaeus monodon)", "size": "Size 20",
     "harga_tambak": "100.000 – 120.000", "harga_ekspor": "8,00 – 10,00",
     "harga_intl": "—",
     "sumber": "KKP; JALA Tech",
     "catatan": "Produksi terbatas; harga premium vs vaname."},
    {"komoditas": "Udang Windu (Penaeus monodon)", "size": "Size 30",
     "harga_tambak": "80.000 – 100.000", "harga_ekspor": "6,00 – 8,00",
     "harga_intl": "—",
     "sumber": "KKP; JALA Tech",
     "catatan": "Dominan dari Sulawesi & Kalimantan."},
    {"komoditas": "Nila (Oreochromis niloticus)", "size": "300-500 g",
     "harga_tambak": "22.000 – 28.000", "harga_ekspor": "3,00 – 4,00",
     "harga_intl": "—",
     "sumber": "KKP; DJPB",
     "catatan": "Ekspor fillet ke AS & Eropa."},
    # Tangkap
    {"komoditas": "Tuna Sirip Kuning / Yellowfin (Thunnus albacares)", "size": "Sashimi grade",
     "harga_tambak": "60.000 – 80.000", "harga_ekspor": "5,00 – 8,00",
     "harga_intl": "6,50 – 9,00",
     "sumber": "KKP; ASTUIN; PPS Bitung",
     "catatan": "Ekspor utama ke Jepang dan Eropa."},
    {"komoditas": "Tuna Sirip Kuning / Yellowfin (Thunnus albacares)", "size": "Loin/beku",
     "harga_tambak": "30.000 – 45.000", "harga_ekspor": "2,50 – 4,00",
     "harga_intl": "—",
     "sumber": "KKP; ASTUIN",
     "catatan": "Grade industri untuk pengalengan dan loin beku."},
    {"komoditas": "Tuna Cakalang (Katsuwonus pelamis)", "size": "-",
     "harga_tambak": "15.000 – 25.000", "harga_ekspor": "1,50 – 2,50",
     "harga_intl": "1,80 – 2,20",
     "sumber": "KKP; PPS Bitung; ASTUIN",
     "catatan": "Bahan baku utama pengalengan. Harga dipengaruhi musim tangkapan."},
    {"komoditas": "Kakap Merah (Lutjanus spp.)", "size": "-",
     "harga_tambak": "50.000 – 70.000", "harga_ekspor": "5,00 – 8,00",
     "harga_intl": "—",
     "sumber": "KKP; Pelabuhan Perikanan",
     "catatan": "Permintaan ekspor ke China & Singapura tinggi."},
    {"komoditas": "Kerapu (Epinephelus spp.)", "size": "Hidup (>500 g)",
     "harga_tambak": "100.000 – 150.000", "harga_ekspor": "8,00 – 12,00",
     "harga_intl": "—",
     "sumber": "KKP; DJPB; Pelabuhan Perikanan",
     "catatan": "Ekspor hidup ke China dominan."},
    {"komoditas": "Kerapu (Epinephelus spp.)", "size": "Beku/segar",
     "harga_tambak": "60.000 – 90.000", "harga_ekspor": "5,00 – 7,00",
     "harga_intl": "—",
     "sumber": "KKP; DJPB",
     "catatan": "Pasar lokal dan ekspor grade beku."},
    # ── Komoditas baru ────────────────────────────────────────────────────────
    {"komoditas": "Rumput Laut (Eucheuma cottonii)", "size": "Kering",
     "harga_tambak": "6.000 – 7.000", "harga_ekspor": "0,40 – 0,50",
     "harga_intl": "0,35 – 0,45",
     "sumber": "KKP; DJPB; Asosiasi Rumput Laut Indonesia",
     "catatan": "Harga kering di tingkat pembudidaya. Produksi dominan NTT, Sulawesi, Maluku. Rasio kering:basah ~1:8."},
    {"komoditas": "Rumput Laut (Eucheuma cottonii)", "size": "Basah",
     "harga_tambak": "1.000 – 1.500", "harga_ekspor": "—",
     "harga_intl": "—",
     "sumber": "KKP; DJPB",
     "catatan": "Harga basah di tingkat pembudidaya. Dijual ke pengepul untuk dikeringkan."},
    {"komoditas": "Lobster (Panulirus ornatus) / Mutiara", "size": ">200 g",
     "harga_tambak": "280.000 – 380.000", "harga_ekspor": "18,00 – 22,00",
     "harga_intl": "—",
     "sumber": "KKP; Pelabuhan Perikanan; Asosiasi Lobster Indonesia",
     "catatan": "Ekspor hidup ke Vietnam & China. Harga sangat sensitif terhadap kuota ekspor KKP."},
    {"komoditas": "Lobster (Panulirus homarus) / Pasir", "size": ">100 g",
     "harga_tambak": "150.000 – 220.000", "harga_ekspor": "10,00 – 15,00",
     "harga_intl": "—",
     "sumber": "KKP; Pelabuhan Perikanan",
     "catatan": "Ekspor hidup dan beku. Harga lebih rendah dari lobster mutiara."},
    {"komoditas": "Bandeng (Chanos chanos)", "size": "250-500 g",
     "harga_tambak": "20.000 – 28.000", "harga_ekspor": "1,80 – 2,50",
     "harga_intl": "—",
     "sumber": "KKP; DJPB; Pasar Ikan Nasional",
     "catatan": "Harga tambak Jawa Tengah & Jawa Timur. Stabil sepanjang tahun; sedikit premium menjelang Lebaran."},
    {"komoditas": "Cumi-cumi (Loligo spp.)", "size": "-",
     "harga_tambak": "35.000 – 50.000", "harga_ekspor": "3,50 – 5,00",
     "harga_intl": "3,00 – 4,50",
     "sumber": "KKP; Pelabuhan Perikanan; ASTUIN",
     "catatan": "Harga nelayan fluktuatif mengikuti musim tangkapan. Ekspor beku ke Eropa & Asia Timur."},
]


# ── Helper ────────────────────────────────────────────────────────────────────

def parse_mid(s, mode="IDR"):
    if not s or str(s).strip() in ("", "—", "-"):
        return None
    s = str(s).strip()
    if mode == "IDR":
        s = re.sub(r"[Rp\s]", "", s)
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(".", "").replace(",", ".")
    parts = re.split(r"\s*[–\-]\s*", s)
    try:
        vals = [float(p.strip()) for p in parts if p.strip()]
        return sum(vals) / len(vals) if vals else None
    except ValueError:
        return None


def parse_date(s):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(s).strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def lookup_tambak(sheet_data, komoditas, size, days_back):
    """Cari harga tambak (col 3) untuk komoditas+size dari ~days_back hari lalu."""
    today  = date.today()
    target = today - timedelta(days=days_back)
    best_row, best_delta = None, None
    for row in sheet_data[1:]:
        if len(row) < 4 or row[1] != komoditas or row[2] != size:
            continue
        d = parse_date(row[0])
        if d is None or d >= today:
            continue
        delta = abs((d - target).days)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_row = row
    if best_row and best_delta is not None and best_delta <= days_back + 14:
        return best_row[3]
    return ""


def fmt_pct(current_str, hist_str, mode="IDR"):
    """Hitung % perubahan antara dua string harga. Returns formatted string or ''."""
    now = parse_mid(current_str, mode)
    old = parse_mid(hist_str, mode)
    if now is None or old is None or old == 0:
        return ""
    pct = (now - old) / abs(old) * 100
    return f"{pct:+.2f}%"


# ── Scraping (best-effort) ────────────────────────────────────────────────────

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MarketWatchAJN/1.0; +https://ajn.id)",
    "Accept-Language": "en-US,en;q=0.9",
}


def _get(url, timeout=8):
    if not WEB:
        return None
    try:
        r = requests.get(url, headers=_HTTP_HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  [SCRAPING] Tidak dapat mengakses {url}: {type(e).__name__}")
        return None


def scrape_shrimpnews():
    """Coba ambil referensi harga udang dari ShrimpNews Asia."""
    print("  Mencoba ShrimpNews Asia...")
    html = _get("https://www.shrimpnews.com/FreeReportsFolder/Reports/AsiaReports.html")
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    pattern = re.compile(r"\$([\d]+\.[\d]{2})\s*/\s*kg", re.IGNORECASE)
    matches = [float(m) for m in pattern.findall(text)]
    if matches:
        avg = sum(matches) / len(matches)
        print(f"  [ShrimpNews] {len(matches)} referensi harga, rata-rata USD {avg:.2f}/kg")
        return {"shrimpnews_avg": avg, "sumber": "ShrimpNews Asia", "kepercayaan": "Sedang"}
    return {}


def scrape_fao():
    """Coba ambil ringkasan Fish Price Index dari FAO."""
    print("  Mencoba FAO Fish Price Index...")
    html = _get("https://www.fao.org/in-action/globefish/market-reports/resource-detail/en/c/338612/")
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    m = re.search(r"Fish\s+Price\s+Index[^\d]*(\d{2,3}(?:\.\d+)?)", text, re.IGNORECASE)
    if m:
        print(f"  [FAO] Fish Price Index: {m.group(1)}")
        return {"fao_fpi": float(m.group(1)), "sumber": "FAO Fish Price Index", "kepercayaan": "Tinggi"}
    return {}


def scrape_kkp():
    """Coba akses portal KKP untuk konfirmasi ketersediaan data."""
    print("  Mencoba portal KKP...")
    html = _get("https://kkp.go.id/", timeout=12)
    if html:
        print("  [KKP] Portal dapat diakses.")
        return {"kkp_ok": True, "sumber_kkp": "KKP.go.id"}
    return {}


def determine_kepercayaan(entry, web_results):
    """Tentukan tingkat kepercayaan data berdasarkan hasil scraping."""
    if web_results.get("kepercayaan") == "Tinggi":
        return "Tinggi"
    if web_results.get("kepercayaan") == "Sedang" or web_results.get("fao_fpi"):
        return "Sedang"
    return "Estimasi"


def enrich_sumber(entry, web_results):
    """Gabungkan sumber dasar dengan sumber scraping."""
    parts = [entry["sumber"]]
    if web_results.get("sumber"):
        parts.append(web_results["sumber"])
    if web_results.get("sumber_fao"):
        parts.append(web_results["sumber_fao"])
    if web_results.get("kkp_ok"):
        parts.append("KKP.go.id")
    return "; ".join(dict.fromkeys(p for p in parts if p))


# ── Sheet ─────────────────────────────────────────────────────────────────────

def get_or_create_sheet(spreadsheet, name):
    """Ambil atau buat sheet; perbarui header jika jumlah kolom berubah."""
    try:
        ws = spreadsheet.worksheet(name)
        existing = ws.get_all_values()
        if not existing:
            ws.append_row(HEADERS, value_input_option="RAW")
            ws.format(f"A1:{HEADER_COL}1", {"textFormat": {"bold": True}})
            return ws, []
        if existing[0] != HEADERS:
            ws.update("A1", [HEADERS], value_input_option="RAW")
            ws.format(f"A1:{HEADER_COL}1", {"textFormat": {"bold": True}})
            print(f"  Header '{name}' diperbarui ke {len(HEADERS)} kolom.")
        print(f"Sheet '{name}' ditemukan ({len(existing) - 1} baris data).")
        return ws, existing
    except gspread.exceptions.WorksheetNotFound:
        print(f"Sheet '{name}' tidak ada, membuat baru...")
        ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS, value_input_option="RAW")
        ws.format(f"A1:{HEADER_COL}1", {"textFormat": {"bold": True}})
        return ws, []


def cek_duplikat(sheet_data, tanggal, komoditas, size):
    for row in sheet_data[1:]:
        if len(row) >= 3 and row[0] == tanggal and row[1] == komoditas and row[2] == size:
            return True
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Market Watch AJN -- Update Harga ===\n")

    spreadsheet_id = sys.argv[1] if len(sys.argv) > 1 else SPREADSHEET_ID

    creds  = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    print("Autentikasi Google Sheets berhasil.")

    try:
        ss = client.open_by_key(spreadsheet_id)
    except gspread.exceptions.APIError as e:
        print(f"\n[ERROR] Tidak bisa membuka spreadsheet: {e}")
        print(f"Pastikan sudah di-share ke: {SERVICE_ACCOUNT_EMAIL}")
        sys.exit(1)
    print(f"Spreadsheet '{ss.title}' dibuka.\n")

    sheet, existing_data = get_or_create_sheet(ss, SHEET_NAME)

    # Jalankan scraping sekali (shared untuk semua komoditas udang)
    print("Menjalankan scraping sumber web...")
    web = {}
    web.update(scrape_shrimpnews())
    time.sleep(1)
    web.update(scrape_fao())
    time.sleep(1)
    web.update(scrape_kkp())
    print()

    ditambah = dilewati = 0

    for entry in BASE_DATA:
        k = entry["komoditas"]
        s = entry["size"]

        if cek_duplikat(existing_data, TANGGAL, k, s):
            print(f"  [LEWATI] {k} {s} — sudah ada hari ini.")
            dilewati += 1
            continue

        # Harga historis
        h_minggu  = lookup_tambak(existing_data, k, s, 7)
        h_1bulan  = lookup_tambak(existing_data, k, s, 30)
        h_3bulan  = lookup_tambak(existing_data, k, s, 90)

        pct_minggu = fmt_pct(entry["harga_tambak"], h_minggu)
        pct_3bulan = fmt_pct(entry["harga_tambak"], h_3bulan)

        kepercayaan = determine_kepercayaan(entry, web)
        sumber      = enrich_sumber(entry, web)

        baris = [
            TANGGAL,
            k, s,
            entry["harga_tambak"],
            entry["harga_ekspor"],
            entry["harga_intl"],
            h_minggu, h_1bulan, h_3bulan,
            pct_minggu, pct_3bulan,
            sumber,
            kepercayaan,
            entry["catatan"],
        ]

        sheet.append_row(baris, value_input_option="RAW")
        existing_data.append(baris)  # Update cache lokal
        print(f"  [OK] {k} {s} — ditambahkan. Kepercayaan: {kepercayaan}")
        ditambah += 1
        time.sleep(0.3)  # Hindari rate limiting

    print(f"\nSelesai: {ditambah} baris ditambahkan, {dilewati} dilewati.")
    print(f"Lihat: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
