"""
Market Watch - AJN
Buat infografis harga semua komoditas perikanan di Google Sheet tab "Infografis"
"""

from datetime import date
from google.oauth2.service_account import Credentials
import gspread

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
SHEET_NAME = "Infografis"
CREDS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
_today = date.today()
TANGGAL = f"{_today.day} {_BULAN[_today.month]} {_today.year}"

# ── Palette warna AJN ─────────────────────────────────────────────────────────
C_BIRU_TUA    = {"red": 0.02, "green": 0.27, "blue": 0.45}
C_BIRU_MUDA   = {"red": 0.06, "green": 0.49, "blue": 0.63}
C_HIJAU_TUA   = {"red": 0.08, "green": 0.37, "blue": 0.20}
C_BIRU_PALE   = {"red": 0.88, "green": 0.95, "blue": 0.98}
C_HIJAU_PALE  = {"red": 0.87, "green": 0.96, "blue": 0.89}
C_ORANGE_PALE = {"red": 1.00, "green": 0.93, "blue": 0.82}
C_KREM        = {"red": 1.00, "green": 0.97, "blue": 0.88}
C_PUTIH       = {"red": 1.00, "green": 1.00, "blue": 1.00}
C_HITAM       = {"red": 0.10, "green": 0.10, "blue": 0.10}
C_ABU         = {"red": 0.40, "green": 0.40, "blue": 0.40}

# ── Layout (0-indexed) ────────────────────────────────────────────────────────
# R0       : Header AJN
# R1       : Subtitle
# R2       : Tanggal & sumber
# R3       : spacer
# R4       : Section A — BUDIDAYA (header)
# R5       : Header kolom A
# R6–R12   : Data budidaya (vaname ×4, windu ×2, nila ×1)
# R13      : spacer
# R14      : Section B — PERIKANAN TANGKAP (header)
# R15      : Header kolom B
# R16–R21  : Data tangkap (yellowfin ×2, cakalang ×1, kakap ×1, kerapu ×2)
# R22      : spacer
# R23      : Highlight header
# R24–R25  : Highlight rows (kiri A:B, kanan C:F)
# R26      : spacer
# R27      : Footer
# ─────────────────────────────────────────────────────────────────────────────

DATA = [
    # R0
    ["PT AGRINAS JALADRI NUSANTARA (AJN)", "", "", "", "", ""],
    # R1
    ["MARKET WATCH  |  HARGA KOMODITAS PERIKANAN STRATEGIS", "", "", "", "", ""],
    # R2
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
     "Produksi terbatas; harga premium vs vaname. Dominan dari Sulawesi & Kalimantan.", ""],
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
    # R18  Tuna Cakalang
    ["Tuna Cakalang", "—", "15.000 – 25.000", "1,50 – 2,50",
     "Bahan baku utama pengalengan. Harga dipengaruhi musim tangkapan.", ""],
    # R19  Kakap Merah
    ["Kakap Merah", "—", "50.000 – 70.000", "5,00 – 8,00",
     "Permintaan ekspor ke China & Singapura tinggi dan stabil.", ""],
    # R20–R21  Kerapu
    ["Kerapu", "Hidup (>500 g)", "100.000 – 150.000", "8,00 – 12,00",
     "Ekspor hidup ke China dominan. Harga sangat sensitif terhadap permintaan China.", ""],
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

    # R27 Footer
    ["Dibuat otomatis oleh Market Watch AJN   |   Data bersifat indikatif, bukan harga resmi.",
     "", "", "", "", ""],
]


# ── Helper builders ───────────────────────────────────────────────────────────

def rng(sid, r1, r2, c1, c2):
    return {"sheetId": sid,
            "startRowIndex": r1, "endRowIndex": r2,
            "startColumnIndex": c1, "endColumnIndex": c2}


def fmt(sid, r1, r2, c1, c2, bg=None, fg=None, bold=None, size=None,
        halign=None, valign=None, wrap=None):
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
        "range": {"sheetId": sid, "dimension": "COLUMNS",
                  "startIndex": c1, "endIndex": c2},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}


def row_px(sid, r1, r2, px):
    return {"updateDimensionProperties": {
        "range": {"sheetId": sid, "dimension": "ROWS",
                  "startIndex": r1, "endIndex": r2},
        "properties": {"pixelSize": px}, "fields": "pixelSize"}}


def border_box(sid, r1, r2, c1, c2, color=None, style="SOLID"):
    color = color or C_ABU
    b = {"style": style, "colorStyle": {"rgbColor": color}}
    return {"updateBorders": {
        "range": rng(sid, r1, r2, c1, c2),
        "top": b, "bottom": b, "left": b, "right": b,
        "innerHorizontal": b, "innerVertical": b}}


def build_requests(sid):
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
        row_px(sid, 24, 26, 52),   # highlight rows
        row_px(sid, 26, 27,  8),   # spacer
        row_px(sid, 27, 28, 22),   # footer
    ]

    # ── Merge ────────────────────────────────────────────────────────────────
    reqs += [
        merge(sid,  0,  1, 0, 6),   # header AJN
        merge(sid,  1,  2, 0, 6),   # subtitle
        merge(sid,  2,  3, 0, 6),   # tanggal
        merge(sid,  4,  5, 0, 6),   # section A
        merge(sid, 14, 15, 0, 6),   # section B
        merge(sid, 23, 24, 0, 6),   # highlight header
        merge(sid, 24, 25, 0, 2),   # highlight R24 kiri
        merge(sid, 24, 25, 2, 6),   # highlight R24 kanan
        merge(sid, 25, 26, 0, 2),   # highlight R25 kiri
        merge(sid, 25, 26, 2, 6),   # highlight R25 kanan
        merge(sid, 27, 28, 0, 6),   # footer
    ]

    # ── Header & meta ────────────────────────────────────────────────────────
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
    for i in range(7):                   # R6–R12
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
    for i in range(6):                   # R16–R21
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

    # ── Footer ───────────────────────────────────────────────────────────────
    reqs.append(fmt(sid, 27, 28, 0, 6, bg=C_BIRU_TUA, fg=C_PUTIH, size=9,
                    halign="CENTER", valign="MIDDLE"))

    # ── Border ───────────────────────────────────────────────────────────────
    reqs.append(border_box(sid,  5, 13, 0, 5))   # tabel budidaya (header + 7 data)
    reqs.append(border_box(sid, 15, 22, 0, 5))   # tabel tangkap (header + 6 data)

    return reqs


def main():
    print("=== Market Watch AJN -- Buat Infografis Komprehensif ===\n")

    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    ss = client.open_by_key(SPREADSHEET_ID)
    print(f"Spreadsheet '{ss.title}' dibuka.")

    try:
        ss.del_worksheet(ss.worksheet(SHEET_NAME))
        print(f"Sheet lama '{SHEET_NAME}' dihapus.")
    except gspread.exceptions.WorksheetNotFound:
        pass

    ws = ss.add_worksheet(title=SHEET_NAME, rows=35, cols=10)
    sid = ws.id
    print(f"Sheet '{SHEET_NAME}' dibuat (id={sid}).")

    ws.update(DATA, "A1", value_input_option="RAW")
    print("Data berhasil ditulis.")

    reqs = [r for r in build_requests(sid) if r is not None]
    ss.batch_update({"requests": reqs})
    print("Formatting diterapkan.")

    print(f"\nInfografis selesai!")
    print(f"Lihat: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")


if __name__ == "__main__":
    main()
