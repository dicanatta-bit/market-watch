"""
scrape_sihi.py — Scrape harga ikan per TPI dari SIHI KKP
Target utama : https://sihi.kkp.go.id
Fallback     : https://pipp.kkp.go.id  (rata-rata harga per pelabuhan)
Output       : data/tpi_harga.csv
Kolom        : nama_tpi, kabupaten, provinsi, komoditas, harga, tanggal, satuan

Penggunaan:
  python scrape_sihi.py                     # hari ini, semua TPI
  python scrape_sihi.py --tanggal 2024-05-01
  python scrape_sihi.py --provinsi Sulawesi
  python scrape_sihi.py --append            # tambah ke CSV yang ada (default: overwrite)
  python scrape_sihi.py --sumber pipp       # paksa gunakan fallback PIPP
  python scrape_sihi.py --probe             # hanya cek endpoint mana yang aktif

Catatan: SIHI menggunakan autentikasi sesi; skrip ini mengakses endpoint publik saja.
Jika SIHI tidak dapat dijangkau (di luar Indonesia atau sementara down),
skrip otomatis berpindah ke sumber PIPP.
"""

import argparse
import csv
import json
import logging
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin, urlencode

import requests
from bs4 import BeautifulSoup

# ── Konfigurasi ───────────────────────────────────────────────────────────────

OUTPUT_CSV = Path("data/tpi_harga.csv")
CSV_FIELDNAMES = [
    "nama_tpi", "kabupaten", "provinsi",
    "komoditas", "harga", "tanggal", "satuan",
]

TIMEOUT    = 18
DELAY      = 1.2   # detik antar request (hormati rate limit KKP)
MAX_PAGES  = 50    # batas halaman DataTables per endpoint

SIHI_BASE  = "https://sihi.kkp.go.id"
PIPP_BASE  = "https://pipp.kkp.go.id"
PIPP_OLD   = "https://pipp.djpt.kkp.go.id"

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
}

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── HTTP helper ───────────────────────────────────────────────────────────────

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HTTP_HEADERS)
    return s


def safe_get(session, url, *, params=None, timeout=TIMEOUT, label=""):
    """GET dengan retry sekali pada timeout/koneksi error. Returns Response atau None."""
    for attempt in range(2):
        try:
            r = session.get(url, params=params, timeout=timeout, allow_redirects=True)
            log.debug(f"GET {url} → {r.status_code}")
            return r
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                log.debug(f"[{label}] ConnectionError, retry…")
                time.sleep(2)
            else:
                log.debug(f"[{label}] ConnectionRefused: {url}")
                return None
        except requests.exceptions.Timeout:
            log.debug(f"[{label}] Timeout: {url}")
            return None
        except Exception as e:
            log.debug(f"[{label}] {type(e).__name__}: {url}")
            return None


def safe_post(session, url, *, data=None, json_body=None, timeout=TIMEOUT, label=""):
    """POST dengan retry sekali. Returns Response atau None."""
    for attempt in range(2):
        try:
            r = session.post(url, data=data, json=json_body, timeout=timeout)
            log.debug(f"POST {url} → {r.status_code}")
            return r
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                time.sleep(2)
            else:
                return None
        except Exception as e:
            log.debug(f"[{label}] {type(e).__name__}: {url}")
            return None


def try_json(r) -> dict | list | None:
    if r is None:
        return None
    try:
        return r.json()
    except Exception:
        return None


# ── CSV helper ────────────────────────────────────────────────────────────────

