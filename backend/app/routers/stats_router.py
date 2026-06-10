from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import KnmpLocation

router = APIRouter(tags=["stats"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    locations = db.query(KnmpLocation).all()
    total = len(locations)
    return {"success": True, "data": {
        "total_lokasi": total,
        "selesai": 0, "berjalan": 0,
        "total_nelayan": sum(l.jumlah_nelayan or 0 for l in locations),
        "total_kapal": sum(l.jumlah_kapal or 0 for l in locations),
    }}
