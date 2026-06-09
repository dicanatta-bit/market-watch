// Mock data — used when backend is not available
export const mockKnmp = [
  { id_lokasi: 1, nama_kampung: "Kuala Raja", provinsi: "ACEH", kabupaten: "Bireuen", kecamatan: "Kuala", lat: 5.24, lon: 96.73, status_knmp: "HUB", tahun: 2025, penyedia: "PT. Toleransi Aceh", jumlah_nelayan: 300, jumlah_kapal: 278, progress_kumulatif: 100, realisasi_fisik: 80, realisasi_keuangan: 100, snapshot_date: "2026-06-09" },
  { id_lokasi: 2, nama_kampung: "Lancok", provinsi: "ACEH", kabupaten: "Aceh Utara", lat: 5.08, lon: 97.24, status_knmp: "HUB", tahun: 2025, penyedia: "PT. Viola Cipta Mahakarya", jumlah_nelayan: 300, jumlah_kapal: 278, progress_kumulatif: 100, realisasi_fisik: 100, realisasi_keuangan: 100, snapshot_date: "2026-06-09" },
  { id_lokasi: 3, nama_kampung: "Lhok Pawoh", provinsi: "ACEH", kabupaten: "Aceh Barat Daya", lat: 3.76, lon: 96.99, status_knmp: "HUB", tahun: 2025, penyedia: "PT. Kontraktor Aceh", jumlah_nelayan: 200, jumlah_kapal: 150, progress_kumulatif: 100, realisasi_fisik: 70, realisasi_keuangan: 65, snapshot_date: "2026-06-09" },
  { id_lokasi: 4, nama_kampung: "Kayu Batu", provinsi: "PAPUA", kabupaten: "Kota Jayapura", kecamatan: "Jayapura Utara", lat: -2.53, lon: 140.73, status_knmp: "HUB", tahun: 2026, penyedia: "PT. Papua Sejahtera", jumlah_nelayan: 250, jumlah_kapal: 180, progress_kumulatif: 0, realisasi_fisik: 0, realisasi_keuangan: 0, snapshot_date: "2026-06-09" },
  { id_lokasi: 5, nama_kampung: "Enggros", provinsi: "PAPUA", kabupaten: "Kota Jayapura", lat: -2.59, lon: 140.71, status_knmp: "PENYANGGA", tahun: 2026, penyedia: null, jumlah_nelayan: 120, jumlah_kapal: 80, progress_kumulatif: 0, realisasi_fisik: null, realisasi_keuangan: null, snapshot_date: null },
  { id_lokasi: 1363, nama_kampung: "Kuala Tadu", provinsi: "ACEH", kabupaten: "Nagan Raya", lat: 3.69, lon: 96.30, status_knmp: "HUB", tahun: 2026, penyedia: null, jumlah_nelayan: 174, jumlah_kapal: 50, progress_kumulatif: 0, realisasi_fisik: null, realisasi_keuangan: null, snapshot_date: null },
  { id_lokasi: 1364, nama_kampung: "Padang Seurahet", provinsi: "ACEH", kabupaten: "Aceh Barat", lat: 4.45, lon: 96.19, status_knmp: "HUB", tahun: 2026, penyedia: null, jumlah_nelayan: 543, jumlah_kapal: 153, progress_kumulatif: 0, realisasi_fisik: null, realisasi_keuangan: null, snapshot_date: null },
  { id_lokasi: 1365, nama_kampung: "Ujung Pulo Rayeuk", provinsi: "ACEH", kabupaten: "Aceh Selatan", lat: 3.16, lon: 97.29, status_knmp: "PENYANGGA", tahun: 2026, penyedia: null, jumlah_nelayan: 310, jumlah_kapal: 120, progress_kumulatif: 0, realisasi_fisik: null, realisasi_keuangan: null, snapshot_date: null },
]

