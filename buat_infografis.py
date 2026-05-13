"""
Market Watch - AJN
Buat infografis semua komoditas + alert di Google Sheet "Infografis"
dan ekspor HTML interaktif ke /output/
"""

import os
from datetime import date
from google.oauth2.service_account import Credentials
import gspread
import alert_engine

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
SHEET_NAME = "Infografis"
CREDS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
OUTPUT_DIR = "output"

_BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
_today = date.today()
TANGGAL    = f"{_today.day} {_BULAN[_today.month]} {_today.year}"
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

MAX_ALERTS = 5   # Maksimum baris alert di infografis (layout tetap)

GITHUB_HTML_URL = (
    "https://github.com/dicanatta-bit/market-watch/blob/main/output/"
    f"MarketWatch_AJN_{date.today().strftime('%Y%m%d')}.html"
)

# ── Data statis fallback (dipakai jika sheet belum berisi data) ───────────────
STATIC_PRICES = [
    {"komoditas": "Udang Vaname",   "size": "Size 50",        "tambak": "60.000 – 65.000",   "ekspor": "3,55 – 3,64", "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Vaname",   "size": "Size 60",        "tambak": "55.000 – 60.000",   "ekspor": "3,55",             "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Vaname",   "size": "Size 70",        "tambak": "50.000 – 55.000",   "ekspor": "—",           "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Vaname",   "size": "Size 100",       "tambak": "40.000 – 45.000",   "ekspor": "—",           "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Windu",    "size": "Size 20",        "tambak": "100.000 – 120.000", "ekspor": "8,00 – 10,00","pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Udang Windu",    "size": "Size 30",        "tambak": "80.000 – 100.000",  "ekspor": "6,00 – 8,00", "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Nila",           "size": "300–500 g", "tambak": "22.000 – 28.000",   "ekspor": "3,00 – 4,00", "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Tuna Yellowfin", "size": "Sashimi grade",  "tambak": "60.000 – 80.000",   "ekspor": "5,00 – 8,00", "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Tuna Yellowfin", "size": "Loin/beku",      "tambak": "30.000 – 45.000",   "ekspor": "2,50 – 4,00", "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Tuna Cakalang",  "size": "—",         "tambak": "15.000 – 25.000",   "ekspor": "1,50 – 2,50", "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Kakap Merah",    "size": "—",         "tambak": "50.000 – 70.000",   "ekspor": "5,00 – 8,00", "pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Kerapu",         "size": "Hidup (>500 g)", "tambak": "100.000 – 150.000", "ekspor": "8,00 – 12,00","pct_minggu": "", "kepercayaan": "Estimasi"},
    {"komoditas": "Kerapu",         "size": "Beku/segar",     "tambak": "60.000 – 90.000",   "ekspor": "5,00 – 7,00", "pct_minggu": "", "kepercayaan": "Estimasi"},
]

# ── Layout baris (0-indexed) ──────────────────────────────────────────────────
# R0–R3   : header, subtitle, tanggal, spacer
# R4–R12  : Section A Budidaya (header R4, kolom R5, data R6–R12)
# R13     : spacer
# R14–R21 : Section B Tangkap (header R14, kolom R15, data R16–R21)
# R22     : spacer
# R23–R25 : Highlight (header R23, data R24–R25)
# R26     : spacer
# R27–R33 : Alert Aktif (header R27, max 5 baris R28–R32, spacer R33)
# R34     : Footer
# ─────────────────────────────────────────────────────────────────────────────
TOTAL_ROWS = 35
ALERT_START = 28   # 0-indexed baris pertama data alert
FOOTER_ROW  = 34


