from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from ..database import get_db
from ..models import KnmpLocation, KnmpLocationSnapshot
from ..auth import get_superadmin
import io, os, tempfile
from datetime import date

router = APIRouter(tags=["export"])

@router.get("/export/excel")
def export_excel(db: Session = Depends(get_db), _ = Depends(get_superadmin)):
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active; ws.title = "KNMP"
    for c, h in enumerate(["ID", "Nama", "Provinsi", "Kabupaten", "Status", "Progress", "Nelayan", "Kapal"], 1):
        ws.cell(1, c, h)
    for r, loc in enumerate(db.query(KnmpLocation).all(), 2):
        for c, v in enumerate([loc.id_lokasi, loc.nama_kampung, loc.provinsi, loc.kabupaten, loc.status_knmp, None, loc.jumlah_nelayan, loc.jumlah_kapal], 1):
            ws.cell(r, c, v)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    return FileResponse(tmp.name, filename=f"KNMP_{date.today()}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
