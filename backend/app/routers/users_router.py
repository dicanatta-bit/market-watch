from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_superadmin, hash_password

router = APIRouter(tags=["users"])

@router.get("/users")
def list_users(db: Session = Depends(get_db), _ = Depends(get_superadmin)):
    users = db.query(User).all()
    return {"success": True, "data": [{
        "id": u.id, "username": u.username, "role": u.role, "nama": u.nama,
        "id_lokasi": u.id_lokasi, "is_active": u.is_active,
        "last_login": str(u.last_login) if u.last_login else None,
    } for u in users]}

@router.post("/users/{user_id}/reset-pw")
def reset_password(user_id: int, db: Session = Depends(get_db), _ = Depends(get_superadmin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        return {"success": False, "message": "Not found"}
    default = f"knmp_{u.id_lokasi or 'admin'}2026"
    u.password_hash = hash_password(default)
    u.force_pw_change = True
    db.commit()
    return {"success": True, "message": f"Password {u.username} direset"}