def build_data(today_alerts):
    """Bangun list DATA 35 baris dengan section alert dinamis."""

    # Siapkan max 5 baris alert (padded jika kurang)
    alert_rows = []
    for a in today_alerts[:MAX_ALERTS]:
        jenis = a[2] if len(a) > 2 else ""
        alert_rows.append([jenis, a[1] if len(a) > 1 else "", a[5] if len(a) > 5 else "", a[6] if len(a) > 6 else "", "", ""])
    while len(alert_rows) < MAX_ALERTS:
        alert_rows.append(["—", "Tidak ada alert", "", "", "", ""])

    DATA = [
        # R0 Header AJN
        ["PT AGRINAS JALADRI NUSANTARA (AJN)", "", "", "", "", ""],
        # R1 Subtitle
        ["MARKET WATCH  |  HARGA KOMODITAS PERIKANAN STRATEGIS", "", "", "", "", ""],
        # R2 Tanggal
        [f"Update: {TANGGAL}   |   Sumber: KKP · JALA Tech · UCN · ASTUIN · BPS · Pelabuhan Perikanan",
         "", "", "", "", ""],
        # R3 spacer
        ["", "", "", "", "", ""],

        # R4 Section A
        ["A.  KOMODITAS BUDIDAYA", "", "", "", "", ""],
        # R5 header kolom
        ["Komoditas", "Size / Grade", "Harga Tambak (Rp/kg)", "Harga Ekspor (USD/kg)", "Tren & Catatan", ""],
        # R6–R9  Udang Vaname
        ["Udang Vaname", "Size 50",  "60.000 – 65.000", "3,55 – 3,64",
         "Naik 1–3% vs bulan lalu. Harga tambak Jawa Tengah.", ""],
        ["Udang Vaname", "Size 60",  "55.000 – 60.000", "3,55",
         "Stabil. Global turun 5,6% YoY (Mar 2026). Indonesia relatif stabil.", ""],
        ["Udang Vaname", "Size 70",  "50.000 – 55.000", "—",
         "Stabil. Produksi diperkirakan meningkat Apr–Mei.", ""],
        ["Udang Vaname", "Size 100", "40.000 – 45.000", "—",
         "Stabil. Estimasi berdasarkan gradasi harga antar ukuran.", ""],
        # R10–R11  Udang Windu
        ["Udang Windu", "Size 20", "100.000 – 120.000", "8,00 – 10,00",
         "Produksi terbatas; harga premium vs vaname. Dominan Sulawesi & Kalimantan.", ""],
        ["Udang Windu", "Size 30",  "80.000 – 100.000", "6,00 – 8,00",
         "Permintaan ekspor stabil. Sumber utama Sulawesi & Kalimantan.", ""],
        # R12  Nila
        ["Nila", "300–500 g", "22.000 – 28.000", "3,00 – 4,00",
         "Ekspor fillet ke AS & Eropa. Harga relatif stabil.", ""],

        # R13 spacer
        ["", "", "", "", "", ""],

        # R14 Section B
        ["B.  KOMODITAS PERIKANAN TANGKAP", "", "", "", "", ""],
        # R15 header kolom
        ["Komoditas", "Grade / Bentuk", "Harga Nelayan (Rp/kg)", "Harga Ekspor (USD/kg)",
         "Tren & Catatan", ""],
        # R16–R17  Tuna Yellowfin
        ["Tuna Yellowfin", "Sashimi grade", "60.000 – 80.000", "5,00 – 8,00",
         "Ekspor ke Jepang & Eropa. Pasar stabil; harga premium terjaga.", ""],
        ["Tuna Yellowfin", "Loin / beku",   "30.000 – 45.000", "2,50 – 4,00",
         "Grade industri untuk pengalengan & loin beku.", ""],
        # R18  Cakalang
        ["Tuna Cakalang", "—", "15.000 – 25.000", "1,50 – 2,50",
         "Bahan baku utama pengalengan. Harga dipengaruhi musim tangkapan.", ""],
        # R19  Kakap
        ["Kakap Merah", "—", "50.000 – 70.000", "5,00 – 8,00",
         "Permintaan ekspor ke China & Singapura tinggi dan stabil.", ""],
        # R20–R21  Kerapu
        ["Kerapu", "Hidup (>500 g)", "100.000 – 150.000", "8,00 – 12,00",
         "Ekspor hidup ke China dominan. Harga sensitif terhadap permintaan China.", ""],
        ["Kerapu", "Beku / segar",   "60.000 – 90.000",  "5,00 – 7,00",
         "Pasar lokal & ekspor grade beku.", ""],

        # R22 spacer
        ["", "", "", "", "", ""],

        # R23 Highlight header
        ["HIGHLIGHT PASAR", "", "", "", "", ""],
        # R24 Highlight row 1
        ["Udang vaname global turun 5,6% YoY. Indonesia stabil vs China (-10%) dan Ekuador (-11%).",
         "", "Kerapu hidup: permintaan China kuat. Harga Rp 100–150 rb/kg — tertinggi semua komoditas.",
         "", "", ""],
        # R25 Highlight row 2
        ["Tuna yellowfin sashimi stabil di USD 5–8/kg. Jepang & Eropa tetap jadi pasar ekspor utama.",
         "", "Produksi vaname meningkat Apr–Mei (size 60–70). Waspadai potensi tekanan harga.",
         "", "", ""],

        # R26 spacer
        ["", "", "", "", "", ""],

        # R27 Alert Aktif header
        ["ALERT AKTIF", "", "", "", "", ""],
    ]

    # R28–R32 — baris alert (5 baris tetap)
    DATA.extend(alert_rows)

    # R33 spacer
    DATA.append(["", "", "", "", "", ""])
    # R34 Footer
    DATA.append(["Dibuat otomatis oleh Market Watch AJN   |   Data bersifat indikatif, bukan harga resmi.",
                 "", "", "", "", ""])

    return DATA


# ── Helper builders ───────────────────────────────────────────────────────────

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
    """Pilih background color berdasarkan jenis alert."""
    j = str(jenis).upper()
    if "MERAH" in j:   return C_MERAH_PALE
    if "KUNING" in j:  return C_KUNING_PALE
    if "BIRU" in j:    return C_BIRU_PALE
    return C_PUTIH


