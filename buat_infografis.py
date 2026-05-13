"""
Market Watch - AJN
Buat infografis harga udang vaname di Google Sheet tab "Infografis"
"""

from datetime import date
from google.oauth2.service_account import Credentials
import gspread

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
SHEET_NAME     = "Infografis"
CREDS_FILE     = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TANGGAL = date.today().strftime("%d Mei %Y")

# ── Palette warna AJN ────────────────────────────────────────────────────────
C_BIRU_TUA   = {"red": 0.02, "green": 0.27, "blue": 0.45}
C_BIRU_MUDA  = {"red": 0.06, "green": 0.49, "blue": 0.63}
C_EMAS       = {"red": 0.95, "green": 0.65, "blue": 0.10}
C_BIRU_PALE  = {"red": 0.88, "green": 0.95, "blue": 0.98}
C_HIJAU_PALE = {"red": 0.87, "green": 0.96, "blue": 0.89}
C_KREM       = {"red": 1.00, "green": 0.97, "blue": 0.88}
C_PUTIH      = {"red": 1.00, "green": 1.00, "blue": 1.00}
C_HITAM      = {"red": 0.10, "green": 0.10, "blue": 0.10}
C_ABU        = {"red": 0.40, "green": 0.40, "blue": 0.40}


# ── Helper builders ──────────────────────────────────────────────────────────

def rng(sid, r1, r2, c1, c2):
    return {"sheetId": sid,
            "startRowIndex": r1, "endRowIndex": r2,
            "startColumnIndex": c1, "endColumnIndex": c2}


def fmt(sid, r1, r2, c1, c2, bg=None, fg=None, bold=None, size=None,
        halign=None, valign=None, wrap=None):
    """repeatCell — hanya set field yang eksplisit diberikan."""
    cell, flds = {}, []

    if bg is not None:
        cell["backgroundColor"] = bg
        flds.append("backgroundColor")

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
    return {
        "repeatCell": {
            "range": rng(sid, r1, r2, c1, c2),
            "cell": {"userEnteredFormat": cell},
            "fields": "userEnteredFormat(" + ",".join(flds) + ")",
        }
    }


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


def num_fmt(sid, r1, r2, c1, c2, pattern):
    return {"repeatCell": {
        "range": rng(sid, r1, r2, c1, c2),
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": pattern}}},
        "fields": "userEnteredFormat.numberFormat"}}


def chart_column(sid, title, domain_rng, series_rng, anchor_row, anchor_col,
                 color, w=450, h=270, left_title=""):
    return {"addChart": {"chart": {
        "spec": {
            "title": title,
            "titleTextFormat": {"bold": True, "fontSize": 11, "foregroundColor": C_HITAM},
            "basicChart": {
                "chartType": "COLUMN",
                "legendPosition": "NO_LEGEND",
                "axis": [
                    {"position": "BOTTOM_AXIS", "title": ""},
                    {"position": "LEFT_AXIS",   "title": left_title},
                ],
                "domains": [{"domain": {"sourceRange": {"sources": [domain_rng]}}}],
                "series":  [{"series": {"sourceRange": {"sources": [series_rng]}},
                             "targetAxis": "LEFT_AXIS", "color": color}],
                "headerCount": 0,
            }
        },
        "position": {"overlayPosition": {
            "anchorCell": {"sheetId": sid, "rowIndex": anchor_row, "columnIndex": anchor_col},
            "widthPixels": w, "heightPixels": h}}}}}


def chart_bar(sid, title, domain_rng, series_rng, anchor_row, anchor_col,
              color, w=450, h=290):
    return {"addChart": {"chart": {
        "spec": {
            "title": title,
            "titleTextFormat": {"bold": True, "fontSize": 11, "foregroundColor": C_HITAM},
            "basicChart": {
                "chartType": "BAR",
                "legendPosition": "NO_LEGEND",
                "axis": [
                    {"position": "BOTTOM_AXIS", "title": "USD/kg"},
                    {"position": "LEFT_AXIS",   "title": ""},
                ],
                "domains": [{"domain": {"sourceRange": {"sources": [domain_rng]}}}],
                "series":  [{"series": {"sourceRange": {"sources": [series_rng]}},
                             "targetAxis": "BOTTOM_AXIS", "color": color}],
                "headerCount": 0,
            }
        },
        "position": {"overlayPosition": {
            "anchorCell": {"sheetId": sid, "rowIndex": anchor_row, "columnIndex": anchor_col},
            "widthPixels": w, "heightPixels": h}}}}}


# ── Layout (0-indexed) ───────────────────────────────────────────────────────
# R0  : Header utama
# R1  : Sub-header
# R2  : Tanggal & sumber
# R3  : spacer
# R4  : Section A — HARGA TAMBAK
# R5  : Header kolom tambak
# R6-9: Data tambak (4 baris)
# R10 : spacer
# R11 : Section B — HARGA INTERNASIONAL
# R12 : Header kolom intl
# R13-17: Data intl (5 baris)
# R18 : spacer
# R19 : Section C — HIGHLIGHT PASAR
# R20-21: Highlights (2 baris × 2 kolom)
# R22 : spacer
# R23 : Footer
# ─────────────────────────────────────────────────────────────────────────────

