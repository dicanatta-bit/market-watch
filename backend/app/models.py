"""SQLAlchemy models — 11 tables"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

try:
    from sqlalchemy.dialects.mysql import JSON
except ImportError:
    from sqlalchemy import JSON

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="admin_lokasi")
    id_lokasi = Column(Integer, ForeignKey("knmp_locations.id_lokasi"), nullable=True)
    nama = Column(String(200))
    is_active = Column(Boolean, default=True)
    force_pw_change = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    location = relationship("KnmpLocation", backref="users", lazy=True)


class KnmpLocation(Base):
    __tablename__ = "knmp_locations"
    id_lokasi = Column(Integer, primary_key=True)
    nama_kampung = Column(String(200))
    provinsi = Column(String(100))
    kabupaten = Column(String(100))
    kecamatan = Column(String(100))
    desa = Column(String(200))
    lat = Column(Float)
    lon = Column(Float)
    tahun = Column(Integer)
    status_knmp = Column(String(50))
    status_progres = Column(String(50))
    penyedia = Column(String(200))
    jenis_penyedia = Column(String(100))
    tanggal_kontrak = Column(Date)
    jumlah_nelayan = Column(Integer)
    jumlah_kapal = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnmpLocationSnapshot(Base):
    __tablename__ = "knmp_location_snapshots"
    id_lokasi = Column(Integer, ForeignKey("knmp_locations.id_lokasi"), primary_key=True)
    snapshot_date = Column(Date, primary_key=True, default=date.today)
    progress_kumulatif = Column(Float, default=0)
    realisasi_fisik = Column(Float)
    realisasi_keuangan = Column(Float)
    kendala = Column(JSON)
    tindak_lanjut = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnmpProgressItem(Base):
    __tablename__ = "knmp_progress_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_lokasi = Column(Integer, ForeignKey("knmp_locations.id_lokasi"), nullable=False)
    nama_item = Column(String(200), nullable=False)
    urutan = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnmpProgressUpdate(Base):
    __tablename__ = "knmp_progress_updates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    progress_item_id = Column(Integer, ForeignKey("knmp_progress_items.id"), nullable=False)
    progress_persen = Column(Float, default=0)
    catatan = Column(Text)
    kendala = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class KnmpProgressPhoto(Base):
    __tablename__ = "knmp_progress_photos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    progress_update_id = Column(Integer, ForeignKey("knmp_progress_updates.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    caption = Column(String(300))
    foto_type = Column(String(20), default="progress")
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class CommodityPrice(Base):
    __tablename__ = "commodity_prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tanggal = Column(Date, nullable=False)
    komoditas = Column(String(200), nullable=False)
    size = Column(String(100), nullable=False)
    harga_tambak_low = Column(Float)
    harga_tambak_high = Column(Float)
    harga_ekspor_low = Column(Float)
    harga_ekspor_high = Column(Float)
    harga_intl_low = Column(Float)
    harga_intl_high = Column(Float)
    sumber = Column(Text)
    tingkat_kepercayaan = Column(String(50))
    catatan = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("tanggal", "komoditas", "size"),)


class RegionalPrice(Base):
    __tablename__ = "regional_prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tanggal = Column(Date, nullable=False)
    wilayah = Column(String(50), nullable=False)
    komoditas = Column(String(200), nullable=False)
    size = Column(String(100), nullable=False)
    harga_tambak_low = Column(Float)
    harga_tambak_high = Column(Float)
    faktor_wilayah = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("tanggal", "wilayah", "komoditas", "size"),)


class AlertLog(Base):
    __tablename__ = "alert_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tanggal = Column(Date, nullable=False)
    alert_type = Column(String(20), nullable=False)
    komoditas = Column(String(200))
    size = Column(String(100))
    pesan = Column(Text)
    rekomendasi = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class TpiPrice(Base):
    __tablename__ = "tpi_prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_lokasi = Column(Integer, ForeignKey("knmp_locations.id_lokasi"))
    nama_tpi = Column(String(200))
    komoditas = Column(String(200))
    harga = Column(Float)
    tanggal = Column(Date)
    satuan = Column(String(20), default="Rp/kg")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class CctvStream(Base):
    __tablename__ = "cctv_streams"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_lokasi = Column(Integer, ForeignKey("knmp_locations.id_lokasi"), nullable=False)
    label = Column(String(200))
    stream_url = Column(String(500))
    stream_type = Column(String(20), default="none")
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
