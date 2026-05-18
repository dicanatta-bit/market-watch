"""
Market Watch - AJN
Formatting sheet "Harga Komoditas" dengan gspread:
- Header navy, freeze, lebar kolom otomatis
- Kolom harga rata kanan
- Conditional formatting % Minggu & % 3 Bulan (hijau/merah/abu)
- Alternating row colors
- Baris summary di bawah
Jalankan standalone: python sheet_formatter.py
"""

import sys
import re
from datetime import date
from google.oauth2.service_account import Credentials
import gspread
from gspread.utils import rowcol_to_a1

SPREADSHEET_ID  = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
SHEET_NAME      = "Harga Komoditas"
CREDS_FILE      = "credentials.json"
SCOPES          = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ── Kolom (0-indexed) ────────────────────────────────────────────────────────
# 0  Tanggal
# 1  Komoditas
# 2  Size
# 3  Harga Tambak (Rp/kg)
# 4  Harga Ekspor (USD/kg)
# 5  Harga Internasional (USD/kg)
# 6  Harga Minggu Lalu (Rp/kg)
# 7  Harga 1 Bulan Lalu (Rp/kg)
# 8  Harga 3 Bulan Lalu (Rp/kg)
# 9  % vs Minggu Lalu
# 10 % vs 3 Bulan Lalu
# 11 Sumber
# 12 Tingkat Kepercayaan
# 13 Catatan

PRICE_COLS      = [3, 4, 5, 6, 7, 8]   # rata kanan
PCT_COL_MINGGU  = 9
PCT_COL_3BULAN  = 10
TOTAL_COLS      = 14   # A–N


def _rgb(r, g, b):
    return {"red": r / 255, "green": g / 255, "blue": b / 255}


C_NAVY      = _rgb(27,  58, 107)   # #1B3A6B
C_WHITE     = _rgb(255, 255, 255)
C_GREY_ROW  = _rgb(248, 249, 250)  # #F8F9FA alternating row
C_GREY_HDR  = _rgb(233, 236, 239)  # header separator row

C_GREEN_TXT = _rgb(30,  126,  52)  # #1E7E34
C_GREEN_BG  = _rgb(212, 237, 218)  # #D4EDDA
C_RED_TXT   = _rgb(114,  28,  36)  # #721C24
C_RED_BG    = _rgb(248, 215, 218)  # #F8D7DA
C_GREY_TXT  = _rgb(108, 117, 125)  # #6C757D

C_GOLD      = _rgb(201, 168,  76)  # #C9A84C summary row


# ── gspread batchUpdate helper ────────────────────────────────────────────────

def _rng(sid, r1, r2, c1, c2):
    return {
        "sheetId": sid,
        "startRowIndex": r1, "endRowIndex": r2,
        "startColumnIndex": c1, "endColumnIndex": c2,
    }


def _fmt(sid, r1, r2, c1, c2, *, bg=None, fg=None, bold=None,
         size=None, halign=None, valign=None, wrap=None):
    cell, flds = {}, []
    if bg is not None:
        cell["backgroundColor"] = bg; flds.append("backgroundColor")
    tf, tf_f = {}, []
    if bold is not None: tf["bold"] = bold;           tf_f.append("bold")
    if size is not None: tf["fontSize"] = size;       tf_f.append("fontSize")
    if fg   is not None: tf["foregroundColor"] = fg;  tf_f.append("foregroundColor")
    if tf:
        cell["textFormat"] = tf
        flds.append(f"textFormat({','.join(tf_f)})")
    if valign is not None: cell["verticalAlignment"]   = valign; flds.append("verticalAlignment")
    if halign is not None: cell["horizontalAlignment"] = halign; flds.append("horizontalAlignment")
    if wrap   is not None: cell["wrapStrategy"]        = wrap;   flds.append("wrapStrategy")
    if not flds:
        return None
    return {"repeatCell": {
        "range": _rng(sid, r1, r2, c1, c2),
        "cell": {"userEnteredFormat": cell},
        "fields": "userEnteredFormat(" + ",".join(flds) + ")",
    }}


