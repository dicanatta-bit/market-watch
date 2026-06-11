"""Market Watch v3 — Price-focused models (7 tables)"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, ForeignKey, UniqueConstraint
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
    role = Column(String(20), default="superadmin")
    id_lokasi = Column(Integer, ForeignKey("knmp_locations.id_lokasi"), nullable=True)
    nama = Column(String(200))
    is_active = Column(Boolean, default=True)
    force_pw_change = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    jumlah_nelayan = Column(Integer)
    jumlah_kapal = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


class VisitorLog(Base):
    __tablename__ = "visitor_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    page = Column(String(200))
    visited_at = Column(DateTime, default=datetime.utcnow)
