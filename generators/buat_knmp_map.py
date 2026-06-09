"""
generators/buat_knmp_map.py — Peta KNMP publik (light interactive map)
Hover = full popup · Light Voyager tiles · Responsive sidebar
"""
import json, os
from datetime import datetime, date
from config import Config
from app import create_app
from models import db, KnmpLocation, KnmpLocationSnapshot, RegionalPrice, TpiPrice

WILAYAH_PROV = {
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

_SHORT = {
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
    result = {}
    for p in prices:
        w = p.wilayah
        result.setdefault(w, [])
        short = _SHORT.get(p.komoditas, p.komoditas.split("(")[0].strip()[:20])
        lo = int(p.harga_tambak_low or 0)
        hi = int(p.harga_tambak_high or 0)
        result[w].append({"k": short, "s": p.size, "t": f"{lo:,.0f} – {hi:,.0f}".replace(",", ".")})
    return result


def generate():
    app = create_app(Config)
    with app.app_context():
        now = datetime.now()
        tgl = now.strftime("%d %B %Y"); tgl_harga = now.strftime("%d/%m/%Y")
        print("=" * 55)
        print("KNMP Map — light interactive theme")
        print("=" * 55)

        locations = KnmpLocation.query.all()

        sub = (db.session.query(KnmpLocationSnapshot.id_lokasi,
            db.func.max(KnmpLocationSnapshot.snapshot_date).label("md"))
            .group_by(KnmpLocationSnapshot.id_lokasi).subquery())
        snaps = {s.id_lokasi: s for s in KnmpLocationSnapshot.query.join(
            sub, db.and_(KnmpLocationSnapshot.id_lokasi == sub.c.id_lokasi,
            KnmpLocationSnapshot.snapshot_date == sub.c.md)).all()}

        latest_rp = db.session.query(db.func.max(RegionalPrice.tanggal)).scalar()
        rp_data = RegionalPrice.query.filter_by(tanggal=latest_rp).all() if latest_rp else []
        harga_wil = build_harga_wilayah(rp_data)

        tpi_all = TpiPrice.query.order_by(TpiPrice.tanggal.desc()).limit(600).all()
        tpi_map = {}
        for t in tpi_all:
            tpi_map.setdefault(str(t.id_lokasi), []).append({
                "tpi": t.nama_tpi or "", "komoditas": t.komoditas,
                "harga": int(t.harga) if t.harga else 0, "tanggal": str(t.tanggal),
            })

        markers = []
        for loc in locations:
            s = snaps.get(loc.id_lokasi)
            markers.append({
                "id": str(loc.id_lokasi), "nama": loc.nama_kampung or "",
                "provinsi": (loc.provinsi or "").upper(), "kabupaten": loc.kabupaten or "",
                "kecamatan": loc.kecamatan or "", "desa": loc.desa or "",
                "lat": loc.lat, "lon": loc.lon,
                "status_knmp": loc.status_knmp or "", "tahun": loc.tahun,
                "penyedia": loc.penyedia or "",
                "nelayan": loc.jumlah_nelayan, "kapal": loc.jumlah_kapal,
                "progress": float(s.progress_kumulatif) if s and s.progress_kumulatif is not None else None,
                "fisik": float(s.realisasi_fisik) if s and s.realisasi_fisik is not None else None,
                "keuangan": float(s.realisasi_keuangan) if s and s.realisasi_keuangan is not None else None,
                "snap_date": str(s.snapshot_date) if s else None,
                "kendala": s.kendala if s else None,
                "tindak": s.tindak_lanjut if s else None,
            })

        total = len(markers); n_live = len(snaps)
        n100 = sum(1 for m in markers if m["progress"] is not None and m["progress"] >= 100)
        n_run = sum(1 for m in markers if m["progress"] is not None and 0 < m["progress"] < 100)
        avg = sum(m["progress"] for m in markers if m["progress"] is not None) / max(n_live, 1)
        provs = sorted(set(m["provinsi"] for m in markers if m["provinsi"]))

        mj = json.dumps(markers, ensure_ascii=False, separators=(",", ":"))
        hj = json.dumps(harga_wil, ensure_ascii=False, separators=(",", ":"))
        tj = json.dumps(tpi_map, ensure_ascii=False, separators=(",", ":"))
        pj = json.dumps(WILAYAH_PROV, ensure_ascii=False, separators=(",", ":"))

        popts = "\n              ".join(f'<option value="{p}">{p.title()}</option>' for p in provs)

        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Peta KNMP — Market Watch AJN</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%;font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#f0f4f8;overflow:hidden;color:#1e293b}}

/* ── Header ── */
.hdr{{position:fixed;top:0;left:0;right:0;z-index:1020;height:52px;background:linear-gradient(135deg,#1B3A6B 0%,#0d2244 100%);display:flex;align-items:center;justify-content:space-between;padding:0 16px;box-shadow:0 2px 8px rgba(0,0,0,.15)}}
.hdr-l{{display:flex;align-items:center;gap:10px}}
.hdr-menu{{display:none;background:none;border:none;color:#fff;font-size:1.2rem;cursor:pointer;padding:4px}}
.hdr-brand{{display:flex;flex-direction:column;gap:0}}
.hdr-title{{font-size:.85rem;font-weight:700;color:#C9A84C;letter-spacing:.2px}}
.hdr-sub{{font-size:.55rem;color:rgba(148,163,184,.5)}}
.hdr-r{{display:flex;align-items:center;gap:10px}}
.hdr-chip{{font-size:.65rem;background:rgba(201,168,76,.12);border:1px solid rgba(201,168,76,.25);color:#C9A84C;padding:3px 10px;border-radius:12px;white-space:nowrap}}
.hdr-chip.green{{border-color:rgba(16,185,129,.3);color:#10B981;background:rgba(16,185,129,.08)}}
.btn-login{{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;background:#C9A84C;color:#0d2244;border-radius:6px;text-decoration:none;font-size:.68rem;font-weight:700;white-space:nowrap}}
.btn-login:hover{{background:#e2c16f}}

/* ── Sidebar ── */
.sidebar{{position:fixed;top:52px;left:0;bottom:0;width:260px;background:#fff;box-shadow:2px 0 8px rgba(0,0,0,.06);overflow-y:auto;z-index:1010;transition:transform .25s;display:flex;flex-direction:column;gap:6px;padding:10px}}
.sidebar.open{{transform:translateX(0)}}
.sidebar::-webkit-scrollbar{{width:3px}}
.sidebar::-webkit-scrollbar-thumb{{background:#cbd5e1;border-radius:2px}}

.panel{{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px}}
.ptitle{{font-size:.62rem;font-weight:700;color:#1B3A6B;text-transform:uppercase;letter-spacing:.6px;margin-bottom:7px;display:flex;align-items:center;gap:5px}}
.ptitle::before{{content:"";width:5px;height:5px;border-radius:50%;background:#C9A84C;flex-shrink:0}}

.sgrid{{display:grid;grid-template-columns:1fr 1fr;gap:5px}}
.sbox{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:7px 9px}}
.snum{{font-size:1.15rem;font-weight:800;color:#1B3A6B;line-height:1}}
.snum.g{{color:#10B981}}.snum.o{{color:#F59E0B}}
.slbl{{font-size:.55rem;color:#64748b;margin-top:1px}}
.sbox.wide{{grid-column:1/-1}}

.srch{{width:100%;padding:7px 10px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;font-size:.74rem;outline:none}}
.srch:focus{{border-color:#C9A84C}}
select{{width:100%;padding:6px 8px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;font-size:.72rem;outline:none;cursor:pointer}}
select:focus{{border-color:#C9A84C}}
.flbl{{display:block;font-size:.6rem;color:#64748b;margin-bottom:2px}}
.gap{{height:5px}}
.btn-reset{{width:100%;padding:6px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;color:#1B3A6B;font-size:.72rem;font-weight:600;cursor:pointer;margin-top:4px}}
.btn-reset:hover{{background:#e2e8f0}}
.fcount{{font-size:.62rem;color:#3B82F6;margin-top:4px;display:none;text-align:center}}

.leg-item{{display:flex;align-items:center;gap:5px;padding:2px 0;font-size:.64rem;color:#64748b}}
.leg-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;border:1px solid rgba(0,0,0,.1)}}
.leg-cnt{{margin-left:auto;font-size:.55rem;color:#94a3b8}}

/* ── Map ── */
.map-area{{position:fixed;top:52px;left:260px;right:0;bottom:0;background:#eef2f7}}
.map-area.full{{left:0}}
#map{{width:100%;height:100%}}

/* ── Popup ── */
.leaflet-popup-content-wrapper{{border-radius:10px;padding:0;box-shadow:0 4px 20px rgba(0,0,0,.15);background:#fff;overflow:hidden}}
.leaflet-popup-content{{margin:0;min-width:260px;max-width:340px;color:#1e293b}}
.leaflet-popup-tip{{background:#fff}}
.leaflet-popup-close-button{{color:#1B3A6B!important;font-size:15px!important;padding:4px 6px!important}}

.pp-head{{color:#1B3A6B;font-weight:700;font-size:.8rem;padding:9px 11px;background:#f8fafc;border-bottom:1px solid #e2e8f0}}
.pp-bar{{height:4px;background:#e2e8f0;margin:0}}
.pp-fill{{height:100%;transition:width .4s ease}}
.pp-body{{padding:7px 11px;font-size:.7rem}}
.pp-row{{display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px dotted #f1f5f9}}
.pp-rk{{color:#64748b;flex-shrink:0}}.pp-rv{{font-weight:600;text-align:right;margin-left:6px}}
.pp-badges{{display:flex;gap:4px;padding:4px 11px;flex-wrap:wrap}}
.pp-badge{{display:inline-block;padding:1px 6px;border-radius:6px;font-size:.56rem;font-weight:700}}
.bad-hub{{background:#D1FAE5;color:#065F46}}.bad-pen{{background:#F1F5F9;color:#475569}}
.bad-100{{background:#D1FAE5;color:#065F46}}.bad-run{{background:#FEF3C7;color:#92400E}}.bad-siap{{background:#DBEAFE;color:#1E40AF}}
.pp-sec{{border-top:1px solid #f1f5f9;padding:7px 11px}}
.pp-stitle{{font-size:.56rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}}
.pp-hrow{{display:flex;justify-content:space-between;font-size:.64rem;padding:1px 0}}
.pp-hk{{color:#64748b;flex:1}}.pp-hv{{color:#1B3A6B;font-weight:700;margin-left:6px;white-space:nowrap}}
.pp-hnote{{font-size:.48rem;color:#cbd5e1;margin-top:2px}}
.pp-login{{text-align:center;padding:5px;font-size:.55rem;color:#94a3b8}}
.pp-login a{{color:#3B82F6;text-decoration:none;font-weight:600}}
.pp-footer{{padding:4px 11px;font-size:.48rem;color:#cbd5e1;border-top:1px solid #f8fafc;display:flex;justify-content:space-between}}

/* ── Responsive ── */
@media(max-width:768px){{
  .hdr-menu{{display:block}}
  .sidebar{{transform:translateX(-100%);width:280px}}
  .sidebar.open{{transform:translateX(0)}}
  .map-area{{left:0}}
  .hdr-chip{{display:none}}
}}
@media(max-width:480px){{
  .hdr-title{{font-size:.75rem}}
  .btn-login{{font-size:.62rem;padding:4px 8px}}
  .sidebar{{width:100%}}
}}
</style>
</head>
<body>

<div class="hdr">
  <div class="hdr-l">
    <button class="hdr-menu" id="menuBtn" onclick="toggleSidebar()">&#9776;</button>
    <div class="hdr-brand">
      <div class="hdr-title">Peta KNMP Nasional</div>
      <div class="hdr-sub">PT Agrinas Jaladri Nusantara (Persero)</div>
    </div>
  </div>
  <div class="hdr-r">
    {f'<div class="hdr-chip green">&#9679; {n_live} Live</div>' if n_live > 0 else ''}
    <div class="hdr-chip">{total:,} Lokasi</div>
    <a href="/login" class="btn-login">&#128274; Login</a>
  </div>
</div>

<div class="sidebar" id="sidebar">
  <div class="panel">
    <div class="ptitle">Ringkasan</div>
    <div class="sgrid">
      <div class="sbox"><div class="snum" id="st-total">{total}</div><div class="slbl">Total Lokasi</div></div>
      <div class="sbox"><div class="snum g" id="st-live">{n_live}</div><div class="slbl">Live eKNMP</div></div>
      <div class="sbox"><div class="snum" id="st-100">{n100}</div><div class="slbl">Selesai</div></div>
      <div class="sbox"><div class="snum o" id="st-run">{n_run}</div><div class="slbl">Berjalan</div></div>
      <div class="sbox wide"><div class="snum">{avg:.1f}%</div><div class="slbl">Progress Nasional</div></div>
    </div>
  </div>
  <div class="panel">
    <div class="ptitle">Cari</div>
    <input type="text" class="srch" id="search" placeholder="Nama, kab, penyedia…">
  </div>
  <div class="panel">
    <div class="ptitle">Filter</div>
    <label class="flbl">Provinsi</label>
    <select id="fprov"><option value="">Semua</option>{popts}</select>
    <div class="gap"></div>
    <label class="flbl">Status</label>
    <select id="fstat">
      <option value="">Semua</option>
      <option value="HUB">HUB</option>
      <option value="PENYANGGA">Penyangga</option>
      <option value="selesai">Selesai (100%)</option>
      <option value="berjalan">Berjalan</option>
      <option value="siap">Siap Dibangun</option>
    </select>
    <button class="btn-reset" id="resetBtn">&#x21BA; Reset</button>
    <div class="fcount" id="fcount"></div>
  </div>
  <div class="panel">
    <div class="ptitle">Legenda</div>
    <div class="leg-item"><span class="leg-dot" style="background:#10B981"></span><span>Selesai (100%)</span><span class="leg-cnt" id="lc-100"></span></div>
    <div class="leg-item"><span class="leg-dot" style="background:#F59E0B"></span><span>Berjalan</span><span class="leg-cnt" id="lc-run"></span></div>
    <div class="leg-item"><span class="leg-dot" style="background:#3B82F6"></span><span>Siap Dibangun</span><span class="leg-cnt" id="lc-siap"></span></div>
    <div class="leg-item"><span class="leg-dot" style="background:#94A3B8"></span><span>Penyangga</span><span class="leg-cnt" id="lc-pen"></span></div>
  </div>
</div>

<div class="map-area" id="mapArea">
  <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const M={mj};const T={tj};const H={hj};const PW={pj};const HT='{tgl_harga}';const TA={total};

function esc(s){{return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}
function nf(n){{return n!=null?n.toLocaleString('id'):'—'}}

function hrgHTML(prov){{
  const w=PW[prov]||null;
  if(!w||!H[w]||!H[w].length)return'';
  const rs=H[w].slice(0,4).map(h=>'<div class="pp-hrow"><span class="pp-hk">'+esc(h.k)+'<em style="color:#cbd5e1;font-style:normal"> '+esc(h.s)+'</em></span><span class="pp-hv">Rp '+esc(h.t)+'/kg</span></div>').join('');
  return'<div class="pp-sec"><div class="pp-stitle">&#128722; Harga — '+esc(w)+'</div>'+rs+'<div class="pp-hnote">Per '+HT+' · nelayan/tambak</div></div>';
}}
function tpiHTML(mid){{
  const ts=T[mid];if(!ts||!ts.length)return'';
  const rs=ts.slice(0,3).map(t=>'<div class="pp-hrow"><span class="pp-hk">'+esc(t.komoditas)+'<em style="color:#cbd5e1;font-style:normal"> '+esc(t.tpi)+'</em></span><span class="pp-hv">Rp '+Number(t.harga).toLocaleString('id')+'/kg</span></div>').join('');
  return'<div class="pp-sec"><div class="pp-stitle">&#128031; TPI Terdekat</div>'+rs+'</div>';
}}

function popup(m){{
  const p=m.progress,sts=p!=null&&p>=100?'selesai':p!=null&&p>0?'berjalan':'siap';
  const sc=sts==='selesai'?'#10B981':sts==='berjalan'?'#F59E0B':'#3B82F6';
  const lb=sts==='selesai'?'Selesai':sts==='berjalan'?'Berjalan':'Siap';

  const bar=p!=null?'<div class="pp-bar"><div class="pp-fill" style="width:'+Math.min(p,100)+'%;background:'+sc+'"></div></div>':'';
  let bg='';if(m.status_knmp)bg+='<span class="pp-badge '+(m.status_knmp==='HUB'?'bad-hub':'bad-pen')+'">'+esc(m.status_knmp)+'</span>';
  if(p!=null)bg+='<span class="pp-badge '+(sts==='selesai'?'bad-100':sts==='berjalan'?'bad-run':'bad-siap')+'">'+lb+(p>0?' '+p+'%':'')+'</span>';

  let inf='';
  if(m.nelayan||m.kapal)inf+='<div class="pp-row"><span class="pp-rk">Nelayan / Kapal</span><span class="pp-rv">'+(m.nelayan||0)+' / '+(m.kapal||0)+'</span></div>';
  if(m.fisik!=null)inf+='<div class="pp-row"><span class="pp-rk">Fisik</span><span class="pp-rv">'+m.fisik+'%</span></div>';
  if(m.keuangan!=null)inf+='<div class="pp-row"><span class="pp-rk">Keuangan</span><span class="pp-rv">'+m.keuangan+'%</span></div>';
  if(m.penyedia)inf+='<div class="pp-row"><span class="pp-rk">Penyedia</span><span class="pp-rv">'+esc(m.penyedia)+'</span></div>';

  let ft='';if(m.snap_date)ft+='<span>&#9202; '+esc(m.snap_date)+'</span>';ft+='<span>eKNMP · Market Watch AJN</span>';

  return'<div class="pp-head">'+esc(m.nama)+'</div>'+bar+'<div class="pp-badges">'+bg+'</div>'+
    '<div class="pp-body">'+
    '<div class="pp-row"><span class="pp-rk">Provinsi</span><span class="pp-rv">'+esc(m.provinsi)+'</span></div>'+
    '<div class="pp-row"><span class="pp-rk">Kabupaten</span><span class="pp-rv">'+esc(m.kabupaten)+'</span></div>'+
    (m.kecamatan?'<div class="pp-row"><span class="pp-rk">Kecamatan</span><span class="pp-rv">'+esc(m.kecamatan)+'</span></div>':'')+
    (m.desa?'<div class="pp-row"><span class="pp-rk">Desa</span><span class="pp-rv">'+esc(m.desa)+'</span></div>':'')+
    inf+'</div>'+
    hrgHTML(m.provinsi)+tpiHTML(m.id)+
    '<div class="pp-login"><a href="/login">&#128274; Login</a> untuk update progress & upload foto</div>'+
    '<div class="pp-footer">'+ft+'</div>';
}}

function toggleSidebar(){{document.getElementById('sidebar').classList.toggle('open')}}

const map=L.map('map',{{center:[-2.5,118],zoom:5}});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',{{
  attribution:'&copy; OSM &copy; CARTO',subdomains:'abcd',maxZoom:19
}}).addTo(map);
const cl=L.markerClusterGroup({{chunkedLoading:true,maxClusterRadius:55,
  iconCreateFunction:function(c){{const n=c.getChildCount(),s=n<10?30:n<30?36:n<70?42:48;
    return L.divIcon({{html:'<div style="background:#1B3A6B;border:2px solid #C9A84C;border-radius:50%;width:'+s+'px;height:'+s+'px;display:flex;align-items:center;justify-content:center;color:#C9A84C;font-size:'+(s<36?10:12)+'px;font-weight:800">'+n+'</div>',className:'',iconSize:[s,s],iconAnchor:[s/2,s/2]}});
}}}});

var curPop=null;

const am=M.map(function(m){{
  const p=m.progress,sts=p!=null&&p>=100?'selesai':p!=null&&p>0?'berjalan':'siap';
  const sc=sts==='selesai'?'#10B981':sts==='berjalan'?'#F59E0B':m.status_knmp==='PENYANGGA'?'#94A3B8':'#3B82F6';
  const mk=L.marker([m.lat||0,m.lon||0],{{icon:L.divIcon({{html:'<div style="width:20px;height:20px;border-radius:3px;background:'+sc+';border:2px solid rgba(255,255,255,.8);display:flex;align-items:center;justify-content:center;font-size:12px;color:#fff;box-shadow:0 2px 6px rgba(0,0,0,.25)">&#9733;</div>',className:'',iconSize:[20,20],iconAnchor:[10,10],popupAnchor:[0,-10]}})}});

  mk.on('mouseover',function(e){{if(curPop){{map.removeLayer(curPop);curPop=null}}curPop=L.popup({{offset:[0,-12],closeButton:false,autoPan:false}}).setLatLng(e.latlng).setContent(popup(m)).openOn(map)}});
  mk.on('mouseout',function(){{/* keep open - user can interact */}});
  mk.on('click',function(e){{if(curPop){{map.removeLayer(curPop);curPop=null}}curPop=L.popup({{offset:[0,-12]}}).setLatLng(e.latlng).setContent(popup(m)).openOn(map)}});
  mk._d=m;return mk;
}});
cl.addLayers(am);map.addLayer(cl);

function updL(arr){{const cc={{'100':0,run:0,siap:0,pen:0}};arr.forEach(function(m){{const d=m._d,p=d.progress;if(d.status_knmp==='PENYANGGA')cc.pen++;else if(p!=null&&p>=100)cc['100']++;else if(p!=null&&p>0)cc.run++;else cc.siap++}});['100','run','siap','pen'].forEach(function(k){{var e=document.getElementById('lc-'+k);if(e)e.textContent=cc[k]}})}}
updL(am);

var sEl=document.getElementById('search'),pEl=document.getElementById('fprov'),stEl=document.getElementById('fstat'),rBtn=document.getElementById('resetBtn'),fcEl=document.getElementById('fcount');
function apply(){{
  var q=sEl.value.toLowerCase().trim(),pv=pEl.value,st=stEl.value;
  var ft=am.filter(function(m){{var d=m._d,p=d.progress;
    if(pv&&d.provinsi!==pv)return false;
    if(st==='HUB'&&d.status_knmp!=='HUB')return false;
    if(st==='PENYANGGA'&&d.status_knmp!=='PENYANGGA')return false;
    if(st==='selesai'&&(p===null||p<100))return false;
    if(st==='berjalan'&&(p===null||p<=0||p>=100))return false;
    if(st==='siap'&&(p!==null&&p>0))return false;
    if(q&&![d.nama,d.kabupaten,d.kecamatan,d.desa,d.penyedia].some(function(v){{return v&&v.toLowerCase().indexOf(q)>=0}}))return false;
    return true;
  }});
  cl.clearLayers();cl.addLayers(ft);
  var n=ft.length;document.getElementById('st-total').textContent=n;document.getElementById('st-live').textContent=ft.filter(function(m){{return m._d.progress!==null}}).length;document.getElementById('st-100').textContent=ft.filter(function(m){{return(m._d.progress||0)>=100}}).length;document.getElementById('st-run').textContent=ft.filter(function(m){{var p=m._d.progress;return p!==null&&p>0&&p<100}}).length;
  fcEl.style.display=n<TA?'block':'none';if(n<TA)fcEl.textContent='dari '+TA.toLocaleString('id')+' total';
  updL(ft);if(n>0&&n<TA){{var bnd=L.featureGroup(ft).getBounds();if(bnd.isValid())map.fitBounds(bnd,{{padding:[40,40],maxZoom:13}})}}
}}
[sEl,pEl,stEl].forEach(function(el){{el.addEventListener(el.tagName==='INPUT'?'input':'change',apply)}});
rBtn.addEventListener('click',function(){{sEl.value='';pEl.value='';stEl.value='';document.getElementById('st-total').textContent={total};document.getElementById('st-live').textContent={n_live};document.getElementById('st-100').textContent={n100};document.getElementById('st-run').textContent={n_run};fcEl.style.display='none';updL(am);cl.clearLayers();cl.addLayers(am);map.setView([-2.5,118],5)}});
</script>
</body>
</html>"""

        with open("knmp.html", "w", encoding="utf-8") as f:
            f.write(html)
        kb = len(html.encode("utf-8")) // 1024
        print(f"✓ knmp.html ({kb} KB) — {total} lokasi, {n_live} live")
        print(f"  Hover=popup · Voyager tiles · Responsive sidebar")
        print("=" * 55)


if __name__ == "__main__":
    generate()
