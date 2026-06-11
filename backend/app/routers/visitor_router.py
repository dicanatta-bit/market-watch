from datetime import datetime, date
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import VisitorLog
from ..auth import get_superadmin

router = APIRouter(tags=["visitor"])


@router.post("/visitor/log")
def log_visitor(request: Request, db: Session = Depends(get_db)):
    """Log visitor and return total/today counts."""
    ip = request.headers.get("x-real-ip") or request.headers.get("x-forwarded-for") or request.client.host if request.client else "0.0.0.0"
    ua = request.headers.get("user-agent", "")
    page = request.headers.get("referer", "/")

    # Save (1 log per day per IP per page to keep it reasonable)
    existing = db.query(VisitorLog).filter(
        VisitorLog.ip_address == ip,
        func.date(VisitorLog.visited_at) == date.today(),
        VisitorLog.page == page,
    ).first()
    if not existing:
        db.add(VisitorLog(ip_address=ip.split(",")[0].strip(), user_agent=ua, page=page))
        db.commit()

    total = db.query(func.count(VisitorLog.id)).scalar()
    today = db.query(func.count(VisitorLog.id)).filter(
        func.date(VisitorLog.visited_at) == date.today()
    ).scalar()

    return {"success": True, "total": total, "today": today}


@router.get("/visitor/stats")
def visitor_stats(db: Session = Depends(get_db), _=Depends(get_superadmin)):
    """Visitor stats — superadmin only."""
    total = db.query(func.count(VisitorLog.id)).scalar()
    today = db.query(func.count(VisitorLog.id)).filter(
        func.date(VisitorLog.visited_at) == date.today()
    ).scalar()
    unique_ips = db.query(func.count(func.distinct(VisitorLog.ip_address))).scalar()

    recent = (
        db.query(VisitorLog)
        .order_by(VisitorLog.visited_at.desc())
        .limit(50)
        .all()
    )

    top_ips = (
        db.query(VisitorLog.ip_address, func.count(VisitorLog.id).label("cnt"))
        .group_by(VisitorLog.ip_address)
        .order_by(func.count(VisitorLog.id).desc())
        .limit(10)
        .all()
    )

    return {
        "success": True,
        "data": {
            "total": total,
            "today": today,
            "unique_ips": unique_ips,
            "recent_logs": [
                {
                    "ip": v.ip_address,
                    "page": v.page,
                    "ua": (v.user_agent or "")[:60],
                    "time": v.visited_at.strftime("%Y-%m-%d %H:%M") if v.visited_at else "",
                }
                for v in recent
            ],
            "top_ips": [{"ip": ip, "count": cnt} for ip, cnt in top_ips],
        },
    }