def save_csv(rows: list[dict], output: Path, append: bool):
    output.parent.mkdir(parents=True, exist_ok=True)
    mode  = "a" if append and output.exists() else "w"
    wrote = 0
    with output.open(mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        if mode == "w":
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
            wrote += 1
    log.info(f"{'Ditambahkan' if mode == 'a' else 'Ditulis'} {wrote} baris ke {output}")
    return wrote


# ── SIHI KKP Scraper ──────────────────────────────────────────────────────────

class SihiScraper:
    """
    Scraper untuk sihi.kkp.go.id — Sistem Informasi Harga Ikan KKP.

    SIHI menggunakan pola URL umum pada portal pemerintah berbasis
    Laravel/CodeIgniter dengan DataTables server-side.  Skrip ini mencoba
    beberapa pola endpoint; pola yang merespons valid digunakan untuk
    pengambilan data selanjutnya.
    """

    # Pola endpoint yang dicoba, dari yang paling umum
    CANDIDATE_ENDPOINTS = [
        "/harga-ikan",
        "/harga",
        "/data-harga",
        "/public/harga",
        "/harga-tpi",
        "/harga/data",
        "/api/harga",
        "/api/harga-ikan",
        "/api/data/harga",
    ]

    # Endpoint DataTables AJAX yang umum digunakan KKP
    DATATABLES_ENDPOINTS = [
        "/harga-ikan/data",
        "/harga/datatables",
        "/harga/dt",
        "/api/harga/dt",
        "/data/harga",
        "/harga-ikan/list",
        "/harga/list",
        "/public/harga/data",
    ]

    def __init__(self, session: requests.Session, tanggal: str | None = None):
        self.session = session
        self.tanggal = tanggal or date.today().strftime("%Y-%m-%d")
        self.base_url = SIHI_BASE
        self._working_endpoint: str | None = None
        self._is_datatables: bool = False

    # ── Probing ────────────────────────────────────────────────────────────

    def probe(self) -> bool:
        """
        Cek apakah SIHI dapat diakses dan temukan endpoint yang bekerja.
        Returns True jika setidaknya satu endpoint merespons.
        """
        log.info("Memeriksa akses ke SIHI KKP (sihi.kkp.go.id)…")

        # 1. Cek halaman utama
        r = safe_get(self.session, self.base_url, timeout=10, label="SIHI root")
        if r is None:
            log.warning("sihi.kkp.go.id tidak dapat dijangkau (connection refused).")
            return False
        if r.status_code >= 500:
            log.warning(f"sihi.kkp.go.id error server: {r.status_code}")
            return False

        log.info(f"SIHI root merespons {r.status_code}.")

        # 2. Cek endpoint DataTables terlebih dahulu (lebih mudah di-parse)
        for ep in self.DATATABLES_ENDPOINTS:
            url = self.base_url + ep
            payload = {"draw": 1, "start": 0, "length": 10,
                       "tanggal": self.tanggal,
                       "search[value]": "", "search[regex]": "false"}
            r2 = safe_post(self.session, url, data=payload, timeout=10, label="SIHI DT")
            if r2 and r2.status_code == 200:
                data = try_json(r2)
                if isinstance(data, dict) and "data" in data:
                    log.info(f"DataTables endpoint ditemukan: {ep}")
                    self._working_endpoint = ep
                    self._is_datatables = True
                    return True
            time.sleep(0.3)

        # 3. Cek endpoint HTML biasa
        for ep in self.CANDIDATE_ENDPOINTS:
            url = self.base_url + ep
            r2 = safe_get(self.session, url, timeout=10, label="SIHI HTML")
            if r2 and r2.status_code == 200 and len(r2.text) > 500:
                soup = BeautifulSoup(r2.text, "html.parser")
                # Cari tanda-tanda data harga: tag <table>, kata kunci harga
                has_table = bool(soup.find("table"))
                has_harga = any(w in r2.text.lower() for w in
                                ["harga", "tpi", "komoditas", "ikan"])
                if has_table and has_harga:
                    log.info(f"Endpoint HTML ditemukan: {ep}")
                    self._working_endpoint = ep
                    self._is_datatables = False
                    return True
            time.sleep(0.3)

        log.warning("SIHI dapat dijangkau tapi tidak ada endpoint data yang dikenali.")
        return False

    # ── DataTables scraping ─────────────────────────────────────────────────

    def _scrape_datatables(self, provinsi_filter: str | None = None) -> list[dict]:
        rows = []
        url  = self.base_url + self._working_endpoint
        page = 0
        per_page = 100

        while page < MAX_PAGES:
            payload = {
                "draw": page + 1,
                "start": page * per_page,
                "length": per_page,
                "tanggal": self.tanggal,
                "search[value]": provinsi_filter or "",
                "search[regex]": "false",
            }
            r = safe_post(self.session, url, data=payload, label="SIHI DT data")
            if r is None or r.status_code != 200:
                break
            data = try_json(r)
            if not isinstance(data, dict) or "data" not in data:
                break

            batch = data["data"]
            if not batch:
                break

            for item in batch:
                row = self._parse_datatables_row(item)
                if row:
                    rows.append(row)

            total = data.get("recordsFiltered", data.get("recordsTotal", 0))
            fetched = (page + 1) * per_page
            log.info(f"  Halaman {page + 1}: {len(batch)} baris "
                     f"({min(fetched, total)}/{total})")

            if fetched >= total:
                break
            page += 1
            time.sleep(DELAY)

        return rows

    def _parse_datatables_row(self, item) -> dict | None:
        """
        Normalisasi satu baris DataTables ke format CSV standar.
        Menangani variasi kunci yang umum di portal KKP.
        """
        if isinstance(item, (list, tuple)):
            # Urutan kolom umum: tpi, kabupaten, provinsi, komoditas, harga, tanggal, satuan
            cols = list(item)
            while len(cols) < 7:
                cols.append("")
            return {
                "nama_tpi":  _clean(cols[0]),
                "kabupaten": _clean(cols[1]),
                "provinsi":  _clean(cols[2]),
                "komoditas": _clean(cols[3]),
                "harga":     _parse_harga(cols[4]),
                "tanggal":   _normalize_tanggal(str(cols[5])),
                "satuan":    _clean(cols[6]) or "Rp/kg",
            }

        if not isinstance(item, dict):
            return None

        # Peta kunci umum → nama kolom standar
        KEY_MAP = {
            "nama_tpi":  ["nama_tpi", "tpi", "nama_pelabuhan", "pelabuhan",
                          "nama_ppi", "ppi", "tempat"],
            "kabupaten": ["kabupaten", "kab", "kota", "kabkota", "kab_kota"],
            "provinsi":  ["provinsi", "prov", "province", "nama_provinsi"],
            "komoditas": ["komoditas", "nama_ikan", "ikan", "jenis_ikan",
                          "nama_komoditas", "commodity"],
            "harga":     ["harga", "harga_rata", "harga_ikan", "price",
                          "rata_rata", "harga_rata_rata", "nilai"],
            "tanggal":   ["tanggal", "tgl", "date", "created_at", "updated_at"],
            "satuan":    ["satuan", "unit", "keterangan_satuan"],
        }

        row = {}
        item_lower = {k.lower(): v for k, v in item.items()}
        for field, candidates in KEY_MAP.items():
            for key in candidates:
                if key in item_lower:
                    row[field] = item_lower[key]
                    break
            else:
                row[field] = ""

        if not row.get("komoditas") and not row.get("harga"):
            return None

        row["harga"]   = _parse_harga(row.get("harga", ""))
        row["tanggal"] = _normalize_tanggal(str(row.get("tanggal", "")))
        row["satuan"]  = _clean(row.get("satuan", "")) or "Rp/kg"
        return row

    # ── HTML table scraping ─────────────────────────────────────────────────

    def _scrape_html(self, provinsi_filter: str | None = None) -> list[dict]:
        rows = []
        url  = self.base_url + self._working_endpoint
        params = {"tanggal": self.tanggal}
        if provinsi_filter:
            params["provinsi"] = provinsi_filter

        r = safe_get(self.session, url, params=params, label="SIHI HTML data")
        if r is None or r.status_code != 200:
            return rows

        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            log.warning("Tidak ada tabel ditemukan di halaman SIHI.")
            return rows

        for table in tables:
            parsed = _parse_html_table(table)
            rows.extend(parsed)

        # Cek paginasi (link "Next" atau nomor halaman)
        next_url = _find_next_page(soup, url)
        page = 2
        while next_url and page <= MAX_PAGES:
            time.sleep(DELAY)
            r2 = safe_get(self.session, next_url, label=f"SIHI p{page}")
            if r2 is None or r2.status_code != 200:
                break
            soup2 = BeautifulSoup(r2.text, "html.parser")
            for table in soup2.find_all("table"):
                rows.extend(_parse_html_table(table))
            next_url = _find_next_page(soup2, next_url)
            page += 1

        return rows

    # ── Entry point ─────────────────────────────────────────────────────────

    def scrape(self, provinsi_filter: str | None = None) -> list[dict]:
        if not self._working_endpoint:
            if not self.probe():
                return []

        log.info(f"Mengambil data SIHI: tanggal={self.tanggal}, "
                 f"provinsi={provinsi_filter or 'semua'}…")

        if self._is_datatables:
            rows = self._scrape_datatables(provinsi_filter)
        else:
            rows = self._scrape_html(provinsi_filter)

        log.info(f"SIHI: {len(rows)} baris diperoleh.")
        return rows


# ── PIPP Scraper (fallback) ───────────────────────────────────────────────────

class PippScraper:
    """
    Fallback scraper untuk pipp.kkp.go.id — data rata-rata harga ikan
    per pelabuhan perikanan (PPS/PPN/PPP/PPI).

    PIPP menyediakan data harga rata-rata harian per jenis ikan di
    setiap pelabuhan perikanan nasional.  Ini bukan data TPI harian
    penuh seperti SIHI, tapi merupakan sumber publik terbaik yang tersedia.
    """

    # Endpoint rata-rata harga di PIPP (dicoba berurutan)
    HARGA_ENDPOINTS = [
        "/rata-rata-harga",
        "/harga-ikan",
        "/data/harga",
        "/api/harga-rata",
        "/harga",
    ]

    # Daftar pelabuhan utama dengan ID numerik (pipp.djpt format lama)
    # ID dari URL profil_pelabuhan yang diketahui publik
    PELABUHAN_IDS = list(range(1, 201))   # coba 1–200, skip yang 404

    def __init__(self, session: requests.Session, tanggal: str | None = None):
        self.session = session
        self.tanggal = tanggal or date.today().strftime("%Y-%m-%d")

    def _get_harga_by_id(self, pelabuhan_id: int) -> list[dict]:
        """Coba ambil data harga dari profil pelabuhan (pipp.djpt URL lama)."""
        url = f"{PIPP_OLD}/profil_pelabuhan/{pelabuhan_id}/produksi_harga"
        r   = safe_get(self.session, url, timeout=12, label=f"PIPP/{pelabuhan_id}")
        if r is None or r.status_code != 200:
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        # Ambil nama & lokasi pelabuhan dari header halaman
        nama_tpi   = ""
        kabupaten  = ""
        provinsi   = ""
        h_tags = soup.find_all(["h1", "h2", "h3", "h4"])
        if h_tags:
            nama_tpi = _clean(h_tags[0].get_text())
        meta_loc = soup.find(string=re.compile(r"provinsi|kabupaten|kab\.", re.I))
        if meta_loc:
            parent_text = _clean(meta_loc.find_parent().get_text() if meta_loc.find_parent() else "")
            m_prov = re.search(r"provinsi[:\s]+([^\n,;]+)", parent_text, re.I)
            m_kab  = re.search(r"kabupaten[:\s]+([^\n,;]+)", parent_text, re.I)
            if m_prov:
                provinsi = m_prov.group(1).strip()
            if m_kab:
                kabupaten = m_kab.group(1).strip()

        rows = []
        for table in soup.find_all("table"):
            for row in _parse_html_table(table):
                row.setdefault("nama_tpi", nama_tpi)
                row.setdefault("kabupaten", kabupaten)
                row.setdefault("provinsi", provinsi)
                if not row.get("tanggal"):
                    row["tanggal"] = self.tanggal
                rows.append(row)

        return rows

    def _get_harga_endpoint(self) -> list[dict]:
        """Coba endpoint harga langsung di pipp.kkp.go.id."""
        rows = []
        for ep in self.HARGA_ENDPOINTS:
            url = PIPP_BASE + ep
            r = safe_get(
                self.session, url,
                params={"tanggal": self.tanggal},
                timeout=12,
                label="PIPP ep",
            )
            if r is None or r.status_code != 200:
                time.sleep(0.5)
                continue

            # Coba parse sebagai JSON
            data = try_json(r)
            if isinstance(data, (list, dict)):
                extracted = _extract_json_rows(data, self.tanggal)
                if extracted:
                    log.info(f"PIPP endpoint {ep}: {len(extracted)} baris JSON")
                    rows.extend(extracted)
                    break

            # Coba parse sebagai HTML
            soup = BeautifulSoup(r.text, "html.parser")
            tables = soup.find_all("table")
            if tables:
                for table in tables:
                    rows.extend(_parse_html_table(table))
                if rows:
                    log.info(f"PIPP endpoint {ep}: {len(rows)} baris HTML")
                    break

            time.sleep(0.5)

        return rows

    def scrape(self, provinsi_filter: str | None = None,
               max_ports: int = 30) -> list[dict]:
        log.info("Menggunakan fallback PIPP sebagai sumber data harga…")
        rows = []

        # Coba endpoint langsung terlebih dahulu
        ep_rows = self._get_harga_endpoint()
        if ep_rows:
            rows.extend(ep_rows)

        # Jika endpoint langsung gagal, scan per ID pelabuhan (lambat)
        if not rows:
            log.info(f"Scanning {max_ports} ID pelabuhan PIPP…")
            found = 0
            for pid in self.PELABUHAN_IDS[:max_ports]:
                port_rows = self._get_harga_by_id(pid)
                if port_rows:
                    # Filter provinsi jika diminta
                    if provinsi_filter:
                        port_rows = [
                            r for r in port_rows
                            if provinsi_filter.lower() in
                            r.get("provinsi", "").lower()
                        ]
                    rows.extend(port_rows)
                    found += 1
                    log.info(f"  Pelabuhan ID {pid}: {len(port_rows)} baris")
                time.sleep(DELAY)

            log.info(f"PIPP scan: {found} pelabuhan aktif, {len(rows)} baris total.")

        # Filter provinsi untuk hasil endpoint
        if provinsi_filter and rows:
            rows = [
                r for r in rows
                if provinsi_filter.lower() in r.get("provinsi", "").lower()
            ]

        return rows


# ── Parser utilities ──────────────────────────────────────────────────────────

def _clean(s) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def _parse_harga(val) -> str:
    """
    Normalisasi nilai harga ke string angka bulat (tanpa simbol Rp/titik/koma).
    Contoh: 'Rp 45.000' → '45000', '45,000' → '45000', '45.5' → '45500'
    """
    s = re.sub(r"[Rp\s]", "", str(val or ""))
    # Format ribuan: 45.000 atau 45,000
    if re.search(r"\d{1,3}[.,]\d{3}$", s):
        s = re.sub(r"[.,](\d{3})$", r"\1", s)
        s = re.sub(r"[.,]", "", s)
    else:
        # Hapus semua titik/koma non-desimal
        s = re.sub(r"[.,]", "", s)
    s = re.sub(r"[^\d]", "", s)
    return s if s.isdigit() else str(val or "").strip()


def _normalize_tanggal(s: str) -> str:
    """
    Coba kenali berbagai format tanggal dan normalkan ke YYYY-MM-DD.
    Jika tidak bisa di-parse, kembalikan string asli.
    """
    s = _clean(s)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
                "%d %B %Y", "%d %b %Y", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Coba format partial "2024-05" → "2024-05-01"
    m = re.match(r"(\d{4})-(\d{2})$", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    return s


def _parse_html_table(table) -> list[dict]:
    """
    Parse satu elemen <table> HTML menjadi list dict CSV.
    Coba cocokkan header kolom ke nama field standar.
    """
    rows_out = []
    all_rows = table.find_all("tr")
    if not all_rows:
        return rows_out

    # Cari baris header (th atau td di baris pertama)
    header_row = all_rows[0]
    raw_headers = [
        _clean(th.get_text()).lower()
        for th in (header_row.find_all("th") or header_row.find_all("td"))
    ]
    if not raw_headers:
        return rows_out

    # Mapping header → field standar
    HEADER_MAP = {
        "nama_tpi":  ["nama tpi", "tpi", "nama pelabuhan", "pelabuhan",
                      "nama ppi", "ppi", "tempat pelelangan"],
        "kabupaten": ["kabupaten", "kab.", "kota", "kab/kota", "kabkota"],
        "provinsi":  ["provinsi", "prov.", "province"],
        "komoditas": ["komoditas", "jenis ikan", "ikan", "nama ikan",
                      "komoditi", "jenis"],
        "harga":     ["harga", "harga (rp/kg)", "harga rata-rata",
                      "harga ikan", "rata-rata", "price", "nilai"],
        "tanggal":   ["tanggal", "tgl", "date", "waktu"],
        "satuan":    ["satuan", "unit", "ket."],
    }

    col_idx = {}
    for field, candidates in HEADER_MAP.items():
        for i, h in enumerate(raw_headers):
            if any(c in h for c in candidates):
                col_idx[field] = i
                break

    # Harus ada minimal komoditas ATAU harga untuk dianggap tabel harga ikan
    if "komoditas" not in col_idx and "harga" not in col_idx:
        return rows_out

    for tr in all_rows[1:]:
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        vals = [_clean(c.get_text()) for c in cells]

        row = {}
        for field, idx in col_idx.items():
            if idx < len(vals):
                row[field] = vals[idx]
            else:
                row[field] = ""

        # Isi default jika kosong
        row.setdefault("satuan", "Rp/kg")
        row["harga"]   = _parse_harga(row.get("harga", ""))
        row["tanggal"] = _normalize_tanggal(row.get("tanggal", ""))

        # Skip baris kosong / total / sub-header
        if not row.get("komoditas") or row.get("komoditas", "").lower() in (
            "total", "jumlah", "komoditas", "jenis ikan", "rata-rata"
        ):
            continue

        rows_out.append(row)

    return rows_out


def _find_next_page(soup: BeautifulSoup, current_url: str) -> str | None:
    """Cari link halaman berikutnya (paginasi rel=next atau teks 'Berikutnya'/'Next')."""
    # <link rel="next">
    link = soup.find("link", rel="next")
    if link and link.get("href"):
        return urljoin(current_url, link["href"])

    # <a> dengan teks next/berikutnya
    for a in soup.find_all("a", href=True):
        txt = _clean(a.get_text()).lower()
        if txt in ("next", "berikutnya", "›", "»", ">"):
            return urljoin(current_url, a["href"])
        if a.get("aria-label", "").lower() in ("next", "berikutnya"):
            return urljoin(current_url, a["href"])

    return None


def _extract_json_rows(data, default_tanggal: str) -> list[dict]:
    """
    Coba ekstrak baris dari berbagai struktur JSON respons KKP.
    Menangani: list of dicts, {"data": [...]}, {"result": [...]}
    """
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = (data.get("data") or data.get("result") or
                 data.get("rows") or data.get("items") or [])
    else:
        return []

    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        row = {}
        item_l = {k.lower(): v for k, v in item.items()}
        for field in CSV_FIELDNAMES:
            row[field] = str(item_l.get(field, item_l.get(field.split("_")[0], ""))).strip()
        row["harga"]   = _parse_harga(row.get("harga", ""))
        row["tanggal"] = _normalize_tanggal(row.get("tanggal", "")) or default_tanggal
        row.setdefault("satuan", "Rp/kg")
        rows.append(row)
    return rows


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape harga ikan per TPI dari SIHI/PIPP KKP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--tanggal",  default=None,
                   help="Tanggal data (YYYY-MM-DD). Default: hari ini.")
    p.add_argument("--provinsi", default=None,
                   help="Filter nama provinsi (substring, case-insensitive).")
    p.add_argument("--sumber",   choices=["sihi", "pipp", "auto"],
                   default="auto",
                   help="Sumber data: 'sihi' (paksa SIHI), 'pipp' (paksa PIPP), "
                        "'auto' (coba SIHI dulu, fallback ke PIPP). Default: auto.")
    p.add_argument("--max-ports", type=int, default=30,
                   help="Jumlah ID pelabuhan yang di-scan saat fallback PIPP. Default: 30.")
    p.add_argument("--output",   default=str(OUTPUT_CSV),
                   help=f"Path file CSV output. Default: {OUTPUT_CSV}")
    p.add_argument("--append",   action="store_true",
                   help="Tambahkan ke CSV yang ada (default: timpa/buat baru).")
    p.add_argument("--probe",    action="store_true",
                   help="Hanya probe endpoint, tidak ambil data.")
    p.add_argument("--verbose",  action="store_true",
                   help="Tampilkan log DEBUG.")
    return p.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args   = parse_args()
    output = Path(args.output)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    tanggal  = args.tanggal or date.today().strftime("%Y-%m-%d")
    session  = make_session()

    print("=" * 60)
    print("Market Watch AJN — Scraper SIHI KKP Harga Ikan per TPI")
    print(f"Tanggal  : {tanggal}")
    print(f"Provinsi : {args.provinsi or 'semua'}")
    print(f"Sumber   : {args.sumber}")
    print(f"Output   : {output}")
    print("=" * 60)

    rows = []

    if args.sumber in ("sihi", "auto"):
        sihi = SihiScraper(session, tanggal)

        if args.probe:
            ok = sihi.probe()
            print(f"\nSIHI {'DAPAT' if ok else 'TIDAK DAPAT'} diakses.")
            if ok:
                print(f"  Endpoint: {sihi._working_endpoint}")
                print(f"  Mode: {'DataTables' if sihi._is_datatables else 'HTML'}")
            sys.exit(0)

        rows = sihi.scrape(provinsi_filter=args.provinsi)

    if not rows and args.sumber in ("pipp", "auto"):
        if args.sumber == "auto":
            log.warning("SIHI tidak tersedia atau tidak ada data. Mencoba fallback PIPP…")
        pipp = PippScraper(session, tanggal)
        rows = pipp.scrape(
            provinsi_filter=args.provinsi,
            max_ports=args.max_ports,
        )

    if not rows:
        log.error(
            "Tidak ada data diperoleh dari SIHI maupun PIPP.\n"
            "Kemungkinan penyebab:\n"
            "  • sihi.kkp.go.id tidak dapat diakses dari luar Indonesia\n"
            "  • Situs sedang dalam pemeliharaan\n"
            "  • Struktur endpoint berubah (jalankan --probe untuk cek)\n"
            "Coba jalankan dari server yang berlokasi di Indonesia, atau\n"
            "gunakan VPN dengan exit node Indonesia."
        )
        sys.exit(1)

    n = save_csv(rows, output, append=args.append)
    print(f"\nSelesai. {n} baris disimpan ke {output}.")

    # Preview 5 baris pertama
    print("\nContoh data (5 baris pertama):")
    print(",".join(CSV_FIELDNAMES))
    for r in rows[:5]:
        print(",".join(str(r.get(f, "")) for f in CSV_FIELDNAMES))


if __name__ == "__main__":
    main()