def build_requests(sid, today_alerts):
    reqs = []

    # ── Lebar kolom ──────────────────────────────────────────────────────────
    for c, px in [(0, 160), (1, 130), (2, 155), (3, 145), (4, 230), (5, 14)]:
        reqs.append(col_px(sid, c, c + 1, px))

    # ── Tinggi baris ─────────────────────────────────────────────────────────
    reqs += [
        row_px(sid,  0,  1, 50),   # header AJN
        row_px(sid,  1,  2, 36),   # subtitle
        row_px(sid,  2,  3, 24),   # tanggal
        row_px(sid,  3,  4,  8),   # spacer
        row_px(sid,  4,  5, 30),   # section A header
        row_px(sid,  5,  6, 26),   # col headers A
        row_px(sid,  6, 13, 24),   # data budidaya (7 baris)
        row_px(sid, 13, 14,  8),   # spacer
        row_px(sid, 14, 15, 30),   # section B header
        row_px(sid, 15, 16, 26),   # col headers B
        row_px(sid, 16, 22, 24),   # data tangkap (6 baris)
        row_px(sid, 22, 23,  8),   # spacer
        row_px(sid, 23, 24, 28),   # highlight header
        row_px(sid, 24, 26, 50),   # highlight rows
        row_px(sid, 26, 27,  8),   # spacer
        row_px(sid, 27, 28, 28),   # alert header
        row_px(sid, 28, 33, 26),   # alert rows (5)
        row_px(sid, 33, 34,  8),   # spacer
        row_px(sid, 34, 35, 22),   # footer
    ]

    # ── Merge ────────────────────────────────────────────────────────────────
    reqs += [
        merge(sid,  0,  1, 0, 6),   # header
        merge(sid,  1,  2, 0, 6),   # subtitle
        merge(sid,  2,  3, 0, 6),   # tanggal
        merge(sid,  4,  5, 0, 6),   # section A
        merge(sid, 14, 15, 0, 6),   # section B
        merge(sid, 23, 24, 0, 6),   # highlight header
        merge(sid, 24, 25, 0, 2),   # highlight R24 kiri
        merge(sid, 24, 25, 2, 6),   # highlight R24 kanan
        merge(sid, 25, 26, 0, 2),   # highlight R25 kiri
        merge(sid, 25, 26, 2, 6),   # highlight R25 kanan
        merge(sid, 27, 28, 0, 6),   # alert header
        merge(sid, 33, 34, 0, 6),   # spacer sebelum footer
        merge(sid, 34, 35, 0, 6),   # footer
    ]
    # Merge kolom alert: B–D dan E–F tiap baris
    for r in range(28, 33):
        reqs.append(merge(sid, r, r + 1, 1, 4))   # Komoditas merge
        reqs.append(merge(sid, r, r + 1, 4, 6))   # Rekomendasi merge

    # ── Format header & meta ─────────────────────────────────────────────────
    reqs.append(fmt(sid, 0, 1, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True,
                    size=14, halign="CENTER", valign="MIDDLE"))
    reqs.append(fmt(sid, 1, 2, 0, 6, bg=C_BIRU_MUDA, fg=C_PUTIH, bold=True,
                    size=12, halign="CENTER", valign="MIDDLE"))
    reqs.append(fmt(sid, 2, 3, 0, 6, bg=C_KREM, size=9,
                    halign="CENTER", valign="MIDDLE"))

    # ── Section A — Budidaya ─────────────────────────────────────────────────
    reqs.append(fmt(sid,  4,  5, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True,
                    size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid,  5,  6, 0, 5, bg=C_BIRU_MUDA, fg=C_PUTIH, bold=True,
                    size=10, halign="CENTER", valign="MIDDLE"))
    for i in range(7):
        r  = 6 + i
        bg = C_BIRU_PALE if i % 2 == 0 else C_PUTIH
        reqs.append(fmt(sid, r, r + 1, 0, 5, bg=bg, size=10, valign="MIDDLE"))
        reqs.append(fmt(sid, r, r + 1, 0, 1, bold=True))
        reqs.append(fmt(sid, r, r + 1, 1, 4, halign="CENTER"))
        reqs.append(fmt(sid, r, r + 1, 4, 5, wrap="WRAP", size=9))

    # ── Section B — Tangkap ──────────────────────────────────────────────────
    reqs.append(fmt(sid, 14, 15, 0, 6, bg=C_HIJAU_TUA, fg=C_PUTIH, bold=True,
                    size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid, 15, 16, 0, 5, bg=C_BIRU_MUDA, fg=C_PUTIH, bold=True,
                    size=10, halign="CENTER", valign="MIDDLE"))
    for i in range(6):
        r  = 16 + i
        bg = C_ORANGE_PALE if i % 2 == 0 else C_PUTIH
        reqs.append(fmt(sid, r, r + 1, 0, 5, bg=bg, size=10, valign="MIDDLE"))
        reqs.append(fmt(sid, r, r + 1, 0, 1, bold=True))
        reqs.append(fmt(sid, r, r + 1, 1, 4, halign="CENTER"))
        reqs.append(fmt(sid, r, r + 1, 4, 5, wrap="WRAP", size=9))

    # ── Highlight ────────────────────────────────────────────────────────────
    reqs.append(fmt(sid, 23, 24, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True,
                    size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid, 24, 26, 0, 2, bg=C_KREM, size=10,
                    valign="MIDDLE", wrap="WRAP"))
    reqs.append(fmt(sid, 24, 26, 2, 6, bg=C_HIJAU_PALE, size=10,
                    valign="MIDDLE", wrap="WRAP"))

    # ── Alert Aktif ──────────────────────────────────────────────────────────
    reqs.append(fmt(sid, 27, 28, 0, 6, bg=C_MERAH_TUA, fg=C_PUTIH, bold=True,
                    size=11, halign="LEFT", valign="MIDDLE"))
    for i, a in enumerate(today_alerts[:MAX_ALERTS]):
        r  = 28 + i
        jenis = a[2] if len(a) > 2 else ""
        bg = alert_bg(jenis)
        reqs.append(fmt(sid, r, r + 1, 0, 6, bg=bg, size=9, valign="MIDDLE"))
        reqs.append(fmt(sid, r, r + 1, 0, 1, bold=True))
        reqs.append(fmt(sid, r, r + 1, 4, 6, wrap="WRAP"))
    # Baris alert kosong (padding)
    for i in range(len(today_alerts), MAX_ALERTS):
        r = 28 + i
        reqs.append(fmt(sid, r, r + 1, 0, 6, bg=C_PUTIH, size=9,
                        fg={"red": 0.6, "green": 0.6, "blue": 0.6}))

    # ── Footer ───────────────────────────────────────────────────────────────
    reqs.append(fmt(sid, 34, 35, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, size=9,
                    halign="CENTER", valign="MIDDLE"))

    # ── Border ───────────────────────────────────────────────────────────────
    reqs.append(border_box(sid,  5, 13, 0, 5))   # tabel budidaya
    reqs.append(border_box(sid, 15, 22, 0, 5))   # tabel tangkap
    reqs.append(border_box(sid, 27, 33, 0, 6))   # section alert

    return reqs


