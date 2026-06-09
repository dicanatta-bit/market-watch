"""Superadmin blueprint — Full control dashboard"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from models import db, User, KnmpLocation, KnmpLocationSnapshot, KnmpProgressItem, AlertLog, CctvStream, TpiPrice
from auth import superadmin_required, hash_password

superadmin_bp = Blueprint("superadmin", __name__, url_prefix="/admin")


@superadmin_bp.route("/")
@superadmin_required
def dashboard():
    total_lokasi   = KnmpLocation.query.count()
    total_snapshot = KnmpLocationSnapshot.query.distinct(KnmpLocationSnapshot.id_lokasi).count()
    total_users    = User.query.count()
    total_alerts   = AlertLog.query.count()

    latest_snapshots = db.session.query(
        KnmpLocationSnapshot.id_lokasi,
        db.func.max(KnmpLocationSnapshot.snapshot_date).label("max_date"),
    ).group_by(KnmpLocationSnapshot.id_lokasi).subquery()

    progress_data = db.session.query(
        KnmpLocationSnapshot
    ).join(
        latest_snapshots,
        db.and_(
            KnmpLocationSnapshot.id_lokasi == latest_snapshots.c.id_lokasi,
            KnmpLocationSnapshot.snapshot_date == latest_snapshots.c.max_date,
        ),
    ).all()

    selesai = sum(1 for p in progress_data if (p.progress_kumulatif or 0) >= 100)
    berjalan = sum(1 for p in progress_data if 0 < (p.progress_kumulatif or 0) < 100)
    rata_rata = (
        sum(p.progress_kumulatif or 0 for p in progress_data) / len(progress_data)
        if progress_data else 0
    )

    cctv = CctvStream.query.filter_by(is_active=True).count()

    return render_template(
        "superadmin/dashboard.html",
        total_lokasi=total_lokasi,
        total_snapshot=total_snapshot,
        total_users=total_users,
        total_alerts=total_alerts,
        selesai=selesai,
        berjalan=berjalan,
        rata_rata=round(rata_rata, 1),
        cctv_count=cctv,
        title="Dashboard — Superadmin",
    )


@superadmin_bp.route("/locations")
@superadmin_required
def locations():
    provinsi = request.args.get("provinsi", "").strip()
    status   = request.args.get("status", "").strip()
    tahun    = request.args.get("tahun", "").strip()
    search   = request.args.get("q", "").strip()

    query = KnmpLocation.query

    if provinsi:
        query = query.filter(db.func.lower(KnmpLocation.provinsi) == provinsi.lower())
    if status:
        query = query.filter(KnmpLocation.status_knmp == status)
    if tahun:
        query = query.filter(KnmpLocation.tahun == int(tahun))
    if search:
        q = f"%{search}%"
        query = query.filter(
            db.or_(
                KnmpLocation.nama_kampung.ilike(q),
                KnmpLocation.kabupaten.ilike(q),
                KnmpLocation.penyedia.ilike(q),
            )
        )

    locations = query.order_by(KnmpLocation.provinsi, KnmpLocation.nama_kampung).limit(200).all()
    prov_list = sorted(set(
        l.provinsi for l in KnmpLocation.query.with_entities(KnmpLocation.provinsi).distinct()
        if l.provinsi
    ))

    return render_template(
        "superadmin/locations.html",
        locations=locations,
        prov_list=prov_list,
        provinsi=provinsi,
        status=status,
        tahun=tahun,
        search=search,
        title="Manage Locations — Superadmin",
    )


@superadmin_bp.route("/locations/<int:id_lokasi>")
@superadmin_required
def location_detail(id_lokasi):
    location = KnmpLocation.query.get_or_404(id_lokasi)
    snapshots = (
        KnmpLocationSnapshot.query
        .filter_by(id_lokasi=id_lokasi)
        .order_by(KnmpLocationSnapshot.snapshot_date.desc())
        .limit(12)
        .all()
    )
    items = (
        KnmpProgressItem.query
        .filter_by(id_lokasi=id_lokasi, is_active=True)
        .order_by(KnmpProgressItem.urutan)
        .all()
    )
    tpi_prices = (
        TpiPrice.query
        .filter_by(id_lokasi=id_lokasi)
        .order_by(TpiPrice.tanggal.desc())
        .limit(20)
        .all()
    )
    cctv_streams = CctvStream.query.filter_by(id_lokasi=id_lokasi).all()
    admin_user = User.query.filter_by(id_lokasi=id_lokasi, role="admin_lokasi").first()

    return render_template(
        "superadmin/location_detail.html",
        location=location,
        snapshots=snapshots,
        items=items,
        tpi_prices=tpi_prices,
        cctv_streams=cctv_streams,
        admin_user=admin_user,
        title=f"Detail: {location.nama_kampung} — Superadmin",
    )


@superadmin_bp.route("/users")
@superadmin_required
def users():
    all_users = User.query.order_by(User.role, User.username).all()
    return render_template(
        "superadmin/users.html",
        users=all_users,
        title="Manage Users — Superadmin",
    )


@superadmin_bp.route("/users/<int:user_id>/reset-pw", methods=["POST"])
@superadmin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_pw = f"knmp_{user.id_lokasi or 'admin'}2026"
    user.password_hash = hash_password(new_pw)
    user.force_pw_change = True
    db.session.commit()
    flash(f"Password untuk {user.username} direset ke default.", "success")
    return redirect(url_for("superadmin.users"))