def _col_px(sid, c1, c2, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "COLUMNS",
                  "startIndex": c1, "endIndex": c2},
        "properties": {"pixelSize": px}, "fields": "pixelSize",
    }}


def _freeze(sid, rows=1, cols=1):
    return {"updateSheetProperties": {
        "properties": {
            "sheetId": sid,
            "gridProperties": {"frozenRowCount": rows, "frozenColumnCount": cols},
        },
        "fields": "gridProperties.frozenRowCount,gridProperties.frozenColumnCount",
    }}


def _cond_fmt(sid, r1, r2, c, positive=True):
    """
    Conditional formatting satu kolom persen.
    positive=True  → sel > 0 → hijau
    positive=False → sel < 0 → merah
    """
    condition_type = "NUMBER_GREATER" if positive else "NUMBER_LESS"
    value = "0"
    bg  = C_GREEN_BG  if positive else C_RED_BG
    fg  = C_GREEN_TXT if positive else C_RED_TXT
    return {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [_rng(sid, r1, r2, c, c + 1)],
                "booleanRule": {
                    "condition": {
                        "type": condition_type,
                        "values": [{"userEnteredValue": value}],
                    },
                    "format": {
                        "backgroundColor": bg,
                        "textFormat": {"foregroundColor": fg, "bold": True},
                    },
                },
            },
            "index": 0,
        }
    }


def _parse_pct(s):
    """Konversi string pct ke float. '+ 3,5%' → 3.5."""
    if not s or str(s).strip() in ("", "—", "-"):
        return None
    s = re.sub(r"[%\s]", "", str(s)).replace(",", ".").replace("+", "")
    try:
        return float(s)
    except ValueError:
        return None


