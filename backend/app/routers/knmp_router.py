from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import KnmpLocation, KnmpLocationSnapshot

router = APIRouter(tags=["knmp"])

@router.get("/knmp")
def get_all_knmp(db: Session = Depends(get_db)):
    locations = db.query(KnmpLocation).all()

    # Latest snapshot per location
    sub = (
        db.query(KnmpLocationSnapshot.id_lokasi, func.max(KnmpLocationSnapshot.snapshot_date).label("md"))
        .group_by(KnmpLocationSnapshot.id_lokasi).subquery()
    )
    snaps = {
        s.id_lokasi: s
        for s in db.query(KnmpLocationSnapshot).join(
            sub, (KnmpLocationSnapshot.id_lokasi == sub.c.id_lokasi) & (KnmpLocationSnapshot.snapshot_date == sub.c.md)
        ).all()
    }

    data = []
    for loc in locations:
        s = snaps.get(loc.id_lokasi)
        data.append({
            "id_lokasi": loc.id_lokasi,
            "nama_kampung": loc.nama_kampung,
            "provinsi": loc.provinsi,
            "kabupaten": loc.kabupaten,
            "kecamatan": loc.kecamatan,
            "lat": loc.lat,
            "lon": loc.lon,
            "status_knmp": loc.status_knmp,
            "status_progres": loc.status_progres,
            "tahun": loc.tahun,
            "penyedia": loc.penyedia,
            "jumlah_nelayan": loc.jumlah_nelayan,
            "jumlah_kapal": loc.jumlah_kapal,
            "progress_kumulatif": float(s.progress_kumulatif) if s and s.progress_kumulatif is not None else None,
            "realisasi_fisik": float(s.realisasi_fisik) if s and s.realisasi_fisik is not None else None,
            "realisasi_keuangan": float(s.realisasi_keuangan) if s and s.realisasi_keuangan is not None else None,
            "snapshot_date": str(s.snapshot_date) if s else None,
            "kendala": s.kendala if s else None,
            "tindak_lanjut": s.tindak_lanjut if s else None,
        })

    return {"success": True, "data": data, "total": len(data)}


@router.get("/knmp/{id_lokasi}")
def get_knmp_detail(id_lokasi: int, db: Session = Depends(get_db)):
    loc = db.query(KnmpLocation).filter(KnmpLocation.id_lokasi == id_lokasi).first()
    if not loc:
        return {"success": False, "message": "Not found"}

    snaps = (
        db.query(KnmpLocationSnapshot)
        .filter(KnmpLocationSnapshot.id_lokasi == id_lokasi)
        .order_by(KnmpLocationSnapshot.snapshot_date.asc()).all()
    )

    return {
        "success": True,
        "data": {
            "id_lokasi": loc.id_lokasi,
            "nama_kampung": loc.nama_kampung,
            "provinsi": loc.provinsi,
            "kabupaten": loc.kabupaten,
            "lat": loc.lat,
            "lon": loc.lon,
            "status_knmp": loc.status_knmp,
            "tahun": loc.tahun,
            "penyedia": loc.penyedia,
            "jumlah_nelayan": loc.jumlah_nelayan,
            "jumlah_kapal": loc.jumlah_kapal,
            "snapshots": [{
                "date": str(s.snapshot_date),
                "progress": s.progress_kumulatif,
                "realisasi_fisik": s.realisasi_fisik,
                "realisasi_keuangan": s.realisasi_keuangan,
            } for s in snaps],
        }
    }
