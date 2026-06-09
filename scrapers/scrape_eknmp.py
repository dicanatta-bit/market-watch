"""scrape_eknmp.py v2 — Login eKNMP API → INSERT ke MySQL + auto-create accounts"""
import sys, time
from datetime import datetime, date
from config import Config
from app import create_app
from models import db, KnmpLocation, KnmpLocationSnapshot, User
from auth import hash_password

import requests

AUTH_URL = "https://knmp-api.bht.co.id/auth/login"
BASE_URL = "https://eknmp.kkp.go.id"
TIMEOUT = 30
DELAY = 0.2


class EknmpClient:
    def __init__(self, username, password):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; MarketWatchAJN/2.0)",
            "Accept": "application/json",
        })
        self.username = username
        self.password = password

    def login(self):
        print("  Login eKNMP API...")
        resp = self.session.post(AUTH_URL, json={
            "username": self.username, "password": self.password,
        }, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == 200:
            token = data["data"]["token"]
            self.session.headers["Authorization"] = f"Bearer {token}"
            print(f"  ✓ Login OK ({token[:20]}...)")
        else:
            raise RuntimeError(f"Login failed: {data}")

    def fetch_data_tabel(self, tahun):
        print(f"  Fetch data tabel {tahun}...")
        resp = self.session.get(
            f"{BASE_URL}/api/api/knmp/data-tabel",
            params={"id_program": 3, "pulau": "", "status_knmp": "", "tahun": str(tahun)},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        items = resp.json().get("data", [])
        print(f"  ✓ {len(items)} lokasi")
        return items

    def fetch_detail(self, id_lokasi):
        resp = self.session.get(
            f"{BASE_URL}/api/api/knmp/detail",
            params={"id_lokasi": id_lokasi},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {})
        return {}

    def fetch_progress(self):
        print("  Fetch progress mingguan...")
        resp = self.session.get(
            f"{BASE_URL}/api/api/knmp/summary-progres-mingguan",
            timeout=TIMEOUT,
        )
        data = resp.json().get("data", {})
        cards = data.get("list_card", [])
        for c in cards:
            print(f"    {c.get('label')}: {c.get('value')}")
        return data

    def fetch_nelayan_kapal(self):
        resp = self.session.get(
            f"{BASE_URL}/api/api/knmp/jumlah-nelayan-dan-jumlah-kapal",
            params={"status_knmp": "", "tahun": "", "pulau": ""},
            timeout=TIMEOUT,
        )
        return resp.json().get("data", {})


def main():
    app = create_app(Config)
    with app.app_context():
        print("=" * 55)
        print("eKNMP Scraper v2 — Market Watch AJN")
        print(f"Date: {date.today()}")
        print("=" * 55)

        client = EknmpClient(Config.EKNMP_USERNAME, Config.EKNMP_PASSWORD)
        try:
            client.login()
        except Exception as e:
            print(f"\n❌ Login failed: {e}"); sys.exit(1)

        # Fetch all locations
        all_items = []
        all_items.extend(client.fetch_data_tabel(2025))
        time.sleep(DELAY)
        all_items.extend(client.fetch_data_tabel(2026))

        client.fetch_progress()

        today = date.today()
        new_locations = 0
        updated_snapshots = 0
        new_accounts = 0

        for item in all_items:
            id_lokasi = item.get("id_lokasi")
            if not id_lokasi:
                continue

            # UPSERT location master
            loc = KnmpLocation.query.get(id_lokasi)
            if not loc:
                loc = KnmpLocation(id_lokasi=id_lokasi)
                db.session.add(loc)
                new_locations += 1

            loc.nama_kampung   = item.get("nama_kampung")
            loc.provinsi       = item.get("provinsi")
            loc.kabupaten      = item.get("kabupaten")
            loc.tahun          = int(item["tahun"]) if item.get("tahun") else None
            loc.status_knmp    = item.get("status_knmp")
            loc.status_progres = item.get("status_progres")
            loc.penyedia       = item.get("nama_penyedia")
            loc.jumlah_nelayan = int(item["jumlah_nelayan"]) if item.get("jumlah_nelayan") and item["jumlah_nelayan"].isdigit() else None
            loc.jumlah_kapal   = int(item["jumlah_kapal"]) if item.get("jumlah_kapal") and item["jumlah_kapal"].isdigit() else None

            # Check if snapshot already exists for today
            existing = KnmpLocationSnapshot.query.filter_by(id_lokasi=id_lokasi, snapshot_date=today).first()
            if not existing:
                snap = KnmpLocationSnapshot(
                    id_lokasi=id_lokasi,
                    snapshot_date=today,
                    progress_kumulatif=float(item.get("status", 0) or 0),
                    kendala=[{"isi": item["kendala"]}] if item.get("kendala") else None,
                    tindak_lanjut=[{"isi": item["tindak_lanjut"]}] if item.get("tindak_lanjut") else None,
                )
                db.session.add(snap)
                updated_snapshots += 1

        # Step: Fetch detail for locations WITHOUT coordinates
        print(f"\n  Fetching lat/lon from detail API...")
        locs_without_coords = KnmpLocation.query.filter(
            db.or_(KnmpLocation.lat == None, KnmpLocation.lon == None)
        ).all()
        print(f"  {len(locs_without_coords)} locations need coordinates")

        detail_count = 0
        for loc in locs_without_coords:
            try:
                detail = client.fetch_detail(loc.id_lokasi)
                if detail:
                    if detail.get("lat") and detail.get("long"):
                        loc.lat = float(detail["lat"])
                        loc.lon = float(detail["long"])
                    loc.kecamatan = detail.get("kecamatan")
                    loc.desa = detail.get("desa")
                    detail_data = detail.get("detail", {})
                    if detail_data:
                        loc.jenis_penyedia = detail_data.get("jenis_penyedia")
                        loc.tanggal_kontrak = detail_data.get("tanggal_kontrak")
                        if detail_data.get("tanggal_kontrak"):
                            try:
                                loc.tanggal_kontrak = detail_data["tanggal_kontrak"]
                                parsed = datetime.strptime(str(detail_data["tanggal_kontrak"]), "%Y-%m-%d").date()
                                loc.tanggal_kontrak = parsed
                            except:
                                pass
                    monitoring = detail.get("monitoring")
                    if monitoring:
                        existing_snap = KnmpLocationSnapshot.query.filter_by(id_lokasi=loc.id_lokasi, snapshot_date=today).first()
                        if existing_snap:
                            existing_snap.realisasi_fisik = float(monitoring.get("realisasi_fisik", 0) or 0)
                            existing_snap.realisasi_keuangan = float(monitoring.get("realisasi_keuangan", 0) or 0)
                    detail_count += 1
                    if detail_count % 50 == 0:
                        print(f"    {detail_count}/{len(locs_without_coords)} details enriched...")
                time.sleep(DELAY)
            except Exception as e:
                print(f"    ⚠ detail {loc.id_lokasi} failed: {e}")
                continue

        print(f"  ✓ {detail_count} details enriched with coordinates")
        db.session.commit()

        # Auto-create accounts for new locations
        lokasi_tanpa_akun = (
            KnmpLocation.query
            .outerjoin(User, db.and_(User.id_lokasi == KnmpLocation.id_lokasi, User.role == "admin_lokasi"))
            .filter(User.id == None)
            .all()
        )

        for loc in lokasi_tanpa_akun:
            username = f"knmp_{loc.id_lokasi}"
            default_pw = f"knmp_{loc.id_lokasi}2026"

            existing_user = User.query.filter_by(username=username).first()
            if not existing_user:
                user = User(
                    username=username,
                    password_hash=hash_password(default_pw),
                    role="admin_lokasi",
                    id_lokasi=loc.id_lokasi,
                    nama=loc.nama_kampung,
                    is_active=True,
                    force_pw_change=True,
                )
                db.session.add(user)
                new_accounts += 1

        db.session.commit()

        print(f"\n{'='*55}")
        print(f"Total locations fetched: {len(all_items)}")
        print(f"New locations: {new_locations}")
        print(f"New snapshots today: {updated_snapshots}")
        print(f"New accounts created: {new_accounts}")
        print(f"Users without accounts remaining: {max(0, len(lokasi_tanpa_akun) - new_accounts)}")
        print(f"{'='*55}")


if __name__ == "__main__":
    main()
