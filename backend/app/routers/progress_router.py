from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import KnmpLocation, KnmpLocationSnapshot, KnmpProgressItem, KnmpProgressUpdate, KnmpProgressPhoto, TpiPrice
from ..schemas import ProgressUpdateIn, TpiPriceIn
from ..auth import get_current_user
from datetime import date
import os, shutil

router = APIRouter(tags=["progress"])

@router.post("/progress/{item_id}")
def update_progress(item_id: int, body: ProgressUpdateIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(KnmpProgressItem).filter(KnmpProgressItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    update = KnmpProgressUpdate(progress_item_id=item_id, progress_persen=body.progress_persen,
                                 catatan=body.catatan, kendala=body.kendala, created_by=user.id)
    db.add(update); db.commit()
    return {"success": True}

@router.post("/progress/{item_id}/photos")
def upload_photo(item_id: int, user=Depends(get_current_user)):
    return {"success": True, "message": "Photo upload endpoint ready"}

@router.post("/loc/{id_lokasi}/prices")
def add_tpi_price(id_lokasi: int, body: TpiPriceIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    tpi = TpiPrice(id_lokasi=id_lokasi, nama_tpi=body.nama_tpi, komoditas=body.komoditas,
                    harga=body.harga, tanggal=date.today(), created_by=user.id)
    db.add(tpi); db.commit()
    return {"success": True}
