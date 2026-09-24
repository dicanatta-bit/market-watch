from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import KnmpLocation, CommodityPrice, PipelineRun, AlertLog
from ..auth import get_superadmin
from ..scrapers.fishinfo_history import SERIES_SIZE, SOURCE_NAME
from sqlalchemy import func

router = APIRouter(tags=["stats"])

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total, nelayan, kapal = db.query(
        func.count(KnmpLocation.id_lokasi),
        func.coalesce(func.sum(KnmpLocation.jumlah_nelayan), 0),
        func.coalesce(func.sum(KnmpLocation.jumlah_kapal), 0),
    ).one()
    latest_knmp = db.query(func.max(KnmpLocation.updated_at)).scalar()
    return {"success": True, "data": {
        "total_lokasi": total or 0,
        "latest_knmp_update": latest_knmp.isoformat() if latest_knmp else None,
        "selesai": 0, "berjalan": 0,
        "total_nelayan": int(nelayan or 0),
        "total_kapal": int(kapal or 0),
    }}


def iso(value):
    return value.isoformat() if value else None


@router.get("/admin/monitoring")
def get_monitoring(db: Session = Depends(get_db), _=Depends(get_superadmin)):
    """Operational status for the internal console; all timestamps are UTC."""
    now = datetime.utcnow()
    locations, latest_knmp = db.query(
        func.count(KnmpLocation.id_lokasi), func.max(KnmpLocation.updated_at)
    ).one()
    price_filter = (CommodityPrice.sumber == SOURCE_NAME) & (CommodityPrice.size == SERIES_SIZE)
    latest_price, price_rows = db.query(
        func.max(CommodityPrice.tanggal), func.count(CommodityPrice.id)
    ).filter(price_filter).one()
    last_run = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()
    latest_alerts = db.query(AlertLog).order_by(AlertLog.tanggal.desc(), AlertLog.created_at.desc()).limit(6).all()
    price_age = (now.date() - latest_price).days if latest_price else None
    knmp_age = (now - latest_knmp).total_seconds() / 86400 if latest_knmp else None
    return {"success": True, "data": {
        "checked_at": iso(now),
        "price": {"latest_date": str(latest_price) if latest_price else None,
                  "age_days": price_age, "observations": price_rows,
                  "healthy": price_age is not None and price_age <= 8},
        "knmp": {"locations": locations or 0, "last_updated": iso(latest_knmp),
                 "age_days": round(knmp_age, 1) if knmp_age is not None else None,
                 "healthy": knmp_age is not None and knmp_age <= 10},
        "pipeline": None if not last_run else {
            "id": last_run.id, "trigger": last_run.trigger, "status": last_run.status,
            "started_at": iso(last_run.started_at), "finished_at": iso(last_run.finished_at),
            "log": last_run.log or "",
            "healthy": last_run.status == "success" and last_run.finished_at is not None,
        },
        "alerts": [{"date": str(alert.tanggal), "level": alert.alert_type,
                    "commodity": alert.komoditas, "message": alert.pesan}
                   for alert in latest_alerts],
    }}