# ── HTML export ───────────────────────────────────────────────────────────────

_BUDIDAYA_KEYS = ["Vaname", "Windu", "Nila"]

_SHORT_NAMES = [
    ("Udang Vaname",   "Vaname"),
    ("Udang Windu",    "Windu"),
    ("Nila",           "Nila"),
    ("Yellowfin",      "Yellowfin"),
    ("Cakalang",       "Cakalang"),
    ("Kakap",          "Kakap"),
    ("Kerapu",         "Kerapu"),
]


def _short_name(komoditas):
    for k, v in _SHORT_NAMES:
        if k in komoditas:
            return v
    return komoditas.split("(")[0].strip()[:14]


def _parse_mid_simple(s):
    """Ekstrak nilai tengah dari string harga range (tanpa import eksternal)."""
    import re
    if not s or str(s).strip() in ("", "—", "-"):
        return None
    s = str(s).replace(".", "").replace(",", ".").strip()
    parts = re.split(r"\s*[–\-]\s*", s)
    try:
        vals = [float(p.strip()) for p in parts if p.strip()]
        return sum(vals) / len(vals) if vals else None
    except ValueError:
        return None


def _get_latest_prices(ss):
    """
    Baca harga terbaru per komoditas+size dari sheet.
    Fallback ke STATIC_PRICES jika sheet kosong atau error.
    """
    try:
        ws   = ss.worksheet("Harga Komoditas")
        rows = ws.get_all_values()
        if len(rows) < 2:
            print("  Sheet kosong — pakai data statis.")
            return STATIC_PRICES
        latest = {}
        for row in rows[1:]:
            if len(row) < 5:
                continue
            latest[(row[1], row[2])] = row
        if not latest:
            return STATIC_PRICES
        return [
            {
                "komoditas":   k,
                "size":        s,
                "tambak":      row[3]  if len(row) > 3  else "—",
                "ekspor":      row[4]  if len(row) > 4  else "—",
                "pct_minggu":  row[9]  if len(row) > 9  else "",
                "kepercayaan": row[12] if len(row) > 12 else "Estimasi",
            }
            for (k, s), row in latest.items()
        ]
    except Exception as exc:
        print(f"  [WARN] Tidak bisa baca sheet: {exc} — pakai data statis")
        return STATIC_PRICES


