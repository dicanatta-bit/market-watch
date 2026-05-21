"""
Market Watch - AJN
Orchestrator: update harga → cek alert → infografis → laporan PDF
"""

import subprocess
import sys
import os
import time
from datetime import datetime

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"


def run(script, *args, max_retries=0, retry_delay=60):
    cmd = [sys.executable, script, *args]
    print(f"\n{'='*55}")
    print(f"Menjalankan: {' '.join(cmd)}")
    print(f"{'='*55}")
    for attempt in range(1 + max_retries):
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            return
        print(f"[ERROR] {script} gagal dengan exit code {result.returncode}")
        if result.returncode == 1 and attempt < max_retries:
            print(f"[RETRY] Percobaan {attempt + 1}/{max_retries} gagal. Menunggu {retry_delay} detik sebelum retry...")
            time.sleep(retry_delay)
        else:
            sys.exit(result.returncode)


if __name__ == "__main__":
    print(f"Market Watch AJN — Auto Update")
    print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # 1. Pastikan folder output ada
    os.makedirs("output", exist_ok=True)

    # 2. Update harga semua komoditas ke sheet "Harga Komoditas"
    run("update_harga.py", SPREADSHEET_ID, max_retries=2, retry_delay=60)

    # 3. Generate harga per wilayah ke sheet "Harga per Wilayah"
    run("generate_harga_wilayah.py", SPREADSHEET_ID)

    # 4. Cek alert & tulis ke sheet "Alert Log"
    run("alert_engine.py", SPREADSHEET_ID)

    # 5. Build infografis GSheet + ekspor HTML ke /output
    run("buat_infografis.py")

    # 6. Generate laporan mingguan PDF ke /output
    run("laporan_mingguan.py", SPREADSHEET_ID)

    # 7. Generate peta KNMP dengan integrasi harga wilayah
    run("buat_knmp_map.py", SPREADSHEET_ID)

    print("\n" + "="*55)
    print("Auto update selesai.")
    print("="*55)
