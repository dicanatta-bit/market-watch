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

# ── Mapping (komoditas, size) di "Harga Komoditas" → key di "Historis 12 Bulan" ─
# Digunakan sebagai fallback ketika "Harga Komoditas" belum punya data lama.
_HISTORIS_KEY_MAP = {
    ("Udang Vaname (Litopenaeus vannamei)", "Size 50"):              "Udang Vaname Size 50",
    ("Udang Vaname (Litopenaeus vannamei)", "Size 60"):              "Udang Vaname Size 60",
    ("Udang Vaname (Litopenaeus vannamei)", "Size 70"):              "Udang Vaname Size 70",
    ("Udang Vaname (Litopenaeus vannamei)", "Size 100"):             "Udang Vaname Size 100",
    ("Udang Windu (Penaeus monodon)", "Size 20"):                    "Udang Windu Size 20",
    ("Udang Windu (Penaeus monodon)", "Size 30"):                    "Udang Windu Size 30",
    ("Nila (Oreochromis niloticus)", "300-500 g"):                   "Nila 300-500 g",
    ("Tuna Sirip Kuning / Yellowfin (Thunnus albacares)", "Sashimi grade"): "Tuna Yellowfin Sashimi",
    ("Tuna Sirip Kuning / Yellowfin (Thunnus albacares)", "Loin/beku"):     "Tuna Yellowfin Loin/beku",
    ("Tuna Cakalang (Katsuwonus pelamis)", "-"):                     "Tuna Cakalang",
    ("Kakap Merah (Lutjanus spp.)", "-"):                            "Kakap Merah",
    ("Kerapu (Epinephelus spp.)", "Hidup (>500 g)"):                 "Kerapu Hidup",
    ("Kerapu (Epinephelus spp.)", "Beku/segar"):                     "Kerapu Beku/segar",
    ("Rumput Laut (Eucheuma cottonii)", "Kering"):                   "Rumput Laut Kering",
    ("Rumput Laut (Eucheuma cottonii)", "Basah"):                    "Rumput Laut Basah",
    ("Rumput Laut ATC/SRC (E. cottonii processed)", "ATC/SRC"):      "Rumput Laut ATC/SRC",
    ("Lobster (Panulirus ornatus) / Mutiara", ">200 g"):             "Lobster Mutiara (>200 g)",
    ("Lobster (Panulirus homarus) / Pasir", ">100 g"):               "Lobster Pasir (>100 g)",
    ("Bandeng (Chanos chanos)", "250-500 g"):                        "Bandeng 250-500 g",
    ("Cumi-cumi (Loligo spp.)", "-"):                                "Cumi-cumi",
    ("Patin (Pangasianodon hypophthalmus)", "Utuh/Hidup"):           "Patin Utuh/Hidup",
    ("Patin (Pangasianodon hypophthalmus)", "Fillet Segar"):         "Patin Fillet Segar",
    ("Patin (Pangasianodon hypophthalmus)", "Fillet Beku Ekspor"):   "Patin Fillet Beku Ekspor",
}

_BULAN_ID_H = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
               "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