def generate_html(prices, alerts, out_path):
    """
    Generate file HTML infografis interaktif ke out_path.
    - prices: list of dicts {komoditas, size, tambak, ekspor, pct_minggu, kepercayaan}
    - alerts: list of dicts {jenis, komoditas, pct, sebelum, sekarang, rekomendasi}
    """
    data = prices if prices else STATIC_PRICES

    budidaya = [p for p in data if any(k in p["komoditas"] for k in _BUDIDAYA_KEYS)]
    tangkap  = [p for p in data if p not in budidaya]

    # ── Chart data (horizontal bar, sorted desc) ──────────────────────────────
    chart_items = []
    for p in data:
        mid = _parse_mid_simple(p["tambak"])
        if mid is None:
            continue
        nm  = _short_name(p["komoditas"])
        sz  = p["size"]
        lbl = f"{nm} {sz}" if sz not in ("-", "—", "") else nm
        cat = "b" if any(k in p["komoditas"] for k in _BUDIDAYA_KEYS) else "t"
        chart_items.append((lbl, int(mid), cat))

    chart_items.sort(key=lambda x: x[1], reverse=True)

    labels_js = "[" + ", ".join(f'"{lbl}"' for lbl, _, _ in chart_items) + "]"
    values_js = "[" + ", ".join(str(v)   for _, v, _   in chart_items) + "]"
    colors_js = "[" + ", ".join(
        '"rgba(6,80,114,0.82)"' if cat == "b" else '"rgba(20,90,48,0.82)"'
        for _, _, cat in chart_items
    ) + "]"

    # ── Price table rows ──────────────────────────────────────────────────────
    def price_rows(lst):
        rows = []
        for i, p in enumerate(lst):
            pct = (p.get("pct_minggu") or "").strip()
            if pct.startswith("+"):
                pct_cell = f'<span class="up">{pct}</span>'
            elif pct.startswith("-"):
                pct_cell = f'<span class="dn">{pct}</span>'
            else:
                pct_cell = pct or "—"
            kep = p.get("kepercayaan", "Estimasi")
            cls = "alt" if i % 2 else ""
            rows.append(
                f'<tr class="{cls}">'
                f'<td class="b">{p["komoditas"]}</td>'
                f'<td class="c">{p["size"]}</td>'
                f'<td class="c">{p["tambak"]}</td>'
                f'<td class="c">{p["ekspor"]}</td>'
                f'<td class="c">{pct_cell}</td>'
                f'<td class="c kep-{kep.lower()}">{kep}</td>'
                f'</tr>'
            )
        return "\n".join(rows) if rows else '<tr><td colspan="6" class="c muted">Belum ada data.</td></tr>'

    # ── Alert table rows ──────────────────────────────────────────────────────
    def alert_rows(lst):
        if not lst:
            return '<tr><td colspan="5" class="c muted">Tidak ada alert aktif hari ini.</td></tr>'
        rows = []
        for a in lst:
            j = str(a.get("jenis", "")).upper()
            if "MERAH" in j:
                rcls, bcls, btxt = "rm", "bm", "MERAH"
            elif "KUNING" in j:
                rcls, bcls, btxt = "rk", "bk", "KUNING"
            elif "BIRU" in j:
                rcls, bcls, btxt = "rb", "bb", "BIRU"
            else:
                rcls, bcls, btxt = "",   "bg", "INFO"
            rows.append(
                f'<tr class="{rcls}">'
                f'<td><span class="badge {bcls}">{btxt}</span></td>'
                f'<td>{a.get("komoditas","")}</td>'
                f'<td class="c b">{a.get("pct","")}</td>'
                f'<td>{a.get("sebelum","")} &#8594; {a.get("sekarang","")}</td>'
                f'<td class="sm">{a.get("rekomendasi","")}</td>'
                f'</tr>'
            )
        return "\n".join(rows)

    # ── Render HTML ───────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market Watch AJN &mdash; {TANGGAL}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#eef2f7;color:#1a1a1a;font-size:14px}}
