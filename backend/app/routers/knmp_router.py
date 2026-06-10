from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import KnmpLocation

router = APIRouter(tags=["knmp"])


@router.get("/knmp")
def get_all_knmp(db: Session = Depends(get_db)):
    locations = db.query(KnmpLocation).all()
    data = []
    for loc in locations:
        data.append({
            "id_lokasi": loc.id_lokasi,
            "nama_kampung": loc.nama_kampung,
            "provinsi": loc.provinsi,
            "kabupaten": loc.kabupaten,
            "kecamatan": loc.kecamatan,
            "desa": loc.desa,
            "lat": loc.lat,
            "lon": loc.lon,
            "status_knmp": loc.status_knmp,
            "tahun": loc.tahun,
            "jumlah_nelayan": loc.jumlah_nelayan,
            "jumlah_kapal": loc.jumlah_kapal,
        })
    return {"success": True, "data": data, "total": len(data)}


@router.get("/knmp/{id_lokasi}")
def get_knmp_detail(id_lokasi: int, db: Session = Depends(get_db)):
    loc = db.query(KnmpLocation).filter(KnmpLocation.id_lokasi == id_lokasi).first()
    if not loc:
        return {"success": False, "message": "Not found"}
    return {
        "success": True,
        "data": {
            "id_lokasi": loc.id_lokasi,
            "nama_kampung": loc.nama_kampung,
            "provinsi": loc.provinsi,
            "kabupaten": loc.kabupaten,
            "kecamatan": loc.kecamatan,
            "desa": loc.desa,
            "lat": loc.lat, "lon": loc.lon,
            "status_knmp": loc.status_knmp,
            "tahun": loc.tahun,
            "jumlah_nelayan": loc.jumlah_nelayan,
            "jumlah_kapal": loc.jumlah_kapal,
        }
    }