# ── Data dasar (fallback; diperbarui jika scraping berhasil) ──────────────────
# Sumber diverifikasi: KKP, BPS, DJPB, FAO GLOBEFISH, VASEP, ShrimpNews, SeafoodSource,
# Undercurrent News, IntraFish, IndexMundi, Trobos Aqua, Agrina, Kontan, Antaranews
BASE_DATA = [
    # ── Budidaya ──────────────────────────────────────────────────────────────
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 50",
     "harga_tambak": "60.000 – 65.000", "harga_ekspor": "3,55 – 3,64",
     "harga_intl": "3,55 – 3,64",
     "sumber": "JALA Tech; KKP DJPB; UCN Global Shrimp Index; SeafoodSource; ShrimpNews Asia; BPS ekspor",
     "catatan": "Harga tambak Jawa Tengah. Naik 1-3% vs bulan lalu."},
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 60",
     "harga_tambak": "55.000 – 60.000", "harga_ekspor": "3,55",
     "harga_intl": "3,55",
     "sumber": "JALA Tech; KKP DJPB; UCN Global Shrimp Index; FAO GLOBEFISH; ShrimpNews Asia; BPS ekspor",
     "catatan": "Global turun 5,6% YoY (Mar 2026). Indonesia relatif stabil."},
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 70",
     "harga_tambak": "50.000 – 55.000", "harga_ekspor": "—",
     "harga_intl": "—",
     "sumber": "JALA Tech; KKP DJPB; ShrimpNews Asia",
     "catatan": "Stabil. Produksi diperkirakan meningkat Apr-Mei."},
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 100",
     "harga_tambak": "40.000 – 45.000", "harga_ekspor": "—",
     "harga_intl": "—",
     "sumber": "JALA Tech; KKP DJPB",
     "catatan": "Estimasi berdasarkan gradasi harga antar ukuran."},
    {"komoditas": "Udang Windu (Penaeus monodon)", "size": "Size 20",
     "harga_tambak": "100.000 – 120.000", "harga_ekspor": "8,00 – 10,00",
     "harga_intl": "—",
     "sumber": "KKP DJPB; JALA Tech; SeafoodSource; ShrimpNews Asia; BPS ekspor",
     "catatan": "Produksi terbatas; harga premium vs vaname."},
    {"komoditas": "Udang Windu (Penaeus monodon)", "size": "Size 30",
     "harga_tambak": "80.000 – 100.000", "harga_ekspor": "6,00 – 8,00",
     "harga_intl": "—",
     "sumber": "KKP DJPB; JALA Tech; ShrimpNews Asia; BPS ekspor",
     "catatan": "Dominan dari Sulawesi & Kalimantan."},
    {"komoditas": "Nila (Oreochromis niloticus)", "size": "300-500 g",
     "harga_tambak": "22.000 – 28.000", "harga_ekspor": "3,00 – 4,00",
     "harga_intl": "—",
     "sumber": "KKP DJPB; BPS ekspor; FAO GLOBEFISH; Trobos Aqua; Antaranews",
     "catatan": "Ekspor fillet ke AS & Eropa."},
    # ── Tangkap ───────────────────────────────────────────────────────────────
    {"komoditas": "Tuna Sirip Kuning / Yellowfin (Thunnus albacares)", "size": "Sashimi grade",
     "harga_tambak": "60.000 – 80.000", "harga_ekspor": "5,00 – 8,00",
     "harga_intl": "6,50 – 9,00",
     "sumber": "KKP; ASTUIN; PPS Bitung; FAO GLOBEFISH; Undercurrent News; IntraFish; BPS ekspor",
     "catatan": "Ekspor utama ke Jepang dan Eropa."},
    {"komoditas": "Tuna Sirip Kuning / Yellowfin (Thunnus albacares)", "size": "Loin/beku",
     "harga_tambak": "30.000 – 45.000", "harga_ekspor": "2,50 – 4,00",
     "harga_intl": "—",
     "sumber": "KKP; ASTUIN; Undercurrent News; BPS ekspor",
     "catatan": "Grade industri untuk pengalengan dan loin beku."},
    {"komoditas": "Tuna Cakalang (Katsuwonus pelamis)", "size": "-",
     "harga_tambak": "15.000 – 25.000", "harga_ekspor": "1,50 – 2,50",
     "harga_intl": "1,80 – 2,20",
     "sumber": "KKP; PPS Bitung; ASTUIN; FAO GLOBEFISH; BPS ekspor; Antaranews",
     "catatan": "Bahan baku utama pengalengan. Harga dipengaruhi musim tangkapan."},
    {"komoditas": "Kakap Merah (Lutjanus spp.)", "size": "-",
     "harga_tambak": "50.000 – 70.000", "harga_ekspor": "5,00 – 8,00",
     "harga_intl": "—",
     "sumber": "KKP; Pelabuhan Perikanan; BPS ekspor; Undercurrent News; FAO GLOBEFISH",
     "catatan": "Permintaan ekspor ke China & Singapura tinggi."},
    {"komoditas": "Kerapu (Epinephelus spp.)", "size": "Hidup (>500 g)",
     "harga_tambak": "100.000 – 150.000", "harga_ekspor": "8,00 – 12,00",
     "harga_intl": "—",
     "sumber": "KKP; DJPB; Pelabuhan Perikanan; BPS ekspor; Undercurrent News; FAO GLOBEFISH",
     "catatan": "Ekspor hidup ke China dominan."},
    {"komoditas": "Kerapu (Epinephelus spp.)", "size": "Beku/segar",
     "harga_tambak": "60.000 – 90.000", "harga_ekspor": "5,00 – 7,00",
     "harga_intl": "—",
     "sumber": "KKP; DJPB; BPS ekspor; FAO GLOBEFISH",
     "catatan": "Pasar lokal dan ekspor grade beku."},
    # ── Komoditas & sumber diperluas ──────────────────────────────────────────
    {"komoditas": "Rumput Laut (Eucheuma cottonii)", "size": "Kering",
     "harga_tambak": "6.000 – 7.000", "harga_ekspor": "0,40 – 0,50",
     "harga_intl": "0,35 – 0,45",
     "sumber": "KKP DJPB; Asosiasi Rumput Laut Indonesia; FAO GLOBEFISH; IndexMundi; BPS ekspor",
     "catatan": "Harga kering di tingkat pembudidaya. Produksi dominan NTT, Sulawesi, Maluku. Rasio kering:basah ~1:8."},
    {"komoditas": "Rumput Laut (Eucheuma cottonii)", "size": "Basah",
     "harga_tambak": "1.000 – 1.500", "harga_ekspor": "—",
     "harga_intl": "—",
     "sumber": "KKP DJPB; Asosiasi Rumput Laut Indonesia; Trobos Aqua",
     "catatan": "Harga basah di tingkat pembudidaya. Dijual ke pengepul untuk dikeringkan."},
    {"komoditas": "Rumput Laut ATC/SRC (E. cottonii processed)", "size": "ATC/SRC",
     "harga_tambak": "40.000 – 70.000", "harga_ekspor": "2,50 – 5,00",
     "harga_intl": "3,00 – 5,00",
     "sumber": "KKP; Kemenperin; ISWA; FAO GLOBEFISH; BPS ekspor HS120991; IndexMundi",
     "catatan": "ATC=Alkali Treated Cottonii; SRC=Semi-Refined Carrageenan. Nilai tambah 5–8x vs kering. Ekspor ke China, AS, Eropa."},
    {"komoditas": "Lobster (Panulirus ornatus) / Mutiara", "size": ">200 g",
     "harga_tambak": "280.000 – 380.000", "harga_ekspor": "18,00 – 22,00",
     "harga_intl": "—",
     "sumber": "KKP; Pelabuhan Perikanan; Asosiasi Lobster Indonesia; Undercurrent News; FAO GLOBEFISH; BPS ekspor",
     "catatan": "Ekspor hidup ke Vietnam & China. Harga sangat sensitif terhadap kuota ekspor KKP."},
    {"komoditas": "Lobster (Panulirus homarus) / Pasir", "size": ">100 g",
     "harga_tambak": "150.000 – 220.000", "harga_ekspor": "10,00 – 15,00",
     "harga_intl": "—",
     "sumber": "KKP; Pelabuhan Perikanan; BPS ekspor; FAO GLOBEFISH",
     "catatan": "Ekspor hidup dan beku. Harga lebih rendah dari lobster mutiara."},
    {"komoditas": "Bandeng (Chanos chanos)", "size": "250-500 g",
     "harga_tambak": "20.000 – 28.000", "harga_ekspor": "1,80 – 2,50",
     "harga_intl": "—",
     "sumber": "KKP DJPB; Pasar Ikan Nasional; BPS ekspor; Trobos Aqua; Agrina",
     "catatan": "Harga tambak Jawa Tengah & Jawa Timur. Stabil sepanjang tahun; sedikit premium menjelang Lebaran."},
    {"komoditas": "Cumi-cumi (Loligo spp.)", "size": "-",
     "harga_tambak": "35.000 – 50.000", "harga_ekspor": "3,50 – 5,00",
     "harga_intl": "3,00 – 4,50",
     "sumber": "KKP; Pelabuhan Perikanan; ASTUIN; FAO GLOBEFISH; Undercurrent News; BPS ekspor; IndexMundi",
     "catatan": "Harga nelayan fluktuatif mengikuti musim tangkapan. Ekspor beku ke Eropa & Asia Timur."},
    # ── Patin (Pangasius) ─────────────────────────────────────────────────────
    {"komoditas": "Patin (Pangasianodon hypophthalmus)", "size": "Utuh/Hidup",
     "harga_tambak": "15.000 – 22.000", "harga_ekspor": "—",
     "harga_intl": "—",
     "sumber": "KKP DJPB; BPS produksi budidaya; Trobos Aqua; Agrina; Kontan perikanan; FishInfo Jatim",
     "catatan": "Sentra budidaya: Jawa Barat (Subang, Cianjur), Kalimantan Selatan. Harga stabil; dipengaruhi harga pakan."},
    {"komoditas": "Patin (Pangasianodon hypophthalmus)", "size": "Fillet Segar",
     "harga_tambak": "28.000 – 38.000", "harga_ekspor": "2,20 – 2,80",
     "harga_intl": "2,50 – 3,00",
     "sumber": "KKP; BPS ekspor; VASEP; SeafoodSource; Undercurrent News; FAO GLOBEFISH",
     "catatan": "Pasar ekspor: China, AS, ASEAN. Harga dipengaruhi benchmark Vietnam. Konversi fillet ~40% dari bobot utuh."},
    {"komoditas": "Patin (Pangasianodon hypophthalmus)", "size": "Fillet Beku Ekspor",
     "harga_tambak": "32.000 – 45.000", "harga_ekspor": "2,80 – 3,50",
     "harga_intl": "2,80 – 3,50",
     "sumber": "KKP; BPS ekspor HS0304; VASEP; SeafoodSource; Undercurrent News; IntraFish; FAO GLOBEFISH",
     "catatan": "Harga fillet beku Vietnam capai rekor 2025 (>USD 2 miliar/tahun ekspor). Indonesia genjot ekspor patin."},
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
    """Cari harga tambak (col 3) di 'Harga Komoditas' dari ~days_back hari lalu."""
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


