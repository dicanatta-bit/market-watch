from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
import re
from ..database import get_db
from ..models import CommodityPrice
from ..scrapers.fishinfo_history import SERIES_SIZE, SOURCE_NAME

router = APIRouter(tags=["prices"])


def market_count(note):
    match = re.search(r"; (\d+) harga pasar;", note or "")
    return int(match.group(1)) if match else None

@router.get("/prices")
def get_prices(db: Session = Depends(get_db)):
    archive = (CommodityPrice.sumber == SOURCE_NAME) & (CommodityPrice.size == SERIES_SIZE)
    latest = db.query(func.max(CommodityPrice.tanggal)).filter(archive).scalar()
    is_archive = latest is not None
    verified = archive if is_archive else CommodityPrice.sumber.like("FishInfo Jatim%")
    if not latest:
        latest = db.query(func.max(CommodityPrice.tanggal)).filter(verified).scalar()
    items = db.query(CommodityPrice).filter(verified, CommodityPrice.tanggal == latest).all() if latest else []
    data = [{
        "komoditas": p.komoditas, "size": p.size,
        "harga_tambak_low": p.harga_tambak_low, "harga_tambak_high": p.harga_tambak_high,
        "harga_ekspor_low": p.harga_ekspor_low, "harga_ekspor_high": p.harga_ekspor_high,
        "sumber": p.sumber, "tanggal": str(latest),
        "price_basis": ("Rata-rata harga eceran pasar tersedia di Jawa Timur (olah AJN)"
                        if is_archive else "Rata-rata konsumen Jawa Timur"),
        "source_url": (p.catatan.rsplit("; ", 1)[-1] if is_archive and p.catatan else "https://fishinfojatim.net/"),
        "market_count": market_count(p.catatan) if is_archive else None,
    } for p in items]
    age = (date.today() - latest).days if latest else None
    return {"success": True, "data": data, "latest_date": str(latest) if latest else None,
            "source": SOURCE_NAME if is_archive else "FishInfo Jatim (DKP Jawa Timur)",
            "series": "retail_market_mean" if is_archive else "homepage_summary", "age_days": age,
            "fresh": age is not None and age <= 8}

@router.get("/prices/regional")
def get_regional(db: Session = Depends(get_db)):
    # Historical rows were generated from fixed multipliers, not observations.
    return {"success": True, "data": {}, "note": "Harga regional terverifikasi belum tersedia"}

@router.get("/prices/history")
def get_price_history(
    komoditas: str = Query(...),
    size: str = Query(...),
    days: int | None = Query(None, ge=1, le=366),
    db: Session = Depends(get_db),
):
    """All verified observations since the first sync (optional day limit)."""
    verified = CommodityPrice.sumber.like("FishInfo Jatim%")
    filters = (CommodityPrice.komoditas == komoditas,
               CommodityPrice.size == size, verified)
    latest = db.query(func.max(CommodityPrice.tanggal)).filter(*filters).scalar()
    if not latest:
        return {"success": True, "data": [], "window_start": None,
                "window_end": None, "observation_count": 0}
    start = latest - timedelta(days=days - 1) if days else db.query(
        func.min(CommodityPrice.tanggal)).filter(*filters).scalar()
    items = (
        db.query(CommodityPrice)
        .filter(*filters, CommodityPrice.tanggal >= start,
                CommodityPrice.tanggal <= latest)
        .order_by(CommodityPrice.tanggal.asc())
        .all()
    )
    data = [{
        "date": str(p.tanggal),
        "harga_low": p.harga_tambak_low,
        "harga_high": p.harga_tambak_high,
    } for p in items]
    return {"success": True, "data": data, "window_start": str(start),
            "window_end": str(latest), "observation_count": len(data)}
