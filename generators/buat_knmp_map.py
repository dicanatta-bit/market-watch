"""
generators/buat_knmp_map.py — Generate knmp.html peta dari MySQL
Query: knmp_locations + latest snapshots → embedded JS → static HTML
"""
import json, os, sys
from datetime import date as dt
from config import Config
from app import create_app
from models import (
    db, KnmpLocation, KnmpLocationSnapshot, KnmpProgressItem,
    KnmpProgressUpdate, TpiPrice, CommodityPrice, RegionalPrice,
)

WILAYAH_FAKTOR = {
    "Jawa-Bali": 1.00, "Sumatera": 0.95, "Kalimantan": 0.92,
    "Sulawesi": 0.90, "NTT-NTB": 0.88, "Maluku": 0.85, "Papua": 0.85,
}

PROVINSI_WILAYAH = {
    "ACEH": "Sumatera", "SUMATERA UTARA": "Sumatera", "SUMATRA UTARA": "Sumatera",
    "SUMATERA BARAT": "Sumatera", "SUMATRA BARAT": "Sumatera",
    "RIAU": "Sumatera", "KEPULAUAN RIAU": "Sumatera", "JAMBI": "Sumatera",
    "SUMATERA SELATAN": "Sumatera", "SUMATRA SELATAN": "Sumatera",
    "BENGKULU": "Sumatera", "LAMPUNG": "Sumatera",
    "KEPULAUAN BANGKA BELITUNG": "Sumatera", "BANGKA BELITUNG": "Sumatera",
    "DKI JAKARTA": "Jawa-Bali", "JAKARTA": "Jawa-Bali",
    "JAWA BARAT": "Jawa-Bali", "JAWA TENGAH": "Jawa-Bali",
    "DI YOGYAKARTA": "Jawa-Bali", "JAWA TIMUR": "Jawa-Bali",
    "BANTEN": "Jawa-Bali", "BALI": "Jawa-Bali",
    "KALIMANTAN BARAT": "Kalimantan", "KALIMANTAN TENGAH": "Kalimantan",
    "KALIMANTAN SELATAN": "Kalimantan", "KALIMANTAN TIMUR": "Kalimantan",
    "KALIMANTAN UTARA": "Kalimantan",
    "SULAWESI UTARA": "Sulawesi", "SULAWESI TENGAH": "Sulawesi",
    "SULAWESI SELATAN": "Sulawesi", "SULAWESI TENGGARA": "Sulawesi",
    "GORONTALO": "Sulawesi", "SULAWESI BARAT": "Sulawesi",
    "NUSA TENGGARA BARAT": "NTT-NTB", "NTB": "NTT-NTB",
    "NUSA TENGGARA TIMUR": "NTT-NTB", "NTT": "NTT-NTB",
    "MALUKU": "Maluku", "MALUKU UTARA": "Maluku",
    "PAPUA": "Papua", "PAPUA BARAT": "Papua",
    "PAPUA PEGUNUNGAN": "Papua", "PAPUA SELATAN": "Papua",
    "PAPUA TENGAH": "Papua", "PAPUA BARAT DAYA": "Papua",
}

_SHORT_NAMES = {
    "Udang Vaname (Litopenaeus vannamei)": "Udang Vaname",
    "Udang Windu (Penaeus monodon)": "Udang Windu",
    "Nila (Oreochromis niloticus)": "Nila",
    "Tuna Sirip Kuning / Yellowfin (Thunnus albacares)": "Tuna Yellowfin",
    "Tuna Cakalang (Katsuwonus pelamis)": "Tuna Cakalang",
    "Kakap Merah (Lutjanus spp.)": "Kakap Merah",
    "Kerapu (Epinephelus spp.)": "Kerapu",
    "Rumput Laut (Eucheuma cottonii)": "Rumput Laut",
    "Lobster (Panulirus ornatus) / Mutiara": "Lobster Mutiara",
    "Lobster (Panulirus homarus) / Pasir": "Lobster Pasir",
    "Bandeng (Chanos chanos)": "Bandeng",
    "Cumi-cumi (Loligo spp.)": "Cumi-cumi",
    "Patin (Pangasianodon hypophthalmus)": "Patin",
}