export const mockPrices = [
  { komoditas: "Udang Vaname (Litopenaeus vannamei)", size: "Size 50", harga_tambak_low: 60000, harga_tambak_high: 65000, harga_ekspor_low: 3.55, harga_ekspor_high: 3.64, sumber: "JALA Tech; KKP DJPB; UCN" },
  { komoditas: "Udang Vaname (Litopenaeus vannamei)", size: "Size 60", harga_tambak_low: 55000, harga_tambak_high: 60000, harga_ekspor_low: 3.55, harga_ekspor_high: 3.55, sumber: "JALA Tech; KKP DJPB" },
  { komoditas: "Udang Windu (Penaeus monodon)", size: "Size 20", harga_tambak_low: 100000, harga_tambak_high: 120000, harga_ekspor_low: 8.00, harga_ekspor_high: 10.00, sumber: "KKP DJPB; JALA Tech" },
  { komoditas: "Nila (Oreochromis niloticus)", size: "300-500 g", harga_tambak_low: 22000, harga_tambak_high: 28000, harga_ekspor_low: 3.00, harga_ekspor_high: 4.00, sumber: "KKP DJPB; BPS" },
  { komoditas: "Tuna Sirip Kuning / Yellowfin (Thunnus albacares)", size: "Sashimi grade", harga_tambak_low: 60000, harga_tambak_high: 80000, harga_ekspor_low: 5.00, harga_ekspor_high: 8.00, sumber: "KKP; ASTUIN; PPS Bitung" },
  { komoditas: "Tuna Cakalang (Katsuwonus pelamis)", size: "-", harga_tambak_low: 15000, harga_tambak_high: 25000, harga_ekspor_low: 1.50, harga_ekspor_high: 2.50, sumber: "KKP; PPS Bitung" },
  { komoditas: "Rumput Laut (Eucheuma cottonii)", size: "Kering", harga_tambak_low: 6000, harga_tambak_high: 7000, harga_ekspor_low: 0.40, harga_ekspor_high: 0.50, sumber: "KKP DJPB" },
  { komoditas: "Lobster (Panulirus ornatus) / Mutiara", size: ">200 g", harga_tambak_low: 280000, harga_tambak_high: 380000, harga_ekspor_low: 18.00, harga_ekspor_high: 22.00, sumber: "KKP; Pelabuhan Perikanan" },
  { komoditas: "Bandeng (Chanos chanos)", size: "250-500 g", harga_tambak_low: 20000, harga_tambak_high: 28000, harga_ekspor_low: 1.80, harga_ekspor_high: 2.50, sumber: "KKP DJPB" },
  { komoditas: "Cumi-cumi (Loligo spp.)", size: "-", harga_tambak_low: 35000, harga_tambak_high: 50000, harga_ekspor_low: 3.50, harga_ekspor_high: 5.00, sumber: "KKP; Pelabuhan Perikanan" },
]

export const mockRegional = {
  "Jawa-Bali": [{ komoditas: "Udang Vaname", size: "Size 50", harga_low: 60000, harga_high: 65000 }, { komoditas: "Bandeng", size: "250-500 g", harga_low: 20000, harga_high: 28000 }],
  "Sumatera": [{ komoditas: "Udang Vaname", size: "Size 50", harga_low: 57000, harga_high: 61750 }, { komoditas: "Udang Windu", size: "Size 20", harga_low: 95000, harga_high: 114000 }],
  "Sulawesi": [{ komoditas: "Udang Windu", size: "Size 20", harga_low: 90000, harga_high: 108000 }, { komoditas: "Rumput Laut", size: "Kering", harga_low: 5400, harga_high: 6300 }],
  "Papua": [{ komoditas: "Tuna Yellowfin", size: "Sashimi grade", harga_low: 51000, harga_high: 68000 }, { komoditas: "Lobster Mutiara", size: ">200 g", harga_low: 238000, harga_high: 323000 }],
}

export const mockStats = {
  total_lokasi: 723, selesai: 63, berjalan: 36, total_nelayan: 278835, total_kapal: 126674
}
