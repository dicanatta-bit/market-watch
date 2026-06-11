from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import CommodityPrice, RegionalPrice

router = APIRouter(tags=["prices"])

@router.get("/prices")
def get_prices(db: Session = Depends(get_db)):
    latest = db.query(func.max(CommodityPrice.tanggal)).scalar()
    items = db.query(CommodityPrice).filter(CommodityPrice.tanggal == latest).all() if latest else []
    data = [{
        "komoditas": p.komoditas, "size": p.size,
        "harga_tambak_low": p.harga_tambak_low, "harga_tambak_high": p.harga_tambak_high,
        "harga_ekspor_low": p.harga_ekspor_low, "harga_ekspor_high": p.harga_ekspor_high,
        "sumber": p.sumber, "tanggal": str(latest),
    } for p in items]
    return {"success": True, "data": data, "latest_date": str(latest) if latest else None}

@router.get("/prices/regional")
def get_regional(db: Session = Depends(get_db)):
    latest = db.query(func.max(RegionalPrice.tanggal)).scalar()
    items = db.query(RegionalPrice).filter(RegionalPrice.tanggal == latest).all() if latest else []
    result = {}
    for p in items:
        result.setdefault(p.wilayah, []).append({
            "komoditas": p.komoditas, "size": p.size,
            "harga_low": p.harga_tambak_low, "harga_high": p.harga_tambak_high,
        })
    return {"success": True, "data": result}

@router.get("/prices/history")
def get_price_history(
    komoditas: str = Query(...),
    size: str = Query(...),
    weeks: int = Query(12),
    db: Session = Depends(get_db),
):
    """Price history for a commodity — last N weeks."""
    items = (
        db.query(CommodityPrice)
        .filter(CommodityPrice.komoditas == komoditas, CommodityPrice.size == size)
        .order_by(CommodityPrice.tanggal.desc())
        .limit(weeks)
        .all()
    )
    data = [{
        "date": str(p.tanggal),
        "harga_low": p.harga_tambak_low,
        "harga_high": p.harga_tambak_high,
    } for p in reversed(items)]
    return {"success": True, "data": data}
