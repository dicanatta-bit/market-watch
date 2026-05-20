# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Market Watch - AJN

Dashboard pemantauan harga komoditas perikanan untuk PT Agrinas Jaladri Nusantara (BUMN perikanan Indonesia). Pipeline otomatis: scraping → Google Sheet → HTML dashboard + PDF laporan mingguan.

## Menjalankan Pipeline

```bash
# Pipeline lengkap (scraping + sheet + HTML + PDF)
python auto_update.py

# Tes HTML lokal dengan data statis (tanpa Google Sheets)
python buat_infografis.py --test-html

# Skrip individual (semua bisa dijalankan standalone)
python update_harga.py
python alert_engine.py
python buat_infografis.py   # butuh credentials.json
python laporan_mingguan.py
python sheet_formatter.py
```

Install dependensi: `pip install -r requirements.txt`

## Arsitektur

```
auto_update.py          ← orchestrator, memanggil skrip di bawah secara berurutan
│
├── update_harga.py     ← scraping harga (shrimpnews, FAO, KKP) → sheet "Harga Komoditas"
├── alert_engine.py     ← deteksi pergerakan >5% → sheet "Alert Log"
├── buat_infografis.py  ← baca sheet → build sheet "Infografis" + generate HTML dashboard
│     └── sheet_formatter.py  (dipanggil oleh buat_infografis)
└── laporan_mingguan.py ← baca sheet → PDF 1 halaman ke /output/
```

**Output:**
- `index.html` — dashboard interaktif (diperbarui setiap run, di-push ke GitHub Pages)
- `output/MarketWatch_AJN_YYYYMMDD.html` — arsip harian
- `output/MarketWatch_AJN_YYYYMMDD.pdf` — laporan PDF mingguan

## Google Sheets

| Sheet | Ditulis oleh | Dibaca oleh |
|-------|-------------|-------------|
| Harga Komoditas | `update_harga.py` | `alert_engine.py`, `buat_infografis.py` |
| Alert Log | `alert_engine.py` | `buat_infografis.py` |
| Infografis | `buat_infografis.py` | — |

- **Spreadsheet ID:** `1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw`
- **Credentials:** `credentials.json` (service account `knmp-ajn-service@knmp-ajn.iam.gserviceaccount.com`)
- `credentials.json` ada di `.gitignore` — jangan di-commit

## HTML Dashboard (`buat_infografis.py`)

HTML di-generate sebagai f-string raksasa (`html = f"""..."""`) mulai sekitar baris 700. Karena ini f-string Python:
- CSS class selector pakai `{{` dan `}}` sebagai escape (bukan `{` `}`)
- `{TGL}`, `{all_cards}`, dll. adalah variable Python yang di-interpolate
- Flag `--test-html` untuk render lokal dengan `STATIC_PRICES` (tanpa Sheet)

Setelah mengubah template HTML/CSS di `buat_infografis.py`, jalankan `python buat_infografis.py` untuk regenerate `index.html`, lalu push ke GitHub.

## Alert Engine

Empat level alert (didefinisikan di `alert_engine.py`):
- **MERAH** — pergerakan harga tambak >5% minggu ke minggu
- **KUNING** — gap harga ekspor vs tambak >40% (peluang agregator)
- **BIRU** — harga internasional turun >10%
- Threshold dan rekomendasi ada di dict `REKOMENDASI` dan konstanta di atas fungsi `check_alerts()`

## Komoditas & Kolom Sheet

Sheet "Harga Komoditas" punya 14 kolom (A–N): Tanggal, Komoditas, Size, Harga Tambak (Rp/kg), Harga Ekspor (USD/kg), Harga Internasional (USD/kg), Harga Minggu Lalu, Harga 1 Bulan Lalu, Harga 3 Bulan Lalu, % vs Minggu Lalu, % vs 3 Bulan Lalu, Sumber, Tingkat Kepercayaan, Catatan.

Komoditas prioritas: Udang Vaname (size 50/60/70/100), Udang Windu, Nila, Tuna Yellowfin, Tuna Cakalang, Kakap Merah, Kerapu, Lobster Mutiara/Pasir, Rumput Laut, Bandeng, Patin, Cumi-cumi.
