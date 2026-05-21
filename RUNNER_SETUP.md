# Setup Self-Hosted GitHub Actions Runner (Windows)

Runner lokal dibutuhkan supaya `scrape_sihi.py` bisa mengakses SIHI/PIPP KKP (situs yang hanya bisa diakses dari IP Indonesia).

## Prasyarat

- Windows 10/11, 64-bit
- Python 3.12+ sudah terinstall dan ada di PATH
- Git + Git Bash sudah terinstall
- Koneksi internet Indonesia (tidak melalui VPN luar negeri)

---

## Langkah 1 — Buat folder runner

Buka PowerShell sebagai Administrator:

```powershell
mkdir C:\actions-runner
cd C:\actions-runner
```

---

## Langkah 2 — Download runner dari GitHub

Buka: **https://github.com/dicanatta-bit/market-watch/settings/actions/runners/new**

Pilih **OS: Windows**, **Architecture: x64**, lalu copy-paste dua blok perintah yang ditampilkan GitHub (Download + Configure). Token di blok Configure berlaku 1 jam.

Contoh bentuknya (versi bisa berbeda):

```powershell
# Download
Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.323.0/actions-runner-win-x64-2.323.0.zip -OutFile actions-runner-win-x64.zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("$PWD\actions-runner-win-x64.zip", "$PWD")

# Configure (gunakan perintah dari GitHub — bukan contoh ini)
.\config.cmd --url https://github.com/dicanatta-bit/market-watch --token ABCXYZ123
```

Saat konfigurasi ditanya:
- **Runner name**: `market-watch-local` (terserah)
- **Runner group**: Enter (default)
- **Additional labels**: `indonesia` (opsional, untuk kejelasan)
- **Work folder**: Enter (default `_work`)

---

## Langkah 3 — Install sebagai Windows Service (direkomendasikan)

Supaya runner otomatis aktif setiap PC dinyalakan:

```powershell
cd C:\actions-runner
.\svc.cmd install
.\svc.cmd start
```

Cek status: `.\svc.cmd status`

> **Catatan:** Workflow berjalan Senin pukul 08:00 WIB. Pastikan PC tidak sleep/hibernate sebelum jam 08:30 WIB.

---

## Langkah 4 — Jalankan manual (alternatif tanpa service)

Double-click **`Start Runner.bat`** di folder ini, atau:

```
cd C:\actions-runner
run.cmd
```

Runner aktif ditandai dengan pesan `Listening for Jobs`.

---

## Troubleshooting

| Gejala | Kemungkinan penyebab | Solusi |
|--------|---------------------|--------|
| Job antri tapi tidak jalan | Runner offline | Jalankan `Start Runner.bat` atau cek Windows Service |
| `run.cmd tidak ditemukan` | Bat dijalankan dari folder salah | Copy `Start Runner.bat` ke `C:\actions-runner\` |
| Scrape SIHI gagal | Koneksi bukan IP Indonesia | Pastikan tidak sedang VPN luar negeri |
| `pip install` error | Python tidak di PATH | Tambah Python ke System PATH di Environment Variables |

---

## Struktur Workflow

```
auto_update.yml
 ├── Job: scrape_tpi    → runs-on: [self-hosted, Windows, X64]
 │    scrape_sihi.py → match_tpi_knmp.py → commit data/
 │
 └── Job: update        → runs-on: ubuntu-latest  (if: always)
      auto_update.py → infografis → laporan → commit output/ index.html
```

Job `update` menunggu `scrape_tpi` selesai dulu, lalu checkout fresh (sudah include data TPI terbaru).
Jika runner offline, `scrape_tpi` akan antri. **Job `update` baru jalan setelah `scrape_tpi` selesai atau runner online.**
