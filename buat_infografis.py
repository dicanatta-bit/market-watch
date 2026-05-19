"""
Market Watch - AJN
Dashboard HTML interaktif + Google Sheet Infografis + Sheet formatting
"""

import sys
import io
import os
import re
import json
import html as _html
from datetime import date

# Pastikan UTF-8 di Windows agar karakter sheet (→, –, dll.) tidak error
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from google.oauth2.service_account import Credentials
import gspread
import alert_engine
import sheet_formatter

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
SHEET_NAME     = "Infografis"
CREDS_FILE     = "credentials.json"
SCOPES         = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
OUTPUT_DIR = "output"

_BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
_today       = date.today()
TANGGAL      = f"{_today.day} {_BULAN[_today.month]} {_today.year}"
TANGGAL_FILE = _today.strftime("%Y%m%d")

# ── Palette warna AJN ─────────────────────────────────────────────────────────
C_BIRU_TUA    = {"red": 0.02, "green": 0.27, "blue": 0.45}
C_BIRU_MUDA   = {"red": 0.06, "green": 0.49, "blue": 0.63}
C_HIJAU_TUA   = {"red": 0.08, "green": 0.37, "blue": 0.20}
C_MERAH_TUA   = {"red": 0.60, "green": 0.09, "blue": 0.09}
C_BIRU_PALE   = {"red": 0.88, "green": 0.95, "blue": 0.98}
C_HIJAU_PALE  = {"red": 0.87, "green": 0.96, "blue": 0.89}
C_ORANGE_PALE = {"red": 1.00, "green": 0.93, "blue": 0.82}
C_MERAH_PALE  = {"red": 1.00, "green": 0.87, "blue": 0.87}
C_KUNING_PALE = {"red": 1.00, "green": 0.97, "blue": 0.77}
C_KREM        = {"red": 1.00, "green": 0.97, "blue": 0.88}
C_PUTIH       = {"red": 1.00, "green": 1.00, "blue": 1.00}
C_ABU         = {"red": 0.40, "green": 0.40, "blue": 0.40}

MAX_ALERTS = 5

_BUDIDAYA_KEYS = ["Vaname", "Windu", "Nila", "Patin", "Rumput Laut", "Bandeng"]

