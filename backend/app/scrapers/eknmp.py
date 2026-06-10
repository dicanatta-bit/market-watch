"""scrape_eknmp.py — Login eKNMP API → INSERT MySQL (no snapshot, no accounts)"""
import sys, time, requests
from datetime import datetime, date
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import KnmpLocation
from app.config import EKNMP_USERNAME, EKNMP_PASSWORD

AUTH_URL = "https://knmp-api.bht.co.id/auth/login"
BASE_URL = "https://eknmp.kkp.go.id"

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
            print(f"  Fetch tahun {tahun}...")
            r2 = requests.get(f"{BASE_URL}/api/api/knmp/data-tabel",
                params={"id_program": 3, "pulau": "", "status_knmp": "", "tahun": str(tahun)},
                headers=headers, timeout=30)
            items = r2.json().get("data", [])
            print(f"    {len(items)} lokasi")
            all_items.extend(items)
            time.sleep(0.3)

        new_loc = 0
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
            if item.get("jumlah_nelayan") and str(item["jumlah_nelayan"]).isdigit():
                loc.jumlah_nelayan = int(item["jumlah_nelayan"])
            if item.get("jumlah_kapal") and str(item["jumlah_kapal"]).isdigit():
                loc.jumlah_kapal = int(item["jumlah_kapal"])

        # Fetch lat/lon from detail API
        need_coords = db.query(KnmpLocation).filter((KnmpLocation.lat == None) | (KnmpLocation.lon == None)).all()
        print(f"\n  {len(need_coords)} locations need coordinates")
        detail_count = 0
        for loc in need_coords:
            try:
                rd = requests.get(f"{BASE_URL}/api/api/knmp/detail",
                    params={"id_lokasi": loc.id_lokasi}, headers=headers, timeout=15)
                detail = rd.json().get("data", {})
                if detail.get("lat") and detail.get("long"):
                    loc.lat = float(detail["lat"]); loc.lon = float(detail["long"])
                loc.kecamatan = detail.get("kecamatan")
                loc.desa = detail.get("desa")
                detail_count += 1
                if detail_count % 100 == 0: print(f"    {detail_count}/{len(need_coords)} coordinates")
                time.sleep(0.2)
            except Exception as e: pass

        db.commit()
        print(f"\nDone: {len(all_items)} locations, {new_loc} new, {detail_count} with coordinates")
    finally:
        db.close()

if __name__ == "__main__":
    main()
