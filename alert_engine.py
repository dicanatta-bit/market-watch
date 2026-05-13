"""
Market Watch - AJN
Alert engine: deteksi pergerakan harga signifikan & tulis ke sheet Alert Log.
Bisa dijalankan standalone: python alert_engine.py [SPREADSHEET_ID]
"""

import sys
import re
from datetime import date, datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
CREDENTIALS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ALERT_HEADERS = [
    "Tanggal", "Komoditas", "Jenis Alert",
    "Nilai Sebelumnya", "Nilai Sekarang", "% Perubahan", "Rekomendasi",
]

REKOMENDASI = {
    "MERAH_NAIK":  "Harga naik signifikan — pertimbangkan penjualan atau hedging segera.",
    "MERAH_TURUN": "Harga turun signifikan — tahan stok; evaluasi harga pokok produksi.",
    "KUNING":      "Gap ekspor-tambak tinggi — peluang AJN sebagai agregator; review margin distribusi.",
    "BIRU":        "Harga internasional turun tajam — waspadai risiko program ekspor; review kontrak berjalan.",
}

KURS_USD_IDR = 16_000  # estimasi kurs untuk konversi gap ekspor


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_mid(s, mode="IDR"):
    """
    Ekstrak nilai tengah dari string harga range.
    IDR: '60.000 – 65.000' -> 62500.0   (titik = ribuan)
    USD: '3,55 – 3,64'     -> 3.595     (koma  = desimal)
    """
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


# ── Lookup historis ───────────────────────────────────────────────────────────

def _lookup_col(sheet_data, komoditas, size, days_back, col_idx):
    """Cari nilai kolom col_idx untuk komoditas+size dari ~days_back hari lalu."""
    today  = date.today()
    target = today - timedelta(days=days_back)
    best_row, best_delta = None, None
    for row in sheet_data[1:]:
        if len(row) <= col_idx or row[1] != komoditas or row[2] != size:
            continue
        d = parse_date(row[0])
        if d is None or d >= today:
            continue
        delta = abs((d - target).days)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_row = row
    if best_row and best_delta is not None and best_delta <= days_back + 14:
        return best_row[col_idx]
    return None


def lookup_tambak_hist(sheet_data, komoditas, size, days_back):
    return _lookup_col(sheet_data, komoditas, size, days_back, 3)  # col 3 = Harga Tambak


def lookup_intl_hist(sheet_data, komoditas, size, days_back):
    return _lookup_col(sheet_data, komoditas, size, days_back, 5)  # col 5 = Harga Intl


# ── Aturan alert ──────────────────────────────────────────────────────────────

def run_alerts(baris_baru, sheet_data=None):
    """
    Jalankan semua aturan alert terhadap satu baris baru.
    baris_baru: list sesuai HEADERS update_harga.py (14 kolom).
    sheet_data: semua baris sheet untuk lookup historis intl.
    Returns: list of alert rows (masing-masing 7 kolom untuk Alert Log).
    """
    alerts = []

    if len(baris_baru) < 6:
        return alerts

    tanggal   = baris_baru[0]
    komoditas = baris_baru[1]
    size      = baris_baru[2]
    label     = f"{komoditas} ({size})" if size and size not in ("-", "") else komoditas

    tambak_now  = parse_mid(baris_baru[3], "IDR")
    ekspor_now  = parse_mid(baris_baru[4], "USD")
    intl_now    = parse_mid(baris_baru[5], "USD")

    # Harga minggu lalu ada di kolom 6 (jika sudah 14-kolom)
    tambak_lalu_str = baris_baru[6] if len(baris_baru) > 6 else ""
    tambak_lalu = parse_mid(tambak_lalu_str, "IDR")

    # Harga intl bulan lalu: cari dari sheet_data jika tersedia
    intl_bulan = None
    if sheet_data:
        raw = lookup_intl_hist(sheet_data, komoditas, size, 30)
        intl_bulan = parse_mid(raw, "USD")

    # ── Alert MERAH: tambak bergerak >5% dari minggu lalu ────────────────────
    if tambak_now is not None and tambak_lalu is not None and tambak_lalu > 0:
        pct = (tambak_now - tambak_lalu) / tambak_lalu * 100
        if abs(pct) > 5:
            jenis = "MERAH_NAIK" if pct > 0 else "MERAH_TURUN"
            alerts.append([
                tanggal, label,
                "[MERAH] Pergerakan harga tambak >5% dari minggu lalu",
                tambak_lalu_str, baris_baru[3],
                f"{pct:+.2f}%",
                REKOMENDASI[jenis],
            ])

    # ── Alert KUNING: gap ekspor vs tambak >40% ───────────────────────────────
    if tambak_now is not None and ekspor_now is not None and tambak_now > 0:
        ekspor_idr = ekspor_now * KURS_USD_IDR
        gap = (ekspor_idr - tambak_now) / tambak_now * 100
        if gap > 40:
            alerts.append([
                tanggal, label,
                "[KUNING] Gap ekspor vs tambak >40%",
                baris_baru[3],
                f"~Rp {ekspor_idr:,.0f}/kg (ekspor est.)",
                f"{gap:.1f}%",
                REKOMENDASI["KUNING"],
            ])

    # ── Alert BIRU: harga intl turun >10% dari bulan lalu ────────────────────
    if intl_now is not None and intl_bulan is not None and intl_bulan > 0:
        pct = (intl_now - intl_bulan) / intl_bulan * 100
        if pct < -10:
            alerts.append([
                tanggal, label,
                "[BIRU] Harga internasional turun >10% dari bulan lalu",
                f"USD {intl_bulan:.2f}/kg", baris_baru[5],
                f"{pct:+.2f}%",
                REKOMENDASI["BIRU"],
            ])

    return alerts


