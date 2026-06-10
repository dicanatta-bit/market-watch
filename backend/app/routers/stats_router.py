from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import KnmpLocation, KnmpLocationSnapshot

router = APIRouter(tags=["stats"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(KnmpLocation).count()
    sub = (db.query(KnmpLocationSnapshot.id_lokasi, func.max(KnmpLocationSnapshot.snapshot_date).label("md"))
            .group_by(KnmpLocationSnapshot.id_lokasi).subquery())
    snaps = db.query(KnmpLocationSnapshot).join(
        sub, (KnmpLocationSnapshot.id_lokasi == sub.c.id_lokasi) & (KnmpLocationSnapshot.snapshot_date == sub.c.md)
    ).all()
    selesai = sum(1 for s in snaps if (s.progress_kumulatif or 0) >= 100)
    berjalan = sum(1 for s in snaps if 0 < (s.progress_kumulatif or 0) < 100)
    nelayan = sum(l.jumlah_nelayan or 0 for l in db.query(KnmpLocation).all())
    kapal = sum(l.jumlah_kapal or 0 for l in db.query(KnmpLocation).all())
    return {"success": True, "data": {
        "total_lokasi": total, "selesai": selesai, "berjalan": berjalan,
        "total_nelayan": nelayan, "total_kapal": kapal,
    }}
