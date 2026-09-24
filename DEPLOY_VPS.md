# Market Watch AJN — deploy dan operasi VPS

Repo menyimpan kode backend/frontend saja. Data harga dan lokasi tetap di MySQL VPS;
pipeline tidak membuat commit atau mengubah `dist` setiap minggu.

## Deploy sekali setelah review

1. Backup database dan `/etc/cron.d/market-watch`; cek `git status` di VPS.
2. Deploy commit kode ini ke `/var/www/market-watch` dengan prosedur deploy biasa.
   Jangan menimpa perubahan lokal VPS yang belum dibackup.
3. Jalankan build frontend sekali saat deploy: `npm ci && npm run build`.
4. Buat tabel audit pipeline sekali. Ini penting: tanpa tabel ini pipeline tetap
   bisa melakukan scrape, tetapi statusnya tidak akan bisa dimonitor dari admin.

   ```sh
   cd /var/www/market-watch/backend
   venv/bin/python -c 'from app.database import Base, engine; import app.models; Base.metadata.create_all(bind=engine)'
   ```

5. Jalankan tes tanpa menulis database:
   `cd backend && venv/bin/python -m unittest discover -s tests -v`.
6. Jalankan backfill sekali dengan `cd backend && venv/bin/python -m app.scrapers.fishinfo_history`.
   Backfill 20 Mei sampai hari ini mengisi minggu yang belum ada; minggu berjalan
   dan dua minggu sebelumnya dicek ulang untuk koreksi sumber. Proses ini
   menulis hanya DB harga, tanpa mengubah repo atau membangun frontend.
7. Setelah verifikasi, ganti cron lama yang memanggil tiga skrip terpisah dan
   `npm run build` mingguan dengan satu job berikut (zona waktu Asia/Jakarta):

   ```cron
   CRON_TZ=Asia/Jakarta
   15 1 * * * admin cd /var/www/market-watch && /usr/bin/bash run_pipeline.sh >> /var/log/market-watch/pipeline.log 2>&1
   ```

   Buat direktori log agar user `admin` bisa menulis; gunakan logrotate. Jangan
   membiarkan cron lama aktif karena akan membuat snapshot estimasi lebih dulu.
8. Pantau exit status cron dan kesegaran `/market-watch/api/prices` dari luar VPS.
   Respons `fresh: false` atau `latest_date: null` harus memicu notifikasi.
   Cron sendiri hanya menjadwalkan pekerjaan; tanpa monitor, gagal lagi bisa diam-diam.
   Console `/market-watch/admin` menampilkan hasil eksekusi terakhir dari tabel
   `pipeline_runs`; aksesnya wajib memakai akun superadmin yang valid.

## Kontrak data

- `/api/prices` mengutamakan seri historis **rata-rata sederhana harga eceran
  pasar yang tersedia di Jawa Timur (olahan AJN dari data FishInfo Jatim)**.
  Jika backfill belum ada, ringkasan konsumen homepage dipakai sementara.
- Setiap titik seri historis memakai tanggal awal minggu sumber, mencatat
  jumlah harga pasar dan URL filter sumber. Minggu kosong tidak diinterpolasi.
- Minggu berjalan bersifat sementara: jumlah pasar dan rata-rata dapat berubah
  hingga laporan lengkap. Ini bukan harga tambak/TPI/ekspor/nasional.
- `/api/prices/regional` sengaja kosong sampai ada sumber regional yang valid.
- Jika sumber tidak bisa diakses, berubah struktur, terlalu lama, atau berisi
  kurang dari enam harga, scraper exit nonzero dan snapshot terakhir tetap utuh.
- SIHI tidak dijalankan: `sihi.kkp.go.id` gagal DNS dari VPS pada pemeriksaan
  24 September 2026; fallback PIPP yang dipakai kode lama mengembalikan HTTP 404.
  IP Indonesia saja tidak menyelesaikan masalah DNS/endpoint ini.

## Verifikasi pascadeploy

```sh
curl -fsS https://portal.agrinasjaladri.co.id/market-watch/api/prices
curl -fsS https://portal.agrinasjaladri.co.id/market-watch/api/stats
sudo journalctl -u cron --since today
tail -n 100 /var/log/market-watch/pipeline.log
```

Jika eKNMP gagal, cek DNS/TLS dan akun API tanpa mencetak token ke log. Jika
FishInfo gagal, cek periode dan struktur `#tableHead h5`, `#tabel-harga tbody`,
dan `#tb_harga tbody` pada situs resmi. Jangan menjalankan scraper lama untuk
"mengisi" harga dengan angka estimasi.
