"""
Market Watch - AJN
Generate sheet "Harga per Wilayah" dari "Harga Komoditas" × faktor wilayah.
Coba scrape harga regional dari KKP best-effort; jika gagal, gunakan estimasi.
Update setiap Senin bersamaan update harga nasional.
"""

import sys
import re
import time
from datetime import date
from google.oauth2.service_account import Credentials
import gspread

try:
    import requests
    from bs4 import BeautifulSoup
    WEB = True
except ImportError:
    WEB = False

SPREADSHEET_ID   = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
SHEET_SRC        = "Harga Komoditas"
SHEET_DST        = "Harga per Wilayah"
CREDENTIALS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS_WILAYAH = [
    "Tanggal", "Komoditas", "Size/Grade", "Wilayah",
    "Harga Tambak Estimasi (Rp/kg)", "Harga Ekspor Estimasi (USD/kg)",
    "Faktor", "Sumber", "Catatan",
]

# Faktor harga per wilayah relatif terhadap Jawa-Bali (basis nasional).
# Sumber: estimasi berbasis data KKP/BPS harga di tingkat nelayan/pembudidaya.
WILAYAH_FAKTOR = {
    "Jawa-Bali":  1.00,
    "Sumatera":   0.95,
    "Kalimantan": 0.92,
    "Sulawesi":   0.90,
    "NTT-NTB":    0.88,
    "Maluku":     0.85,
    "Papua":      0.85,
}

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MarketWatchAJN/1.0; +https://ajn.id)",
    "Accept-Language": "id-ID,id;q=0.9",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get(url, timeout=10):
    if not WEB:
        return None
    try:
        r = requests.get(url, headers=_HTTP_HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  [SCRAPING] {url}: {type(e).__name__}")
        return None


def _parse_range_idr(s):
    """Parse string harga IDR 'lo – hi' ke list float (periode = ribuan)."""
    if not s or str(s).strip() in ("", "—", "-"):
        return []
    s = re.sub(r"[Rp\s]", "", str(s).strip())
    s = s.replace(".", "").replace(",", ".")
    parts = re.split(r"\s*[–\-]\s*", s)
    try:
        return [float(p.strip()) for p in parts if p.strip()]
    except ValueError:
        return []


def _parse_range_usd(s):
    """Parse string harga USD 'lo – hi' ke list float (koma = desimal)."""
    if not s or str(s).strip() in ("", "—", "-"):
        return []
    s = str(s).strip().replace(".", "").replace(",", ".")
    parts = re.split(r"\s*[–\-]\s*", s)
    try:
        return [float(p.strip()) for p in parts if p.strip()]
    except ValueError:
        return []


def apply_faktor_idr(harga_str, faktor):
    """Terapkan faktor ke string harga IDR, pertahankan format range."""
    nums = _parse_range_idr(harga_str)
    if not nums:
        return "—"
    adjusted = sorted(n * faktor for n in nums)
    if len(adjusted) == 2:
        lo = f"{adjusted[0]:,.0f}".replace(",", ".")
        hi = f"{adjusted[1]:,.0f}".replace(",", ".")
        return f"{lo} – {hi}"
    return f"{adjusted[0]:,.0f}".replace(",", ".")


def apply_faktor_usd(harga_str, faktor):
    """Terapkan faktor ke string harga USD, pertahankan format range."""
    nums = _parse_range_usd(harga_str)
    if not nums:
        return "—"
    adjusted = sorted(n * faktor for n in nums)
    if len(adjusted) == 2:
        lo = f"{adjusted[0]:.2f}".replace(".", ",")
        hi = f"{adjusted[1]:.2f}".replace(".", ",")
        return f"{lo} – {hi}"
    return f"{adjusted[0]:.2f}".replace(".", ",")


# ── Scraping harga regional (best-effort) ─────────────────────────────────────

def scrape_kkp_portal():
    """
    Coba akses portaldata.kkp.go.id dan ambil sinyal harga per wilayah.
    Returns dict {wilayah: harga_ref_str} atau {}.
    """
    print("  Mencoba portaldata.kkp.go.id...")
    results = {}
    html = _get("https://portaldata.kkp.go.id/", timeout=14)
    if not html:
        print("  [KKP Portal] Tidak dapat diakses.")
        return results
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    # Best-effort: cari pola harga per wilayah di teks halaman
    for wilayah, kw in [
        ("Sulawesi",   r"sulawesi"),
        ("Sumatera",   r"sumatera"),
        ("Kalimantan", r"kalimantan"),
        ("Papua",      r"papua"),
        ("Maluku",     r"maluku"),
        ("NTT-NTB",    r"nusa\s+tenggara"),
    ]:
        pat = re.compile(
            rf"{kw}[^0-9]{{0,80}}(\d{{2,3}}(?:[.,]\d{{3}})+)\s*/\s*kg",
            re.IGNORECASE,
        )
        m = pat.search(text)
        if m:
            results[wilayah] = m.group(1)
            print(f"    [KKP] {wilayah}: {m.group(1)}/kg")
    if not results:
        print("  [KKP Portal] Pola harga regional tidak ditemukan.")
    return results


def scrape_bps_harga_nelayan():
    """
    Coba BPS API untuk harga nelayan per provinsi.
    Returns {} (best-effort, struktur data BPS API berubah-ubah).
    """
    print("  Mencoba BPS API harga nelayan...")
    html = _get(
        "https://www.bps.go.id/id/statistics-table/2/MTgxMyMy/harga-rata-rata-produsen-ikan-laut.html",
        timeout=12,
    )
    if html:
        print("  [BPS] Halaman diakses — data tabular membutuhkan scraping lanjutan.")
    else:
        print("  [BPS] Tidak dapat diakses.")
    return {}


# ── Logika utama ──────────────────────────────────────────────────────────────

def build_latest_nasional(harga_data):
    """
    Ambil baris terbaru per (komoditas, size) dari sheet 'Harga Komoditas'.
    Returns dict {(komoditas, size): row}
    """
    latest = {}
    for row in harga_data[1:]:
        if len(row) < 4:
            continue
        key = (row[1], row[2])
        if key not in latest:
            latest[key] = row
    return latest


def build_wilayah_rows(latest_nasional, kkp_regional):
    """
    Bangun semua baris untuk sheet 'Harga per Wilayah'.
    Urutan wilayah: Jawa-Bali → Sumatera → Kalimantan → Sulawesi → NTT-NTB → Maluku → Papua
    """
    tanggal  = date.today().strftime("%d/%m/%Y")
    baris_all = []

    for wilayah, faktor in WILAYAH_FAKTOR.items():
        catatan_faktor = f"Basis Jawa-Bali (1,00) × faktor {wilayah} ({faktor:.2f}) — KKP/BPS"
        if kkp_regional:
            sumber = "KKP Portal Data (regional); Estimasi faktor wilayah"
        else:
            sumber = "Estimasi — harga nasional × faktor wilayah KKP/BPS"

        for (komoditas, size), row in latest_nasional.items():
            h_tambak_nas = row[3] if len(row) > 3 else "—"
            h_ekspor_nas = row[4] if len(row) > 4 else "—"

            h_tambak_est = apply_faktor_idr(h_tambak_nas, faktor)
            h_ekspor_est = apply_faktor_usd(h_ekspor_nas, faktor)

            baris_all.append([
                tanggal, komoditas, size, wilayah,
                h_tambak_est, h_ekspor_est,
                faktor, sumber, catatan_faktor,
            ])

    return baris_all


# ── Sheet helpers ─────────────────────────────────────────────────────────────

def get_or_create_sheet(spreadsheet):
    try:
        ws       = spreadsheet.worksheet(SHEET_DST)
        existing = ws.get_all_values()
        if not existing:
            ws.append_row(HEADERS_WILAYAH, value_input_option="RAW")
            return ws, []
        if existing[0] != HEADERS_WILAYAH:
            ws.update("A1", [HEADERS_WILAYAH], value_input_option="RAW")
            print(f"  Header '{SHEET_DST}' diperbarui.")
        print(f"Sheet '{SHEET_DST}' ditemukan ({len(existing) - 1} baris data).")
        return ws, existing
    except gspread.exceptions.WorksheetNotFound:
        print(f"Sheet '{SHEET_DST}' tidak ada, membuat baru...")
        ws = spreadsheet.add_worksheet(
            title=SHEET_DST, rows=5000, cols=len(HEADERS_WILAYAH)
        )
        ws.append_row(HEADERS_WILAYAH, value_input_option="RAW")
        return ws, []


def delete_today_rows(spreadsheet, sheet, sheet_data, tanggal):
    sid     = sheet.id
    indices = [
        i + 1
        for i, row in enumerate(sheet_data[1:])
        if len(row) >= 1 and row[0] == tanggal
    ]
    if not indices:
        return 0
    indices.sort(reverse=True)
    reqs = [
        {"deleteDimension": {"range": {
            "sheetId": sid, "dimension": "ROWS",
            "startIndex": idx, "endIndex": idx + 1,
        }}}
        for idx in indices
    ]
    spreadsheet.batch_update({"requests": reqs})
    return len(indices)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    force          = "--force" in sys.argv
    spreadsheet_id = next(
        (a for a in sys.argv[1:] if not a.startswith("--")),
        SPREADSHEET_ID,
    )

    print("=== Market Watch AJN -- Generate Harga per Wilayah ===\n")

    creds  = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    ss     = client.open_by_key(spreadsheet_id)
    print(f"Spreadsheet '{ss.title}' dibuka.\n")

    # Baca sheet sumber
    print(f"Membaca sheet '{SHEET_SRC}'...")
    try:
        src_ws     = ss.worksheet(SHEET_SRC)
        harga_data = src_ws.get_all_values()
        print(f"  {len(harga_data) - 1} baris data dibaca.\n")
    except gspread.exceptions.WorksheetNotFound:
        print(f"[ERROR] Sheet '{SHEET_SRC}' tidak ditemukan. Jalankan update_harga.py dulu.")
        sys.exit(1)

    # Scraping harga regional (best-effort)
    print("Mencoba scraping harga regional...")
    kkp_regional = {}
    try:
        kkp_regional.update(scrape_kkp_portal())
        time.sleep(1)
        scrape_bps_harga_nelayan()
    except Exception as e:
        print(f"  [WARN] Scraping regional gagal: {e}")
    print()

    # Bangun data wilayah
    print("Menghitung harga per wilayah...")
    latest = build_latest_nasional(harga_data)
    baris_all = build_wilayah_rows(latest, kkp_regional)
    n_wilayah = len(WILAYAH_FAKTOR)
    n_komod   = len(latest)
    print(f"  {len(baris_all)} baris disiapkan "
          f"({n_wilayah} wilayah × {n_komod} komoditas).\n")

    # Tulis ke sheet
    tanggal      = date.today().strftime("%d/%m/%Y")
    dst_ws, existing = get_or_create_sheet(ss)

    today_exists = any(r[0] == tanggal for r in existing[1:] if r)
    if force or today_exists:
        print(f"[{'--force' if force else 'data sudah ada'}] "
              f"Menghapus data tanggal {tanggal}...")
        n_del = delete_today_rows(ss, dst_ws, existing, tanggal)
        if n_del:
            time.sleep(2)
            print(f"  {n_del} baris dihapus.\n")

    if baris_all:
        dst_ws.append_rows(baris_all, value_input_option="RAW")
        print(f"  {len(baris_all)} baris ditulis ke '{SHEET_DST}'.")

    print(f"\nSelesai.")
    print(f"Lihat: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
