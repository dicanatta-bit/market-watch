"""
Market Watch - AJN
Generate laporan mingguan PDF 1 halaman setiap Senin setelah update harga.
Simpan ke /output/MarketWatch_AJN_[TANGGAL].pdf
"""

import sys
import os
from datetime import date, datetime
from google.oauth2.service_account import Credentials
import gspread
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"
CREDENTIALS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
OUTPUT_DIR = "output"

_BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
          "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
_today = date.today()
TANGGAL_ID = f"{_today.day} {_BULAN[_today.month]} {_today.year}"
TANGGAL_FILE = _today.strftime("%Y%m%d")

# Warna AJN
C_BIRU_TUA  = colors.HexColor("#065072")
C_BIRU_MUDA = colors.HexColor("#0E7EA0")
C_EMAS      = colors.HexColor("#F2A619")
C_ABU_PALE  = colors.HexColor("#F5F5F5")
C_PUTIH     = colors.white
C_HITAM     = colors.HexColor("#1A1A1A")
C_MERAH     = colors.HexColor("#C0392B")
C_KUNING    = colors.HexColor("#D4A017")
C_BIRU_ALRT = colors.HexColor("#2980B9")


# ── Google Sheets helpers ─────────────────────────────────────────────────────

def open_spreadsheet():
    creds  = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.Client(auth=creds)
    return client.open_by_key(SPREADSHEET_ID)


def get_latest_prices(ss):
    """
    Baca harga terbaru per komoditas+size dari 'Harga Komoditas'.
    Returns list of dicts, satu per komoditas+size.
    """
    try:
        ws   = ss.worksheet("Harga Komoditas")
        rows = ws.get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        return []

    if not rows or len(rows) < 2:
        return []

    # Indeks berdasarkan header baru (14 kolom)
    latest = {}
    for row in rows[1:]:
        if len(row) < 6:
            continue
        key = (row[1], row[2])   # (komoditas, size)
        latest[key] = row        # overwrite — baris terakhir = terbaru

    result = []
    for (komoditas, size), row in latest.items():
        result.append({
            "komoditas":   komoditas,
            "size":        size,
            "tambak":      row[3] if len(row) > 3 else "—",
            "ekspor":      row[4] if len(row) > 4 else "—",
            "pct_minggu":  row[9] if len(row) > 9 else "",
            "kepercayaan": row[12] if len(row) > 12 else "Estimasi",
        })
    return result


def get_today_alerts(ss):
    """Baca alert hari ini dari 'Alert Log'. Returns list of dicts."""
    try:
        ws   = ss.worksheet("Alert Log")
        rows = ws.get_all_values()
    except gspread.exceptions.WorksheetNotFound:
        return []

    today_str = _today.strftime("%d/%m/%Y")
    result = []
    for row in rows[1:]:
        if not row or row[0] != today_str:
            continue
        result.append({
            "komoditas": row[1] if len(row) > 1 else "",
            "jenis":     row[2] if len(row) > 2 else "",
            "sebelum":   row[3] if len(row) > 3 else "",
            "sekarang":  row[4] if len(row) > 4 else "",
            "pct":       row[5] if len(row) > 5 else "",
            "rekomendasi": row[6] if len(row) > 6 else "",
        })
    return result


# ── PDF builder ───────────────────────────────────────────────────────────────

def _style(name, **kwargs):
    base = {
        "fontName": "Helvetica",
        "fontSize": 10,
        "textColor": C_HITAM,
        "leading": 14,
    }
    base.update(kwargs)
    return ParagraphStyle(name, **base)