# ── Sheet Alert Log ───────────────────────────────────────────────────────────

def get_or_create_alert_sheet(spreadsheet):
    try:
        ws = spreadsheet.worksheet("Alert Log")
        existing = ws.get_all_values()
        if not existing:
            ws.append_row(ALERT_HEADERS, value_input_option="RAW")
            ws.format("A1:G1", {"textFormat": {"bold": True}})
        return ws
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="Alert Log", rows=500, cols=len(ALERT_HEADERS))
        ws.append_row(ALERT_HEADERS, value_input_option="RAW")
        ws.format("A1:G1", {"textFormat": {"bold": True}})
        print("Sheet 'Alert Log' dibuat baru.")
        return ws


def write_alerts(alert_sheet, alerts):
    for row in alerts:
        alert_sheet.append_row(row, value_input_option="RAW")
    return len(alerts)


def get_today_alerts(spreadsheet):
    """Baca semua alert hari ini dari Alert Log. Returns list of rows."""
    try:
        ws = spreadsheet.worksheet("Alert Log")
        rows = ws.get_all_values()
        today_str = date.today().strftime("%d/%m/%Y")
        return [r for r in rows[1:] if r and r[0] == today_str]
    except gspread.exceptions.WorksheetNotFound:
        return []


# ── Main (standalone) ─────────────────────────────────────────────────────────

def main():
    print("=== Market Watch AJN -- Cek Alert ===\n")

    spreadsheet_id = sys.argv[1] if len(sys.argv) > 1 else SPREADSHEET_ID

    creds  = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    ss     = client.open_by_key(spreadsheet_id)
    print(f"Spreadsheet '{ss.title}' dibuka.")

    # Baca sheet harga
    try:
        harga_ws  = ss.worksheet("Harga Komoditas")
        all_data  = harga_ws.get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        print("[WARN] Sheet 'Harga Komoditas' tidak ditemukan. Alert tidak dapat dijalankan.")
        return

    today_str  = date.today().strftime("%d/%m/%Y")
    today_rows = [r for r in all_data[1:] if r and r[0] == today_str]

    if not today_rows:
        print("Tidak ada data baru hari ini untuk dicek alert.")
        return

    alert_ws = get_or_create_alert_sheet(ss)
    existing = alert_ws.get_all_values()
    # Hindari duplikat: set (komoditas, jenis_alert) yang sudah ada hari ini
    existing_keys = {
        (r[1], r[2]) for r in existing[1:]
        if r and r[0] == today_str
    }

    total = 0
    for row in today_rows:
        new_alerts = run_alerts(row, all_data)
        new_alerts = [a for a in new_alerts if (a[1], a[2]) not in existing_keys]
        if new_alerts:
            n = write_alerts(alert_ws, new_alerts)
            total += n
            for a in new_alerts:
                print(f"  {a[2][:50]}")
                print(f"    Komoditas : {a[1]}")
                print(f"    Perubahan : {a[5]}")
                print(f"    Rekomendasi: {a[6]}\n")

    print(f"Total {total} alert baru ditulis ke 'Alert Log'.")


if __name__ == "__main__":
    main()