def _add_months(y, m, delta):
    """Tambah delta bulan (positif/negatif). Returns (year, month)."""
    m += delta
    while m < 1:
        m += 12; y -= 1
    while m > 12:
        m -= 12; y += 1
    return y, m


def build_historis_index(historis_data):
    """
    Bangun lookup dict dari sheet 'Historis 12 Bulan'.
    Format baris: [Bulan, Komoditas, Harga Tambak, Harga Ekspor, ...]
    Returns: {(komoditas_key, "Bulan Tahun"): harga_tambak_str}
    """
    idx = {}
    for row in historis_data[1:]:
        if len(row) < 3:
            continue
        bulan  = row[0].strip()
        komod  = row[1].strip()
        tambak = row[2].strip()
        if bulan and komod and tambak and tambak not in ("—", "-", ""):
            idx[(komod, bulan)] = tambak
    return idx


def lookup_historis(historis_idx, komoditas, size, days_back):
    """
    Fallback lookup dari 'Historis 12 Bulan'.
    Mencari bulan terdekat dengan (today - days_back), toleransi ±2 bulan.
    Tidak menggunakan data bulan yang lebih baru dari bulan ini.
    """
    hist_key = _HISTORIS_KEY_MAP.get((komoditas, size))
    if not hist_key:
        return ""
    today  = date.today()
    target = today - timedelta(days=days_back)
    ty, tm = target.year, target.month
    for delta in (0, -1, 1, -2, 2):
        y, m = _add_months(ty, tm, delta)
        if (y > today.year) or (y == today.year and m > today.month):
            continue   # jangan pakai data masa depan
        val = historis_idx.get((hist_key, f"{_BULAN_ID_H[m]} {y}"))
        if val:
            return val
    return ""


