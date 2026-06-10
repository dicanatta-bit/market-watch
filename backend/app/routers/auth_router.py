from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import LoginRequest, ChangePwRequest
from ..auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(tags=["auth"])

@router.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username, User.is_active == True).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Username atau password salah")

    token = create_token({"sub": str(user.id)})
    return {
        "token": token,
        "user": {
            "id": user.id, "username": user.username, "role": user.role,
            "id_lokasi": user.id_lokasi, "nama": user.nama,
            "force_pw_change": user.force_pw_change,
        }
    }

@router.post("/auth/change-password")
def change_password(body: ChangePwRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(400, "Password lama salah")
    if len(body.new_password) < 6:
        raise HTTPException(400, "Password minimal 6 karakter")
    user.password_hash = hash_password(body.new_password)
    user.force_pw_change = False
    db.commit()
    return {"message": "Password berhasil diubah"}
