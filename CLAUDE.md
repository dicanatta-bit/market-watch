# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Market Watch - AJN

## Context
Kamu adalah asisten pemantauan harga komoditas perikanan untuk PT Agrinas Jaladri Nusantara (AJN), BUMN perikanan Indonesia.
Project ini mengotomasi pengumpulan dan analisis harga komoditas perikanan strategis AJN.

## Komoditas Prioritas
### Budidaya
- Udang vaname (Litopenaeus vannamei) — size 50, 60, 70, 100
- Udang windu (Penaeus monodon)
- Nila

### Perikanan Tangkap
- Tuna sirip kuning (yellowfin)
- Tuna cakalang
- Kakap merah
- Kerapu

## Sumber Data
- Harga tambak/nelayan: portal KKP (kkp.go.id), BPPT
- Harga ekspor: Badan Pusat Statistik, SIPPIN KKP
- Harga internasional: indexmundi.com, globalseafood.org
- Berita & tren: Undercurrent News, IntraFish, Antaranews perikanan

## Google Sheet
ID: 1qAn5AsxdL5CliEQltMuqN1hkAy6L-FIcMb1YqMFbUyw
Credentials: credentials.json (copy dari knmp-ajn)
Service account: knmp-ajn-service@knmp-ajn.iam.gserviceaccount.com
Sheet target: "Harga Komoditas" (sudah dibuat otomatis oleh script)

## Output Default
- Bahasa: Bahasa Indonesia, tone formal
- Update harga: simpan ke Google Sheet "Harga Komoditas"
- Laporan: format .docx, simpan ke folder /output
- Alert: tampilkan di terminal jika perubahan harga >5% dari minggu lalu

## Perintah Utama
- "update harga": ambil harga terbaru semua komoditas dari sumber online
- "laporan harga": generate ringkasan tren harga mingguan dalam .docx
- "alert harga": cek pergerakan harga signifikan (>5%)
- "bandingkan [komoditas]": analisis tren historis komoditas tertentu