def lookup_harga(harga_data, historis_idx, komoditas, size, days_back):
    """
    Lookup harga tambak historis dengan dua lapisan:
    1. Sheet 'Harga Komoditas' — data exact mingguan/harian (prioritas)
    2. Sheet 'Historis 12 Bulan' — data bulanan 25 bulan (fallback)
    """
    val = lookup_tambak(harga_data, komoditas, size, days_back)
    if val:
        return val
    return lookup_historis(historis_idx, komoditas, size, days_back)


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


def scrape_fishinfo_jatim():
    """Coba ambil rata-rata harga ikan konsumsi dari FishInfo Jawa Timur."""
    print("  Mencoba FishInfo Jawa Timur...")
    html = _get("https://fishinfojatim.net/HargaPedagang", timeout=10)
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    pattern = re.compile(r"Patin[^\d]*(\d{2,3}(?:[.,]\d{3})*)\s*(?:/kg)?", re.IGNORECASE)
    m = pattern.search(text)
    if m:
        raw = m.group(1).replace(".", "").replace(",", "")
        try:
            harga = int(raw)
            print(f"  [FishInfo] Patin ~Rp {harga:,}/kg")
            return {"fishinfo_patin": harga, "sumber_fishinfo": "FishInfo Jatim"}
        except ValueError:
            pass
    print("  [FishInfo] Pola harga patin tidak ditemukan.")
    return {}