def apply_sheet_formatting(ss=None):
    """
    Terapkan formatting lengkap ke sheet 'Harga Komoditas'.
    Dapat dipanggil dari script lain atau dijalankan standalone.
    """
    if ss is None:
        creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        client = gspread.Client(auth=creds)
        ss     = client.open_by_key(SPREADSHEET_ID)

    print(f"  Membuka sheet '{SHEET_NAME}'...")
    try:
        ws = ss.worksheet(SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print(f"  [SKIP] Sheet '{SHEET_NAME}' belum ada — lewati formatting.")
        return

    sid  = ws.id
    rows = ws.get_all_values()
    n    = len(rows)   # total baris termasuk header

    if n < 2:
        print(f"  [SKIP] Sheet '{SHEET_NAME}' kosong — lewati formatting.")
        return

    data_rows = n - 1   # baris data (tanpa header)
    summary_row = n     # 0-indexed: n  (baris berikutnya setelah data)

    # ── 1. Tambahkan baris summary ───────────────────────────────────────────
    pct_minggu_vals = []
    for row in rows[1:]:
        v = _parse_pct(row[PCT_COL_MINGGU] if len(row) > PCT_COL_MINGGU else "")
        if v is not None:
            pct_minggu_vals.append(v)

    jumlah_komoditas = data_rows
    rata_pct = (sum(pct_minggu_vals) / len(pct_minggu_vals)) if pct_minggu_vals else 0
    tanggal_update = date.today().strftime("%d/%m/%Y")

    summary_label = f"SUMMARY — {tanggal_update}  |  Total: {jumlah_komoditas} komoditas  |  Rata-rata % Minggu Ini: {rata_pct:+.2f}%"
    # Tulis satu sel karena merge akan menutupi kolom lain
    summary_cell = rowcol_to_a1(n + 1, 1)   # baris n+1 (1-indexed)
    ws.update([[summary_label] + [""] * (TOTAL_COLS - 1)],
              f"A{n + 1}", value_input_option="RAW")
    print(f"  Baris summary ditambahkan di baris {n + 1}.")

    # ── 2. Bangun request batch formatting ───────────────────────────────────
    reqs = []

    # Freeze baris 1 dan kolom A
    reqs.append(_freeze(sid, rows=1, cols=1))

    # Lebar kolom (px)
    col_widths = {
        0: 90,   # Tanggal
        1: 200,  # Komoditas
        2: 130,  # Size
        3: 145,  # Tambak
        4: 140,  # Ekspor
        5: 155,  # Internasional
        6: 155,  # Minggu Lalu
        7: 155,  # 1 Bulan Lalu
        8: 155,  # 3 Bulan Lalu
        9: 120,  # % Minggu
        10: 120, # % 3 Bulan
        11: 150, # Sumber
        12: 130, # Kepercayaan
        13: 200, # Catatan
    }
    for c, px in col_widths.items():
        reqs.append(_col_px(sid, c, c + 1, px))

    # Header row (baris 0): navy bg, putih bold, size 11
    reqs.append(_fmt(sid, 0, 1, 0, TOTAL_COLS,
                     bg=C_NAVY, fg=C_WHITE, bold=True, size=11,
                     halign="CENTER", valign="MIDDLE"))

    # Alternating row colors (baris data 1..n-1)
    for i in range(data_rows):
        r  = i + 1
        bg = C_WHITE if i % 2 == 0 else C_GREY_ROW
        reqs.append(_fmt(sid, r, r + 1, 0, TOTAL_COLS, bg=bg, valign="MIDDLE"))

    # Kolom harga → rata kanan
    for c in PRICE_COLS:
        reqs.append(_fmt(sid, 1, n, c, c + 1, halign="RIGHT"))

    # Kolom % → rata tengah, default abu-abu (nol)
    for c in [PCT_COL_MINGGU, PCT_COL_3BULAN]:
        reqs.append(_fmt(sid, 1, n, c, c + 1,
                         halign="CENTER", fg=C_GREY_TXT))

    # Baris summary (0-indexed: n)
    reqs.append(_fmt(sid, n, n + 1, 0, TOTAL_COLS,
                     bg=C_GOLD, fg=C_WHITE, bold=True, size=10,
                     halign="LEFT", valign="MIDDLE"))

    # ── 3. Hapus conditional formatting lama dulu ────────────────────────────
    # Hapus dari indeks tertinggi ke terendah agar indeks tidak bergeser saat batch
    current_meta = ss.fetch_sheet_metadata()
    cf_delete_reqs = []
    for sheet in current_meta.get("sheets", []):
        if sheet["properties"]["sheetId"] == sid:
            existing_cf = sheet.get("conditionalFormats", [])
            for idx in reversed(range(len(existing_cf))):
                cf_delete_reqs.append({
                    "deleteConditionalFormatRule": {"sheetId": sid, "index": idx}
                })
            break

    # CF delete harus di depan agar formatting baru tidak kena hapus
    reqs_clean = cf_delete_reqs + [r for r in reqs if r is not None]

    # ── 4. Terapkan batch format ─────────────────────────────────────────────
    if reqs_clean:
        ss.batch_update({"requests": reqs_clean})
    print(f"  Formatting dasar diterapkan ({len(reqs_clean)} requests).")

    # ── 5. Conditional formatting % (tambahkan setelah CF lama dihapus) ─────
    cf_reqs = []
    for c in [PCT_COL_MINGGU, PCT_COL_3BULAN]:
        cf_reqs.append(_cond_fmt(sid, 1, n, c, positive=True))   # >0 hijau
        cf_reqs.append(_cond_fmt(sid, 1, n, c, positive=False))  # <0 merah
    ss.batch_update({"requests": cf_reqs})
    print(f"  Conditional formatting % diterapkan.")

    print(f"  Sheet '{SHEET_NAME}' selesai diformat. ({data_rows} baris data + 1 summary)")
    return ws


# ── Standalone entry point ────────────────────────────────────────────────────

def main():
    print("=== Sheet Formatter — Market Watch AJN ===\n")
    creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    ss     = client.open_by_key(SPREADSHEET_ID)
    print(f"Spreadsheet '{ss.title}' dibuka.\n")
    apply_sheet_formatting(ss)
    print(f"\nSelesai. Buka sheet di:")
    print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=")


if __name__ == "__main__":
    main()