def build_pdf(prices, alerts, out_path):
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    W = A4[0] - 3.6 * cm   # lebar konten

    s_title    = _style("title",    fontName="Helvetica-Bold", fontSize=16,
                        textColor=C_PUTIH, alignment=TA_CENTER, leading=20)
    s_sub      = _style("sub",      fontName="Helvetica-Bold", fontSize=11,
                        textColor=C_PUTIH, alignment=TA_CENTER)
    s_date     = _style("date",     fontSize=9, textColor=C_PUTIH,
                        alignment=TA_CENTER)
    s_section  = _style("section",  fontName="Helvetica-Bold", fontSize=10,
                        textColor=C_PUTIH)
    s_normal   = _style("normal",   fontSize=9)
    s_small    = _style("small",    fontSize=8, textColor=colors.HexColor("#555555"))
    s_alert_hd = _style("alert_hd", fontName="Helvetica-Bold", fontSize=9,
                        textColor=C_HITAM)
    s_footer   = _style("footer",   fontSize=7.5,
                        textColor=colors.HexColor("#777777"), alignment=TA_CENTER)

    story = []

    # ── Header block ─────────────────────────────────────────────────────────
    hdr_data = [[
        Paragraph("PT AGRINAS JALADRI NUSANTARA (Persero)", s_title),
    ], [
        Paragraph("LAPORAN MINGGUAN — MARKET WATCH KOMODITAS PERIKANAN", s_sub),
    ], [
        Paragraph(f"Tanggal: {TANGGAL_ID}   |   Periode: Mingguan   |   Konfidensial", s_date),
    ]]
    hdr = Table(hdr_data, colWidths=[W])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BIRU_TUA),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.3 * cm))

    # ── Tabel harga ──────────────────────────────────────────────────────────
    sec1 = Table([[Paragraph("  HARGA KOMODITAS TERKINI", s_section)]], colWidths=[W])
    sec1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BIRU_MUDA),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sec1)

    col_w = [W * 0.36, W * 0.14, W * 0.20, W * 0.17, W * 0.13]
    tbl_head = [
        Paragraph("<b>Komoditas</b>", s_normal),
        Paragraph("<b>Size/Grade</b>", s_normal),
        Paragraph("<b>Harga Tambak (Rp/kg)</b>", s_normal),
        Paragraph("<b>Harga Ekspor (USD/kg)</b>", s_normal),
        Paragraph("<b>% Minggu Lalu</b>", s_normal),
    ]
    tbl_data = [tbl_head]

    for i, p in enumerate(prices):
        bg = C_ABU_PALE if i % 2 == 0 else C_PUTIH
        pct_str = p["pct_minggu"]
        if pct_str.startswith("+"):
            pct_cell = Paragraph(f'<font color="#27AE60"><b>{pct_str}</b></font>', s_normal)
        elif pct_str.startswith("-"):
            pct_cell = Paragraph(f'<font color="#E74C3C"><b>{pct_str}</b></font>', s_normal)
        else:
            pct_cell = Paragraph(pct_str or "—", s_normal)

        tbl_data.append([
            Paragraph(p["komoditas"][:55], s_normal),
            Paragraph(p["size"],           s_normal),
            Paragraph(p["tambak"],         s_normal),
            Paragraph(p["ekspor"],         s_normal),
            pct_cell,
        ])

    price_tbl = Table(tbl_data, colWidths=col_w, repeatRows=1)
    price_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), C_BIRU_TUA),
        ("TEXTCOLOR",    (0, 0), (-1, 0), C_PUTIH),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_ABU_PALE, C_PUTIH]),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(price_tbl)
    story.append(Spacer(1, 0.35 * cm))

    # ── Alert ─────────────────────────────────────────────────────────────────
    sec2 = Table([[Paragraph("  ALERT AKTIF HARI INI", s_section)]], colWidths=[W])
    sec2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BIRU_MUDA),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sec2)

    if not alerts:
        story.append(Paragraph(
            "Tidak ada alert aktif hari ini. Semua harga dalam batas normal.",
            s_normal,
        ))
    else:
        alt_col_w = [W * 0.18, W * 0.28, W * 0.12, W * 0.42]
        alt_head = [
            Paragraph("<b>Jenis</b>",       s_normal),
            Paragraph("<b>Komoditas</b>",   s_normal),
            Paragraph("<b>% Perubahan</b>", s_normal),
            Paragraph("<b>Rekomendasi</b>", s_normal),
        ]
        alt_data = [alt_head]
        for a in alerts:
            jenis = a["jenis"]
            if "MERAH" in jenis:
                color_hex = "#C0392B"
            elif "KUNING" in jenis:
                color_hex = "#B7950B"
            else:
                color_hex = "#1A5276"
            alt_data.append([
                Paragraph(f'<font color="{color_hex}"><b>{jenis[:20]}</b></font>', s_small),
                Paragraph(a["komoditas"][:40], s_small),
                Paragraph(f'<b>{a["pct"]}</b>', s_small),
                Paragraph(a["rekomendasi"][:120], s_small),
            ])
        alt_tbl = Table(alt_data, colWidths=alt_col_w, repeatRows=1)
        alt_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), C_BIRU_TUA),
            ("TEXTCOLOR",    (0, 0), (-1, 0), C_PUTIH),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_ABU_PALE, C_PUTIH]),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(alt_tbl)

    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width=W, thickness=0.5, color=C_BIRU_TUA))
    story.append(Spacer(1, 0.15 * cm))

    # ── Catatan & footer ──────────────────────────────────────────────────────
    notes = (
        "<b>Catatan:</b> Data bersifat indikatif berdasarkan sumber JALA Tech, UCN, KKP, ASTUIN, "
        "BPS, dan portal perikanan Indonesia. Harga dapat berubah tanpa pemberitahuan. "
        "Laporan ini dibuat secara otomatis oleh sistem Market Watch AJN."
    )
    story.append(Paragraph(notes, s_small))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"PT Agrinas Jaladri Nusantara (Persero)  |  Market Watch AJN  |  "
        f"Diterbitkan: {datetime.now().strftime('%d/%m/%Y %H:%M')} WIB  |  RAHASIA",
        s_footer,
    ))

    doc.build(story)
    print(f"PDF berhasil dibuat: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Market Watch AJN -- Laporan Mingguan PDF ===\n")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    out_path = os.path.join(OUTPUT_DIR, f"MarketWatch_AJN_{TANGGAL_FILE}.pdf")

    print("Menghubungkan ke Google Sheets...")
    ss = open_spreadsheet()
    print(f"Spreadsheet '{ss.title}' dibuka.")

    prices = get_latest_prices(ss)
    alerts = get_today_alerts(ss)

    print(f"Data harga: {len(prices)} komoditas | Alert aktif: {len(alerts)}")

    if not prices:
        print("[WARN] Tidak ada data harga — laporan dibuat dengan data kosong.")

    build_pdf(prices, alerts, out_path)
    print(f"\nLaporan disimpan: {out_path}")


if __name__ == "__main__":
    main()