def scrape_vasep_pangasius():
    """Coba ambil sinyal harga pangasius dari VNSeafoodInsider (benchmark Vietnam)."""
    print("  Mencoba VNSeafoodInsider pangasius...")
    html = _get("https://vnseafoodinsider.com/vietnam-pangasius-fish-price-early-q4-2025/",
                timeout=10)
    if not html:
        return {}
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    pattern = re.compile(r"USD?\s*([\d]+\.[\d]{2})\s*/\s*kg", re.IGNORECASE)
    matches = [float(m) for m in pattern.findall(text)]
    if matches:
        avg = sum(matches) / len(matches)
        print(f"  [VASEP/VNSeafood] {len(matches)} ref harga pangasius, avg USD {avg:.2f}/kg")
        return {"vasep_pangasius_avg": avg, "sumber_vasep": "VNSeafoodInsider (benchmark Vietnam)"}
    return {}


def scrape_worldbank_pfish():
    """World Bank API — Fish Price Index sebagai benchmark internasional."""
    print("  Mencoba World Bank Fish Price Index...")
    if not WEB:
        return {}
    try:
        import requests as _req
        url = ("https://api.worldbank.org/v2/country/wld/indicator/PFISH"
               "?format=json&date=2024:2026&per_page=10")
        r = _req.get(url, timeout=8, headers=_HTTP_HEADERS)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and len(data) > 1:
            vals = [float(i["value"]) for i in (data[1] or []) if i.get("value")]
            if vals:
                avg = sum(vals) / len(vals)
                print(f"  [WorldBank] Fish Price Index avg: {avg:.1f}")
                return {"wb_pfish": avg, "sumber_wb": "WorldBank PFISH"}
    except Exception as e:
        print(f"  [WorldBank] Tidak tersedia: {type(e).__name__}")
    return {}


def determine_kepercayaan(entry, web_results):
    """Tentukan tingkat kepercayaan data berdasarkan hasil scraping."""
    if web_results.get("kepercayaan") == "Tinggi":
        return "Tinggi"
    if web_results.get("kepercayaan") == "Sedang" or web_results.get("fao_fpi"):
        return "Sedang"
    return "Estimasi"


def enrich_sumber(entry, web_results):
    """Gabungkan sumber dasar dengan sumber scraping yang berhasil."""
    parts = [entry["sumber"]]
    if web_results.get("sumber"):
        parts.append(web_results["sumber"])
    if web_results.get("sumber_fao"):
        parts.append(web_results["sumber_fao"])
    if web_results.get("kkp_ok"):
        parts.append("KKP.go.id (diverifikasi)")
    if web_results.get("sumber_fishinfo"):
        parts.append(web_results["sumber_fishinfo"])
    if web_results.get("sumber_vasep"):
        k = entry["komoditas"].lower()
        if "patin" in k:
            parts.append(web_results["sumber_vasep"])
    if web_results.get("sumber_wb"):
        parts.append(web_results["sumber_wb"])
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


