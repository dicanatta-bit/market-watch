from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePwRequest(BaseModel):
    old_password: str
    new_password: str

class TokenResponse(BaseModel):
    token: str
    user: dict

class KnmpMarker(BaseModel):
    id_lokasi: int
    nama_kampung: Optional[str]
    provinsi: Optional[str]
    kabupaten: Optional[str]
    kecamatan: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    status_knmp: Optional[str]
    status_progres: Optional[str]
    tahun: Optional[int]
    penyedia: Optional[str]
    jumlah_nelayan: Optional[int]
    jumlah_kapal: Optional[int]
    progress_kumulatif: Optional[float]
    realisasi_fisik: Optional[float]
    realisasi_keuangan: Optional[float]
    snapshot_date: Optional[str]
    kendala: Optional[list] = None
    tindak_lanjut: Optional[list] = None

class CommodityPriceOut(BaseModel):
    komoditas: str
    size: str
    harga_tambak_low: Optional[float]
    harga_tambak_high: Optional[float]
    harga_ekspor_low: Optional[float]
    harga_ekspor_high: Optional[float]
    sumber: Optional[str]

class RegionalPriceOut(BaseModel):
    komoditas: str
    size: str
    harga_low: Optional[float]
    harga_high: Optional[float]

class StatsOut(BaseModel):
    total_lokasi: int
    selesai: int
    berjalan: int
    total_nelayan: int
    total_kapal: int

class ProgressUpdateIn(BaseModel):
    progress_persen: float
    catatan: Optional[str] = None
    kendala: Optional[str] = None

class TpiPriceIn(BaseModel):
    komoditas: str
    nama_tpi: Optional[str] = None
    harga: float
