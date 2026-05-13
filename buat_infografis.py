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

def _alert_badge(jenis):
    j = str(jenis).upper()
    if "MERAH" in j:  return "badge-red",   "MERAH"
    if "KUNING" in j: return "badge-yellow", "KUNING"
    if "BIRU" in j:   return "badge-blue",   "BIRU"
    return "badge-grey", "INFO"


def generate_html(prices, alerts, out_path):
    """Generate HTML infografis interaktif ke out_path."""

    # Build price rows HTML
    def price_rows(data_list):
        rows = []
        for i, p in enumerate(data_list):
            pct = p.get("pct_minggu", "")
            if pct.startswith("+"):
                pct_html = f'<span class="up">{pct}</span>'
            elif pct.startswith("-"):
                pct_html = f'<span class="down">{pct}</span>'
            else:
                pct_html = pct or "—"
            rows.append(f"""
      <tr class="{'row-alt' if i % 2 else ''}">
        <td class="bold">{p['komoditas']}</td>
        <td class="center">{p['size']}</td>
        <td class="center">{p['tambak']}</td>
        <td class="center">{p['ekspor']}</td>
        <td class="center">{pct_html}</td>
        <td class="center badge-{p['kepercayaan'].lower()}">{p['kepercayaan']}</td>
      </tr>""")
        return "".join(rows)

    budidaya = [p for p in prices if any(k in p["komoditas"] for k in
                ["Vaname", "Windu", "Nila"])]
    tangkap  = [p for p in prices if p not in budidaya]

    # Build alert rows HTML
    alert_html = ""
    if not alerts:
        alert_html = '<tr><td colspan="5" class="center muted">Tidak ada alert aktif hari ini.</td></tr>'
    else:
        for a in alerts:
            cls, label = _alert_badge(a.get("jenis", ""))
            alert_html += f"""
      <tr>
        <td><span class="badge {cls}">{label}</span></td>
        <td>{a.get('komoditas', '')}</td>
        <td class="center bold">{a.get('pct', '')}</td>
        <td>{a.get('sebelum', '')} → {a.get('sekarang', '')}</td>
        <td class="small">{a.get('rekomendasi', '')}</td>
      </tr>"""

    # Chart data (harga tambak midpoint untuk komoditas utama)
    chart_labels, chart_values = [], []
    seen = set()
    for p in prices:
        k = p["komoditas"].split("(")[0].strip()[:20]
        s = p["size"]
        key = f"{k} {s}"
        if key not in seen:
            seen.add(key)
            mid = _parse_mid_simple(p["tambak"])
            if mid:
                chart_labels.append(f'"{key}"')
                chart_values.append(str(int(mid)))

    chart_js = ""
    if chart_labels:
        chart_js = f"""
  <script>
    const ctx = document.getElementById('priceChart').getContext('2d');
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: [{', '.join(chart_labels)}],
        datasets: [{{
          label: 'Harga Tambak/Nelayan (Rp/kg)',
          data: [{', '.join(chart_values)}],
          backgroundColor: 'rgba(6,80,114,0.75)',
          borderColor: 'rgba(6,80,114,1)',
          borderWidth: 1
        }}]
      }},
      options: {{
        responsive: true,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          y: {{ beginAtZero: true, ticks: {{ callback: v => 'Rp ' + v.toLocaleString('id') }} }},
          x: {{ ticks: {{ font: {{ size: 10 }} }} }}
        }}
      }}
    }});
  </script>"""

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Market Watch AJN — {TANGGAL}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #1a1a1a; }}
  .header {{ background: #065072; color: #fff; padding: 18px 24px; }}
  .header h1 {{ font-size: 1.35rem; font-weight: 700; }}
  .header p  {{ font-size: 0.82rem; opacity: 0.85; margin-top: 4px; }}
  .container {{ max-width: 1100px; margin: 20px auto; padding: 0 16px; }}
  .card {{ background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.1);
           margin-bottom: 20px; overflow: hidden; }}
  .card-header {{ padding: 10px 16px; font-weight: 700; font-size: 0.9rem; color: #fff; }}
  .bg-blue  {{ background: #065072; }}
  .bg-green {{ background: #145A30; }}
  .bg-red   {{ background: #922B21; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.84rem; }}
  th {{ background: #065072; color: #fff; padding: 8px 10px; text-align: left; font-weight: 600; }}
  td {{ padding: 7px 10px; border-bottom: 1px solid #eee; vertical-align: middle; }}
  .row-alt {{ background: #f7fbfd; }}
  .center {{ text-align: center; }}
  .bold   {{ font-weight: 600; }}
  .small  {{ font-size: 0.78rem; color: #555; }}
  .muted  {{ color: #888; }}
  .up   {{ color: #27AE60; font-weight: 700; }}
  .down {{ color: #E74C3C; font-weight: 700; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px;
            font-size: 0.72rem; font-weight: 700; letter-spacing: .5px; }}
  .badge-red    {{ background: #FADBD8; color: #C0392B; }}
  .badge-yellow {{ background: #FDEBD0; color: #B7950B; }}
  .badge-blue   {{ background: #D6EAF8; color: #1A5276; }}
  .badge-grey   {{ background: #ECF0F1; color: #555; }}
  .badge-tinggi  {{ background: #D5F5E3; color: #1E8449; }}
  .badge-sedang  {{ background: #FDEBD0; color: #B7950B; }}
  .badge-estimasi{{ background: #ECF0F1; color: #777; }}
  .chart-wrap {{ padding: 16px; max-height: 300px; }}
  .footer {{ text-align: center; font-size: 0.75rem; color: #888;
             padding: 14px; margin-top: 10px; }}
</style>
</head>
<body>
<div class="header">
  <h1>PT AGRINAS JALADRI NUSANTARA (AJN)</h1>
  <p>MARKET WATCH &mdash; HARGA KOMODITAS PERIKANAN STRATEGIS &nbsp;|&nbsp; Update: {TANGGAL}</p>
</div>

<div class="container">

  <!-- Chart -->
  <div class="card">
    <div class="card-header bg-blue">Grafik Harga Tambak / Nelayan (Rp/kg) — Semua Komoditas</div>
    <div class="chart-wrap">
      <canvas id="priceChart"></canvas>
    </div>
  </div>

  <!-- Alert -->
  <div class="card">
    <div class="card-header bg-red">Alert Aktif &mdash; {TANGGAL}</div>
    <table>
      <thead><tr>
        <th>Jenis</th><th>Komoditas</th><th>% Perubahan</th>
        <th>Nilai Sebelum → Sekarang</th><th>Rekomendasi</th>
      </tr></thead>
      <tbody>{alert_html}</tbody>
    </table>
  </div>

  <!-- Budidaya -->
  <div class="card">
    <div class="card-header bg-blue">A. Komoditas Budidaya</div>
    <table>
      <thead><tr>
        <th>Komoditas</th><th>Size/Grade</th><th>Harga Tambak (Rp/kg)</th>
        <th>Harga Ekspor (USD/kg)</th><th>% vs Minggu Lalu</th><th>Kepercayaan</th>
      </tr></thead>
      <tbody>{price_rows(budidaya)}</tbody>
    </table>
  </div>

  <!-- Tangkap -->
  <div class="card">
    <div class="card-header bg-green">B. Komoditas Perikanan Tangkap</div>
    <table>
      <thead><tr>
        <th>Komoditas</th><th>Grade/Bentuk</th><th>Harga Nelayan (Rp/kg)</th>
        <th>Harga Ekspor (USD/kg)</th><th>% vs Minggu Lalu</th><th>Kepercayaan</th>
      </tr></thead>
      <tbody>{price_rows(tangkap)}</tbody>
    </table>
  </div>

</div><!-- /container -->

<div class="footer">
  Dibuat otomatis oleh Market Watch AJN &nbsp;&bull;&nbsp;
  Data bersifat indikatif &nbsp;&bull;&nbsp;
  {TANGGAL}
</div>

{chart_js}
</body>
</html>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML infografis disimpan: {out_path}")


def _parse_mid_simple(s):
    """Versi ringan parse_mid untuk HTML generation (tanpa import alert_engine)."""
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Market Watch AJN -- Buat Infografis Komprehensif ===\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    ss     = client.open_by_key(SPREADSHEET_ID)
    print(f"Spreadsheet '{ss.title}' dibuka.")

    # Baca alert hari ini
    today_alerts = alert_engine.get_today_alerts(ss)
    print(f"Alert aktif hari ini: {len(today_alerts)}")

    # Baca harga terbaru untuk HTML
    from laporan_mingguan import get_latest_prices
    prices = get_latest_prices(ss)

    # ── Google Sheet Infografis ──────────────────────────────────────────────
    try:
        ss.del_worksheet(ss.worksheet(SHEET_NAME))
        print(f"Sheet lama '{SHEET_NAME}' dihapus.")
    except gspread.exceptions.WorksheetNotFound:
        pass

    ws  = ss.add_worksheet(title=SHEET_NAME, rows=TOTAL_ROWS + 5, cols=10)
    sid = ws.id
    print(f"Sheet '{SHEET_NAME}' dibuat (id={sid}).")

    data = build_data(today_alerts)
    ws.update(data, "A1", value_input_option="RAW")
    print("Data berhasil ditulis ke GSheet.")

    reqs = [r for r in build_requests(sid, today_alerts) if r is not None]
    ss.batch_update({"requests": reqs})
    print("Formatting diterapkan.")

    # ── HTML export ──────────────────────────────────────────────────────────
    html_path = os.path.join(OUTPUT_DIR, f"MarketWatch_AJN_{TANGGAL_FILE}.html")
    alert_dicts = [
        {
            "jenis":      a[2] if len(a) > 2 else "",
            "komoditas":  a[1] if len(a) > 1 else "",
            "pct":        a[5] if len(a) > 5 else "",
            "sebelum":    a[3] if len(a) > 3 else "",
            "sekarang":   a[4] if len(a) > 4 else "",
            "rekomendasi":a[6] if len(a) > 6 else "",
        }
        for a in today_alerts
    ]
    generate_html(prices, alert_dicts, html_path)

    print(f"\nInfografis selesai!")
    print(f"GSheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"HTML  : {html_path}")


if __name__ == "__main__":
    main()
