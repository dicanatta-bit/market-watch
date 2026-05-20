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
            komod = row[1].strip() if len(row) > 1 else ""
            tambak = row[3].strip() if len(row) > 3 else ""
            if not komod or not tambak or tambak in ("—", "-"):
                continue
            key  = (komod, row[2])
            tgl  = _parse_tanggal(row[0]) if len(row) > 0 else date.min
            prev = latest.get(key)
            if prev is None or tgl > prev[0]:
                latest[key] = (tgl, row)

        if not latest:
            return STATIC_PRICES

        result = []
        latest_date = date.min
        for (_k, _s), (_tgl, row) in latest.items():
            komod = row[1].strip() if len(row) > 1 else ""
            if not komod:
                continue
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
.hdr-inner{{max-width:1200px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;justify-content:space-between;gap:16px}}
.hdr-logos{{display:flex;align-items:center;gap:12px;flex-shrink:0}}
.hdr-logos .logo-danantara{{height:38px;width:auto;display:block;filter:brightness(0) invert(1)}}
.hdr-logos .logo-jaladri{{height:48px;width:auto;display:block}}
.hdr-brand{{display:flex;flex-direction:column;gap:4px;text-align:center;flex:1}}
.hdr-logo{{font-size:1.5rem;font-weight:800;letter-spacing:.5px;color:#C9A84C}}
.hdr-sub{{font-size:.75rem;opacity:.85;color:#cbd5e1}}
.hdr-right{{flex-shrink:0}}
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

/* ── CSS Tooltip ── */
.tip-wrap{{position:relative;cursor:help;display:inline-flex;align-items:center;gap:3px;border-bottom:1px dashed #d1d5db}}
.tip-wrap::after{{
  content:attr(data-tip);
  position:absolute;top:calc(100% + 8px);right:0;
  background:#1f2937;color:#f9fafb;
  font-size:.72rem;font-weight:400;text-transform:none;letter-spacing:0;line-height:1.55;
  padding:9px 13px;border-radius:7px;
  white-space:pre-line;width:260px;
  opacity:0;pointer-events:none;
  transition:opacity .15s ease;
  z-index:9999;
  box-shadow:0 6px 18px rgba(0,0,0,.3);
}}
.tip-wrap::before{{
  content:'';
  position:absolute;top:calc(100% + 2px);right:14px;
  border:5px solid transparent;border-bottom-color:#1f2937;
  opacity:0;pointer-events:none;
  transition:opacity .15s ease;
  z-index:9999;
}}
.tip-wrap:hover::after,.tip-wrap:hover::before{{opacity:1}}
</style>
</head>
<body>

<!-- Header -->
<div class="hdr">
  <div class="hdr-inner">
    <div class="hdr-logos">
      <img class="logo-danantara" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABQAAAANWCAYAAACh4yEnAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAABmJLR0QA/wD/AP+gvaeTAAAAB3RJTUUH6gIYCAA6XHk2XgAAgABJREFUeNrs3Xd4FdW+xvE3CRBCC4SOlNCk1wCht9AFqdJEUGlSVIoKgigc1AOKUgREqgIiKh3pSO9dEnoLvUMKpJBkz/0D9XrOUUjCnl0m38/z7OfcK3uvWfNbM7u8WbPGwzAMQwAAAAAAAAAsyZMSAAAAAAAAANZFAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAAAACAhREAAgAAAAAAABZGAAgAAAAAAABYGAEgAAAAAAAAYGEEgAAAAAAAAICFEQACAAAAAAAAFkYACAAAAAAAAFgYASAAAAAAAABgYQSAAAAAAAAAgIURAAIAAAAAAAAWRgAIAAAAAAAAWBgBIAAAAAAAAGBhBIAAAAAA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9+/fl5eXlzJkyCBfX19VqFDBYX94efjwoY4ePaqQkBAdO3ZMZ8+e1fXr13Xjxg3dunVL8fHx//jatGnT/jnmzz33nAoVKqTnn39ezz//vCpXrpzsm6gBsB8Pg+vPgESZOXOmevbsSSFgmrfeekvjxo3jh84zqFq1qvbu3Wta+z179tT06dOdsm/3799XjRo1dOLECYdsr169etq0aZND9/Hs2bNatGiRfv31V+3cuVPR0dHmfPnx8FDx4sVVv359vfjii6pTp47DZqucO3fO7msspkqVSuXKlUv08/ft26dx48bpl19+eeYae3l5qUGDBnrjjTfUsmVLh10mnxw2m01bt27VihUrtGnTJgUHB5u2DIOPj48qVaqkpk2bqkWLFipdurTD9vHw4cN2bzdHjhzKly9fop4bFxenBQsWaPLkyTp48OAz1zhbtmzq2LGjBgwYoMKFC9tlf3777bcnBhmS9PHHH2vZsmV2r+WSJUtUt27dJL3GkcHJoUOH9Msvv2jz5s3avXu3YmNjTdlOoUKFVL16dTVr1kxNmjRx2D4+evRIwcHBdm+3ePHiSp8+faKf//DhQy1dulTLly/Xvn37nrg2tLe3t7Zs2aKqVavavd+GYWjPnj1as2aNNm3apH379iXqD0HJ+dwtVqyYqlevrhdeeEGNGjVShgwZ+OIKOJoBIFFmzJhhSOLBw9RHpUqVjNDQUE64ZAoMDDR1fHr27OnU/Tt79qyRMWNGhxyLHh4exunTp03fp4cPHxpTpkwxfeye9MiUKZPRp08f48iRI6bvb+vWre3e/xw5ciRq2zt37jTq169vWh3LlStnrF692uXeF86dO2cMGjTIeO6555x2jBUrVsz44osvjDt37pi6r9HR0ab0/+23337qtuPj443Jkycb+fPnN6UPqVKlMl599VXj6tWrz1ynHDlyuNV3g/j4eFOPm2vXrhn/+te/jOLFiztl/1KlSmU0adLEWLJkiREXF2fqvl68eNGUfdizZ0+itn/p0iWjR48eRoYMGZLU/q+//mrXOly4cMEYNmyYUbBgQaeMube3t9G6dWtj7dq1RkJCAl9gAQchAAQIAHm42CNbtmzG+vXrOelcMADs1auX0/fx22+/ddix+MEHH5i2HxEREcbHH39sZM+e3aXOv6CgoET/kHOXADAsLMzo06eP4enp6ZAadunSxfSg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X7p0SQ0bNnSZ4CAqKkqtWrXShQsXTN/W1atXVaNGDc2ZM8etjre33npLb775phISEkzbTlxcnDp06KAvv/zSbT+XvvrqK7Vr186UJWBcyZAhQ/T++++bejyY6Y8/Xjlr9i8AxyMABOAwV65cUY0aNbR69epktzF06FC3nu3h6ipXrqyKFStSCDdx+PBhtWzZUjExMS7VrzNnzqhr166mnKtnz57VCy+8oHv37rnceFy+fFmdO3d2mx+DhmFo6NCh6t+/v1uvB7Vs2TIFBQW55DHxT8LCwtSoUSO7zYy3l7t376pt27amrkN46dIl1alTR4cOHXLL423y5Mlq27atKeFWQkKCOnXqpCVLlrj959Py5cvVqVMny84EHDJkiD777DO3349Hjx6pbdu2Lrm+JAD7IwAE4FAPHjxQy5YtNW3atCS/dunSpU5fqNzqevbsSRHcREREhNq3b++yl86tXLlSM2bMsGubt2/fVtOmTV36UquNGzeqT58+Ln/82Gw29evXT2PHjrXE+XDgwAHVq1dPN2/edPm+Goah119/3WUvGT98+LA++ugjU9o+f/68ateu7fY3zlm+fLm6desmm81m13Y/+OADt1jvL7EWL16sYcOGWe7z95tvvrFE+PfX7+YtWrRwu8uYASQdASAAh4uPj1efPn304YcfJnqGUEJCgoYPH07xTJQhQwZ17NiRQriJXr16ufwdF4cMGaJr167Zpa2EhAS99NJLbnGXyfnz57t0/wzDUM+ePfX1119b6pw4evSo6tatqzt37rh0PydNmqSlS5e6dB/Hjx9v9xl6N27cUP369R1+t26z/PDDD+rXr5/dZjqvXLnSMoH8X40bN87lj/ek2LFjh/r372+5cbp16xZ/BAZSAAJAAE4zevRodejQIVGXLy5evFgnTpygaCZ6+eWXlTFjRgrhBt555x39+OOPLt/PsLAwu80k+uSTT7R161YG3w4++ugjy96p8+TJk2rRooWioqJcsn8LFy7Ue++95/J1/OMmFPYSHR2tli1bWib8+8O0adM0atSoZ24nKirKrmGiKzEMQ3369HGrm5n8k8jISHXt2tWylzWvWLFCCxYs4EMSsDACQABO9fPPP6tZs2ZP/WJopUstXJGHh4fefvttCuEmTp8+7TZ9/e6773T+/PlnamPHjh0aPXo0A28HM2bMsHwt9+zZ47Jr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w9i6davdxqlChQqm1GnTpk38AAQshpuAAEAK5OXlpU8//ZRCWExAQID27dunr7/+WlWqVHnibKfChQvrk08+UXBwsMqXL++Q/h05ciRRzzt48KBOnjxpal9KlSqlrVu3qmjRosluI1OmTFq6dKnat2/vksfDnDlzTJ1FOWHCBLVo0cIubdWpU0ezZ882tR5ffPGFy567uXPn1qJFi7Rq1So1a9ZMadKk+cfnZsuWTX369NHJkycdduwdPnw4Scfdw4cP7d6H1KlT6+eff1aJEiXs0l7x4sW1cOHCp878TY5vvvkmUTe7sPcsyZw5c9q9vSZNmti1zYSEBJ0+fdptPlcT+7mVFM2bN1ft2rXt1p693of/m5mzxwE4BwEgAKRAPXr0UIUKFSiEhTRs2FDbt29XxYoVk/S6okWLasOGDSpVqpTpfTx79myinjd//nxT++Hn56dVq1Ype/bsz9yWl5eX5s2bp8DAQJc6Hmw2myZNmmRa+82aNVPfvn3t2manTp302muvmdbnPXv2uOTlh/7+/tq1a5fatm2bpNdlyZJFCxYs0EsvvWR6H8+dO5fo427KlCmm9OGjjz5S/fr17dpmvXr19K9//cvufb1y5YpWrFjx1Oc9ePDArtu9e/eu3felRo0adm/T1ZdO+KvffvvN7m3a+32uZMmSpuz7+fPn+XIFWAxrAAJACpMlSxaNHj2aQlhIUFCQli9fLh8fn2S9Plu2bFq9erXKli2r8PBw0/p55cqVRD1v8eLFptbrm2++UYECBezWXpo0abRw4UKVLl3alJlPybF69epEB65J5ePjo8mTJ5uynt6XX36p1atX6+bNm6b0feLEiapevbrLnLv58+fXli1bkn08enl5af78+Tp79mySZumZde6uX7/elNAgf/78GjRokCn7NmjQIE2bNk2XLl2ya7tTp05VmzZtnvic6Ohou27z1KlTOnLkiF1ndbdp00aGYdi1nwULFnSbz9fEHvuJ/vGdKpXdZ1VmzZrVlH13p6AWQCLfgygBAKQso0aNssvMJ7gGPz8/zZ8/P9nh319/YE+aNClZN3NIrKtXrybqB+zly5dN60P9+vXVrl07u7fr7++v9957Tx999JFLHBc//PCDaW3369fPtB/wmTNn1qeffqru3bub0v7KlStdZmF7Dw8Pffvtt88cRqdJk0bz5s1TpUqVFBMT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Nq3D65UvXz6n1NCsICZ9+vROmV2WN29eU9o1DEOXLl3i3LUTMy/ft4KnnZcffvihPD3d+2eZzWbTmjVr1LBhQ1WpUuU/1hBMCWw2m3799Vd169ZNOXPmVGBgoEaOHKk9e/a41exOANZGAAgAFtOgQQONHj2aQlicFS/tjoqKMqVdZwRXzroUMyIiwlL7kylTJtPaDg8P59y1k4cPH/Km/ARPm91coUIFvfrqq5bZ3/3796tOnTrq3r27IiMjLT22ERERGjdunAoVKqQGDRpo7ty5unPnDgc9AJdEAAgAFuLv768ffvhBXl5eFANux6w181JSAGhWiJohQwan7I+ZASChlesfd1Zx9erVpz7nyy+/lL+/v6X2e/bs2apcubIl14iMjIzURx99pHz58undd9/lMngAboEAEAAsIkuWLFq1apWyZctGMeCWCACfnVnr2llxBiABoP0QAD5ZYtY39fX11YoVKyx3ifipU6dUo0YNnT9/3hL7YxiG5syZoyJFiuhf//qXabOuAcAMBIAAYAFp0qTRzz//7JRF+gF7efTokSntent7O3xf0qdP75QamhUAOmt/zAweCa1c/9y1isTMAJQe3/Rm06ZNKlSokKX2/9q1a2ratKnTLru35zg2btxYr7/+um7dusWBDcDtEAACgJv7446/QUFBFANuzay10R48eODwfXFWuGRWDWNjY52yP2bNCpUe/+EE9pE2bVqK8ARJmSVWoUIFHTx4UC1btrRUDU6fPq3+/fu7bf83b96sihUrasOGDRzQANwWASAAuLmxY8fqlVdeoRBwe2aFCM5YhN5ZM13SpUtnmRpKMvXyOrNqlRJRyydLaoCeOXNmLV26VN9++62ee+45y9Rh/vz5bhmgrVmzRk2aNHHJWX8+Pj7q1auXKleuzIkG4KkIAAHAjY0YMULvvvsuhYAlmHWpLgHgs3PGLEqJANBdUMsnS85MVg8PD3Xr1k2nTp3SyJEjnXYZvr298847stlsbtPfPXv2qG3bti53mXvVqlX11Vdf6dKlS/rmm2+UK1cuTjQAT0UACABuasCAAfrXv/5FIWAZZs0AfPDggQzDcOi+hIWFOaWGZoUEVpwB6Kw7G1sRtXyyZ7mEPn369Proo4906dIljR8/3u3X+j169KhWr17tFn0NDw9X586dTVtbNSl8fX3Vpk0bffPNNwoNDdXu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bNhQBQsWNKXtgQMH6vz586a0HRsbq1GjRun+/ft2f9SuXft/tmfG5/3t27e1Y8cO08Y2T548dm8zY8aMLncMx8TEmNLuo0ePTGn34cOHmjdvHm8+ABKFABAAnMTf31+bN2/WmDFjWO8P+IsOHTqYvo233npLP/zwwzO1kZCQoIEDB2rixIkuV0M/Pz917drVtPYnTJigLVu22LXNq1ev6o033jCtz76+vnr99dc5wUzk5eWlvn37mtL2vXv31KZNG1NmaI0YMcKUcNHHx0cNGjT4n/8eEBBgSo3mzp1r2tiaMcM5U6ZMLncMe3t7m9LurVu3TGn3s88+Y/0/AIlGAAgATviBNGDAAAUHB6tmzZoUBPgvHTp0MP3SsISEBL388ssaNWqU4uPjk/z60NBQNW7cWBMmTHDZOr799tvy8PAwpW2bzaYOHTro9OnTdmkvIiJCLVu21N27d02rR/fu3V1yxpHVdO/e3bSbxPz2229q3769oqOj7dbmTz/9pC+++MKU/rZt21YZMmT4n/9etmxZU/7wN3/+fJ09e9aUfQkJCbF7m6545YOPj48p7e7atcvubR49elTjxo3jTQdAohEAAoADlStXTrt27dL48eP/9kcBgMeXmtWtW9f07RiGoZEjR6py5cpasWJFotadO3funN555x2VLFlSv/76q0vXsVixYmrfvr1p7d+6dUsNGjTQ0aNHn7mdpk2b2v2mCH+VPn36v12LDfaXJUsW02YBStKqVatUp04du8zY+/bbb9WlSxfT1pzs3r373/73tGnTmvIHwJiYGL355pt2Xwvw0KFDOnz4sN37W7x4cZc7frNmzWrKH06uXLli1xDw0qVLatq0qWlrFgKwJgJAAHCAjBkz6osvvtD/tXfnQVKVZ6CHX2aAGdahQPZFQIKoAVwQ0UkmoqIigkJYCkFSKFETrcJQGkkQCqIVUaOhNEpKBUFEEVArbqWgWRhABDVGMaCouBuDokQwGlTuH7mxkntjFJmGmZfnqZo/oKbP+fr06dPdvzl9vscffzx69+5tg8CXOO+883bbup566qk45ZRTokOHDnH22WfHDTfcEEuWLImlS5fGggUL4pprrokf/vCH0bNnz+jSpUtcddVVVXoGUiFNnz49SktLC7b81157LcrLy+P666//WhHlwQcfjMMPP7wgZ8f8uwsvvDDatm3ribWbTJo0KZo1a1aw5a9ZsyZ69OgRl1xySWzZsmWnb//KK6/EqFGjYuzYsbF9+/aCjPGwww77nxNnnHLKKQVZ74MPPhjjx4+vsuV99NFHMW7cuCofZ0lJSbUMgPXq1SvIJC0RERMnToxPP/10l5ezbt26OP744331F9hpAiBAIQ+yRUVx+umnx/PPPx8TJkyI2rVr2yjwFQwaNCj233//3brON954I2644YY4++yz44QTTojjjz8+Ro4cGePHj4+ZM2fu8plue0LHjh0Lfubb1q1b49xzz42ePXvGzTffHO+9996XBoV77703+vXrF/37949XX321oONr165dXHjhhZ5Uu1GTJk1i8uTJBV3Htm3bYsqUKdG+ffsYPXp0zJ07N15//fUv/P1NmzbFnXfeGSNHjoyuXbvGbbfdVtDxTZ069X+eSTZ48OCCXerg2muvjXHjxu3ybN3vvfdeDBw4sCBn/1VUVBTs67a7qmvXrgVZbmVlZZxzzjlfOwLu2LEj5syZE4cffng899xzDjTATvNJFKBA+vbtG1dffXUcfPDBNgbspKKiorjgggvi+9//vo2xiyZOnBi33357bNy4saDrWbt2bZxxxhlx1llnxaGHHhrdu3ePFi1aRFlZWWzbti3efffdWLduXaxevTq2bdu22+7/L3/5y4Jdk44v9oMf/CBmz55d8HD+wQcfxPz582P+/PkREdGwYcNo3rx5tGjRIkpKSuJvf/tbvPnmmwWbhOG/+da3vhUnn3zy//ydDh06xKBBg+Luu+8uyBhmzZoVDz/8cPzsZz+L4cOH79SZwJ988knceuutMXXq1HjllVcKMr4TTzyx2u67ffr0qfJJjv7lpptuirVr18aMGTPiiCOO+Eq32b59eyxcuDCuuOKKGvmHKKD6EAABqljv3r1j6tSp0b9/fxsDdsGYMWPiF7/4hTMddlGjRo3i1ltvje985ztfa8KTnfXJJ5/E6tWrY/Xq1Xv8vo8dOzaGDh1qJ9gD6tatG/PmzYvevXvHxx9/vNvWu3Xr1ti6dWvBg/cXqVOnTvz617/+Sr97/vnnFywARvzzq87f+9734kc/+lGceuqpccQRR0SvXr2iVatW0aRJk6hfv3589NFHsW3btti4cWP8+c9/jmXLlsU999wTmzZtKui+cdppp1XbfbfQE7StWrUq+vTpE927d49+/frFIYccEq1bt44mTZpExD/PvHznnXfipZdeisrKyli+fHls3brVQQXYZQIgQBXp0aNHXHzxxTF06NCCzbwJe1tAmDFjhpheBY466qiYNGlSTJs2ba+5z126dIlrrrnGg7+HXxcvvfTSveor2BMnToyDDjroK/1uRUVFnHDCCfHQQw8VdEybN2+O2bNnx+zZs6vFNhoyZEi0atWq2j6Gxx57bJSVlX2t60vujGeeeSaeeeYZBwpgt3ENQIBd1Ldv37jvvvviqaeeimHDhol/UIVOPPHEGDRokA1RBS6++OI47rjj9or72qBBg7jjjjvMtl4NTJgwIU466aS95v3AlClTduo2M2bMiDp16uw1+0NxcXFMnDixWo+xtLQ0hgwZstc/dws1Ozaw5wiAAF9DnTp1YtiwYbFq1ar47W9/GwMGDBD+oEBmzpwZzZs3tyF2Ue3atWPx4sXRvXv39PfzjjvuiEMPPdSDXh0+bBQVxYIFC6Jnz56p72f79u3j9ttv3+nJvrp16xY//elP95r94eyzz64R+8L48eP3+vd1NWW2e2AnXpNtAoCvrlOnTjFt2rR4+eWXY+HChV/5As7A19emTZuYM2dOjfowdtlll1XLcZWVlcX9998fbdu2Tbu/XHvttTFgwABPnGqkUaNGce+990br1q1T3r999tknHnrooWjZsuXXuv3kyZPjmGOOSb8fdOjQIS655JIaMdaePXvGwIED9+rnrQAI+QiAAF+ipKQkhg0bFvfcc09s2LAhpkyZEm3atLFhYDc66aST4oILLqgRYx0yZEgMHz682o6vffv2sXTp0nQRsFatWnHFFVfEOeec4wlTjfe7bK+fTZo0ifvvvz8OOOCAr72M4uLimD9/fnTu3Dn1e6lFixZF06ZNa8yYr7766hoxg3j79u0/n0CkKn344YcOXJCMAAjwBW/Gy8vLY8aMGfHaa6/FwoULY+DAgVFcXGzjwB4yffr0GDlyZLUeY7NmzeK6666r9tvygAMOiMrKythvv/1yvKEtKorrr79+r5psoiY66KCDorKyMk3oatOmTSxbtix69+69y8tq1apVykD6r/dUs2bNqpLttDvtt99+cemll1brMZaWlsbdd98dffr0qfJlb9u2Lf7xj384cEEiAiDA/1VWVhaDBw+OuXPnxjvvvBPLly+P8ePHu/YYVJc3LUVFMWfOnDjhhBOq5fjq1KkTixcvrtazW/67Tp06RWVlZRx88ME1er8oLS2NefPmOfOvhujcuXNUVlbGIYccUqPvR8+ePWPFihVVek3Nzp07xyOPPBIdO3ZM83gXFxfH3LlzY9SoUTVy/Oeff36cdtpp1XZ81113XRx22GEFua7ip59+Gi+++KKDFmR6L20TAHur4uLi6NWrV0yaNCmWLVsW77zzTtx1110xZsyYgnyVAth1devWjbvuuitOOeWUaje2mTNnxtFHH12jtmfr1q1j5cqVMW7cuBq5P3Tu3DlWrFhRrT+g8/9r06ZNrFy5ssZG2zFjxsTKlSsLEuq6desWq1atSnGN4aZNm8a9995bY+NfxD8vLXDTTTdVyz88/fznP48zzjgjIqJgkx4999xzDliQiAAI7DUaNmwY5eXlcdFFF8U999wTf/3rX2PNmjVx6aWXxre//e2dnrkP2DPq168fd955Z5x77rnV5gPi9OnT48wzz6yR27NevXpx4403xty5c6Nhw4Y1ZtynnnpqPPHEE2b7raFKS0tj5syZcdttt9WYP7o1bdo05s2bF3Pnzi3oteFatmwZv/vd72LChAk19tIjvXr1ijVr1kT//v1r/L5ar169+M1vfhODBw+uNmO6/PLL4yc/+cnn/66oqCjIRFmPP/64gxUkIgAC6ZSUlES3bt1i6NChMW3atLjzzjtjw4YNsWXLlli+fHlMnz49Bg4cWKMuRA38p+Li4vjVr34VN9544x6NVrVr145Zs2bFRRddVOO36ZgxY2LdunUxbNiwaj3Odu3axaJFi+Luu+92tnYCI0eOjPXr18fYsWOr9UzfQ4cOjWeffTZGjx69W9ZXr169uOqqq6KysjIOOuigGvN41q9fP6688sp49NFHU01qUlJSEosXL44pU6bs0f20rKwsFi1aFD/+8Y//4/9btWoV3bp1q/L1LViwIHbs2OFABUk43QWo9srKyqKoqCjq1KkTjRo1imbNmv3HT/PmzaNjx47RsWPH6NSpU7Ru3bpaf4gAqs64cePi6KOPjjFjxsSjjz66W9fdtm3bmDNnThx33HFptme7du1i4cKFsXTp0pgwYUKsXbu2WoWF8847LyZPnlyjzlTky7Vs2TJmz54dZ511Vlx00UWxbNmyajO2I488Mq688sooLy/fY+v/05/+FLfccktMnTo1Xn311er5obJ27Rg9enRMnTo19t1335T7aVFRUUybNi2OPvroOOuss+KFF17YresvLy+PW2655QvD6ne/+90qn7TkxRdfjEceeSTV6xzszZwBCDvxIXPHjh1+9sDP+++/H5s3b4633347XnjhhXjsscfigQceiHnz5sWMGTNi0qRJMWrUqCgvL482bdqIf7CX6dKlSyxfvjzmzZsXnTp12i3rPP3002Pt2rVpPxT169cvnn766bjvvvuioqJij46ladOmMXny5Hj55Zfj8ssvF/8S69OnT/zhD3+Ixx57LIYNG7bHvv5aq1at6N+/fyxZsiRWrFixx+LfvxQXF8fYsWPj+eefj9mzZ0evXr2qzWPWoEGDGDduXDz77LNx8803p41//65v377x9NNPx2WXXRb77LNPwdfXuXPnWLhw4ZfOoH366acX5Dlz5plnxptvvukABQk4AxCANHr37h1lZWX/9cNT48aN/+dt69atGw0aNPjS5e+MFi1a7HQgaty48Vd6A1/I60917NixYGGrUNfaLCoqitGjR8fw4cNj9uzZccMNN8Qf//jHKo8CJ598ckyaNOlLL9DfoEGDgnyV9sADD9xtz6datWrFgAEDYsCAAbFmzZqYP39+LF68ON54443Cv0GtXTv69u0bI0aMiBEjRuz26FdSUlKwr0K3b9++YONu0qRJwZ67jRo12q3H8oULF8Zrr70WixYtisWLF8eqVasK/lXEb3zjGzFy5MgYNWpUdO3atdq9xpWUlMTYsWNj7NixsXr16liwYEHcdddd8corr+zWcRQXF8dRRx0VI0aMiNGjR//X191dVVpa+pWeg5999lls2bJlp5bdoUOHXR5fvXr1YuLEiXHuuefGLbfcErNmzarS15yioqLo169fjBs3LgYNGhR169b90tt07do1Lrnkkip/7YuI2Lx5c7Rp08YbTajhau3wpX4AIKEnnngi5s+fH0uWLIlnn312l6LAkCFDYtSoUdG9e/e9ept+9tlnsWLFinjggQdixYoV8fjjj8ff//73Kll2x44do7y8PCoqKmLw4MHRvHlzOzGfe/3112Pp0qWxcuXKePTRR2PdunXx2Wef7dIymzVrFkceeWQce+yxccwxx0SPHj1q5LZ58skn4/e//30sX748Vq5cGW+//XaVr2P//fePI488MioqKmLAgAHRokULO+X/47nnnosHH3wwHn744XjyySd3+qy5fffdNyoqKuLYY4+N4447Ltq2bWujAlVKAAQA0nvrrbeisrIy1q9fH+vXr4+NGzfGu+++G9u2bfs8YDVp0iQaN24cLVq0iB49ekT37t3j8MMP361n3dU027dvjyeffDLWr18fL730UmzcuDFeeuml+OCDD2Lr1q2xdevW2L59e0T8cyb20tLSaNy4cbRq1So6d+4cnTp1iv322y8OO+wwH3bZKVu2bIkNGzbEyy+/HBs3boxXX301Nm/eHB9//HFs2bIlPvrooyguLo46depEw4YNo6ysLNq1axetWrWKrl27xje/+c20ZzS99dZbsW7duli/fn1s2LAhNm3aFH/5y1/i7bffjg8//DA+/PDD+Pjjjz///dq1a0ejRo2iQYMG0bJly2jZsmW0bt069t9//+jWrVsceOCBJk77GjZt2hQvvPBCvPXWW7Fp06Z4//3349NPP42ioqKoX79+1K9fP5o3bx6dOnWKLl26FPTMfoAIARAAAAAAUjMJCAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGICIAAAAAAkJgACAAAAQGK1I2K4zQAAAAAAOf0fT4DVT5FOYAYAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjYtMDItMjRUMDg6MDA6NTgrMDA6MDAr2HWtAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDI2LTAyLTI0VDA4OjAwOjU4KzAwOjAwWoXNEQAAAABJRU5ErkJggg==" alt="Danantara Indonesia">
      <img class="logo-jaladri" src="data:image/png;base64,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" alt="Agrinas Jaladri Nusantara">
    </div>
    <div class="hdr-brand">
      <div class="hdr-logo">Market Watch AJN</div>
      <div class="hdr-sub">PT Agrinas Jaladri Nusantara (Persero) &mdash; Pemantauan Harga Komoditas Perikanan Strategis</div>
    </div>
    <div class="hdr-right">
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
  Dibuat otomatis oleh Market Watch AJN &bull; Data bersifat indikatif, bukan harga resmi &bull; Last Update: {TGL}
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
      var tipTxt = 'Tinggi = sumber resmi pemerintah / lembaga internasional\\nSedang = sumber industri / asosiasi\\nEstimasi = kalkulasi berdasarkan tren';
      html += '<div style="display:flex;justify-content:space-between;align-items:center;font-size:.67rem;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:.5px;padding:0 0 5px;border-bottom:1px solid #f3f4f6;margin-bottom:7px">' +
              '<span>Sumber</span>' +
              '<span class="tip-wrap" data-tip="' + tipTxt + '">Tingkat Kepercayaan Data &#9432;</span></div>';
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