DATA = [
    ["PT AGRINAS JALADRI NUSANTARA (AJN)"],                                   # R0
    ["MARKET WATCH  |  HARGA UDANG VANAME (Litopenaeus vannamei)"],            # R1
    [f"Update: {TANGGAL}   |   Sumber: JALA Tech · UCN Global Shrimp Index · SeafoodSource · FRED St. Louis"],  # R2
    [""],                                                                       # R3 spacer
    ["HARGA TAMBAK INDONESIA (Rp/kg)"],                                        # R4
    ["Ukuran", "Harga Min", "Harga Maks", "Rata-rata", "Tren"],               # R5
    ["Size 50",   60000, 65000, 62500, "+1% s/d +3%"],                        # R6
    ["Size 60",   55000, 60000, 57500, "Stabil"],                             # R7
    ["Size 70",   50000, 55000, 52500, "Stabil"],                             # R8
    ["Size 100",  40000, 45000, 42500, "Stabil"],                             # R9
    [""],                                                                       # R10 spacer
    ["HARGA PASAR INTERNASIONAL (Referensi Maret 2026)"],                      # R11
    ["Negara / Sumber", "Ref. Size", "Harga (USD/kg)", "Keterangan"],         # R12
    ["Vietnam (Delta Mekong)",  "Size 30",    5.70, "Turun 8-12% pasca Imlek"],   # R13
    ["China (Guangdong)",       "Size 60",    5.80, "Turun >10% mom"],            # R14
    ["India (Andhra Pradesh)",  "Size 60",    3.64, "Naik 3%"],                   # R15
    ["Ekuador",                 "Size 30-40", 3.60, "Turun 11% mom"],             # R16
    ["Rata-rata Global (UCN)",  "Size 60",    3.55, "Turun 5,6% YoY — benchmark"],# R17
    [""],                                                                       # R18 spacer
    ["HIGHLIGHT PASAR"],                                                        # R19
    ["Harga global turun 5,6% YoY (Maret 2026). Tekanan pasca musim liburan.",
     "", "Indonesia relatif stabil vs China (-10%) dan Ekuador (-11%).", ""],  # R20
    ["Produksi diperkirakan meningkat April-Mei (size 60-70). Potensi tekanan harga.",
     "", "Rekomendasi: Pertimbangkan posisi jual sebelum panen massal Apr-Mei.", ""], # R21
    [""],                                                                       # R22 spacer
    ["Dibuat otomatis oleh Market Watch AJN   |   Data bersifat indikatif, bukan harga resmi."],  # R23
]