def build_harga_wilayah(prices):
    """Convert regional_prices from DB into the {wilayah: [{k,s,t}]} format."""
    result = {}
    for p in prices:
        w = p.wilayah
        if w not in result:
            result[w] = []
        short = _SHORT_NAMES.get(p.komoditas, p.komoditas.split("(")[0].strip()[:20])
        low = int(p.harga_tambak_low or 0)
        high = int(p.harga_tambak_high or 0)
        t_str = f"{low:,.0f} – {high:,.0f}".replace(",", ".")
        result[w].append({"k": short, "s": p.size, "t": t_str})
    return result


def generate():
    app = create_app(Config)
    with app.app_context():
        print("=" * 55)
        print("KNMP Map Generator — MySQL → knmp.html")
        print("=" * 55)

        # ── Query all locations ──
        locations = KnmpLocation.query.all()
        print(f"  Locations: {len(locations)}")

        # ── Latest snapshots ──
        sub = (
            db.session.query(
                KnmpLocationSnapshot.id_lokasi,
                db.func.max(KnmpLocationSnapshot.snapshot_date).label("max_date"),
            )
            .group_by(KnmpLocationSnapshot.id_lokasi)
            .subquery()
        )
        snapshots = {
            s.id_lokasi: s
            for s in KnmpLocationSnapshot.query.join(
                sub,
                db.and_(
                    KnmpLocationSnapshot.id_lokasi == sub.c.id_lokasi,
                    KnmpLocationSnapshot.snapshot_date == sub.c.max_date,
                ),
            ).all()
        }
        print(f"  Snapshots: {len(snapshots)}")

        # ── Regional prices ──
        latest_rp_date = db.session.query(db.func.max(RegionalPrice.tanggal)).scalar()
        if latest_rp_date:
            rp = RegionalPrice.query.filter_by(tanggal=latest_rp_date).all()
        else:
            rp = []
        harga_wilayah = build_harga_wilayah(rp)
        print(f"  Regional prices: {len(rp)} rows from {latest_rp_date}")

        # ── TPI prices ──
        tpi_list = TpiPrice.query.order_by(TpiPrice.tanggal.desc()).limit(500).all()
        tpi_map = {}
        for t in tpi_list:
            tpi_map.setdefault(str(t.id_lokasi), []).append({
                "tpi": t.nama_tpi or "",
                "komoditas": t.komoditas,
                "harga": int(t.harga) if t.harga else 0,
                "tanggal": str(t.tanggal),
            })
        print(f"  TPI prices: {len(tpi_list)} from {len(tpi_map)} locations")

        # ── Build markers ──
        markers = []
        for loc in locations:
            snap = snapshots.get(loc.id_lokasi)
            m = {
                "id": str(loc.id_lokasi),
                "nama": loc.nama_kampung or "",
                "provinsi": (loc.provinsi or "").upper(),
                "kabupaten": loc.kabupaten or "",
                "kecamatan": loc.kecamatan or "",
                "desa": loc.desa or "",
                "lat": loc.lat,
                "lon": loc.lon,
                "status_knmp": loc.status_knmp or "",
                "status_progres": loc.status_progres or "",
                "penyedia": loc.penyedia or "",
                "tahun": loc.tahun,
                "nelayan": loc.jumlah_nelayan,
                "kapal": loc.jumlah_kapal,
                "sumber": "eknmp",
                "progress": snap.progress_kumulatif if snap else None,
                "realisasi_fisik": snap.realisasi_fisik if snap else None,
                "realisasi_keuangan": snap.realisasi_keuangan if snap else None,
                "snapshot_date": str(snap.snapshot_date) if snap else None,
                "kendala": snap.kendala if snap else None,
                "tindak_lanjut": snap.tindak_lanjut if snap else None,
            }
            markers.append(m)

        # ── Stats ──
        total = len(markers)
        n_eknmp = len([m for m in markers if snapshots.get(int(m["id"]))])
        n_selesai = len([m for m in markers if (m["progress"] or 0) >= 100])
        n_berjalan = len([m for m in markers if 0 < (m["progress"] or 0) < 100])

        progress_per_loc = [m["progress"] for m in markers if m["progress"] is not None]
        avg_progress = sum(progress_per_loc) / len(progress_per_loc) if progress_per_loc else 0

        prov_all = sorted(set(m["provinsi"] for m in markers if m["provinsi"]))

        # ── Serialize for JS ──
        marker_js = json.dumps(markers, ensure_ascii=False, separators=(",", ":"))
        harga_js = json.dumps(harga_wilayah, ensure_ascii=False, separators=(",", ":"))
        tpi_js = json.dumps(tpi_map, ensure_ascii=False, separators=(",", ":"))
        prov_wil_js = json.dumps(PROVINSI_WILAYAH, ensure_ascii=False, separators=(",", ":"))
        prov_opts = "\n              ".join(
            f'<option value="{p}">{p.title()}</option>' for p in prov_all
        )

        from datetime import datetime
        now = datetime.now()
        tgl = now.strftime("%d %B %Y")
        tgl_harga = now.strftime("%d/%m/%Y")

        fmt = lambda n: f"Rp {n/1e12:.2f} T" if n>=1e12 else f"Rp {n/1e9:.2f} M" if n>=1e9 else f"Rp {n/1e6:.0f} Jt" if n>=1e6 else f"Rp {n:,.0f}" if n else "—"

        # ── HTML template ──
        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Peta KNMP — Market Watch AJN</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;font-family:'Segoe UI',system-ui,sans-serif;background:#0a1128;overflow:hidden;color:#e2e8f0}}
