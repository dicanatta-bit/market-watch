"""
Market Watch - AJN
Entry point untuk GitHub Actions: update harga + rebuild infografis.
"""

import subprocess
import sys
import os
from datetime import datetime

SPREADSHEET_ID = "1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw"


def run(script, *args):
    cmd = [sys.executable, script, *args]
    print(f"\n{'='*50}")
    print(f"Menjalankan: {' '.join(cmd)}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {script} gagal dengan exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    print(f"Market Watch AJN — Auto Update")
    print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    run("update_harga.py", SPREADSHEET_ID)
    run("buat_infografis.py")

    print("\nAuto update selesai.")
