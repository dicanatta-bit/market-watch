"""Market Watch v2 — SQLAlchemy Models (11 tables)"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

try:
    from sqlalchemy.dialects.mysql import JSON
except ImportError:
    from sqlalchemy import JSON

db = SQLAlchemy()


# ── 1. Users ───────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username        = db.Column(db.String(100), unique=True, nullable=False)
    password_hash   = db.Column(db.String(255), nullable=False)
    role            = db.Column(db.Enum("superadmin", "admin_lokasi"), default="admin_lokasi")
    id_lokasi       = db.Column(db.Integer, db.ForeignKey("knmp_locations.id_lokasi"), nullable=True)
    nama            = db.Column(db.String(200))
    is_active       = db.Column(db.Boolean, default=True)
    force_pw_change = db.Column(db.Boolean, default=True)
    last_login      = db.Column(db.DateTime)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    location = db.relationship("KnmpLocation", backref="users", lazy=True)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


# ── 2. KNMP Locations (master) ─────────────────────────────────────────────────
class KnmpLocation(db.Model):
    __tablename__ = "knmp_locations"

    id_lokasi       = db.Column(db.Integer, primary_key=True)
    nama_kampung    = db.Column(db.String(200))
    provinsi        = db.Column(db.String(100))
    kabupaten       = db.Column(db.String(100))
    kecamatan       = db.Column(db.String(100))
    desa            = db.Column(db.String(200))
    lat             = db.Column(db.Float)
    lon             = db.Column(db.Float)
    tahun           = db.Column(db.Integer)
    status_knmp     = db.Column(db.String(50))
    status_progres  = db.Column(db.String(50))
    penyedia        = db.Column(db.String(200))
    jenis_penyedia  = db.Column(db.String(100))
    tanggal_kontrak = db.Column(db.Date)
    jumlah_nelayan  = db.Column(db.Integer)
    jumlah_kapal    = db.Column(db.Integer)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── 3. Location Snapshots (weekly history) ─────────────────────────────────────
class KnmpLocationSnapshot(db.Model):
    __tablename__ = "knmp_location_snapshots"

    id_lokasi           = db.Column(db.Integer, db.ForeignKey("knmp_locations.id_lokasi"), primary_key=True)
    snapshot_date       = db.Column(db.Date, primary_key=True, default=date.today)
    progress_kumulatif  = db.Column(db.Float, default=0)
    realisasi_fisik     = db.Column(db.Float)
    realisasi_keuangan  = db.Column(db.Float)
    kendala             = db.Column(JSON)
    tindak_lanjut       = db.Column(JSON)
    jumlah_nelayan      = db.Column(db.Integer)
    jumlah_kapal        = db.Column(db.Integer)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)


# ── 4. Progress Items (per konstruksi di 1 lokasi) ─────────────────────────────
class KnmpProgressItem(db.Model):
    __tablename__ = "knmp_progress_items"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_lokasi   = db.Column(db.Integer, db.ForeignKey("knmp_locations.id_lokasi"), nullable=False)
    nama_item   = db.Column(db.String(200), nullable=False)
    urutan      = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    location = db.relationship("KnmpLocation", backref="progress_items")


# ── 5. Progress Updates (history per item) ─────────────────────────────────────
class KnmpProgressUpdate(db.Model):
    __tablename__ = "knmp_progress_updates"

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    progress_item_id  = db.Column(db.Integer, db.ForeignKey("knmp_progress_items.id"), nullable=False)
    progress_persen   = db.Column(db.Float, default=0)
    catatan           = db.Column(db.Text)
    kendala           = db.Column(db.Text)
    created_by        = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    item   = db.relationship("KnmpProgressItem", backref="updates")
    author = db.relationship("User", backref="progress_updates")


# ── 6. Progress Photos ─────────────────────────────────────────────────────────
class KnmpProgressPhoto(db.Model):
    __tablename__ = "knmp_progress_photos"

    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    progress_update_id = db.Column(db.Integer, db.ForeignKey("knmp_progress_updates.id"), nullable=False)
    file_path          = db.Column(db.String(500), nullable=False)
    caption            = db.Column(db.String(300))
    foto_type          = db.Column(db.Enum("before", "after", "progress"), default="progress")
    uploaded_by        = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    update = db.relationship("KnmpProgressUpdate", backref="photos")
    uploader = db.relationship("User", backref="uploaded_photos")


# ── 7. Commodity Prices (ganti sheet "Harga Komoditas") ────────────────────────
class CommodityPrice(db.Model):
    __tablename__ = "commodity_prices"

    id                    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tanggal               = db.Column(db.Date, nullable=False)
    komoditas             = db.Column(db.String(200), nullable=False)
    size                  = db.Column(db.String(100), nullable=False)
    harga_tambak_low      = db.Column(db.Float)
    harga_tambak_high     = db.Column(db.Float)
    harga_ekspor_low      = db.Column(db.Float)
    harga_ekspor_high     = db.Column(db.Float)
    harga_intl_low        = db.Column(db.Float)
    harga_intl_high       = db.Column(db.Float)
    sumber                = db.Column(db.Text)
    tingkat_kepercayaan   = db.Column(db.String(50))
    catatan               = db.Column(db.Text)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("tanggal", "komoditas", "size", name="uq_commodity_daily"),
    )


# ── 8. Regional Prices (ganti sheet "Harga per Wilayah") ───────────────────────
class RegionalPrice(db.Model):
    __tablename__ = "regional_prices"

    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tanggal          = db.Column(db.Date, nullable=False)
    wilayah          = db.Column(db.String(50), nullable=False)
    komoditas        = db.Column(db.String(200), nullable=False)
    size             = db.Column(db.String(100), nullable=False)
    harga_tambak_low = db.Column(db.Float)
    harga_tambak_high = db.Column(db.Float)
    faktor_wilayah   = db.Column(db.Float)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("tanggal", "wilayah", "komoditas", "size", name="uq_regional_daily"),
    )


# ── 9. Alert Log (ganti sheet "Alert Log") ─────────────────────────────────────
class AlertLog(db.Model):
    __tablename__ = "alert_log"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tanggal       = db.Column(db.Date, nullable=False)
    alert_type    = db.Column(db.Enum("MERAH", "KUNING", "BIRU"), nullable=False)
    komoditas     = db.Column(db.String(200))
    size          = db.Column(db.String(100))
    pesan         = db.Column(db.Text)
    rekomendasi   = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ── 10. TPI Prices (harga ikan per TPI per lokasi) ─────────────────────────────
class TpiPrice(db.Model):
    __tablename__ = "tpi_prices"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_lokasi  = db.Column(db.Integer, db.ForeignKey("knmp_locations.id_lokasi"))
    nama_tpi   = db.Column(db.String(200))
    komoditas  = db.Column(db.String(200))
    harga      = db.Column(db.Float)
    tanggal    = db.Column(db.Date)
    satuan     = db.Column(db.String(20), default="Rp/kg")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    location = db.relationship("KnmpLocation", backref="tpi_prices")


# ── 11. CCTV Streams (placeholder) ─────────────────────────────────────────────
class CctvStream(db.Model):
    __tablename__ = "cctv_streams"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_lokasi   = db.Column(db.Integer, db.ForeignKey("knmp_locations.id_lokasi"), nullable=False)
    label       = db.Column(db.String(200))
    stream_url  = db.Column(db.String(500))
    stream_type = db.Column(db.Enum("rtsp", "hls", "webrtc", "youtube", "none"), default="none")
    is_active   = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    location = db.relationship("KnmpLocation", backref="cctv_streams")
