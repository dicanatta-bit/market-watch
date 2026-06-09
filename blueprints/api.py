"""JSON API blueprint for map + data endpoints"""
from datetime import date
from flask import Blueprint, jsonify, request
from models import (
    KnmpLocation, KnmpLocationSnapshot, KnmpProgressItem,
    KnmpProgressUpdate, CommodityPrice, RegionalPrice,
    TpiPrice, AlertLog, db,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/knmp")
def all_locations():
    """All KNMP locations with latest progress snapshot."""
    locations = KnmpLocation.query.all()

    latest_snapshots = {}
    snapshots = (
        KnmpLocationSnapshot.query
        .order_by(KnmpLocationSnapshot.snapshot_date.desc())
        .all()
    )
    for s in snapshots:
        if s.id_lokasi not in latest_snapshots:
            latest_snapshots[s.id_lokasi] = s

    result = []
    for loc in locations:
        snap = latest_snapshots.get(loc.id_lokasi)
        result.append({
            "id_lokasi": loc.id_lokasi,
            "nama_kampung": loc.nama_kampung,
            "provinsi": loc.provinsi,
            "kabupaten": loc.kabupaten,
            "kecamatan": loc.kecamatan,
            "lat": loc.lat,
            "lon": loc.lon,
            "tahun": loc.tahun,
            "status_knmp": loc.status_knmp,
            "status_progres": loc.status_progres,
            "penyedia": loc.penyedia,
            "jumlah_nelayan": loc.jumlah_nelayan,
            "jumlah_kapal": loc.jumlah_kapal,
            "progress_kumulatif": snap.progress_kumulatif if snap else None,
            "realisasi_fisik": snap.realisasi_fisik if snap else None,
            "realisasi_keuangan": snap.realisasi_keuangan if snap else None,
            "snapshot_date": str(snap.snapshot_date) if snap else None,
        })

    return jsonify({"success": True, "data": result, "total": len(result)})


@api_bp.route("/knmp/<int:id_lokasi>")
def location_detail(id_lokasi):
    """Detail 1 lokasi + progress history + items."""
    loc = KnmpLocation.query.get_or_404(id_lokasi)

    snapshots = (
        KnmpLocationSnapshot.query
        .filter_by(id_lokasi=id_lokasi)
        .order_by(KnmpLocationSnapshot.snapshot_date.asc())
        .all()
    )

    items = (
        KnmpProgressItem.query
        .filter_by(id_lokasi=id_lokasi, is_active=True)
        .order_by(KnmpProgressItem.urutan)
        .all()
    )

    items_data = []
    for item in items:
        latest_update = (
            KnmpProgressUpdate.query
            .filter_by(progress_item_id=item.id)
            .order_by(KnmpProgressUpdate.created_at.desc())
            .first()
        )
        items_data.append({
            "id": item.id,
            "nama_item": item.nama_item,
            "latest_progress": latest_update.progress_persen if latest_update else 0,
            "latest_update": str(latest_update.created_at) if latest_update else None,
        })

    return jsonify({
        "success": True,
        "data": {
            "id_lokasi": loc.id_lokasi,
            "nama_kampung": loc.nama_kampung,
            "provinsi": loc.provinsi,
            "kabupaten": loc.kabupaten,
            "lat": loc.lat,
            "lon": loc.lon,
            "snapshots": [{
                "date": str(s.snapshot_date),
                "progress": s.progress_kumulatif,
                "realisasi_fisik": s.realisasi_fisik,
                "realisasi_keuangan": s.realisasi_keuangan,
            } for s in snapshots],
            "progress_items": items_data,
        },
    })


@api_bp.route("/prices")
def commodity_prices():
    """Latest commodity prices."""
    latest_date = db.session.query(db.func.max(CommodityPrice.tanggal)).scalar()
    if not latest_date:
        latest_date = date.today()

    prices = CommodityPrice.query.filter_by(tanggal=latest_date).all()
    data = [{
        "komoditas": p.komoditas,
        "size": p.size,
        "tambak_low": p.harga_tambak_low,
        "tambak_high": p.harga_tambak_high,
        "ekspor_low": p.harga_ekspor_low,
        "ekspor_high": p.harga_ekspor_high,
        "sumber": p.sumber,
    } for p in prices]

    return jsonify({"success": True, "tanggal": str(latest_date), "data": data})


@api_bp.route("/prices/regional")
def regional_prices():
    """Regional prices per wilayah."""
    latest_date = db.session.query(db.func.max(RegionalPrice.tanggal)).scalar()
    if not latest_date:
        return jsonify({"success": True, "data": {}})

    prices = RegionalPrice.query.filter_by(tanggal=latest_date).all()
    wilayah_data = {}
    for p in prices:
        if p.wilayah not in wilayah_data:
            wilayah_data[p.wilayah] = []
        wilayah_data[p.wilayah].append({
            "komoditas": p.komoditas,
            "size": p.size,
            "harga_low": p.harga_tambak_low,
            "harga_high": p.harga_tambak_high,
        })

    return jsonify({"success": True, "tanggal": str(latest_date), "data": wilayah_data})


@api_bp.route("/alerts")
def alerts():
    """Latest alerts."""
    alerts = AlertLog.query.order_by(AlertLog.tanggal.desc()).limit(20).all()
    data = [{
        "tanggal": str(a.tanggal),
        "type": a.alert_type,
        "komoditas": a.komoditas,
        "pesan": a.pesan,
    } for a in alerts]
    return jsonify({"success": True, "data": data})


@api_bp.route("/stats")
def stats():
    """Overall statistics."""
    total = KnmpLocation.query.count()
    snapshots = KnmpLocationSnapshot.query.all()
    latest_map = {}
    for s in snapshots:
        if s.id_lokasi not in latest_map or s.snapshot_date > latest_map[s.id_lokasi].snapshot_date:
            latest_map[s.id_lokasi] = s

    selesai = sum(1 for s in latest_map.values() if (s.progress_kumulatif or 0) >= 100)
    berjalan = sum(1 for s in latest_map.values() if 0 < (s.progress_kumulatif or 0) < 100)

    return jsonify({
        "success": True,
        "data": {
            "total_lokasi": total,
            "selesai": selesai,
            "berjalan": berjalan,
            "total_nelayan": sum(l.jumlah_nelayan or 0 for l in KnmpLocation.query.all()),
            "total_kapal": sum(l.jumlah_kapal or 0 for l in KnmpLocation.query.all()),
        },
    })