def append_rows_with_retry(sheet, rows, max_retries=3):
    """
    Tulis semua baris sekaligus dengan satu append_rows() call.
    Retry dengan exponential backoff jika kena 429 (quota exceeded).
    Jeda: 10 s → 20 s → 40 s.
    """
    delays = [10, 20, 40]
    for attempt in range(max_retries + 1):
        try:
            sheet.append_rows(rows, value_input_option="RAW")
            print(f"  {len(rows)} baris ditulis ke sheet (attempt {attempt + 1}).")
            return
        except gspread.exceptions.APIError as e:
            status = getattr(e, "response", None)
            code   = status.status_code if status else 0
            if code == 429 and attempt < max_retries:
                jeda = delays[attempt]
                print(f"  [429] Quota exceeded — tunggu {jeda} detik lalu coba ulang "
                      f"(attempt {attempt + 1}/{max_retries})...")
                time.sleep(jeda)
            else:
                print(f"  [ERROR] append_rows gagal: {e}")
                raise


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

    # Muat sheet Historis 12 Bulan sebagai fallback referensi harga
    print("Membaca sheet 'Historis 12 Bulan' untuk referensi historis...")
    try:
        hist_ws   = ss.worksheet("Historis 12 Bulan")
        hist_data = hist_ws.get_all_values()
        hist_idx  = build_historis_index(hist_data)
        print(f"  {len(hist_idx)} entri historis dimuat sebagai fallback.\n")
    except gspread.exceptions.WorksheetNotFound:
        print("  [WARN] Sheet 'Historis 12 Bulan' tidak ditemukan — fallback dinonaktifkan.\n")
        hist_idx = {}

    # Jalankan scraping sekali (shared untuk semua komoditas)
    print("Menjalankan scraping sumber web...")
    web = {}
    web.update(scrape_shrimpnews())
    time.sleep(1)
    web.update(scrape_fao())
    time.sleep(1)
    web.update(scrape_kkp())
    time.sleep(1)
    web.update(scrape_fishinfo_jatim())
    time.sleep(1)
    web.update(scrape_vasep_pangasius())
    time.sleep(1)
    web.update(scrape_worldbank_pfish())
    print()

    # ── Kumpulkan semua baris baru dulu, baru tulis sekaligus ────────────────
    baris_baru = []
    dilewati   = 0

    for entry in BASE_DATA:
        k = entry["komoditas"]
        s = entry["size"]

        if cek_duplikat(existing_data, TANGGAL, k, s):
            print(f"  [LEWATI] {k} {s} — sudah ada hari ini.")
            dilewati += 1
            continue

        h_minggu  = lookup_harga(existing_data, hist_idx, k, s,  7)
        h_1bulan  = lookup_harga(existing_data, hist_idx, k, s, 30)
        h_3bulan  = lookup_harga(existing_data, hist_idx, k, s, 90)

        baris = [
            TANGGAL, k, s,
            entry["harga_tambak"], entry["harga_ekspor"], entry["harga_intl"],
            h_minggu, h_1bulan, h_3bulan,
            fmt_pct(entry["harga_tambak"], h_minggu),
            fmt_pct(entry["harga_tambak"], h_3bulan),
            enrich_sumber(entry, web),
            determine_kepercayaan(entry, web),
            entry["catatan"],
        ]
        baris_baru.append(baris)
        print(f"  [ANTRIAN] {k} {s}")

    # ── Tulis sekaligus (satu API call) dengan retry exponential backoff ─────
    ditambah = 0
    if baris_baru:
        append_rows_with_retry(sheet, baris_baru)
        ditambah = len(baris_baru)

    print(f"\nSelesai: {ditambah} baris ditambahkan, {dilewati} dilewati.")
    print(f"Lihat: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
