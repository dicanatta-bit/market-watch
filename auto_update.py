"""
Market Watch - AJN
Orchestrator: update harga → cek alert → infografis → laporan PDF
"""

import subprocess
import sys
import os
from datetime import datetime

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"


def run(script, *args):
    cmd = [sys.executable, script, *args]
    print(f"\n{'='*55}")
    print(f"Menjalankan: {' '.join(cmd)}")
    print(f"{'='*55}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {script} gagal dengan exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    print(f"Market Watch AJN — Auto Update")
    print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # 1. Pastikan folder output ada
    os.makedirs("output", exist_ok=True)

    # 2. Update harga semua komoditas ke sheet "Harga Komoditas"
    run("update_harga.py", SPREADSHEET_ID)

    # 3. Cek alert & tulis ke sheet "Alert Log"
    run("alert_engine.py", SPREADSHEET_ID)

    # 4. Build infografis GSheet + ekspor HTML ke /output
    run("buat_infografis.py")

    # 5. Generate laporan mingguan PDF ke /output
    run("laporan_mingguan.py", SPREADSHEET_ID)

    print("\n" + "="*55)
    print("Auto update selesai.")
    print("="*55)