.hdr{{background:#065072;color:#fff;padding:16px 24px}}
.hdr h1{{font-size:1.2rem;font-weight:700}}
.hdr p{{font-size:.8rem;opacity:.85;margin-top:3px}}
.wrap{{max-width:1140px;margin:16px auto;padding:0 14px}}
.card{{background:#fff;border-radius:8px;box-shadow:0 1px 5px rgba(0,0,0,.1);margin-bottom:16px;overflow:hidden}}
.ch{{padding:9px 14px;font-weight:700;font-size:.86rem;color:#fff}}
.blue{{background:#065072}}.green{{background:#145A30}}.red{{background:#8B1A1A}}
.chart-box{{padding:14px 14px 20px;height:400px;position:relative}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{background:#065072;color:#fff;padding:7px 10px;text-align:left;font-weight:600;white-space:nowrap}}
td{{padding:6px 10px;border-bottom:1px solid #eee;vertical-align:middle}}
.alt td{{background:#f7fbfd}}
tr:hover td{{filter:brightness(.97)}}
.c{{text-align:center}}.b{{font-weight:600}}.sm{{font-size:.76rem;color:#555}}.muted{{color:#aaa}}
.up{{color:#1e8449;font-weight:700}}.dn{{color:#c0392b;font-weight:700}}
/* Alert row backgrounds */
.rm td{{background:#fde8e8}}.rk td{{background:#fef9df}}.rb td{{background:#e6f2fd}}
.rm:hover td{{background:#fbdcdc}}.rk:hover td{{background:#fdf3bb}}.rb:hover td{{background:#d5eafb}}
/* Badges */
.badge{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.7rem;font-weight:700}}
.bm{{background:#fde8e8;color:#c0392b}}.bk{{background:#fef9df;color:#9a7d0a}}
.bb{{background:#e6f2fd;color:#1a5276}}.bg{{background:#eee;color:#555}}
/* Kepercayaan */
.kep-tinggi{{color:#1e8449;font-weight:600}}.kep-sedang{{color:#9a7d0a;font-weight:600}}.kep-estimasi{{color:#888}}
.ftr{{text-align:center;font-size:.72rem;color:#aaa;padding:12px 0 20px}}
</style>
</head>
<body>

<div class="hdr">
  <h1>PT AGRINAS JALADRI NUSANTARA (AJN)</h1>
  <p>MARKET WATCH &mdash; HARGA KOMODITAS PERIKANAN STRATEGIS &nbsp;|&nbsp; Update: {TANGGAL}</p>
</div>

<div class="wrap">

  <!-- Chart harga tambak -->
  <div class="card">
    <div class="ch blue">Harga Tambak / Nelayan (Rp/kg) &mdash; Semua Komoditas</div>
    <div class="chart-box">
      <canvas id="priceChart"></canvas>
    </div>
  </div>

  <!-- Alert aktif -->
  <div class="card">
    <div class="ch red">&#9888; Alert Aktif &mdash; {TANGGAL}</div>
    <table>
      <thead><tr>
        <th>Jenis</th><th>Komoditas</th><th>% Perubahan</th>
        <th>Sebelum &#8594; Sekarang</th><th>Rekomendasi</th>
      </tr></thead>
      <tbody>
{alert_rows(alerts)}
      </tbody>
    </table>
  </div>

  <!-- Budidaya -->
  <div class="card">
    <div class="ch blue">A. Komoditas Budidaya</div>
    <table>
      <thead><tr>
        <th>Komoditas</th><th>Size / Grade</th>
        <th>Harga Tambak (Rp/kg)</th><th>Harga Ekspor (USD/kg)</th>
        <th>% vs Minggu Lalu</th><th>Kepercayaan</th>
      </tr></thead>
      <tbody>
{price_rows(budidaya)}
      </tbody>
    </table>
  </div>

  <!-- Tangkap -->
  <div class="card">
    <div class="ch green">B. Komoditas Perikanan Tangkap</div>
    <table>
      <thead><tr>
        <th>Komoditas</th><th>Grade / Bentuk</th>
        <th>Harga Nelayan (Rp/kg)</th><th>Harga Ekspor (USD/kg)</th>
        <th>% vs Minggu Lalu</th><th>Kepercayaan</th>
      </tr></thead>
      <tbody>
{price_rows(tangkap)}
      </tbody>
    </table>
  </div>

</div>

<div class="ftr">
  Dibuat otomatis oleh Market Watch AJN &bull; Data bersifat indikatif &bull; {TANGGAL}
</div>

<!-- Chart.js dimuat di akhir body (setelah canvas ada di DOM) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<script>
(function () {{
  'use strict';
  try {{
    var canvas = document.getElementById('priceChart');
    if (!canvas) {{ throw new Error('Canvas tidak ditemukan'); }}
    new Chart(canvas, {{
      type: 'bar',
      data: {{
        labels: {labels_js},
        datasets: [{{
          label: 'Harga (Rp/kg)',
          data: {values_js},
          backgroundColor: {colors_js},
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
              label: function (ctx) {{
                return ' Rp ' + ctx.parsed.x.toLocaleString('id-ID') + '/kg';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            beginAtZero: true,
            ticks: {{
              callback: function (v) {{
                return 'Rp ' + (v / 1000).toFixed(0) + ' rb';
              }},
              font: {{ size: 11 }}
            }},
            grid: {{ color: 'rgba(0,0,0,.06)' }}
          }},
          y: {{
            ticks: {{ font: {{ size: 11 }} }},
            grid: {{ display: false }}
          }}
        }}
      }}
    }});
  }} catch (e) {{
    console.error('Chart render error:', e);
    var box = document.querySelector('.chart-box');
    if (box) {{
      box.innerHTML = '<p style="padding:40px;text-align:center;color:#999">'
        + 'Grafik tidak dapat dimuat. Periksa koneksi internet.</p>';
    }}
  }}
}})();
</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    kb = os.path.getsize(out_path) // 1024
    print(f"HTML disimpan: {out_path} ({kb} KB, {len(chart_items)} bar chart)")


# ── Dashboard sheet ──────────────────────────────────────────────────────────

def create_dashboard_sheet(ss):
    """
    Buat atau perbarui sheet 'Dashboard' — TIDAK menghapus sheet lain.
    Berisi: judul, link GitHub output, tanggal last update otomatis.
    """
    DS_NAME    = "Dashboard"
    URL_OUTPUT = "https://github.com/dicanatta-bit/market-watch/tree/main/output"
    URL_REPO   = "https://github.com/dicanatta-bit/market-watch"
    URL_HTML   = (
        "https://github.com/dicanatta-bit/market-watch/blob/main/output/"
        f"MarketWatch_AJN_{TANGGAL_FILE}.html"
    )
    HTML_FILE  = f"MarketWatch_AJN_{TANGGAL_FILE}.html"

    NAVY     = {"red": 0.02, "green": 0.15, "blue": 0.35}
    WHITE    = {"red": 1.00, "green": 1.00, "blue": 1.00}
    BLUE_HDR = {"red": 0.02, "green": 0.27, "blue": 0.45}
    PALE_BG  = {"red": 0.92, "green": 0.95, "blue": 0.99}
    KREM_HL  = {"red": 1.00, "green": 0.97, "blue": 0.88}
    LABEL_FG = {"red": 0.30, "green": 0.30, "blue": 0.30}
    GREY_FG  = {"red": 0.60, "green": 0.60, "blue": 0.60}

    # Ambil sheet jika sudah ada (clear isinya), atau buat baru
    # — tidak menyentuh sheet lain sama sekali
    try:
        ws = ss.worksheet(DS_NAME)
        ws.clear()
        print(f"  Sheet '{DS_NAME}' sudah ada — isi diperbarui.")
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=DS_NAME, rows=25, cols=4)
        print(f"  Sheet '{DS_NAME}' dibuat baru.")
    sid = ws.id

    # ── Layout (0-indexed) ──────────────────────────────────────────────────
    # R0  : Judul utama            (merged A:D)
    # R1  : Subtitle               (merged A:D)
    # R2  : spacer
    # R3  : Section LAPORAN        (merged A:D)
    # R4  : Folder output + link
    # R5  : Infografis HTML terkini + link
    # R6  : spacer
    # R7  : Section INFORMASI      (merged A:D)
    # R8  : Repository + link
    # R9  : Jadwal update
    # R10 : Last Update            ← highlight krem
    # R11 : File HTML aktif
    # R12 : spacer
    # R13 : Section KOMODITAS      (merged A:D)
    # R14 : Budidaya
    # R15 : Perikanan Tangkap
    # R16 : spacer
    # R17 : Footer                 (merged A:D)
    # ────────────────────────────────────────────────────────────────────────
    rows = [
        ["Market Watch AJN - Dashboard", "", "", ""],                              # R0
        ["PT Agrinas Jaladri Nusantara (Persero)  |  Pemantauan Harga Komoditas Perikanan",
         "", "", ""],                                                               # R1
        ["", "", "", ""],                                                           # R2
        ["LAPORAN & INFOGRAFIS", "", "", ""],                                       # R3
        ["Folder Laporan (PDF & HTML)",
         f'=HYPERLINK("{URL_OUTPUT}","Buka folder output di GitHub")',
         "", ""],                                                                   # R4
        ["Infografis HTML Terkini",
         f'=HYPERLINK("{URL_HTML}","Buka infografis {TANGGAL}")',
         "", ""],                                                                   # R5
        ["", "", "", ""],                                                           # R6
        ["INFORMASI SISTEM", "", "", ""],                                           # R7
        ["Repository GitHub",
         f'=HYPERLINK("{URL_REPO}","dicanatta-bit/market-watch")',
         "", ""],                                                                   # R8
        ["Jadwal Update Otomatis", "Setiap Senin, 08:00 WIB (via GitHub Actions)",
         "", ""],                                                                   # R9
        ["Last Update", TANGGAL, "", ""],                                           # R10
        ["File HTML Aktif", HTML_FILE, "", ""],                                     # R11
        ["", "", "", ""],                                                           # R12
        ["KOMODITAS YANG DIPANTAU", "", "", ""],                                    # R13
        ["Budidaya",
         "Udang Vaname (Size 50/60/70/100)  |  Udang Windu (Size 20/30)  |  Nila",
         "", ""],                                                                   # R14
        ["Perikanan Tangkap",
         "Tuna Yellowfin  |  Tuna Cakalang  |  Kakap Merah  |  Kerapu",
         "", ""],                                                                   # R15
        ["", "", "", ""],                                                           # R16
        ["Dibuat otomatis oleh Market Watch AJN  |  Data bersifat indikatif",
         "", "", ""],                                                               # R17
    ]

    # USER_ENTERED agar formula HYPERLINK dievaluasi oleh Sheets
    ws.update(rows, "A1", value_input_option="USER_ENTERED")

    reqs = [
        # Lebar kolom: Label | Nilai/Link | thin buffer × 2
        col_px(sid, 0, 1, 210),
        col_px(sid, 1, 2, 400),
        col_px(sid, 2, 3,  12),
        col_px(sid, 3, 4,  12),
        # Tinggi baris
        row_px(sid,  0,  1, 54),
        row_px(sid,  1,  2, 26),
        row_px(sid,  2,  3,  8),
        row_px(sid,  3,  4, 28),
        row_px(sid,  4,  6, 28),
        row_px(sid,  6,  7,  8),
        row_px(sid,  7,  8, 28),
        row_px(sid,  8, 12, 26),
        row_px(sid, 12, 13,  8),
        row_px(sid, 13, 14, 28),
        row_px(sid, 14, 16, 28),
        row_px(sid, 16, 17,  8),
        row_px(sid, 17, 18, 22),
        # Merge
        merge(sid,  0,  1, 0, 4),
        merge(sid,  1,  2, 0, 4),
        merge(sid,  3,  4, 0, 4),
        merge(sid,  7,  8, 0, 4),
        merge(sid, 13, 14, 0, 4),
        merge(sid, 17, 18, 0, 4),
        # Judul: navy bg, putih bold, size 15, tengah
        fmt(sid, 0, 1, 0, 4, bg=NAVY, fg=WHITE, bold=True, size=15,
            halign="CENTER", valign="MIDDLE"),
        # Subtitle: biru, putih, size 9, tengah
        fmt(sid, 1, 2, 0, 4, bg=BLUE_HDR, fg=WHITE, size=9,
            halign="CENTER", valign="MIDDLE"),
        # Section headers: pale blue bg, navy bold
        fmt(sid,  3,  4, 0, 4, bg=PALE_BG, fg=NAVY, bold=True, size=10, valign="MIDDLE"),
        fmt(sid,  7,  8, 0, 4, bg=PALE_BG, fg=NAVY, bold=True, size=10, valign="MIDDLE"),
        fmt(sid, 13, 14, 0, 4, bg=PALE_BG, fg=NAVY, bold=True, size=10, valign="MIDDLE"),
        # Label kolom A: abu-abu bold size 9
        fmt(sid,  4,  6, 0, 1, fg=LABEL_FG, bold=True, size=9, valign="MIDDLE"),
        fmt(sid,  8, 12, 0, 1, fg=LABEL_FG, bold=True, size=9, valign="MIDDLE"),
        fmt(sid, 14, 16, 0, 1, fg=LABEL_FG, bold=True, size=9, valign="MIDDLE"),
        # Nilai kolom B: size 9, wrap untuk teks panjang
        fmt(sid,  4,  6, 1, 2, size=9, valign="MIDDLE"),
        fmt(sid,  8, 12, 1, 2, size=9, valign="MIDDLE"),
        fmt(sid, 14, 16, 1, 2, size=9, valign="MIDDLE", wrap="WRAP"),
        # Last Update (R10 = index 10) → highlight krem + bold
        fmt(sid, 10, 11, 1, 2, bg=KREM_HL, bold=True, size=9),
        # Footer: abu-abu, tengah, size 8
        fmt(sid, 17, 18, 0, 4, fg=GREY_FG, size=8,
            halign="CENTER", valign="MIDDLE"),
    ]

    ss.batch_update({"requests": [r for r in reqs if r is not None]})
    print(f"  Formatting 'Dashboard' diterapkan (id={sid}).")
    return ws


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import sys
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── Mode test: generate HTML dengan data statis, tanpa credentials ────────
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
        print(f"\nBuka file ini di browser untuk verifikasi:")
        print(f"  {os.path.abspath(out)}")
        return

    # ── Mode normal: butuh credentials ───────────────────────────────────────
    print("=== Market Watch AJN -- Buat Infografis Komprehensif ===\n")

    creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    ss     = client.open_by_key(SPREADSHEET_ID)
    print(f"Spreadsheet '{ss.title}' dibuka.")

    today_alerts = alert_engine.get_today_alerts(ss)
    print(f"Alert aktif hari ini: {len(today_alerts)}")

    prices = _get_latest_prices(ss)
    print(f"Data harga: {len(prices)} komoditas/size")

    # ── Google Sheet Infografis ──────────────────────────────────────────────
    try:
        ss.del_worksheet(ss.worksheet(SHEET_NAME))
        print(f"Sheet lama '{SHEET_NAME}' dihapus.")
    except gspread.exceptions.WorksheetNotFound:
        pass

    ws  = ss.add_worksheet(title=SHEET_NAME, rows=TOTAL_ROWS + 5, cols=10)
    sid = ws.id
    print(f"Sheet '{SHEET_NAME}' dibuat (id={sid}).")

    ws.update(build_data(today_alerts), "A1", value_input_option="RAW")
    print("Data berhasil ditulis ke GSheet.")

    reqs = [r for r in build_requests(sid, today_alerts) if r is not None]
    ss.batch_update({"requests": reqs})
    print("Formatting diterapkan.")

    # ── HTML export ──────────────────────────────────────────────────────────
    html_path   = os.path.join(OUTPUT_DIR, f"MarketWatch_AJN_{TANGGAL_FILE}.html")
    alert_dicts = [
        {
            "jenis":       a[2] if len(a) > 2 else "",
            "komoditas":   a[1] if len(a) > 1 else "",
            "pct":         a[5] if len(a) > 5 else "",
            "sebelum":     a[3] if len(a) > 3 else "",
            "sekarang":    a[4] if len(a) > 4 else "",
            "rekomendasi": a[6] if len(a) > 6 else "",
        }
        for a in today_alerts
    ]
    generate_html(prices, alert_dicts, html_path)

    # ── Dashboard sheet (tanpa hapus sheet lain) ─────────────────────────────
    print("\nMemperbarui sheet Dashboard...")
    create_dashboard_sheet(ss)

    print(f"\nInfografis selesai!")
    print(f"GSheet : https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"HTML   : {html_path}")


if __name__ == "__main__":
    main()