STATIC_PRICES = [
    {"komoditas": "Udang Vaname",    "size": "Size 50",            "tambak": "60.000 – 65.000",   "ekspor": "3,55 – 3,64",  "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Vaname",    "size": "Size 60",            "tambak": "55.000 – 60.000",   "ekspor": "3,55",          "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Vaname",    "size": "Size 70",            "tambak": "50.000 – 55.000",   "ekspor": "—",             "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Vaname",    "size": "Size 100",           "tambak": "40.000 – 45.000",   "ekspor": "—",             "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Windu",     "size": "Size 20",            "tambak": "100.000 – 120.000", "ekspor": "8,00 – 10,00",  "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Windu",     "size": "Size 30",            "tambak": "80.000 – 100.000",  "ekspor": "6,00 – 8,00",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Nila",            "size": "300–500 g",          "tambak": "22.000 – 28.000",   "ekspor": "3,00 – 4,00",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Patin",           "size": "Utuh/Hidup",         "tambak": "15.000 – 22.000",   "ekspor": "—",             "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Bandeng",         "size": "250-500 g",          "tambak": "20.000 – 28.000",   "ekspor": "1,80 – 2,50",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Tuna Yellowfin",  "size": "Sashimi grade",      "tambak": "60.000 – 80.000",   "ekspor": "5,00 – 8,00",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Tuna Yellowfin",  "size": "Loin/beku",          "tambak": "30.000 – 45.000",   "ekspor": "2,50 – 4,00",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Tuna Cakalang",   "size": "—",                  "tambak": "15.000 – 25.000",   "ekspor": "1,50 – 2,50",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Kakap Merah",     "size": "—",                  "tambak": "50.000 – 70.000",   "ekspor": "5,00 – 8,00",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Kerapu",          "size": "Hidup (>500 g)",     "tambak": "100.000 – 150.000", "ekspor": "8,00 – 12,00",  "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Kerapu",          "size": "Beku/segar",         "tambak": "60.000 – 90.000",   "ekspor": "5,00 – 7,00",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Lobster Mutiara", "size": ">200 g",             "tambak": "280.000 – 380.000", "ekspor": "18,00 – 22,00", "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Lobster Pasir",   "size": ">100 g",             "tambak": "150.000 – 220.000", "ekspor": "10,00 – 15,00", "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Rumput Laut",     "size": "Kering",             "tambak": "6.000 – 7.000",     "ekspor": "0,40 – 0,50",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Cumi-cumi",       "size": "—",                  "tambak": "35.000 – 50.000",   "ekspor": "3,50 – 5,00",   "pct_minggu": "",  "pct_3bulan": "", "kepercayaan": "Estimasi"},
]


# ── Helper ────────────────────────────────────────────────────────────────────

def _parse_mid(s):
    if not s or str(s).strip() in ("", "—", "-"):
        return None
    s = str(s).replace(".", "").replace(",", ".").strip()
    parts = re.split(r"\s*[–\-]\s*", s)
    try:
        vals = [float(p.strip()) for p in parts if p.strip()]
        return sum(vals) / len(vals) if vals else None
    except ValueError:
        return None


def _parse_pct_float(s):
    if not s or str(s).strip() in ("", "—", "-"):
        return None
    s = re.sub(r"[%\s]", "", str(s)).replace(",", ".").replace("+", "")
    try:
        return float(s)
    except ValueError:
        return None


def _is_budidaya(komoditas):
    return any(k in komoditas for k in _BUDIDAYA_KEYS)


def _trend_icon(pct):
    if pct is None:
        return "→"
    if pct > 1:
        return "↑"
    if pct < -1:
        return "↓"
    return "→"


def _pct_badge_class(pct):
    if pct is None or pct == 0:
        return "badge-neutral"
    return "badge-up" if pct > 0 else "badge-dn"


def _pct_str(s):
    s = str(s).strip() if s else ""
    if not s or s in ("", "—", "-"):
        return "—"
    return s


# ── Sumber data mapping ───────────────────────────────────────────────────────

_SOURCE_URL = {
    "JALA Tech":            "https://jala.tech",
    "KKP DJPB":             "https://kkp.go.id/direktorat-jenderal/djpb",
    "KKP":                  "https://kkp.go.id",
    "DJPB":                 "https://kkp.go.id/direktorat-jenderal/djpb",
    "UCN":                  "https://www.undercurrentnews.com",
    "Undercurrent News":    "https://www.undercurrentnews.com",
    "SeafoodSource":        "https://www.seafoodsource.com",
    "ShrimpNews":           "https://www.shrimpnews.com",
    "FAO GLOBEFISH":        "https://www.fao.org/in-action/globefish/en/",
    "FAO":                  "https://www.fao.org",
    "BPS ekspor":           "https://www.bps.go.id",
    "BPS":                  "https://www.bps.go.id",
    "ASTUIN":               "https://astuin.or.id",
    "PPS Bitung":           "https://ppsbitung.kkp.go.id",
    "Pelabuhan Perikanan":  "https://kkp.go.id",
    "IndexMundi":           "https://www.indexmundi.com",
    "Trobos Aqua":          "https://aqua.trobos.com",
    "Agrina":               "https://www.agrina-online.com",
    "VASEP":                "https://vasep.com.vn",
    "IntraFish":            "https://www.intrafish.com",
    "Antaranews":           "https://www.antaranews.com",
    "Kontan":               "https://www.kontan.co.id",
    "Kemenperin":           "https://kemenperin.go.id",
}

_SOURCE_TRUST = {
    "KKP": "Tinggi", "BPS": "Tinggi", "FAO": "Tinggi",
    "DJPB": "Tinggi", "Kemenperin": "Tinggi",
    "JALA Tech": "Sedang", "Undercurrent News": "Sedang", "UCN": "Sedang",
    "IntraFish": "Sedang", "SeafoodSource": "Sedang", "ShrimpNews": "Sedang",
    "VASEP": "Sedang", "ASTUIN": "Sedang", "PPS": "Sedang",
    "Pelabuhan": "Sedang", "IndexMundi": "Sedang",
    "Trobos": "Estimasi", "Agrina": "Estimasi", "Kontan": "Estimasi",
    "Antaranews": "Estimasi", "Asosiasi": "Estimasi",
    "Pasar Ikan": "Estimasi", "FishInfo": "Estimasi", "ISWA": "Estimasi",
}


def _parse_sources(sumber_str):
    if not sumber_str or str(sumber_str).strip() in ("", "—", "-"):
        return [{"nama": "Estimasi internal", "url": "", "level": "Estimasi"}]
    parts = [s.strip() for s in str(sumber_str).split(";") if s.strip()]
    result = []
    for part in parts:
        url, level = "", "Sedang"
        for key, u in _SOURCE_URL.items():
            if key.lower() in part.lower():
                url = u
                break
        for key, lv in _SOURCE_TRUST.items():
            if key.lower() in part.lower():
                level = lv
                break
        result.append({"nama": part, "url": url, "level": level})
    return result


# ── Google Sheet data ─────────────────────────────────────────────────────────

def _parse_tanggal(s):
    """Parse tanggal DD/MM/YYYY ke objek date; kembalikan date.min jika gagal."""
    from datetime import datetime as _dt
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return _dt.strptime(str(s).strip(), fmt).date()
        except ValueError:
            continue
    return date.min


def _get_latest_prices(ss):
    """Baca harga terbaru per (komoditas, size) — deduplikasi berdasarkan kolom Tanggal."""
    try:
        ws   = ss.worksheet("Harga Komoditas")
        rows = ws.get_all_values()
        if len(rows) < 2:
            print("  Sheet kosong — pakai data statis.")
            return STATIC_PRICES

        # Kumpulkan semua baris; simpan hanya yang paling baru per key
        latest: dict = {}   # (komoditas, size) → (date, row)
        for row in rows[1:]:
            if len(row) < 5:
                continue
            key  = (row[1], row[2])
            tgl  = _parse_tanggal(row[0]) if len(row) > 0 else date.min
            prev = latest.get(key)
            if prev is None or tgl > prev[0]:
                latest[key] = (tgl, row)

        if not latest:
            return STATIC_PRICES

        result = []
        latest_date = date.min
        for (_k, _s), (_tgl, row) in latest.items():
            if _tgl > latest_date:
                latest_date = _tgl
            result.append({
                "komoditas":        row[1]  if len(row) > 1  else "—",
                "size":             row[2]  if len(row) > 2  else "—",
                "tambak":           row[3]  if len(row) > 3  else "—",
                "ekspor":           row[4]  if len(row) > 4  else "—",
                "intl":             row[5]  if len(row) > 5  else "—",
                "harga_minggu_lalu": row[6] if len(row) > 6  else "—",
                "harga_1bulan_lalu": row[7] if len(row) > 7  else "—",
                "harga_3bulan_lalu": row[8] if len(row) > 8  else "—",
                "pct_minggu":       row[9]  if len(row) > 9  else "",
                "pct_3bulan":       row[10] if len(row) > 10 else "",
                "sumber":           row[11] if len(row) > 11 else "",
                "kepercayaan":      row[12] if len(row) > 12 else "Estimasi",
                "catatan":          row[13] if len(row) > 13 else "",
            })
        print(f"  Deduplikasi: {len(rows) - 1} baris → {len(result)} komoditas/size unik")
        return result, latest_date
    except Exception as exc:
        print(f"  [WARN] Tidak bisa baca sheet: {exc} — pakai data statis")
        return STATIC_PRICES, date.min


def _get_historical_series(ss):
    """Baca semua baris historis; return {(komoditas,size): [{x,y},...]} maks 12 titik."""
    _BULAN_S = ["","Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]
    try:
        from collections import defaultdict
        ws   = ss.worksheet("Harga Komoditas")
        rows = ws.get_all_values()
        raw  = defaultdict(list)
        for row in rows[1:]:
            if len(row) < 4:
                continue
            komod  = row[1].strip() if len(row) > 1 else ""
            size   = row[2].strip() if len(row) > 2 else ""
            tambak = row[3].strip() if len(row) > 3 else ""
            tgl    = _parse_tanggal(row[0]) if row else date.min
            mid    = _parse_mid(tambak)
            if not komod or mid is None or tgl == date.min:
                continue
            raw[(komod, size)].append((tgl, int(mid)))
        result = {}
        for key, pts in raw.items():
            pts.sort(key=lambda x: x[0])
            pts = pts[-12:]
            result[key] = [
                {"x": f"{p[0].day} {_BULAN_S[p[0].month]} '{str(p[0].year)[2:]}", "y": p[1]}
                for p in pts
            ]
        print(f"  Historis: {len(result)} seri komoditas/size ditemukan")
        return result
    except Exception as exc:
        print(f"  [WARN] Gagal baca historis: {exc}")
        return {}


def _get_latest_alerts(ss):
    """Baca alert dari tanggal update terakhir di Alert Log (bukan hari ini)."""
    try:
        ws   = ss.worksheet("Alert Log")
        rows = ws.get_all_values()
        if len(rows) < 2:
            return []
        latest_date = date.min
        for row in rows[1:]:
            if row and row[0]:
                d = _parse_tanggal(row[0])
                if d != date.min and d > latest_date:
                    latest_date = d
        if latest_date == date.min:
            return []
        latest_str = latest_date.strftime("%d/%m/%Y")
        return [r for r in rows[1:] if r and r[0] == latest_str]
    except gspread.exceptions.WorksheetNotFound:
        return []
    except Exception as exc:
        print(f"  [WARN] Gagal baca Alert Log: {exc}")
        return []


# ── Google Sheet Infografis (tetap dipertahankan) ────────────────────────────

def rng(sid, r1, r2, c1, c2):
    return {"sheetId": sid,
            "startRowIndex": r1, "endRowIndex": r2,
            "startColumnIndex": c1, "endColumnIndex": c2}


def fmt(sid, r1, r2, c1, c2, bg=None, fg=None, bold=None, size=None,
        halign=None, valign=None, wrap=None):
    cell, flds = {}, []
    if bg is not None:
        cell["backgroundColor"] = bg; flds.append("backgroundColor")
    tf, tf_f = {}, []
    if bold is not None: tf["bold"]            = bold;  tf_f.append("bold")
    if size is not None: tf["fontSize"]        = size;  tf_f.append("fontSize")
    if fg   is not None: tf["foregroundColor"] = fg;    tf_f.append("foregroundColor")
    if tf:
        cell["textFormat"] = tf
        flds.append(f"textFormat({','.join(tf_f)})")
    if valign is not None: cell["verticalAlignment"]   = valign; flds.append("verticalAlignment")
    if halign is not None: cell["horizontalAlignment"] = halign; flds.append("horizontalAlignment")
    if wrap   is not None: cell["wrapStrategy"]        = wrap;   flds.append("wrapStrategy")
    if not flds:
        return None
    return {"repeatCell": {
        "range": rng(sid, r1, r2, c1, c2),
        "cell": {"userEnteredFormat": cell},
        "fields": "userEnteredFormat(" + ",".join(flds) + ")",
    }}


def merge(sid, r1, r2, c1, c2):
    return {"mergeCells": {"range": rng(sid, r1, r2, c1, c2), "mergeType": "MERGE_ALL"}}


def col_px(sid, c1, c2, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c1, "endIndex": c2},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}


def row_px(sid, r1, r2, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS", "startIndex": r1, "endIndex": r2},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}


def border_box(sid, r1, r2, c1, c2, color=None, style="SOLID"):
    color = color or C_ABU
    b = {"style": style, "colorStyle": {"rgbColor": color}}
    return {"updateBorders": {
        "range": rng(sid, r1, r2, c1, c2),
        "top": b, "bottom": b, "left": b, "right": b,
        "innerHorizontal": b, "innerVertical": b}}


def alert_bg(jenis):
    j = str(jenis).upper()
    if "MERAH" in j:   return C_MERAH_PALE
    if "KUNING" in j:  return C_KUNING_PALE
    if "BIRU" in j:    return C_BIRU_PALE
    return C_PUTIH


TOTAL_ROWS = 35
ALERT_START = 28
FOOTER_ROW  = 34


def build_data(today_alerts):
    alert_rows = []
    for a in today_alerts[:MAX_ALERTS]:
        jenis = a[2] if len(a) > 2 else ""
        alert_rows.append([jenis, a[1] if len(a) > 1 else "", a[5] if len(a) > 5 else "", a[6] if len(a) > 6 else "", "", ""])
    while len(alert_rows) < MAX_ALERTS:
        alert_rows.append(["—", "Tidak ada alert", "", "", "", ""])

    DATA = [
        ["PT AGRINAS JALADRI NUSANTARA (AJN)", "", "", "", "", ""],
        ["MARKET WATCH  |  HARGA KOMODITAS PERIKANAN STRATEGIS", "", "", "", "", ""],
        [f"Update: {TANGGAL}   |   Sumber: KKP · JALA Tech · UCN · ASTUIN · BPS · Pelabuhan Perikanan", "", "", "", "", ""],
        ["", "", "", "", "", ""],
        ["A.  KOMODITAS BUDIDAYA", "", "", "", "", ""],
        ["Komoditas", "Size / Grade", "Harga Tambak (Rp/kg)", "Harga Ekspor (USD/kg)", "Tren & Catatan", ""],
        ["Udang Vaname", "Size 50",  "60.000 – 65.000", "3,55 – 3,64", "Naik 1–3% vs bulan lalu.", ""],
        ["Udang Vaname", "Size 60",  "55.000 – 60.000", "3,55",        "Stabil. Global turun 5,6% YoY.", ""],
        ["Udang Vaname", "Size 70",  "50.000 – 55.000", "—",           "Stabil. Produksi meningkat Apr–Mei.", ""],
        ["Udang Vaname", "Size 100", "40.000 – 45.000", "—",           "Stabil. Estimasi gradasi harga.", ""],
        ["Udang Windu",  "Size 20",  "100.000 – 120.000", "8,00 – 10,00", "Premium vs vaname. Sulawesi & Kalimantan.", ""],
        ["Udang Windu",  "Size 30",  "80.000 – 100.000",  "6,00 – 8,00",  "Permintaan ekspor stabil.", ""],
        ["Nila",         "300–500 g","22.000 – 28.000",  "3,00 – 4,00",  "Ekspor fillet ke AS & Eropa.", ""],
        ["", "", "", "", "", ""],
        ["B.  KOMODITAS PERIKANAN TANGKAP", "", "", "", "", ""],
        ["Komoditas", "Grade / Bentuk", "Harga Nelayan (Rp/kg)", "Harga Ekspor (USD/kg)", "Tren & Catatan", ""],
        ["Tuna Yellowfin", "Sashimi grade", "60.000 – 80.000", "5,00 – 8,00",   "Ekspor ke Jepang & Eropa. Stabil.", ""],
        ["Tuna Yellowfin", "Loin / beku",   "30.000 – 45.000", "2,50 – 4,00",   "Grade industri pengalengan & loin beku.", ""],
        ["Tuna Cakalang",  "—",             "15.000 – 25.000", "1,50 – 2,50",   "Bahan baku pengalengan. Musiman.", ""],
        ["Kakap Merah",    "—",             "50.000 – 70.000", "5,00 – 8,00",   "Permintaan China & Singapura tinggi.", ""],
        ["Kerapu", "Hidup (>500 g)", "100.000 – 150.000", "8,00 – 12,00", "Ekspor hidup China dominan.", ""],
        ["Kerapu", "Beku / segar",   "60.000 – 90.000",   "5,00 – 7,00",  "Pasar lokal & ekspor grade beku.", ""],
        ["", "", "", "", "", ""],
        ["HIGHLIGHT PASAR", "", "", "", "", ""],
        ["Udang vaname global turun 5,6% YoY. Indonesia stabil vs China (-10%) dan Ekuador (-11%).",
         "", "Kerapu hidup: permintaan China kuat. Harga Rp 100–150 rb/kg — tertinggi semua komoditas.",
         "", "", ""],
        ["Tuna yellowfin sashimi stabil di USD 5–8/kg. Jepang & Eropa tetap jadi pasar ekspor utama.",
         "", "Produksi vaname meningkat Apr–Mei (size 60–70). Waspadai potensi tekanan harga.",
         "", "", ""],
        ["", "", "", "", "", ""],
        ["ALERT AKTIF", "", "", "", "", ""],
    ]

    DATA.extend(alert_rows)
    DATA.append(["", "", "", "", "", ""])
    DATA.append(["Dibuat otomatis oleh Market Watch AJN   |   Data bersifat indikatif, bukan harga resmi.",
                 "", "", "", "", ""])
    return DATA


def build_requests(sid, today_alerts):
    reqs = []
    for c, px in [(0, 160), (1, 130), (2, 155), (3, 145), (4, 230), (5, 14)]:
        reqs.append(col_px(sid, c, c + 1, px))
    reqs += [
        row_px(sid,  0,  1, 50), row_px(sid,  1,  2, 36), row_px(sid,  2,  3, 24),
        row_px(sid,  3,  4,  8), row_px(sid,  4,  5, 30), row_px(sid,  5,  6, 26),
        row_px(sid,  6, 13, 24), row_px(sid, 13, 14,  8), row_px(sid, 14, 15, 30),
        row_px(sid, 15, 16, 26), row_px(sid, 16, 22, 24), row_px(sid, 22, 23,  8),
        row_px(sid, 23, 24, 28), row_px(sid, 24, 26, 50), row_px(sid, 26, 27,  8),
        row_px(sid, 27, 28, 28), row_px(sid, 28, 33, 26), row_px(sid, 33, 34,  8),
        row_px(sid, 34, 35, 22),
    ]
    reqs += [
        merge(sid,  0,  1, 0, 6), merge(sid,  1,  2, 0, 6), merge(sid,  2,  3, 0, 6),
        merge(sid,  4,  5, 0, 6), merge(sid, 14, 15, 0, 6), merge(sid, 23, 24, 0, 6),
        merge(sid, 24, 25, 0, 2), merge(sid, 24, 25, 2, 6), merge(sid, 25, 26, 0, 2),
        merge(sid, 25, 26, 2, 6), merge(sid, 27, 28, 0, 6), merge(sid, 33, 34, 0, 6),
        merge(sid, 34, 35, 0, 6),
    ]
    for r in range(28, 33):
        reqs.append(merge(sid, r, r + 1, 1, 4))
        reqs.append(merge(sid, r, r + 1, 4, 6))
    reqs.append(fmt(sid, 0, 1, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True, size=14, halign="CENTER", valign="MIDDLE"))
    reqs.append(fmt(sid, 1, 2, 0, 6, bg=C_BIRU_MUDA, fg=C_PUTIH, bold=True, size=12, halign="CENTER", valign="MIDDLE"))
    reqs.append(fmt(sid, 2, 3, 0, 6, bg=C_KREM, size=9, halign="CENTER", valign="MIDDLE"))
    reqs.append(fmt(sid, 4, 5, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True, size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid, 5, 6, 0, 5, bg=C_BIRU_MUDA, fg=C_PUTIH, bold=True, size=10, halign="CENTER", valign="MIDDLE"))
    for i in range(7):
        r  = 6 + i
        bg = C_BIRU_PALE if i % 2 == 0 else C_PUTIH
        reqs.append(fmt(sid, r, r + 1, 0, 5, bg=bg, size=10, valign="MIDDLE"))
        reqs.append(fmt(sid, r, r + 1, 0, 1, bold=True))
        reqs.append(fmt(sid, r, r + 1, 1, 4, halign="CENTER"))
        reqs.append(fmt(sid, r, r + 1, 4, 5, wrap="WRAP", size=9))
    reqs.append(fmt(sid, 14, 15, 0, 6, bg=C_HIJAU_TUA, fg=C_PUTIH, bold=True, size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid, 15, 16, 0, 5, bg=C_BIRU_MUDA, fg=C_PUTIH, bold=True, size=10, halign="CENTER", valign="MIDDLE"))
    for i in range(6):
        r  = 16 + i
        bg = C_ORANGE_PALE if i % 2 == 0 else C_PUTIH
        reqs.append(fmt(sid, r, r + 1, 0, 5, bg=bg, size=10, valign="MIDDLE"))
        reqs.append(fmt(sid, r, r + 1, 0, 1, bold=True))
        reqs.append(fmt(sid, r, r + 1, 1, 4, halign="CENTER"))
        reqs.append(fmt(sid, r, r + 1, 4, 5, wrap="WRAP", size=9))
    reqs.append(fmt(sid, 23, 24, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True, size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid, 24, 26, 0, 2, bg=C_KREM, size=10, valign="MIDDLE", wrap="WRAP"))
    reqs.append(fmt(sid, 24, 26, 2, 6, bg=C_HIJAU_PALE, size=10, valign="MIDDLE", wrap="WRAP"))
    reqs.append(fmt(sid, 27, 28, 0, 6, bg=C_MERAH_TUA, fg=C_PUTIH, bold=True, size=11, halign="LEFT", valign="MIDDLE"))
    for i, a in enumerate(today_alerts[:MAX_ALERTS]):
        r     = 28 + i
        jenis = a[2] if len(a) > 2 else ""
        bg    = alert_bg(jenis)
        reqs.append(fmt(sid, r, r + 1, 0, 6, bg=bg, size=9, valign="MIDDLE"))
        reqs.append(fmt(sid, r, r + 1, 0, 1, bold=True))
        reqs.append(fmt(sid, r, r + 1, 4, 6, wrap="WRAP"))
    for i in range(len(today_alerts), MAX_ALERTS):
        r = 28 + i
        reqs.append(fmt(sid, r, r + 1, 0, 6, bg=C_PUTIH, size=9, fg={"red": 0.6, "green": 0.6, "blue": 0.6}))
    reqs.append(fmt(sid, 34, 35, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, size=9, halign="CENTER", valign="MIDDLE"))
    reqs.append(border_box(sid,  5, 13, 0, 5))
    reqs.append(border_box(sid, 15, 22, 0, 5))
    reqs.append(border_box(sid, 27, 33, 0, 6))
    return reqs


# ── HTML Dashboard ────────────────────────────────────────────────────────────

def generate_html(prices, alerts, out_path, hist_series=None, tanggal_data=None):
    data = prices if prices else STATIC_PRICES
    if hist_series is None:
        hist_series = {}
    TGL = tanggal_data if tanggal_data else TANGGAL

    budidaya = [p for p in data if _is_budidaya(p["komoditas"])]
    tangkap  = [p for p in data if not _is_budidaya(p["komoditas"])]

    # Summary stats
    naik = sum(1 for p in data if (_parse_pct_float(p.get("pct_minggu", "")) or 0) > 0)
    turun = sum(1 for p in data if (_parse_pct_float(p.get("pct_minggu", "")) or 0) < 0)

    # Popup payloads untuk summary cards (SC_DATA)
    _mk = lambda p: {"nama": p["komoditas"], "size": p["size"],
                     "tambak": p.get("tambak","—"), "kepercayaan": p.get("kepercayaan","Estimasi")}
    _mn = lambda p: {"nama": p["komoditas"], "size": p["size"],
                     "tambak": p.get("tambak","—"), "pct": _pct_str(p.get("pct_minggu",""))}
    naik_list  = sorted([_mn(p) for p in data if (_parse_pct_float(p.get("pct_minggu","")) or 0) > 0],
                        key=lambda x: _parse_pct_float(x["pct"]) or 0, reverse=True)
    turun_list = sorted([_mn(p) for p in data if (_parse_pct_float(p.get("pct_minggu","")) or 0) < 0],
                        key=lambda x: _parse_pct_float(x["pct"]) or 0)
    budi_list  = [_mk(p) for p in budidaya]
    tang_list  = [_mk(p) for p in tangkap]
    alert_popup = [{"jenis": a.get("jenis",""), "komoditas": a.get("komoditas",""),
                    "pct": a.get("pct",""), "sebelum": a.get("sebelum",""),
                    "sekarang": a.get("sekarang",""), "rekomendasi": a.get("rekomendasi","")}
                   for a in alerts]
    sc_data = {
        "_tgl": TGL,
        "total": {"budidaya": budi_list, "tangkap": tang_list},
        "alert": alert_popup,
        "naik":  naik_list,
        "turun": turun_list,
        "budi":  budi_list,
        "tang":  tang_list,
    }
    sc_data_js = json.dumps(sc_data, ensure_ascii=False)

    # Chart bar: harga tambak semua komoditas
    chart_items = []
    for p in data:
        mid = _parse_mid(p["tambak"])
        if mid is None:
            continue
        nm  = p["komoditas"].split("(")[0].strip()
        sz  = p["size"]
        lbl = f"{nm} {sz}" if sz not in ("-", "—", "") else nm
        cat = "b" if _is_budidaya(p["komoditas"]) else "t"
        chart_items.append((lbl, int(mid), cat))
    chart_items.sort(key=lambda x: x[1], reverse=True)

    bar_labels = json.dumps([x[0] for x in chart_items])
    bar_values = json.dumps([x[1] for x in chart_items])
    bar_colors = json.dumps([
        "rgba(27,58,107,0.85)" if c == "b" else "rgba(20,90,48,0.85)"
        for _, _, c in chart_items
    ])

    # Top 5 komoditas by harga tambak untuk line chart tren
    top5 = [lbl for lbl, _, _ in chart_items[:5]]
    top5_labels_js = json.dumps(["3 Bln Lalu", "1 Bln Lalu", "Minggu Lalu", "Sekarang"])
    line_datasets = []
    palette = ["#1B3A6B", "#C9A84C", "#145A30", "#8B1A1A", "#065072"]
    for idx, p in enumerate([x for x in data if x["komoditas"].split("(")[0].strip() + " " + x["size"] in top5 or x["komoditas"].split("(")[0].strip() in top5][:5]):
        mid_now    = _parse_mid(p["tambak"]) or 0
        # Estimasi historis dari pct jika tidak ada data
        pct_w = _parse_pct_float(p.get("pct_minggu", "")) or 0
        pct_3 = _parse_pct_float(p.get("pct_3bulan", "")) or 0
        mid_w = round(mid_now / (1 + pct_w / 100)) if pct_w else mid_now
        mid_3 = round(mid_now / (1 + pct_3 / 100)) if pct_3 else mid_now
        nm  = p["komoditas"].split("(")[0].strip()
        sz  = p["size"]
        lbl = f"{nm} {sz}" if sz not in ("-", "—", "") else nm
        color = palette[idx % len(palette)]
        line_datasets.append({
            "label": lbl,
            "data": [mid_3, mid_3, mid_w, int(mid_now)],
            "borderColor": color,
            "backgroundColor": color + "22",
            "tension": 0.3,
            "fill": False,
        })
    line_datasets_js = json.dumps(line_datasets)

    # ── Commodity cards ───────────────────────────────────────────────────────
    def commodity_cards(lst, cat_class):
        cards = []
        for p in lst:
            pct_w   = _parse_pct_float(p.get("pct_minggu", ""))
            pct_3   = _parse_pct_float(p.get("pct_3bulan", ""))
            trend   = _trend_icon(pct_w)
            bcls_w  = _pct_badge_class(pct_w)
            bcls_3  = _pct_badge_class(pct_3)
            pct_w_s = _pct_str(p.get("pct_minggu", ""))
            pct_3_s = _pct_str(p.get("pct_3bulan", ""))
            trend_cls = "trend-up" if trend == "↑" else ("trend-dn" if trend == "↓" else "trend-flat")
            cat_label = "Budidaya" if _is_budidaya(p["komoditas"]) else "Tangkap"
            cat_badge = "cat-b" if _is_budidaya(p["komoditas"]) else "cat-t"
            kep       = p.get("kepercayaan", "Estimasi")
            kep_cls   = f"kep-{kep.lower()}"

            # Hitung % vs 1 bulan
            mid_now = _parse_mid(p.get("tambak", ""))
            mid_bl  = _parse_mid(p.get("harga_1bulan_lalu", ""))
            if mid_now and mid_bl and mid_bl != 0:
                v = (mid_now - mid_bl) / mid_bl * 100
                pct_1bulan_s = f"+{v:.1f}%" if v > 0 else f"{v:.1f}%"
            else:
                pct_1bulan_s = "—"

            # Tren historis (fallback 3-titik jika tak ada data)
            tren_pts = hist_series.get((p["komoditas"], p["size"]), [])
            if len(tren_pts) < 2 and mid_now:
                pw = _parse_pct_float(p.get("pct_minggu", "")) or 0
                p3 = _parse_pct_float(p.get("pct_3bulan", "")) or 0
                m3 = round(mid_now / (1 + p3 / 100)) if p3 else mid_now
                mw = round(mid_now / (1 + pw / 100)) if pw else mid_now
                tren_pts = [
                    {"x": "3 Bln Lalu", "y": int(m3)},
                    {"x": "Minggu Lalu", "y": int(mw)},
                    {"x": "Sekarang",    "y": int(mid_now)},
                ]

            # Modal JSON payload
            modal_data = {
                "nama":             p["komoditas"],
                "size":             p["size"],
                "kategori":         cat_label,
                "tambak":           p.get("tambak", "—"),
                "ekspor":           p.get("ekspor", "—"),
                "intl":             p.get("intl", "—"),
                "minggu_lalu":      p.get("harga_minggu_lalu", "—"),
                "bulan_lalu":       p.get("harga_1bulan_lalu", "—"),
                "tiga_bulan_lalu":  p.get("harga_3bulan_lalu", "—"),
                "pct_minggu":       pct_w_s,
                "pct_1bulan":       pct_1bulan_s,
                "pct_3bulan":       pct_3_s,
                "kepercayaan":      kep,
                "sumber":           _parse_sources(p.get("sumber", "")),
                "catatan":          p.get("catatan", ""),
                "tren":             tren_pts,
                "tanggal":          TGL,
            }
            modal_json = _html.escape(json.dumps(modal_data, ensure_ascii=False))
            is_b = 'b' if _is_budidaya(p['komoditas']) else 't'

            cards.append(f"""
      <div class="komod-card {cat_class}" data-cat="{is_b}" data-modal="{modal_json}" onclick="openModal(this)" role="button" tabindex="0">
        <div class="kcard-top">
          <span class="cat-badge {cat_badge}">{cat_label}</span>
          <span class="trend-icon {trend_cls}">{trend}</span>
        </div>
        <div class="kcard-name">{p['komoditas']}</div>
        <div class="kcard-size">{p['size']}</div>
        <div class="kcard-harga">Rp {p['tambak']}<span class="kcard-unit">/kg</span></div>
        <div class="kcard-ekspor">Ekspor: USD {p['ekspor']}/kg</div>
        <div class="kcard-badges">
          <span class="pct-badge {bcls_w}" title="% vs Minggu Lalu">W: {pct_w_s}</span>
          <span class="pct-badge {bcls_3}" title="% vs 3 Bulan Lalu">3M: {pct_3_s}</span>
          <span class="kep-badge {kep_cls}">{kep}</span>
        </div>
        <div class="kcard-hint">&#9432; klik untuk detail</div>
      </div>""")
        return "\n".join(cards)

    # ── Alert table rows ──────────────────────────────────────────────────────
    def alert_rows_html(lst):
        if not lst:
            return '<tr><td colspan="5" class="c muted">Tidak ada alert aktif hari ini.</td></tr>'
        rows = []
        for a in lst:
            j = str(a.get("jenis", "")).upper()
            if "MERAH" in j:
                rcls, bcls, btxt = "row-merah", "badge-merah", "MERAH"
            elif "KUNING" in j:
                rcls, bcls, btxt = "row-kuning", "badge-kuning", "KUNING"
            elif "BIRU" in j:
                rcls, bcls, btxt = "row-biru", "badge-biru", "BIRU"
            else:
                rcls, bcls, btxt = "", "badge-grey", "INFO"
            rows.append(
                f'<tr class="{rcls}">'
                f'<td><span class="badge {bcls}">{btxt}</span></td>'
                f'<td>{a.get("komoditas","")}</td>'
                f'<td class="c b">{a.get("pct","")}</td>'
                f'<td>{a.get("sebelum","")} &rarr; {a.get("sekarang","")}</td>'
                f'<td class="sm">{a.get("rekomendasi","")}</td>'
                f'</tr>'
            )
        return "\n".join(rows)

    # ── Render HTML ───────────────────────────────────────────────────────────
    all_cards    = commodity_cards(data, "")
    budidaya_cards = commodity_cards(budidaya, "")
    tangkap_cards  = commodity_cards(tangkap, "")

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market Watch AJN &mdash; {TGL}</title>
<style>
/* ── Reset & Base ── */
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#eef2f7;color:#1a1a1a;font-size:14px;min-height:100vh}}

/* ── Header ── */
.hdr{{background:linear-gradient(135deg,#1B3A6B 0%,#0d2244 100%);color:#fff;padding:0}}
.hdr-inner{{max-width:1200px;margin:0 auto;padding:18px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
.hdr-brand{{display:flex;flex-direction:column;gap:4px}}
.hdr-logo{{font-size:1.5rem;font-weight:800;letter-spacing:.5px;color:#C9A84C}}
.hdr-sub{{font-size:.75rem;opacity:.85;color:#cbd5e1}}
.hdr-meta{{text-align:right}}
.hdr-date{{font-size:.8rem;background:rgba(201,168,76,.2);border:1px solid rgba(201,168,76,.4);color:#C9A84C;padding:5px 12px;border-radius:20px;white-space:nowrap}}


/* ── Wrap ── */
.wrap{{max-width:1200px;margin:0 auto;padding:20px 14px}}

/* ── Summary Cards ── */
.summary-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:20px}}
.sum-card{{background:#fff;border-radius:10px;padding:16px 20px;box-shadow:0 1px 6px rgba(0,0,0,.09);border-left:4px solid #1B3A6B;display:flex;flex-direction:column;gap:4px}}
.sum-card.gold{{border-left-color:#C9A84C}}
.sum-card.green{{border-left-color:#1E7E34}}
.sum-card.red{{border-left-color:#721C24}}
.sum-num{{font-size:2rem;font-weight:800;color:#1B3A6B;line-height:1}}
.sum-card.gold .sum-num{{color:#C9A84C}}
.sum-card.green .sum-num{{color:#1E7E34}}
.sum-card.red .sum-num{{color:#721C24}}
.sum-lbl{{font-size:.78rem;color:#666;font-weight:500}}
.sum-hint{{font-size:.6rem;color:#ccc;margin-top:4px;letter-spacing:.2px}}
.sc-click{{cursor:pointer;transition:transform .15s,box-shadow .15s}}
.sc-click:hover{{transform:translateY(-2px);box-shadow:0 4px 16px rgba(0,0,0,.14)}}
.sc-click:focus-visible{{outline:2px solid #C9A84C;outline-offset:2px}}

/* ── Section Title ── */
.sec-title{{font-size:.92rem;font-weight:700;color:#1B3A6B;margin-bottom:12px;padding-bottom:6px;border-bottom:2px solid #C9A84C;display:flex;align-items:center;gap:8px}}
.sec-title .dot{{width:8px;height:8px;border-radius:50%;background:#C9A84C;flex-shrink:0}}

/* ── Filter Buttons ── */
.filter-bar{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}}
.filter-btn{{padding:6px 16px;border-radius:20px;border:2px solid #1B3A6B;background:#fff;color:#1B3A6B;font-size:.8rem;font-weight:600;cursor:pointer;transition:all .18s}}
.filter-btn:hover,.filter-btn.active{{background:#1B3A6B;color:#fff}}
.filter-btn.active-gold{{background:#C9A84C;color:#fff;border-color:#C9A84C}}

/* ── Commodity Cards Grid ── */
.komod-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}}
@media(max-width:900px){{.komod-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:580px){{.komod-grid{{grid-template-columns:1fr}}}}

.komod-card{{background:#fff;border-radius:10px;padding:14px 16px;box-shadow:0 1px 5px rgba(0,0,0,.09);border-top:3px solid #1B3A6B;display:flex;flex-direction:column;gap:5px;transition:transform .18s,box-shadow .18s;cursor:pointer}}
.komod-card:hover{{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.16)}}
.komod-card:focus-visible{{outline:2px solid #C9A84C;outline-offset:2px}}
.komod-card[data-cat="t"]{{border-top-color:#145A30}}
.komod-card.hidden{{display:none}}
.kcard-hint{{font-size:.6rem;color:#bbb;text-align:right;margin-top:auto;padding-top:6px;letter-spacing:.3px}}

.kcard-top{{display:flex;justify-content:space-between;align-items:center}}
.cat-badge{{font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px}}
.cat-b{{background:#dbeafe;color:#1e3a8a}}
.cat-t{{background:#dcfce7;color:#14532d}}
.trend-icon{{font-size:1.3rem;font-weight:800;line-height:1}}
.trend-up{{color:#1E7E34}}.trend-dn{{color:#721C24}}.trend-flat{{color:#6C757D}}

.kcard-name{{font-size:.88rem;font-weight:700;color:#1B3A6B;margin-top:2px}}
.kcard-size{{font-size:.75rem;color:#888}}
.kcard-harga{{font-size:1.25rem;font-weight:800;color:#1a1a1a;margin-top:4px}}
.kcard-unit{{font-size:.7rem;font-weight:400;color:#888}}
.kcard-ekspor{{font-size:.75rem;color:#555}}
.kcard-badges{{display:flex;gap:5px;flex-wrap:wrap;margin-top:5px}}

.pct-badge{{font-size:.68rem;font-weight:700;padding:2px 7px;border-radius:8px}}
.badge-up{{background:#D4EDDA;color:#1E7E34}}
.badge-dn{{background:#F8D7DA;color:#721C24}}
.badge-neutral{{background:#f0f0f0;color:#6C757D}}
.kep-badge{{font-size:.65rem;padding:2px 6px;border-radius:8px;background:#f0f0f0;color:#555}}
.kep-tinggi{{background:#d1fae5;color:#065f46}}
.kep-sedang{{background:#fef3c7;color:#92400e}}
.kep-estimasi{{background:#f3f4f6;color:#6b7280}}

/* ── Card Sections ── */
.card-section{{background:#fff;border-radius:10px;box-shadow:0 1px 5px rgba(0,0,0,.09);margin-bottom:20px;overflow:hidden}}
.ch{{padding:10px 16px;font-weight:700;font-size:.87rem;color:#fff;display:flex;align-items:center;gap:8px}}
.ch-navy{{background:#1B3A6B}}.ch-green{{background:#145A30}}.ch-red{{background:#8B1A1A}}

/* ── Alert Table ── */
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{background:#1B3A6B;color:#fff;padding:8px 10px;text-align:left;font-weight:600;white-space:nowrap}}
td{{padding:7px 10px;border-bottom:1px solid #eee;vertical-align:middle}}
tr:hover td{{filter:brightness(.97)}}
.c{{text-align:center}}.b{{font-weight:600}}.sm{{font-size:.76rem;color:#555}}.muted{{color:#aaa}}

.row-merah td{{background:#fde8e8}}.row-kuning td{{background:#fef9df}}.row-biru td{{background:#e6f2fd}}
.badge{{display:inline-block;padding:2px 9px;border-radius:10px;font-size:.7rem;font-weight:700}}
.badge-merah{{background:#fde8e8;color:#721C24}}.badge-kuning{{background:#fef9df;color:#9a7d0a}}
.badge-biru{{background:#e6f2fd;color:#1a5276}}.badge-grey{{background:#eee;color:#555}}

/* ── Charts ── */
.chart-wrap{{padding:16px;position:relative}}
.chart-box{{height:380px;position:relative}}
.chart-box-lg{{height:280px;position:relative}}

/* ── Footer ── */
.ftr{{text-align:center;font-size:.72rem;color:#aaa;padding:16px 0 28px}}

/* ── Modal ── */
.modal-ov{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.58);z-index:9000;align-items:center;justify-content:center;padding:16px}}
.modal-ov.active{{display:flex;animation:mFade .18s ease}}
@keyframes mFade{{from{{opacity:0}}to{{opacity:1}}}}
.modal-card{{background:#fff;border-radius:14px;max-width:600px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 24px 70px rgba(0,0,0,.35);animation:mSlide .2s ease;display:flex;flex-direction:column}}
@keyframes mSlide{{from{{transform:translateY(18px);opacity:0}}to{{transform:none;opacity:1}}}}

.m-hdr{{background:#1B3A6B;color:#fff;padding:16px 20px;border-radius:14px 14px 0 0;display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-shrink:0}}
.m-hdr-left{{display:flex;flex-direction:column;gap:4px}}
.m-nama{{font-size:1.05rem;font-weight:800;line-height:1.25}}
.m-size{{font-size:.78rem;opacity:.75}}
.m-kat{{display:inline-block;font-size:.63rem;font-weight:700;padding:2px 9px;border-radius:10px;margin-top:4px;width:fit-content}}
.m-kat.cat-b{{background:#dbeafe;color:#1e3a8a}}
.m-kat.cat-t{{background:#dcfce7;color:#14532d}}
.m-close{{background:rgba(255,255,255,.18);border:none;color:#fff;font-size:1rem;cursor:pointer;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s;line-height:1}}
.m-close:hover{{background:rgba(255,255,255,.32)}}

.m-body{{padding:18px 20px;overflow-y:auto;flex:1}}
.m-sec{{margin-bottom:18px}}
.m-sec-ttl{{font-size:.72rem;font-weight:700;color:#1B3A6B;text-transform:uppercase;letter-spacing:.6px;border-bottom:1px solid #e5e7eb;padding-bottom:5px;margin-bottom:11px}}

.m-harga-big{{font-size:1.9rem;font-weight:800;color:#1a1a1a;line-height:1}}
.m-harga-big span{{font-size:.78rem;font-weight:400;color:#888}}
.m-harga-sub{{display:flex;gap:18px;margin-top:8px;margin-bottom:12px;flex-wrap:wrap}}
.m-harga-sub-item{{font-size:.79rem;color:#555}}
.m-harga-sub-item strong{{color:#1B3A6B}}

.m-tbl{{width:100%;border-collapse:collapse;font-size:.79rem}}
.m-tbl th{{background:#f8fafc;padding:6px 10px;text-align:left;font-weight:600;color:#555;border-bottom:2px solid #e5e7eb}}
.m-tbl td{{padding:6px 10px;border-bottom:1px solid #f3f4f6;vertical-align:middle}}
.m-tbl .pu{{color:#1E7E34;font-weight:700}}.m-tbl .pd{{color:#721C24;font-weight:700}}

.m-src-list{{display:flex;flex-direction:column;gap:7px}}
.m-src-item{{display:flex;align-items:center;gap:10px}}
.m-src-link{{color:#1B3A6B;text-decoration:none;font-size:.79rem;font-weight:500;flex:1;line-height:1.3}}
.m-src-link:hover{{text-decoration:underline}}
.m-src-lbl{{font-size:.79rem;color:#555;flex:1;line-height:1.3}}
.m-src-badge{{font-size:.62rem;font-weight:700;padding:2px 8px;border-radius:10px;white-space:nowrap;flex-shrink:0}}
.src-tinggi{{background:#d1fae5;color:#065f46}}
.src-sedang{{background:#fef3c7;color:#92400e}}
.src-estimasi{{background:#f3f4f6;color:#6b7280}}

.m-chart-wrap{{height:175px;position:relative;margin-bottom:8px}}
.m-chart-meta{{display:flex;justify-content:space-between;font-size:.72rem;color:#666;gap:8px}}
.m-catatan{{font-size:.74rem;color:#666;background:#f8fafc;border-radius:8px;padding:9px 12px;margin-top:10px;font-style:italic;line-height:1.5}}

.m-ftr{{border-top:1px solid #e5e7eb;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;gap:12px}}
.m-ftr-date{{font-size:.72rem;color:#999}}
.m-ftr-btn{{background:#1B3A6B;color:#fff;border:none;border-radius:8px;padding:7px 22px;font-size:.8rem;font-weight:600;cursor:pointer;transition:background .15s}}
.m-ftr-btn:hover{{background:#0d2244}}

@media(max-width:480px){{
  .modal-ov{{align-items:flex-end;padding:0}}
  .modal-card{{max-height:92vh;border-radius:12px 12px 0 0;max-width:100%}}
  .m-harga-big{{font-size:1.55rem}}
}}
</style>
</head>
<body>

<!-- Header -->
<div class="hdr">
  <div class="hdr-inner">
    <div class="hdr-brand">
      <div class="hdr-logo">Market Watch AJN</div>
      <div class="hdr-sub">PT Agrinas Jaladri Nusantara (Persero) &mdash; Pemantauan Harga Komoditas Perikanan Strategis</div>
    </div>
    <div class="hdr-meta">
      <div class="hdr-date">Last Update: {TGL}</div>
    </div>
  </div>
</div>

<div class="wrap">

  <!-- Summary Cards -->
  <div class="summary-row">
    <div class="sum-card sc-click" onclick="openSumCard('total')" role="button" tabindex="0">
      <div class="sum-num">{len(data)}</div>
      <div class="sum-lbl">Total Komoditas Dipantau</div>
      <div class="sum-hint">&#9432; klik detail</div>
    </div>
    <div class="sum-card gold sc-click" onclick="openSumCard('alert')" role="button" tabindex="0">
      <div class="sum-num">{len(alerts)}</div>
      <div class="sum-lbl">Alert Aktif</div>
      <div class="sum-hint">&#9432; klik detail</div>
    </div>
    <div class="sum-card green sc-click" onclick="openSumCard('naik')" role="button" tabindex="0">
      <div class="sum-num">{naik}</div>
      <div class="sum-lbl">Komoditas Naik Minggu Ini</div>
      <div class="sum-hint">&#9432; klik detail</div>
    </div>
    <div class="sum-card red sc-click" onclick="openSumCard('turun')" role="button" tabindex="0">
      <div class="sum-num">{turun}</div>
      <div class="sum-lbl">Komoditas Turun Minggu Ini</div>
      <div class="sum-hint">&#9432; klik detail</div>
    </div>
    <div class="sum-card sc-click" onclick="openSumCard('budi')" role="button" tabindex="0">
      <div class="sum-num">{len(budidaya)}</div>
      <div class="sum-lbl">Komoditas Budidaya</div>
      <div class="sum-hint">&#9432; klik detail</div>
    </div>
    <div class="sum-card sc-click" onclick="openSumCard('tang')" role="button" tabindex="0">
      <div class="sum-num">{len(tangkap)}</div>
      <div class="sum-lbl">Komoditas Tangkap</div>
      <div class="sum-hint">&#9432; klik detail</div>
    </div>
  </div>

  <!-- Commodity Cards -->
  <div class="sec-title"><span class="dot"></span>Kartu Komoditas</div>
  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterCards('all', this)">Semua</button>
    <button class="filter-btn" onclick="filterCards('b', this)">Budidaya</button>
    <button class="filter-btn" onclick="filterCards('t', this)">Tangkap</button>
  </div>
  <div class="komod-grid" id="komodGrid">
{all_cards}
  </div>

  <!-- Chart: Bar harga tambak -->
  <div class="card-section">
    <div class="ch ch-navy">&#9632; Harga Tambak / Nelayan (Rp/kg) &mdash; Semua Komoditas</div>
    <div class="chart-wrap">
      <div class="chart-box"><canvas id="barChart"></canvas></div>
    </div>
  </div>

  <!-- Chart: Line tren top 5 -->
  <div class="card-section">
    <div class="ch ch-navy">&#9632; Tren Harga 3 Bulan &mdash; Top 5 Komoditas</div>
    <div class="chart-wrap">
      <div class="chart-box-lg"><canvas id="lineChart"></canvas></div>
    </div>
  </div>

  <!-- Alert Aktif -->
  <div class="card-section">
    <div class="ch ch-red">&#9888; Alert Aktif &mdash; {TGL}</div>
    <table>
      <thead><tr>
        <th>Jenis</th><th>Komoditas</th><th>% Perubahan</th>
        <th>Sebelum &rarr; Sekarang</th><th>Rekomendasi</th>
      </tr></thead>
      <tbody>
{alert_rows_html(alerts)}
      </tbody>
    </table>
  </div>

</div>

<div class="ftr">
  Dibuat otomatis oleh Market Watch AJN &bull; Data bersifat indikatif, bukan harga resmi &bull; {TGL}
</div>

<!-- Modal -->
<div class="modal-ov" id="modalOv">
  <div class="modal-card" id="modalCard">
    <div class="m-hdr">
      <div class="m-hdr-left">
        <div class="m-nama" id="mNama"></div>
        <div class="m-size" id="mSize"></div>
        <span class="m-kat" id="mKat"></span>
      </div>
      <button class="m-close" id="mCloseBtn" aria-label="Tutup">&#x2715;</button>
    </div>
    <div class="m-body" id="mBody"></div>
    <div class="m-ftr">
      <span class="m-ftr-date" id="mDate"></span>
      <button class="m-ftr-btn" id="mFtrBtn">Tutup</button>
    </div>
  </div>
</div>

<script>var SC_DATA={sc_data_js};</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<script>
(function () {{
  'use strict';

  /* ── Filter cards ── */
  window.filterCards = function(cat, btn) {{
    document.querySelectorAll('.filter-btn').forEach(function(b){{ b.classList.remove('active'); }});
    btn.classList.add('active');
    document.querySelectorAll('.komod-card').forEach(function(c) {{
      if (cat === 'all' || c.dataset.cat === cat) {{
        c.classList.remove('hidden');
      }} else {{
        c.classList.add('hidden');
      }}
    }});
  }};

  /* ── Bar Chart ── */
  try {{
    var bc = document.getElementById('barChart');
    if (bc) {{
      new Chart(bc, {{
        type: 'bar',
        data: {{
          labels: {bar_labels},
          datasets: [{{
            label: 'Harga (Rp/kg)',
            data: {bar_values},
            backgroundColor: {bar_colors},
            borderRadius: 4,
            borderSkipped: false
          }}]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: function(ctx) {{
                  return ' Rp ' + ctx.parsed.x.toLocaleString('id-ID') + '/kg';
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              beginAtZero: true,
              ticks: {{
                callback: function(v) {{ return 'Rp ' + (v/1000).toFixed(0) + ' rb'; }},
                font: {{ size: 10 }}
              }},
              grid: {{ color: 'rgba(0,0,0,.06)' }}
            }},
            y: {{ ticks: {{ font: {{ size: 10 }} }}, grid: {{ display: false }} }}
          }}
        }}
      }});
    }}
  }} catch(e) {{ console.error('Bar chart error:', e); }}

  /* ── Line Chart ── */
  try {{
    var lc = document.getElementById('lineChart');
    if (lc) {{
      new Chart(lc, {{
        type: 'line',
        data: {{
          labels: {top5_labels_js},
          datasets: {line_datasets_js}
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'top', labels: {{ font: {{ size: 11 }} }} }},
            tooltip: {{
              callbacks: {{
                label: function(ctx) {{
                  return ctx.dataset.label + ': Rp ' + ctx.parsed.y.toLocaleString('id-ID') + '/kg';
                }}
              }}
            }}
          }},
          scales: {{
            y: {{
              ticks: {{
                callback: function(v) {{ return 'Rp ' + (v/1000).toFixed(0) + ' rb'; }},
                font: {{ size: 10 }}
              }},
              grid: {{ color: 'rgba(0,0,0,.06)' }}
            }},
            x: {{ ticks: {{ font: {{ size: 11 }} }} }}
          }}
        }}
      }});
    }}
  }} catch(e) {{ console.error('Line chart error:', e); }}

}})();

/* ── Modal ─────────────────────────────────────────────────────────────────── */
(function() {{
  'use strict';
  var _mc = null;

  function esc(s) {{
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }}
  function fmtRp(n) {{
    return n ? n.toLocaleString('id-ID') : '—';
  }}
  function pctClass(s) {{
    if (!s || s === '—') return '';
    var v = parseFloat(String(s).replace(',','.').replace('%','').replace('+',''));
    return isNaN(v) ? '' : (v > 0 ? 'pu' : (v < 0 ? 'pd' : ''));
  }}

  window.openModal = function(card) {{
    var d;
    try {{ d = JSON.parse(card.dataset.modal); }} catch(e) {{ return; }}

    document.getElementById('mNama').textContent = d.nama;
    document.getElementById('mSize').textContent = d.size;
    var katEl = document.getElementById('mKat');
    katEl.textContent = d.kategori;
    katEl.className = 'm-kat ' + (d.kategori === 'Budidaya' ? 'cat-b' : 'cat-t');
    document.getElementById('mDate').textContent = 'Data per ' + d.tanggal;

    var catClr = d.kategori === 'Budidaya' ? '#1B3A6B' : '#145A30';
    var html = '';

    /* --- Section 1: Harga --- */
    html += '<div class="m-sec">';
    html += '<div class="m-sec-ttl">Harga Terkini</div>';
    html += '<div class="m-harga-big">Rp ' + esc(d.tambak) + '<span>/kg</span></div>';
    html += '<div class="m-harga-sub">';
    if (d.ekspor && d.ekspor !== '—')
      html += '<div class="m-harga-sub-item"><strong>Ekspor:</strong> USD ' + esc(d.ekspor) + '/kg</div>';
    if (d.intl && d.intl !== '—')
      html += '<div class="m-harga-sub-item"><strong>Internasional:</strong> USD ' + esc(d.intl) + '/kg</div>';
    html += '</div>';

    /* Tabel perbandingan */
    var tblRows = [
      ['Minggu Lalu',   d.minggu_lalu,     d.pct_minggu],
      ['1 Bulan Lalu',  d.bulan_lalu,      d.pct_1bulan],
      ['3 Bulan Lalu',  d.tiga_bulan_lalu, d.pct_3bulan],
    ];
    html += '<table class="m-tbl"><thead><tr><th>Periode</th><th>Harga Tambak</th><th>Perubahan</th></tr></thead><tbody>';
    tblRows.forEach(function(r) {{
      var harga = (r[1] && r[1] !== '—') ? 'Rp ' + esc(r[1]) + '/kg' : '—';
      var pc    = r[2] || '—';
      html += '<tr><td>' + r[0] + '</td><td>' + harga + '</td>' +
              '<td class="' + pctClass(pc) + '">' + esc(pc) + '</td></tr>';
    }});
    html += '</tbody></table>';
    if (d.catatan)
      html += '<div class="m-catatan">' + esc(d.catatan) + '</div>';
    html += '</div>';

    /* --- Section 2: Sumber Data --- */
    if (d.sumber && d.sumber.length) {{
      html += '<div class="m-sec"><div class="m-sec-ttl">Sumber Data</div>';
      html += '<div style="display:flex;justify-content:space-between;font-size:.67rem;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:.5px;padding:0 0 5px;border-bottom:1px solid #f3f4f6;margin-bottom:7px">' +
              '<span>Sumber</span><span>Kepercayaan</span></div>';
      html += '<div class="m-src-list">';
      d.sumber.forEach(function(s) {{
        var bc = 'src-' + s.level.toLowerCase();
        var nm = s.url && s.url !== '#'
          ? '<a class="m-src-link" href="' + s.url + '" target="_blank" rel="noopener">' + esc(s.nama) + ' &#8599;</a>'
          : '<span class="m-src-lbl">' + esc(s.nama) + '</span>';
        html += '<div class="m-src-item">' + nm +
                '<span class="m-src-badge ' + bc + '">' + s.level + '</span></div>';
      }});
      html += '</div></div>';
    }}

    /* --- Section 3: Tren --- */
    html += '<div class="m-sec"><div class="m-sec-ttl">Tren Harga Tambak (Rp/kg)</div>';
    html += '<div class="m-chart-wrap"><canvas id="mChartCvs"></canvas></div>';
    if (d.tren && d.tren.length >= 2) {{
      var vals = d.tren.map(function(p) {{ return p.y; }});
      var mx = Math.max.apply(null, vals), mn = Math.min.apply(null, vals);
      html += '<div class="m-chart-meta">' +
              '<span>&#9650; Tertinggi: Rp ' + fmtRp(mx) + '</span>' +
              '<span>&#9660; Terendah: Rp ' + fmtRp(mn) + '</span>' +
              '</div>';
    }}
    html += '</div>';

    document.getElementById('mBody').innerHTML = html;
    document.getElementById('modalOv').classList.add('active');
    document.body.style.overflow = 'hidden';

    /* Render mini chart */
    if (d.tren && d.tren.length >= 2) {{
      setTimeout(function() {{
        var cvs = document.getElementById('mChartCvs');
        if (!cvs) return;
        if (_mc) {{ _mc.destroy(); _mc = null; }}
        _mc = new Chart(cvs, {{
          type: 'line',
          data: {{
            labels: d.tren.map(function(p) {{ return p.x; }}),
            datasets: [{{
              label: 'Harga Tambak',
              data: d.tren.map(function(p) {{ return p.y; }}),
              borderColor: catClr,
              backgroundColor: catClr + '28',
              tension: 0.35,
              fill: true,
              pointRadius: 4,
              pointHoverRadius: 6,
              borderWidth: 2,
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
              legend: {{ display: false }},
              tooltip: {{
                callbacks: {{
                  label: function(ctx) {{
                    return 'Rp ' + ctx.parsed.y.toLocaleString('id-ID') + '/kg';
                  }}
                }}
              }}
            }},
            scales: {{
              y: {{
                ticks: {{ callback: function(v) {{ return 'Rp '+(v/1000).toFixed(0)+'rb'; }}, font:{{size:9}} }},
                grid: {{ color: 'rgba(0,0,0,.05)' }}
              }},
              x: {{ ticks: {{ font:{{size:9}}, maxRotation:40 }} }}
            }}
          }}
        }});
      }}, 30);
    }}
  }};

  function closeModal() {{
    document.getElementById('modalOv').classList.remove('active');
    document.body.style.overflow = '';
    if (_mc) {{ _mc.destroy(); _mc = null; }}
  }}

  document.getElementById('mCloseBtn').addEventListener('click', closeModal);
  document.getElementById('mFtrBtn').addEventListener('click', closeModal);
  document.getElementById('modalOv').addEventListener('click', function(e) {{
    if (e.target === this) closeModal();
  }});
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape' && document.getElementById('modalOv').classList.contains('active'))
      closeModal();
  }});

  /* ── Summary Card Popups ─────────────────────────────────────────────── */
  function kepClr(k) {{
    return k === 'Tinggi' ? 'src-tinggi' : (k === 'Sedang' ? 'src-sedang' : 'src-estimasi');
  }}
  function pctSpan(p) {{
    if (!p || p === '—') return '<span style="color:#aaa">—</span>';
    var v = parseFloat(String(p).replace(',','.').replace('%','').replace('+',''));
    var cl = isNaN(v) ? '' : (v > 0 ? 'color:#1E7E34;font-weight:700' : (v < 0 ? 'color:#721C24;font-weight:700' : ''));
    return '<span style="' + cl + '">' + esc(p) + '</span>';
  }}

  function buildKomodTbl(arr, catBg) {{
    if (!arr.length) return '<p style="color:#aaa;font-size:.8rem">Tidak ada data.</p>';
    var h = '<table class="m-tbl"><thead><tr><th>Komoditas</th><th>Size/Grade</th><th>Harga Tambak</th><th>Data</th></tr></thead><tbody>';
    arr.forEach(function(p) {{
      h += '<tr>' +
           '<td style="font-weight:600;color:#1B3A6B">' + esc(p.nama) + '</td>' +
           '<td style="color:#666">' + esc(p.size) + '</td>' +
           '<td>Rp ' + esc(p.tambak) + '/kg</td>' +
           '<td><span class="m-src-badge ' + kepClr(p.kepercayaan) + '">' + esc(p.kepercayaan) + '</span></td>' +
           '</tr>';
    }});
    return h + '</tbody></table>';
  }}

  function buildNaikTurunTbl(arr, dir) {{
    if (!arr.length) return '<p style="color:#aaa;font-size:.8rem;padding:12px 0">Tidak ada komoditas yang ' + (dir==='naik'?'naik':'turun') + ' minggu ini.</p>';
    var h = '<table class="m-tbl"><thead><tr><th>#</th><th>Komoditas</th><th>Size</th><th>Harga Tambak</th><th>% Minggu Ini</th></tr></thead><tbody>';
    arr.forEach(function(p, i) {{
      h += '<tr>' +
           '<td style="color:#aaa">' + (i+1) + '</td>' +
           '<td style="font-weight:600;color:#1B3A6B">' + esc(p.nama) + '</td>' +
           '<td style="color:#666">' + esc(p.size) + '</td>' +
           '<td>Rp ' + esc(p.tambak) + '/kg</td>' +
           '<td>' + pctSpan(p.pct) + '</td>' +
           '</tr>';
    }});
    return h + '</tbody></table>';
  }}

  function buildAlertTbl(arr) {{
    if (!arr.length) return '<div style="text-align:center;padding:20px 0;color:#aaa;font-size:.85rem">&#x2714; Tidak ada alert aktif dari update terakhir.</div>';
    var jenisBadge = function(j) {{
      j = (j||'').toUpperCase();
      if (j.indexOf('MERAH')>=0) return '<span class="badge badge-merah">MERAH</span>';
      if (j.indexOf('KUNING')>=0) return '<span class="badge badge-kuning">KUNING</span>';
      if (j.indexOf('BIRU')>=0)   return '<span class="badge badge-biru">BIRU</span>';
      return '<span class="badge badge-grey">INFO</span>';
    }};
    var h = '<table class="m-tbl"><thead><tr><th>Jenis</th><th>Komoditas</th><th>%</th><th>Rekomendasi</th></tr></thead><tbody>';
    arr.forEach(function(a) {{
      h += '<tr>' +
           '<td>' + jenisBadge(a.jenis) + '</td>' +
           '<td style="font-weight:600">' + esc(a.komoditas) + '</td>' +
           '<td>' + pctSpan(a.pct) + '</td>' +
           '<td style="font-size:.74rem;color:#555">' + esc(a.rekomendasi) + '</td>' +
           '</tr>';
    }});
    return h + '</tbody></table>';
  }}

  window.openSumCard = function(type) {{
    var d = SC_DATA[type];
    if (!d) return;
    var title = '', sub = '', bodyHtml = '';

    if (type === 'total') {{
      title = 'Total Komoditas Dipantau';
      sub   = (d.budidaya.length + d.tangkap.length) + ' komoditas';
      bodyHtml  = '<div class="m-sec"><div class="m-sec-ttl">Budidaya (' + d.budidaya.length + ')</div>' + buildKomodTbl(d.budidaya) + '</div>';
      bodyHtml += '<div class="m-sec"><div class="m-sec-ttl">Perikanan Tangkap (' + d.tangkap.length + ')</div>' + buildKomodTbl(d.tangkap) + '</div>';
    }} else if (type === 'alert') {{
      title = 'Alert Aktif';
      sub   = d.length ? d.length + ' alert terdeteksi' : 'Tidak ada alert';
      bodyHtml = '<div class="m-sec">' + buildAlertTbl(d) + '</div>';
    }} else if (type === 'naik') {{
      title = 'Komoditas Naik Minggu Ini';
      sub   = d.length + ' komoditas ↑ vs minggu lalu';
      bodyHtml = '<div class="m-sec">' + buildNaikTurunTbl(d, 'naik') + '</div>';
    }} else if (type === 'turun') {{
      title = 'Komoditas Turun Minggu Ini';
      sub   = d.length + ' komoditas ↓ vs minggu lalu';
      bodyHtml = '<div class="m-sec">' + buildNaikTurunTbl(d, 'turun') + '</div>';
    }} else if (type === 'budi') {{
      title = 'Komoditas Budidaya';
      sub   = d.length + ' komoditas';
      bodyHtml = '<div class="m-sec">' + buildKomodTbl(d) + '</div>';
    }} else if (type === 'tang') {{
      title = 'Komoditas Tangkap';
      sub   = d.length + ' komoditas';
      bodyHtml = '<div class="m-sec">' + buildKomodTbl(d) + '</div>';
    }}

    document.getElementById('mNama').textContent = title;
    document.getElementById('mSize').textContent = sub;
    var katEl = document.getElementById('mKat');
    katEl.textContent = '';
    katEl.className   = 'm-kat';
    document.getElementById('mDate').textContent = 'Data per ' + (SC_DATA._tgl || '');
    document.getElementById('mBody').innerHTML = bodyHtml;
    if (_mc) {{ _mc.destroy(); _mc = null; }}
    document.getElementById('modalOv').classList.add('active');
    document.body.style.overflow = 'hidden';
  }};
}})();
</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    kb = os.path.getsize(out_path) // 1024
    print(f"HTML disimpan: {out_path} ({kb} KB)")

    # Selalu simpan juga sebagai nama tetap (untuk GitHub Pages)
    dashboard_path = os.path.join(os.path.dirname(out_path), "MarketWatch_AJN_Dashboard.html")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML disimpan: {dashboard_path} ({kb} KB)")


# ── Dashboard Sheet ───────────────────────────────────────────────────────────

def create_dashboard_sheet(ss):
    DS_NAME    = "Dashboard"
    URL_OUTPUT = "https://github.com/dicanatta-bit/market-watch/tree/main/output"
    URL_REPO   = "https://github.com/dicanatta-bit/market-watch"
    URL_HTML   = "https://market-watch-ajn.netlify.app"

    NAVY     = {"red": 0.02, "green": 0.15, "blue": 0.35}
    WHITE    = {"red": 1.00, "green": 1.00, "blue": 1.00}
    BLUE_HDR = {"red": 0.02, "green": 0.27, "blue": 0.45}
    PALE_BG  = {"red": 0.92, "green": 0.95, "blue": 0.99}
    KREM_HL  = {"red": 1.00, "green": 0.97, "blue": 0.88}
    LABEL_FG = {"red": 0.30, "green": 0.30, "blue": 0.30}
    GREY_FG  = {"red": 0.60, "green": 0.60, "blue": 0.60}

    try:
        ws = ss.worksheet(DS_NAME)
        ws.clear()
        print(f"  Sheet '{DS_NAME}' sudah ada — isi diperbarui.")
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=DS_NAME, rows=25, cols=4)
        print(f"  Sheet '{DS_NAME}' dibuat baru.")
    sid = ws.id

    rows = [
        ["Market Watch AJN - Dashboard", "", "", ""],
        ["PT Agrinas Jaladri Nusantara (Persero)  |  Pemantauan Harga Komoditas Perikanan", "", "", ""],
        ["", "", "", ""],
        ["LAPORAN & INFOGRAFIS", "", "", ""],
        ["Folder Laporan (PDF & HTML)", f'=HYPERLINK("{URL_OUTPUT}","Buka folder output di GitHub")', "", ""],
        ["Infografis HTML Terkini", f'=HYPERLINK("{URL_HTML}","market-watch-ajn.netlify.app")', "", ""],
        ["", "", "", ""],
        ["INFORMASI SISTEM", "", "", ""],
        ["Repository GitHub", f'=HYPERLINK("{URL_REPO}","dicanatta-bit/market-watch")', "", ""],
        ["Jadwal Update Otomatis", "Setiap Senin, 08:00 WIB (via GitHub Actions)", "", ""],
        ["Last Update", TANGGAL, "", ""],
        ["", "", "", ""],
        ["KOMODITAS YANG DIPANTAU", "", "", ""],
        ["Budidaya", "Udang Vaname (Size 50/60/70/100)  |  Udang Windu (Size 20/30)  |  Nila  |  Patin  |  Bandeng  |  Rumput Laut", "", ""],
        ["Perikanan Tangkap", "Tuna Yellowfin  |  Tuna Cakalang  |  Kakap Merah  |  Kerapu  |  Lobster (Mutiara/Pasir)  |  Cumi-cumi", "", ""],
        ["", "", "", ""],
        ["Dibuat otomatis oleh Market Watch AJN  |  Data bersifat indikatif", "", "", ""],
    ]

    ws.update(rows, "A1", value_input_option="USER_ENTERED")

    reqs = [
        col_px(sid, 0, 1, 210), col_px(sid, 1, 2, 400), col_px(sid, 2, 3, 12), col_px(sid, 3, 4, 12),
        row_px(sid, 0, 1, 54), row_px(sid, 1, 2, 26), row_px(sid, 2, 3, 8),
        row_px(sid, 3, 4, 28), row_px(sid, 4, 6, 28), row_px(sid, 6, 7, 8),
        row_px(sid, 7, 8, 28), row_px(sid, 8, 11, 26), row_px(sid, 11, 12, 8),
        row_px(sid, 12, 13, 28), row_px(sid, 13, 15, 28), row_px(sid, 15, 16, 8),
        row_px(sid, 16, 17, 22),
        merge(sid, 0, 1, 0, 4), merge(sid, 1, 2, 0, 4), merge(sid, 3, 4, 0, 4),
        merge(sid, 7, 8, 0, 4), merge(sid, 12, 13, 0, 4), merge(sid, 16, 17, 0, 4),
        fmt(sid, 0, 1, 0, 4, bg=NAVY, fg=WHITE, bold=True, size=15, halign="CENTER", valign="MIDDLE"),
        fmt(sid, 1, 2, 0, 4, bg=BLUE_HDR, fg=WHITE, size=9, halign="CENTER", valign="MIDDLE"),
        fmt(sid, 3, 4, 0, 4, bg=PALE_BG, fg=NAVY, bold=True, size=10, valign="MIDDLE"),
        fmt(sid, 7, 8, 0, 4, bg=PALE_BG, fg=NAVY, bold=True, size=10, valign="MIDDLE"),
        fmt(sid, 12, 13, 0, 4, bg=PALE_BG, fg=NAVY, bold=True, size=10, valign="MIDDLE"),
        fmt(sid, 4, 6, 0, 1, fg=LABEL_FG, bold=True, size=9, valign="MIDDLE"),
        fmt(sid, 8, 11, 0, 1, fg=LABEL_FG, bold=True, size=9, valign="MIDDLE"),
        fmt(sid, 13, 15, 0, 1, fg=LABEL_FG, bold=True, size=9, valign="MIDDLE"),
        fmt(sid, 4, 6, 1, 2, size=9, valign="MIDDLE"),
        fmt(sid, 8, 11, 1, 2, size=9, valign="MIDDLE"),
        fmt(sid, 13, 15, 1, 2, size=9, valign="MIDDLE", wrap="WRAP"),
        fmt(sid, 10, 11, 1, 2, bg=KREM_HL, bold=True, size=9),
        fmt(sid, 16, 17, 0, 4, fg=GREY_FG, size=8, halign="CENTER", valign="MIDDLE"),
    ]

    ss.batch_update({"requests": [r for r in reqs if r is not None]})
    print(f"  Formatting 'Dashboard' diterapkan.")
    return ws


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import sys
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if "--test-html" in sys.argv:
        print("=== TEST MODE: generate HTML dengan data statis ===")
        test_alerts = [
            {"jenis": "[MERAH] Pergerakan harga tambak >5%",
             "komoditas": "Udang Vaname (Size 50)", "pct": "+7.20%",
             "sebelum": "58.000", "sekarang": "60.000 - 65.000",
             "rekomendasi": "Pertimbangkan penjualan atau hedging segera."},
            {"jenis": "[KUNING] Gap ekspor vs tambak >40%",
             "komoditas": "Udang Windu (Size 20)", "pct": "65.1%",
             "sebelum": "100.000 - 120.000", "sekarang": "~Rp 160.000/kg (ekspor)",
             "rekomendasi": "Peluang AJN sebagai agregator; review margin distribusi."},
            {"jenis": "[BIRU] Harga internasional turun >10%",
             "komoditas": "Tuna Cakalang", "pct": "-12.40%",
             "sebelum": "USD 2.10/kg", "sekarang": "1,50 - 2,50",
             "rekomendasi": "Waspadai risiko program ekspor; review kontrak."},
        ]
        out = os.path.join(OUTPUT_DIR, f"MarketWatch_AJN_{TANGGAL_FILE}.html")
        generate_html(STATIC_PRICES, test_alerts, out)
        print(f"\nBuka di browser: {os.path.abspath(out)}")
        return

    print("=== Market Watch AJN -- Buat Infografis & Dashboard ===\n")

    creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    ss     = client.open_by_key(SPREADSHEET_ID)
    print(f"Spreadsheet '{ss.title}' dibuka.")

    # Harga dari update terakhir (bukan hari ini)
    prices, last_update_date = _get_latest_prices(ss)
    print(f"Data harga: {len(prices)} komoditas/size")
    if last_update_date != date.min:
        tanggal_data = f"{last_update_date.day} {_BULAN[last_update_date.month]} {last_update_date.year}"
        print(f"Tanggal update terakhir: {tanggal_data}")
    else:
        tanggal_data = TANGGAL

    hist_series = _get_historical_series(ss)

    # Alert dari tanggal update terakhir (bukan hari ini)
    latest_alerts_raw = _get_latest_alerts(ss)
    print(f"Alert dari update terakhir: {len(latest_alerts_raw)}")
    alert_dicts = [
        {
            "jenis":       a[2] if len(a) > 2 else "",
            "komoditas":   a[1] if len(a) > 1 else "",
            "pct":         a[5] if len(a) > 5 else "",
            "sebelum":     a[3] if len(a) > 3 else "",
            "sekarang":    a[4] if len(a) > 4 else "",
            "rekomendasi": a[6] if len(a) > 6 else "",
        }
        for a in latest_alerts_raw
    ]

    # Google Sheet Infografis (tetap pakai today_alerts agar up-to-date saat dijalankan hari H)
    today_alerts = alert_engine.get_today_alerts(ss)
    try:
        ss.del_worksheet(ss.worksheet(SHEET_NAME))
        print(f"Sheet lama '{SHEET_NAME}' dihapus.")
    except gspread.exceptions.WorksheetNotFound:
        pass
    ws  = ss.add_worksheet(title=SHEET_NAME, rows=TOTAL_ROWS + 5, cols=10)
    sid = ws.id
    ws.update(build_data(today_alerts), "A1", value_input_option="RAW")
    reqs = [r for r in build_requests(sid, today_alerts) if r is not None]
    ss.batch_update({"requests": reqs})
    print("Sheet Infografis selesai.")

    # HTML Dashboard
    html_path = os.path.join(OUTPUT_DIR, f"MarketWatch_AJN_{TANGGAL_FILE}.html")
    generate_html(prices, alert_dicts, html_path, hist_series, tanggal_data)

    # Salin Dashboard.html ke index.html di root (untuk GitHub Pages)
    import shutil
    dashboard_path = os.path.join(OUTPUT_DIR, "MarketWatch_AJN_Dashboard.html")
    shutil.copy2(dashboard_path, "index.html")
    print(f"index.html diperbarui dari {dashboard_path}")

    # Sheet Formatter: "Harga Komoditas"
    print("\nMemformat sheet 'Harga Komoditas'...")
    sheet_formatter.apply_sheet_formatting(ss)

    # Dashboard sheet
    print("\nMemperbarui sheet Dashboard...")
    create_dashboard_sheet(ss)

    print(f"\nSelesai!")
    print(f"GSheet : https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"HTML   : {html_path}")


if __name__ == "__main__":
    main()