def build_requests(sid):
    reqs = []

    # ── Dimensi kolom & baris ────────────────────────────────────────────────
    for c, px in [(0, 165), (1, 125), (2, 125), (3, 125), (4, 150), (5, 18)]:
        reqs.append(col_px(sid, c, c+1, px))

    reqs += [
        row_px(sid,  0,  1, 52),   # header utama
        row_px(sid,  1,  2, 40),   # sub-header
        row_px(sid,  2,  3, 28),   # tanggal
        row_px(sid,  3,  4, 10),   # spacer
        row_px(sid,  4,  5, 32),   # section A
        row_px(sid,  5,  6, 28),   # header kolom
        row_px(sid,  6, 10, 26),   # data tambak
        row_px(sid, 10, 11, 10),   # spacer
        row_px(sid, 11, 12, 32),   # section B
        row_px(sid, 12, 13, 28),   # header kolom
        row_px(sid, 13, 18, 26),   # data intl
        row_px(sid, 18, 19, 10),   # spacer
        row_px(sid, 19, 20, 32),   # section C
        row_px(sid, 20, 22, 54),   # highlights
        row_px(sid, 22, 23, 10),   # spacer
        row_px(sid, 23, 24, 24),   # footer
    ]

    # ── Merge ────────────────────────────────────────────────────────────────
    reqs += [
        merge(sid,  0,  1, 0, 6),   # header utama
        merge(sid,  1,  2, 0, 6),   # sub-header
        merge(sid,  2,  3, 0, 6),   # tanggal
        merge(sid,  4,  5, 0, 5),   # section A header
        merge(sid, 11, 12, 0, 4),   # section B header
        merge(sid, 19, 20, 0, 5),   # section C header
        merge(sid, 20, 21, 0, 2),   # highlight R20 kiri
        merge(sid, 20, 21, 2, 5),   # highlight R20 kanan
        merge(sid, 21, 22, 0, 2),   # highlight R21 kiri
        merge(sid, 21, 22, 2, 5),   # highlight R21 kanan
        merge(sid, 23, 24, 0, 6),   # footer
    ]

    # ── Format ───────────────────────────────────────────────────────────────
    # Header & sub-header
    reqs.append(fmt(sid, 0, 1, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True,
                    size=14, halign="CENTER", valign="MIDDLE"))
    reqs.append(fmt(sid, 1, 2, 0, 6, bg=C_BIRU_MUDA, fg=C_PUTIH, bold=True,
                    size=12, halign="CENTER", valign="MIDDLE"))
    reqs.append(fmt(sid, 2, 3, 0, 6, bg=C_KREM, size=9,
                    halign="CENTER", valign="MIDDLE"))

    # Section A — Tambak
    reqs.append(fmt(sid, 4, 5, 0, 5, bg=C_EMAS, fg=C_HITAM, bold=True,
                    size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid, 5, 6, 0, 5, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True,
                    size=10, halign="CENTER", valign="MIDDLE"))
    for i in range(4):
        r = 6 + i
        bg = C_BIRU_PALE if i % 2 == 0 else C_PUTIH
        reqs.append(fmt(sid, r, r+1, 0, 5, bg=bg, size=10, valign="MIDDLE"))
        reqs.append(fmt(sid, r, r+1, 0, 1, bold=True))
        reqs.append(fmt(sid, r, r+1, 1, 5, halign="CENTER"))

    # Section B — Internasional
    reqs.append(fmt(sid, 11, 12, 0, 4, bg=C_EMAS, fg=C_HITAM, bold=True,
                    size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid, 12, 13, 0, 4, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True,
                    size=10, halign="CENTER", valign="MIDDLE"))
    for i in range(5):
        r = 13 + i
        bg = C_HIJAU_PALE if i % 2 == 0 else C_PUTIH
        reqs.append(fmt(sid, r, r+1, 0, 4, bg=bg, size=10, valign="MIDDLE"))
        reqs.append(fmt(sid, r, r+1, 2, 3, halign="CENTER"))

    # Section C — Highlights
    reqs.append(fmt(sid, 19, 20, 0, 5, bg=C_BIRU_TUA, fg=C_PUTIH, bold=True,
                    size=11, halign="LEFT", valign="MIDDLE"))
    reqs.append(fmt(sid, 20, 22, 0, 2, bg=C_KREM, size=10,
                    valign="MIDDLE", wrap="WRAP"))
    reqs.append(fmt(sid, 20, 22, 2, 5, bg=C_HIJAU_PALE, size=10,
                    valign="MIDDLE", wrap="WRAP"))

    # Footer
    reqs.append(fmt(sid, 23, 24, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, size=9,
                    halign="CENTER", valign="MIDDLE"))

    # ── Border ───────────────────────────────────────────────────────────────
    reqs.append(border_box(sid,  5, 10, 0, 5))   # tabel tambak
    reqs.append(border_box(sid, 12, 18, 0, 4))   # tabel intl

    # ── Format angka ─────────────────────────────────────────────────────────
    reqs.append(num_fmt(sid,  6, 10, 1, 4, '#,##0'))       # IDR
    reqs.append(num_fmt(sid, 13, 18, 2, 3, '#,##0.00'))    # USD

    # ── Charts ───────────────────────────────────────────────────────────────
    # Chart 1 — Column chart harga tambak (anchor G5)
    reqs.append(chart_column(
        sid,
        title="Harga Rata-rata Tambak per Ukuran (Rp/kg)",
        domain_rng=rng(sid, 6, 10, 0, 1),   # A7:A10 — ukuran
        series_rng=rng(sid, 6, 10, 3, 4),   # D7:D10 — rata-rata
        anchor_row=4, anchor_col=6,
        color=C_BIRU_MUDA,
        left_title="Rp/kg",
    ))

    # Chart 2 — Horizontal bar harga internasional (anchor G12)
    reqs.append(chart_bar(
        sid,
        title="Harga Internasional per Negara (USD/kg)",
        domain_rng=rng(sid, 13, 18, 0, 1),  # A14:A18 — negara
        series_rng=rng(sid, 13, 18, 2, 3),  # C14:C18 — harga USD
        anchor_row=11, anchor_col=6,
        color=C_EMAS,
    ))

    return reqs


def main():
    print("=== Market Watch AJN -- Buat Infografis ===\n")

    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    ss = client.open_by_key(SPREADSHEET_ID)
    print(f"Spreadsheet '{ss.title}' dibuka.")

    # Hapus sheet lama jika ada, buat baru
    try:
        ss.del_worksheet(ss.worksheet(SHEET_NAME))
        print(f"Sheet lama '{SHEET_NAME}' dihapus.")
    except gspread.exceptions.WorksheetNotFound:
        pass

    ws = ss.add_worksheet(title=SHEET_NAME, rows=30, cols=15)
    sid = ws.id
    print(f"Sheet '{SHEET_NAME}' dibuat (id={sid}).")

    # Tulis data
    ws.update(DATA, "A1", value_input_option="USER_ENTERED")
    print("Data berhasil ditulis.")

    # Terapkan formatting + chart
    reqs = [r for r in build_requests(sid) if r is not None]
    ss.batch_update({"requests": reqs})
    print("Formatting dan chart diterapkan.")

    print(f"\nInfografis selesai!")
    print(f"Lihat: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    main()
