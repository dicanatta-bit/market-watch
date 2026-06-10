"""Scrape eKNMP API → INSERT MySQL + auto-create user accounts"""
import sys, time, requests
from datetime import datetime, date
sys.path.insert(0, ".")

from app.database import SessionLocal, engine, Base
from app.models import User, KnmpLocation, KnmpLocationSnapshot
from app.config import EKNMP_USERNAME, EKNMP_PASSWORD, DEFAULT_PASSWORD_PATTERN
from app.auth import hash_password

AUTH_URL = "https://knmp-api.bht.co.id/auth/login"
BASE_URL = "https://eknmp.kkp.go.id"
TODAY = date.today()

def main():
    db = SessionLocal()
    try:
        print("Login eKNMP...")
        r = requests.post(AUTH_URL, json={"username": EKNMP_USERNAME, "password": EKNMP_PASSWORD}, timeout=30)
        token = r.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"  ✓ Token: {token[:20]}...")

        all_items = []
        for tahun in [2025, 2026]:
            print(f"  Fetch {tahun}...")
            r2 = requests.get(f"{BASE_URL}/api/api/knmp/data-tabel",
                params={"id_program": 3, "pulau": "", "status_knmp": "", "tahun": str(tahun)},
                headers=headers, timeout=30)
            items = r2.json().get("data", [])
            print(f"    {len(items)} lokasi")
            all_items.extend(items)
            time.sleep(0.5)

        new_loc, new_snap, detail_count = 0, 0, 0
        for item in all_items:
            id_lokasi = item.get("id_lokasi")
            if not id_lokasi: continue

            loc = db.query(KnmpLocation).filter(KnmpLocation.id_lokasi == id_lokasi).first()
            if not loc:
                loc = KnmpLocation(id_lokasi=id_lokasi)
                db.add(loc)
                new_loc += 1
            loc.nama_kampung = item.get("nama_kampung")
            loc.provinsi = item.get("provinsi")
            loc.kabupaten = item.get("kabupaten")
            loc.tahun = int(item["tahun"]) if item.get("tahun") else None
            loc.status_knmp = item.get("status_knmp")
            loc.status_progres = item.get("status_progres")
            loc.penyedia = item.get("nama_penyedia")
            if item.get("jumlah_nelayan") and str(item["jumlah_nelayan"]).isdigit():
                loc.jumlah_nelayan = int(item["jumlah_nelayan"])
            if item.get("jumlah_kapal") and str(item["jumlah_kapal"]).isdigit():
                loc.jumlah_kapal = int(item["jumlah_kapal"])

            snap_exists = db.query(KnmpLocationSnapshot).filter_by(id_lokasi=id_lokasi, snapshot_date=TODAY).first()
            if not snap_exists:
                s = KnmpLocationSnapshot(id_lokasi=id_lokasi, snapshot_date=TODAY,
                    progress_kumulatif=float(item.get("status", 0) or 0),
                    kendala=[{"isi": item["kendala"]}] if item.get("kendala") else None,
                    tindak_lanjut=[{"isi": item["tindak_lanjut"]}] if item.get("tindak_lanjut") else None)
                db.add(s)
                new_snap += 1

        # Fetch lat/lon from detail API for locations without coordinates
        need_coords = db.query(KnmpLocation).filter(
            (KnmpLocation.lat == None) | (KnmpLocation.lon == None)
        ).all()
        print(f"\n  Fetching coordinates for {len(need_coords)} locations...")
        for loc in need_coords:
            try:
                rd = requests.get(f"{BASE_URL}/api/api/knmp/detail", params={"id_lokasi": loc.id_lokasi}, headers=headers, timeout=15)
                detail = rd.json().get("data", {})
                if detail.get("lat") and detail.get("long"):
                    loc.lat = float(detail["lat"])
                    loc.lon = float(detail["long"])
                loc.kecamatan = detail.get("kecamatan")
                loc.desa = detail.get("desa")
                detail_count += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"    ⚠ {loc.id_lokasi}: {e}")
                continue
        print(f"  ✓ {detail_count} locations enriched with coordinates")

        # Auto-create admin accounts
        all_locs = db.query(KnmpLocation).all()
        existing_users = set(u.id_lokasi for u in db.query(User).filter(User.role == "admin_lokasi").all())
        new_users = 0
        for loc in all_locs:
            if loc.id_lokasi not in existing_users:
                pw = DEFAULT_PASSWORD_PATTERN.format(id_lokasi=loc.id_lokasi)
                u = User(username=f"knmp_{loc.id_lokasi}", password_hash=hash_password(pw),
                          role="admin_lokasi", id_lokasi=loc.id_lokasi, nama=loc.nama_kampung,
                          is_active=True, force_pw_change=True)
                db.add(u)
                new_users += 1
                existing_users.add(loc.id_lokasi)

        db.commit()
        print(f"\nDone: {len(all_items)} locations, {new_loc} new, {new_snap} snapshots, {new_users} new users")
    finally:
        db.close()

if __name__ == "__main__":
    main()
