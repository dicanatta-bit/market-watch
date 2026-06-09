"""Location admin blueprint — Per-lokasi CRUD & progress update"""
import os
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from models import (
    db, KnmpLocation, KnmpLocationSnapshot,
    KnmpProgressItem, KnmpProgressUpdate, KnmpProgressPhoto,
    TpiPrice, CctvStream,
)
from auth import location_admin_required

location_bp = Blueprint("location", __name__, url_prefix="/loc")


def _get_location(id_lokasi):
    return KnmpLocation.query.get_or_404(id_lokasi)


def _can_access(id_lokasi):
    if current_user.role == "superadmin":
        return True
    return current_user.id_lokasi == id_lokasi


def _check_access(id_lokasi):
    if not _can_access(id_lokasi):
        flash("Akses terbatas ke lokasi ini.", "danger")
        return False
    return True


@location_bp.route("/")
@login_required
def dashboard():
    """Redirect to user's own location or list for superadmin."""
    if current_user.role == "superadmin":
        return redirect(url_for("superadmin.dashboard"))
    if current_user.id_lokasi:
        return redirect(url_for("location.dashboard", id_lokasi=current_user.id_lokasi))
    flash("Tidak ada lokasi terkait akun ini.", "warning")
    return redirect(url_for("auth.logout"))


@location_bp.route("/<int:id_lokasi>")
@login_required
def dashboard_location(id_lokasi):
    if not _check_access(id_lokasi):
        return redirect(url_for("location.dashboard"))

    location = _get_location(id_lokasi)
    snapshots = (
        KnmpLocationSnapshot.query
        .filter_by(id_lokasi=id_lokasi)
        .order_by(KnmpLocationSnapshot.snapshot_date.desc())
        .limit(52)
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
    cctv = CctvStream.query.filter_by(id_lokasi=id_lokasi).all()

    latest = snapshots[0] if snapshots else None

    return render_template(
        "location/dashboard.html",
        location=location,
        latest=latest,
        snapshots=snapshots,
        items=items,
        tpi_prices=tpi_prices,
        cctv=cctv,
        title=f"Dashboard: {location.nama_kampung}",
    )


@location_bp.route("/<int:id_lokasi>/progress/<int:item_id>", methods=["POST"])
@location_admin_required
def update_progress(id_lokasi, item_id):
    if not _check_access(id_lokasi):
        return redirect(url_for("location.dashboard"))

    item = KnmpProgressItem.query.filter_by(id=item_id, id_lokasi=id_lokasi).first_or_404()
    persen  = request.form.get("progress_persen", type=float, default=0)
    catatan = request.form.get("catatan", "").strip()
    kendala = request.form.get("kendala", "").strip()

    update = KnmpProgressUpdate(
        progress_item_id=item.id,
        progress_persen=persen,
        catatan=catatan or None,
        kendala=kendala or None,
        created_by=current_user.id,
    )
    db.session.add(update)

    # Update the item's last known progress via its latest update
    # Actually, we keep all updates as history. The latest is always queryable.

    db.session.commit()
    flash("Progress berhasil diupdate.", "success")
    return redirect(url_for("location.dashboard_location", id_lokasi=id_lokasi))


@location_bp.route("/<int:id_lokasi>/photos/<int:update_id>", methods=["POST"])
@location_admin_required
def upload_photo(id_lokasi, update_id):
    if not _check_access(id_lokasi):
        return redirect(url_for("location.dashboard"))

    progress_update = KnmpProgressUpdate.query.get_or_404(update_id)

    if "photo" not in request.files:
        flash("Tidak ada file.", "danger")
        return redirect(url_for("location.dashboard_location", id_lokasi=id_lokasi))

    file = request.files["photo"]
    if file.filename == "":
        flash("File kosong.", "danger")
        return redirect(url_for("location.dashboard_location", id_lokasi=id_lokasi))

    filename = secure_filename(f"{id_lokasi}_{date.today()}_{file.filename}")
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    foto_type = request.form.get("foto_type", "progress")
    caption = request.form.get("caption", "").strip()

    photo = KnmpProgressPhoto(
        progress_update_id=update_id,
        file_path=f"uploads/{filename}",
        caption=caption or None,
        foto_type=foto_type,
        uploaded_by=current_user.id,
    )
    db.session.add(photo)
    db.session.commit()

    flash("Foto berhasil diupload.", "success")
    return redirect(url_for("location.dashboard_location", id_lokasi=id_lokasi))


@location_bp.route("/<int:id_lokasi>/prices", methods=["POST"])
@location_admin_required
def add_price(id_lokasi):
    if not _check_access(id_lokasi):
        return redirect(url_for("location.dashboard"))

    komoditas = request.form.get("komoditas", "").strip()
    harga     = request.form.get("harga", type=float)
    nama_tpi  = request.form.get("nama_tpi", "").strip()

    if not komoditas or not harga:
        flash("Komoditas dan harga wajib diisi.", "danger")
        return redirect(url_for("location.dashboard_location", id_lokasi=id_lokasi))

    tpi = TpiPrice(
        id_lokasi=id_lokasi,
        nama_tpi=nama_tpi or None,
        komoditas=komoditas,
        harga=harga,
        tanggal=date.today(),
        satuan="Rp/kg",
        created_by=current_user.id,
    )
    db.session.add(tpi)
    db.session.commit()
    flash("Harga berhasil ditambahkan.", "success")
    return redirect(url_for("location.dashboard_location", id_lokasi=id_lokasi))


@location_bp.route("/<int:id_lokasi>/kendala", methods=["POST"])
@location_admin_required
def update_kendala(id_lokasi):
    if not _check_access(id_lokasi):
        return redirect(url_for("location.dashboard"))

    kendala_text = request.form.get("kendala", "").strip()
    tindak_text  = request.form.get("tindak_lanjut", "").strip()

    snapshot = KnmpLocationSnapshot.query.filter_by(
        id_lokasi=id_lokasi, snapshot_date=date.today()
    ).first()

    if snapshot:
        if kendala_text:
            existing = snapshot.kendala or []
            existing.append({"tanggal": str(date.today()), "isi": kendala_text})
            snapshot.kendala = existing
        if tindak_text:
            existing = snapshot.tindak_lanjut or []
            existing.append({"tanggal": str(date.today()), "isi": tindak_text})
            snapshot.tindak_lanjut = existing
        db.session.commit()

    flash("Kendala / tindak lanjut disimpan.", "success")
    return redirect(url_for("location.dashboard_location", id_lokasi=id_lokasi))