#hdr{{position:fixed;top:0;left:0;right:0;z-index:1000;height:52px;background:linear-gradient(135deg,#0f1d3d 0%,#0a1628 100%);display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-bottom:1px solid rgba(201,168,76,.25)}}
#hdr-brand{{display:flex;flex-direction:column;gap:1px}}
#hdr-title{{font-size:.95rem;font-weight:700;color:#C9A84C;letter-spacing:.3px}}
#hdr-sub{{font-size:.62rem;color:rgba(148,163,184,.6)}}
#hdr-right{{display:flex;align-items:center;gap:10px}}
.hdr-chip{{font-size:.7rem;background:rgba(201,168,76,.12);border:1px solid rgba(201,168,76,.3);color:#C9A84C;padding:3px 10px;border-radius:14px;white-space:nowrap}}
.hdr-chip.live{{border-color:rgba(16,185,129,.4);color:#10B981;background:rgba(16,185,129,.1)}}
#hdr-date{{font-size:.65rem;color:rgba(148,163,184,.5)}}

/* ── Nav ── */
.nav-bar{{position:fixed;top:52px;left:0;right:0;z-index:999;background:#0a1628;border-top:1px solid rgba(201,168,76,.2)}}
.nav-bar-inner{{max-width:1400px;margin:0 auto;padding:0 20px;display:flex;gap:0}}
.nav-link{{color:rgba(255,255,255,.4);text-decoration:none;font-size:.72rem;font-weight:500;padding:7px 14px;border-bottom:2px solid transparent;transition:all .15s}}
.nav-link:hover{{color:#C9A84C;background:rgba(201,168,76,.06)}}
.nav-link.active{{color:#C9A84C;border-bottom-color:#C9A84C;background:rgba(201,168,76,.08)}}

/* ── Layout ── */
#layout{{display:flex;height:100vh;padding-top:84px}}
#sidebar{{width:270px;flex-shrink:0;background:rgba(15,29,61,.6);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);overflow-y:auto;overflow-x:hidden;padding:12px;display:flex;flex-direction:column;gap:8px;border-right:1px solid rgba(201,168,76,.12)}}
#sidebar::-webkit-scrollbar{{width:3px}}
#sidebar::-webkit-scrollbar-thumb{{background:rgba(201,168,76,.25);border-radius:2px}}
.panel{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:10px;padding:12px 14px;backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px)}}
.ptitle{{font-size:.62rem;font-weight:700;color:#C9A84C;text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px;display:flex;align-items:center;gap:6px}}
.ptitle::before{{content:"";width:4px;height:4px;border-radius:50%;background:#C9A84C;flex-shrink:0}}
.stats-grid{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}
.stat-box{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.05);border-radius:8px;padding:8px 10px;transition:all .2s}}
.stat-box:hover{{background:rgba(201,168,76,.05);border-color:rgba(201,168,76,.15)}}
.stat-num{{font-size:1.3rem;font-weight:800;color:#C9A84C;line-height:1.1}}
.stat-num.green{{color:#10B981}}
.stat-lbl{{font-size:.6rem;color:rgba(148,163,184,.7);margin-top:2px}}
.stat-box.wide{{grid-column:1/-1}}
#search{{width:100%;padding:8px 12px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:8px;color:#e2e8f0;font-size:.8rem;outline:none}}
#search::placeholder{{color:rgba(255,255,255,.2)}}
#search:focus{{border-color:rgba(201,168,76,.4)}}
select{{width:100%;padding:7px 10px;background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:8px;color:#e2e8f0;font-size:.76rem;outline:none;cursor:pointer;-webkit-appearance:none}}
select option{{background:#0f1d3d;color:#e2e8f0}}
select:focus{{border-color:rgba(201,168,76,.4)}}
.flbl{{display:block;font-size:.65rem;color:rgba(148,163,184,.6);margin-bottom:4px}}
.fgap{{height:6px}}
#btn-reset{{width:100%;padding:7px;margin-top:8px;background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.2);border-radius:8px;color:#C9A84C;font-size:.75rem;font-weight:600;cursor:pointer;transition:all .15s}}
#btn-reset:hover{{background:rgba(201,168,76,.18)}}
#filter-count{{font-size:.68rem;color:rgba(96,165,250,.8);margin-top:6px;display:none;text-align:center}}
.prog-item{{display:flex;justify-content:space-between;align-items:center;padding:5px 8px;border-radius:6px;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.04)}}
.prog-label{{font-size:.62rem;color:rgba(148,163,184,.7)}}
.prog-value{{font-size:.72rem;font-weight:700;color:#C9A84C}}
.prog-value.green{{color:#10B981}}

.leg-item{{display:flex;align-items:center;gap:7px;padding:3px 0;font-size:.7rem;color:rgba(203,213,225,.7)}}
.leg-dot{{width:9px;height:9px;border-radius:50%;flex-shrink:0;border:1.5px solid rgba(255,255,255,.2)}}
.leg-star{{width:16px;height:16px;border-radius:3px;flex-shrink:0;border:1.5px solid rgba(255,255,255,.3);display:flex;align-items:center;justify-content:center;font-size:9px;color:#fff}}
.leg-cnt{{margin-left:auto;font-size:.6rem;color:rgba(148,163,184,.5);font-variant-numeric:tabular-nums}}
.leg-sep{{font-size:.58rem;color:#C9A84C;font-weight:700;text-transform:uppercase;letter-spacing:.6px;margin:4px 0 2px}}
#map{{flex:1;z-index:0}}

.leaflet-control-zoom a{{background:rgba(15,29,61,.85)!important;color:#e2e8f0!important;border-color:rgba(201,168,76,.2)!important;backdrop-filter:blur(8px)}}
.leaflet-control-attribution{{background:rgba(10,22,40,.7)!important;color:rgba(255,255,255,.3)!important;font-size:.55rem!important}}
.leaflet-popup-content-wrapper{{border-radius:12px;padding:0;box-shadow:0 8px 32px rgba(0,0,0,.5);background:linear-gradient(135deg,#0f1d3d 0%,#0a1628 100%);border:1px solid rgba(201,168,76,.15);overflow:hidden}}
.leaflet-popup-content{{margin:0;min-width:280px;max-width:380px;color:#e2e8f0}}
.leaflet-popup-tip{{background:#0f1d3d;border:1px solid rgba(201,168,76,.15)}}
.leaflet-popup-close-button{{color:#C9A84C!important;font-size:18px!important;padding:6px!important}}

.pu-head{{color:#C9A84C;font-weight:700;font-size:.85rem;padding:10px 14px;background:linear-gradient(135deg,rgba(201,168,76,.08),rgba(201,168,76,.02));border-bottom:1px solid rgba(201,168,76,.1);display:flex;align-items:center;gap:6px}}
.pu-progress-bar{{height:5px;background:rgba(255,255,255,.06);margin:0}}
.pu-progress-fill{{height:100%;border-radius:0 2px 2px 0;transition:width .5s ease}}
.pu-body{{padding:8px 14px}}
.pu-row{{display:flex;justify-content:space-between;align-items:baseline;font-size:.72rem;padding:3px 0;border-bottom:1px dotted rgba(255,255,255,.04)}}
.pu-row-k{{color:rgba(148,163,184,.7);flex-shrink:0}}
.pu-row-v{{color:#e2e8f0;font-weight:600;text-align:right;margin-left:8px}}
.pu-badges{{display:flex;gap:5px;flex-wrap:wrap;padding:4px 14px}}
.pu-badge{{display:inline-block;padding:2px 8px;border-radius:8px;font-size:.62rem;font-weight:700}}
.badge-hub{{background:rgba(16,185,129,.15);color:#10B981}}
.badge-prog{{background:rgba(245,158,11,.15);color:#F59E0B}}
.badge-siap{{background:rgba(96,165,250,.15);color:#60A5FA}}
.badge-selesai{{background:rgba(16,185,129,.2);color:#10B981}}
.pu-section{{border-top:1px solid rgba(255,255,255,.06);padding:8px 14px}}
.pu-section-title{{font-size:.6rem;font-weight:700;color:rgba(148,163,184,.5);text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px}}
.pu-harga-row{{display:flex;justify-content:space-between;align-items:baseline;font-size:.68rem;padding:2px 0}}
.pu-harga-k{{color:rgba(148,163,184,.8);flex:1}}
.pu-harga-v{{color:#C9A84C;font-weight:700;white-space:nowrap;margin-left:6px}}
.pu-harga-note{{font-size:.55rem;color:rgba(148,163,184,.4);margin-top:4px}}
.pu-kendala{{font-size:.65rem;color:#F59E0B;padding:2px 0}}
.pu-tindak{{font-size:.65rem;color:#10B981;padding:2px 0}}
.pu-footer{{padding:6px 14px;font-size:.55rem;color:rgba(148,163,184,.3);border-top:1px solid rgba(255,255,255,.03);display:flex;justify-content:space-between}}
@media(max-width:600px){{#sidebar{{display:none}}#hdr-date{{display:none}}}}
</style>
</head>
<body>

<div id="hdr">
  <div id="hdr-brand">
    <div id="hdr-title">Peta KNMP Nasional</div>
    <div id="hdr-sub">Market Watch AJN — PT Agrinas Jaladri Nusantara (Persero)</div>
  </div>
  <div id="hdr-right">
    {f'<div class="hdr-chip live">&#9679; {n_eknmp} Live</div>' if n_eknmp > 0 else ''}
    <div class="hdr-chip">{total:,} Lokasi</div>
    <div id="hdr-date">{tgl}</div>
  </div>
</div>

<div class="nav-bar">
  <div class="nav-bar-inner">
    <a class="nav-link" href="./index.html">&#128202; Harga</a>
    <a class="nav-link active" href="./knmp.html">&#128506;&#65039; Peta KNMP</a>
  </div>
</div>

<div id="layout">
  <div id="sidebar">
    <div class="panel">
      <div class="ptitle">Ringkasan</div>
      <div class="stats-grid">
        <div class="stat-box"><div class="stat-num" id="st-total">{total}</div><div class="stat-lbl">Total Lokasi</div></div>
        <div class="stat-box"><div class="stat-num green" id="st-live">{n_eknmp}</div><div class="stat-lbl">Live eKNMP</div></div>
        <div class="stat-box"><div class="stat-num" id="st-selesai">{n_selesai}</div><div class="stat-lbl">Selesai</div></div>
        <div class="stat-box"><div class="stat-num" id="st-berjalan">{n_berjalan}</div><div class="stat-lbl">Berjalan</div></div>
        <div class="stat-box wide"><div class="stat-num sm">{avg_progress:.1f}%</div><div class="stat-lbl">Progress Nasional</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="ptitle">Progress Minggu Ini</div>
      <div class="prog-cards">
        <div class="prog-item"><span class="prog-label">Lokasi di-track</span><span class="prog-value">{n_eknmp}</span></div>
        <div class="prog-item"><span class="prog-label">Selesai (100%)</span><span class="prog-value green">{n_selesai}</span></div>
        <div class="prog-item"><span class="prog-label">Berjalan</span><span class="prog-value">{n_berjalan}</span></div>
      </div>
    </div>

    <div class="panel">
      <div class="ptitle">Cari</div>
      <input type="text" id="search" placeholder="Nama, kab, penyedia…">
    </div>

    <div class="panel">
      <div class="ptitle">Filter</div>
      <label class="flbl">Provinsi</label>
      <select id="filter-prov">
        <option value="">Semua Provinsi</option>
        {prov_opts}
      </select>
      <div class="fgap"></div>
      <label class="flbl">Status</label>
      <select id="filter-status">
        <option value="">Semua</option>
        <option value="HUB">HUB</option>
        <option value="PENYANGGA">Penyangga</option>
        <option value="selesai">Selesai (100%)</option>
        <option value="berjalan">Berjalan</option>
      </select>
      <div class="fgap"></div>
      <label class="flbl">Jenis Data</label>
      <select id="filter-sumber">
        <option value="">Semua</option>
        <option value="eknmp">eKNMP Live</option>
      </select>
      <button id="btn-reset">&#x21BA; Reset Filter</button>
      <div id="filter-count"></div>
    </div>

    <div class="panel">
      <div class="ptitle">Legenda</div>
      <div class="leg-sep">Status</div>
      <div class="leg-item"><span class="leg-dot" style="background:#10B981"></span><span>Selesai (100%)</span><span class="leg-cnt" id="lc-selesai"></span></div>
      <div class="leg-item"><span class="leg-dot" style="background:#F59E0B"></span><span>Berjalan</span><span class="leg-cnt" id="lc-berjalan"></span></div>
      <div class="leg-item"><span class="leg-dot" style="background:#60A5FA"></span><span>Siap Dibangun</span><span class="leg-cnt" id="lc-siap"></span></div>
    </div>
  </div>

  <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const MARKERS = {marker_js};
const TPI      = {tpi_js};
const HARGA_WILAYAH   = {harga_js};
const PROVINSI_WILAYAH = {prov_wil_js};
const HARGA_TGL = '{tgl_harga}';
const TOTAL_ALL = {total};

function esc(s){{return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}

function buildHargaHTML(prov){{
  const wil = PROVINSI_WILAYAH[prov]||null;
  if(!wil||!HARGA_WILAYAH[wil]||!HARGA_WILAYAH[wil].length)return'';
  const rows = HARGA_WILAYAH[wil].slice(0,4);
  const rowsHtml = rows.map(h=>
    '<div class="pu-harga-row"><span class="pu-harga-k">'+esc(h.k)+' <em style="color:rgba(148,163,184,.5);font-style:normal">'+esc(h.s)+'</em></span><span class="pu-harga-v">Rp '+esc(h.t)+'/kg</span></div>'
  ).join('');
  return'<div class="pu-section"><div class="pu-section-title">&#128722; Harga Komoditas — '+esc(wil)+'</div>'+rowsHtml+'<div class="pu-harga-note">Per '+HARGA_TGL+' · Estimasi tingkat nelayan/tambak</div></div>';
}}

function buildTPIHTML(mid){{
  const tpis = TPI[mid];
  if(!tpis||!tpis.length)return'';
  const rows = tpis.slice(0,3).map(t=>
    '<div class="pu-harga-row"><span class="pu-harga-k">'+esc(t.komoditas)+' <em style="color:rgba(148,163,184,.4);font-style:normal">'+esc(t.tpi)+'</em></span><span class="pu-harga-v">Rp '+esc(t.harga)+'/kg</span></div>'
  ).join('');
  return'<div class="pu-section"><div class="pu-section-title">&#128031; Harga TPI Terdekat</div>'+rows+'</div>';
}}

function buildPopup(m){{
  const p = m.progress;
  const sts = p!==null&&p>=100?'selesai':p!==null&&p>0?'berjalan':'siap';
  const sc = sts==='selesai'?'#10B981':sts==='berjalan'?'#F59E0B':'#60A5FA';
  const sLabel = sts==='selesai'?'Selesai':sts==='berjalan'?'Berjalan':'Siap Dibangun';
  const progBar = p!==null
    ?'<div class="pu-progress-bar"><div class="pu-progress-fill" style="width:'+p+'%;background:'+sc+'"></div></div>'
    :'';

  let badges = '';
  if(m.status_knmp)badges+='<span class="pu-badge badge-hub">'+esc(m.status_knmp)+'</span>';
  if(p!==null)badges+='<span class="pu-badge '+(sts==='selesai'?'badge-selesai':sts==='berjalan'?'badge-prog':'badge-siap')+'">'+sLabel+(p>0?' '+p+'%':'')+'</span>';

  const infoRows = [];
  if(m.nelayan||m.kapal)infoRows.push('<div class="pu-row"><span class="pu-row-k">Nelayan / Kapal</span><span class="pu-row-v">'+(m.nelayan||0)+' / '+(m.kapal||0)+'</span></div>');
  if(m.penyedia)infoRows.push('<div class="pu-row"><span class="pu-row-k">Penyedia</span><span class="pu-row-v">'+esc(m.penyedia)+'</span></div>');
  if(m.realisasi_fisik)infoRows.push('<div class="pu-row"><span class="pu-row-k">Realisasi Fisik</span><span class="pu-row-v">'+m.realisasi_fisik+'%</span></div>');
  if(m.realisasi_keuangan)infoRows.push('<div class="pu-row"><span class="pu-row-k">Realisasi Keuangan</span><span class="pu-row-v">'+m.realisasi_keuangan+'%</span></div>');

  let kendalaHtml = '';
  if(m.kendala&&m.kendala.length){{
    kendalaHtml='<div class="pu-section"><div class="pu-section-title">&#9888; Kendala</div>';
    m.kendala.slice(0,3).forEach(function(k){{kendalaHtml+='<div class="pu-kendala">• '+esc(typeof k==='string'?k:(k.isi||''))+'</div>'}});
    kendalaHtml+='</div>';
  }}
  let tindakHtml = '';
  if(m.tindak_lanjut&&m.tindak_lanjut.length){{
    tindakHtml='<div class="pu-section"><div class="pu-section-title">&#9989; Tindak Lanjut</div>';
    m.tindak_lanjut.slice(0,3).forEach(function(t){{tindakHtml+='<div class="pu-tindak">• '+esc(typeof t==='string'?t:(t.isi||''))+'</div>'}});
    tindakHtml+='</div>';
  }}

  let footer = '';
  if(m.snapshot_date)footer+='<span>&#9202; '+esc(m.snapshot_date)+'</span>';
  footer+='<span>Sumber: '+esc(m.sumber)+'</span>';

  return '<div class="pu-head"><span>'+esc(m.nama)+'</span></div>'+
    progBar+
    '<div class="pu-badges">'+badges+'</div>'+
    '<div class="pu-body">'+
    '<div class="pu-row"><span class="pu-row-k">Provinsi</span><span class="pu-row-v">'+esc(m.provinsi)+'</span></div>'+
    '<div class="pu-row"><span class="pu-row-k">Kabupaten</span><span class="pu-row-v">'+esc(m.kabupaten)+'</span></div>'+
    (m.kecamatan?'<div class="pu-row"><span class="pu-row-k">Kecamatan</span><span class="pu-row-v">'+esc(m.kecamatan)+'</span></div>':'')+
    (m.desa?'<div class="pu-row"><span class="pu-row-k">Desa</span><span class="pu-row-v">'+esc(m.desa)+'</span></div>':'')+
    infoRows.join('')+
    '</div>'+
    buildHargaHTML(m.provinsi)+
    buildTPIHTML(m.id)+
    kendalaHtml+
    tindakHtml+
    '<div class="pu-footer">'+footer+'</div>';
}}

const map = L.map('map',{{center:[-2.5,118],zoom:5}});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
  attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
  subdomains:'abcd',maxZoom:19
}}).addTo(map);

const cluster = L.markerClusterGroup({{
  chunkedLoading:true,maxClusterRadius:55,
  iconCreateFunction:function(c){{
    const n=c.getChildCount();
    const sz=n<10?30:n<30?36:n<70?42:48;
    return L.divIcon({{
      html:'<div style="background:rgba(15,29,61,.85);border:2.5px solid #C9A84C;border-radius:50%;width:'+sz+'px;height:'+sz+'px;display:flex;align-items:center;justify-content:center;color:#C9A84C;font-size:'+(sz<36?11:13)+'px;font-weight:800;box-shadow:0 0 12px rgba(201,168,76,.2)">'+n+'</div>',
      className:'',iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]
    }});
  }}
}});

const allMarkers = MARKERS.map(function(m){{
  const p = m.progress;
  const sts = p!==null&&p>=100?'selesai':p!==null&&p>0?'berjalan':'siap';
  const sc = sts==='selesai'?'#10B981':sts==='berjalan'?'#F59E0B':'#60A5FA';

  const marker = L.marker([m.lat||0,m.lon||0],{{
    icon:L.divIcon({{
      html:'<div style="width:20px;height:20px;border-radius:3px;background:'+sc+';border:2px solid rgba(255,255,255,.3);display:flex;align-items:center;justify-content:center;font-size:12px;line-height:1;color:#fff;box-shadow:0 2px 8px rgba(0,0,0,.5)">&#9733;</div>',
      className:'',iconSize:[20,20],iconAnchor:[10,10],popupAnchor:[0,-10]
    }})
  }});
  marker.bindPopup(buildPopup(m),{{maxWidth:380}});
  marker._d = m;
  return marker;
}});

cluster.addLayers(allMarkers);
map.addLayer(cluster);

function updLegend(arr){{
  const cc={{selesai:0,berjalan:0,siap:0}};
  arr.forEach(function(m){{
    const p=m._d.progress;
    if(p!==null&&p>=100)cc.selesai++;
    else if(p!==null&&p>0)cc.berjalan++;
    else cc.siap++;
  }});
  var lc,el;
  if((el=document.getElementById('lc-selesai')))el.textContent=cc.selesai;
  if((el=document.getElementById('lc-berjalan')))el.textContent=cc.berjalan;
  if((el=document.getElementById('lc-siap')))el.textContent=cc.siap;
}}
updLegend(allMarkers);

const searchEl=document.getElementById('search');
const provEl  =document.getElementById('filter-prov');
const statusEl=document.getElementById('filter-status');
const sbrEl   =document.getElementById('filter-sumber');
const resetBtn=document.getElementById('btn-reset');
const fcountEl=document.getElementById('filter-count');

function applyFilters(){{
  const q   =searchEl.value.toLowerCase().trim();
  const prov=provEl.value;
  const stat=statusEl.value;
  const sbr =sbrEl.value;

  const filtered=allMarkers.filter(function(m){{
    const d=m._d;
    const p=d.progress;

    if(prov && d.provinsi!==prov) return false;
    if(sbr==='eknmp' && d.sumber!=='eknmp') return false;
    if(stat==='HUB' && d.status_knmp!=='HUB') return false;
    if(stat==='PENYANGGA' && d.status_knmp!=='PENYANGGA') return false;
    if(stat==='selesai' && (p===null||p<100)) return false;
    if(stat==='berjalan' && (p===null||p<=0||p>=100)) return false;

    if(q && ![d.nama,d.kabupaten,d.kecamatan,d.desa,d.penyedia]
             .some(function(v){{return v&&v.toLowerCase().includes(q)}})) return false;
    return true;
  }});

  cluster.clearLayers();
  cluster.addLayers(filtered);

  const n=filtered.length;
  document.getElementById('st-total').textContent=n;
  document.getElementById('st-live').textContent=filtered.filter(function(m){{return m._d.sumber==='eknmp'}}).length;
  document.getElementById('st-selesai').textContent=filtered.filter(function(m){{return (m._d.progress||0)>=100}}).length;
  document.getElementById('st-berjalan').textContent=filtered.filter(function(m){{var p=m._d.progress;return p!==null&&p>0&&p<100}}).length;

  if(n<TOTAL_ALL){{fcountEl.style.display='block';fcountEl.textContent='dari '+TOTAL_ALL.toLocaleString('id')+' total'}}else fcountEl.style.display='none';

  updLegend(filtered);
  if(n>0&&n<TOTAL_ALL){{const bnd=L.featureGroup(filtered).getBounds();if(bnd.isValid())map.fitBounds(bnd,{{padding:[40,40],maxZoom:13}})}}
}}

[searchEl,provEl,statusEl,sbrEl].forEach(function(el){{el.addEventListener(el.tagName==='INPUT'?'input':'change',applyFilters)}});

resetBtn.addEventListener('click',function(){{
  searchEl.value='';provEl.value='';statusEl.value='';sbrEl.value='';
  document.getElementById('st-total').textContent={total};
  document.getElementById('st-live').textContent={n_eknmp};
  document.getElementById('st-selesai').textContent={n_selesai};
  document.getElementById('st-berjalan').textContent={n_berjalan};
  fcountEl.style.display='none';
  updLegend(allMarkers);
  cluster.clearLayers();cluster.addLayers(allMarkers);
  map.setView([-2.5,118],5);
}});
</script>
</body>
</html>"""

        os.makedirs("output", exist_ok=True)
        with open("knmp.html", "w", encoding="utf-8") as f:
            f.write(html)

        kb = len(html.encode("utf-8")) // 1024
        print(f"\n✓ knmp.html ({kb} KB)")
        print(f"  Total: {total} | eKNMP Live: {n_eknmp} | Selesai: {n_selesai} | Berjalan: {n_berjalan}")
        print("=" * 55)


if __name__ == "__main__":
    generate()
