"""Authenticated KNMP exports with a consistent filter contract."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import KnmpLocation
from ..auth import get_superadmin
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import tempfile
import os
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

router = APIRouter(tags=["export"])

# ── Mapping provinsi → pulau ──
PROV_WILAYAH = {
    "Sumatera": ["ACEH", "SUMATERA UTARA", "SUMATRA UTARA", "SUMATERA BARAT", "SUMATRA BARAT",
                 "RIAU", "KEPULAUAN RIAU", "JAMBI", "BENGKULU", "SUMATERA SELATAN",
                 "SUMATRA SELATAN", "LAMPUNG", "KEPULAUAN BANGKA BELITUNG", "BANGKA BELITUNG"],
    "Jawa-Bali": ["BANTEN", "DKI JAKARTA", "JAKARTA", "JAWA BARAT", "JAWA TENGAH",
                  "DI YOGYAKARTA", "JAWA TIMUR", "BALI"],
    "Kalimantan": ["KALIMANTAN BARAT", "KALIMANTAN TENGAH", "KALIMANTAN SELATAN",
                   "KALIMANTAN TIMUR", "KALIMANTAN UTARA"],
    "Sulawesi": ["SULAWESI UTARA", "SULAWESI TENGAH", "SULAWESI SELATAN",
                 "SULAWESI TENGGARA", "GORONTALO", "SULAWESI BARAT"],
    "NTT-NTB": ["NUSA TENGGARA BARAT", "NTB", "NUSA TENGGARA TIMUR", "NTT"],
    "Maluku": ["MALUKU", "MALUKU UTARA"],
    "Papua": ["PAPUA", "PAPUA BARAT", "PAPUA SELATAN", "PAPUA TENGAH",
              "PAPUA PEGUNUNGAN", "PAPUA BARAT DAYA", "IRIAN JAYA BARAT"],
}

PULAU_LIST = sorted(PROV_WILAYAH.keys())


def filtered_locations(db, pulau, provinsi):
    prov_filter = set()
    if pulau and pulau.strip() in PROV_WILAYAH:
        prov_filter.update(PROV_WILAYAH[pulau.strip()])
    if provinsi:
        prov_filter.update(p.strip().upper() for p in provinsi)
    query = db.query(KnmpLocation)
    if prov_filter:
        query = query.filter(KnmpLocation.provinsi.in_(list(prov_filter)))
    return query.order_by(KnmpLocation.provinsi, KnmpLocation.kabupaten, KnmpLocation.nama_kampung).all(), prov_filter


def export_label(pulau, prov_filter):
    if pulau:
        return pulau
    return "_".join(sorted(prov_filter)[:3]) if prov_filter else "Semua"


@router.get("/export/excel")
def export_excel(
    pulau: str = None,
    provinsi: list[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_superadmin),
):
    """Export KNMP locations to Excel with optional filtering.

    - `pulau`: filter by island (Sumatera, Jawa-Bali, Kalimantan, Sulawesi, NTT-NTB, Maluku, Papua)
    - `provinsi`: filter by specific provinces (repeatable: ?provinsi=ACEH&provinsi=JAWA+BARAT)
    """
    locations, prov_filter = filtered_locations(db, pulau, provinsi)
    filename = f"KNMP_{export_label(pulau, prov_filter)}_{date.today()}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "KNMP Locations"

    header_font = Font(bold=True, color="FFFFFF", size=10)
    header_fill = PatternFill(start_color="1B3A6B", end_color="1B3A6B", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    headers = ["ID", "Nama Kampung", "Provinsi", "Kabupaten", "Kecamatan",
                "Latitude", "Longitude", "Status KNMP", "Nelayan", "Kapal"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center")

    for row, loc in enumerate(locations, 2):
        data = [
            loc.id_lokasi, loc.nama_kampung, loc.provinsi, loc.kabupaten,
            loc.kecamatan, loc.lat, loc.lon, loc.status_knmp,
            loc.jumlah_nelayan, loc.jumlah_kapal,
        ]
        for col, val in enumerate(data, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = thin_border
            cell.font = Font(size=9)

    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 12
    ws.column_dimensions["G"].width = 12
    ws.column_dimensions["H"].width = 14
    ws.column_dimensions["I"].width = 10
    ws.column_dimensions["J"].width = 10

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    return FileResponse(
        tmp.name, filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        background=BackgroundTask(os.unlink, tmp.name),
    )



@router.get("/export/pdf")
def export_pdf(
    pulau: str = None,
    provinsi: list[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_superadmin),
):
    """A4 landscape PDF of filtered KNMP locations; preserves actual source values."""
    locations, prov_filter = filtered_locations(db, pulau, provinsi)
    label = export_label(pulau, prov_filter)
    filename = f"KNMP_{label}_{date.today()}.pdf"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(tmp.name, pagesize=landscape(A4),
                            leftMargin=1.1*cm, rightMargin=1.1*cm,
                            topMargin=1.1*cm, bottomMargin=1.1*cm)
    rows = [["No", "Kampung", "Provinsi", "Kabupaten", "Kecamatan", "Status", "Nelayan", "Kapal"]]
    for index, location in enumerate(locations, 1):
        rows.append([str(index), location.nama_kampung or "-", location.provinsi or "-",
                     location.kabupaten or "-", location.kecamatan or "-",
                     location.status_knmp or "-", f"{location.jumlah_nelayan or 0:,}",
                     f"{location.jumlah_kapal or 0:,}"])
    table = Table(rows, colWidths=[0.7*cm, 4.5*cm, 3.2*cm, 3.5*cm, 3.1*cm, 2.1*cm, 2*cm, 1.5*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17699B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("LEADING", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D8E4EC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F9FB")]),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (-2, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    title = Paragraph(f"<b>MARKET WATCH AJN</b> — Sebaran KNMP: {label}", styles["Title"])
    subtitle = Paragraph(f"{len(locations):,} lokasi · diekspor {date.today().isoformat()} · sumber: eKNMP", styles["Normal"])
    doc.build([title, Spacer(1, 0.2*cm), subtitle, Spacer(1, 0.45*cm), table])
    return FileResponse(
        tmp.name, filename=filename, media_type="application/pdf",
        background=BackgroundTask(os.unlink, tmp.name),
    )
