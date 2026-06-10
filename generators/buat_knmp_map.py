"""
generators/buat_knmp_map.py — Generate peta KNMP static HTML dari MySQL
Query: knmp_locations + tpi_prices + regional_prices → knmp.html
"""
import json, os, sys
from datetime import datetime
sys.path.insert(0, "backend")

from app.database import SessionLocal
from app.models import KnmpLocation, RegionalPrice, CommodityPrice

WILAYAH_PROV = {
    "ACEH": "Sumatera", "SUMATERA UTARA": "Sumatera", "SUMATRA UTARA": "Sumatera",
    "SUMATERA BARAT": "Sumatera", "SUMATRA BARAT": "Sumatera",
    "RIAU": "Sumatera", "KEPULAUAN RIAU": "Sumatera", "JAMBI": "Sumatera",
    "BENGKULU": "Sumatera", "SUMATERA SELATAN": "Sumatera", "SUMATRA SELATAN": "Sumatera",
    "LAMPUNG": "Sumatera", "KEPULAUAN BANGKA BELITUNG": "Sumatera", "BANGKA BELITUNG": "Sumatera",
    "BANTEN": "Jawa-Bali", "DKI JAKARTA": "Jawa-Bali", "JAKARTA": "Jawa-Bali",
    "JAWA BARAT": "Jawa-Bali", "JAWA TENGAH": "Jawa-Bali", "JAWA TIMUR": "Jawa-Bali",
    "DI YOGYAKARTA": "Jawa-Bali", "BALI": "Jawa-Bali",
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


def generate():
    db = SessionLocal()
    now = datetime.now()
    tgl = now.strftime("%d %B %Y")
    print("=" * 55)
    print("KNMP Map Generator — MySQL → knmp.html")
    print("=" * 55)

    try:
        locations = db.query(KnmpLocation).all()
        print(f"  Locations: {len(locations)}")

        # Regional prices
        latest_rp = db.query(RegionalPrice.tanggal).order_by(RegionalPrice.tanggal.desc()).first()
        rp_data = db.query(RegionalPrice).filter(RegionalPrice.tanggal == latest_rp[0]).all() if latest_rp else []

        harga_wilayah = {}
        for p in rp_data:
            w = p.wilayah
            harga_wilayah.setdefault(w, [])
            short = _SHORT.get(p.komoditas, p.komoditas.split("(")[0].strip()[:20])
            lo = int(p.harga_tambak_low or 0)
            hi = int(p.harga_tambak_high or 0)
            t_str = f"{lo:,.0f} – {hi:,.0f}".replace(",", ".")
            harga_wilayah[w].append({"k": short, "s": p.size, "t": t_str})

        # Build markers
        markers = []
        for loc in locations:
            markers.append({
                "id": str(loc.id_lokasi),
                "nama": loc.nama_kampung or "",
                "provinsi": (loc.provinsi or "").upper(),
                "kabupaten": loc.kabupaten or "",
                "kecamatan": loc.kecamatan or "",
                "lat": loc.lat,
                "lon": loc.lon,
                "status_knmp": loc.status_knmp or "",
                "tahun": loc.tahun,
                "nelayan": loc.jumlah_nelayan,
                "kapal": loc.jumlah_kapal,
            })

        total = len(markers)
        valid = [m for m in markers if m["lat"] is not None and m["lon"] is not None]
        provs = sorted(set(m["provinsi"] for m in markers if m["provinsi"]))
        hub = len([m for m in markers if m["status_knmp"] == "HUB"])
        penyangga = len([m for m in markers if m["status_knmp"] == "PENYANGGA"])

        marker_js = json.dumps(markers, ensure_ascii=False, separators=(",", ":"))
        valid_js = json.dumps(valid, ensure_ascii=False, separators=(",", ":"))
        harga_js = json.dumps(harga_wilayah, ensure_ascii=False, separators=(",", ":"))
        prov_wil_js = json.dumps(WILAYAH_PROV, ensure_ascii=False, separators=(",", ":"))
        prov_opts = "\n              ".join(
            f'<option value="{p}">{p.title()}</option>' for p in provs
        )
        tgl_harga = now.strftime("%d/%m/%Y")

    finally:
        db.close()

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Peta KNMP — Market Watch AJN</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{height:100%;font-family:'Segoe UI',system-ui,sans-serif;background:#0d2244;overflow:hidden}}
#hdr{{position:fixed;top:0;left:0;right:0;z-index:1020;height:52px;background:linear-gradient(135deg,#1B3A6B 0%,#0d2244 100%);display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-bottom:1px solid rgba(201,168,76,.35)}}
#hdr-brand{{display:flex;flex-direction:column;gap:1px}}
#hdr-title{{font-size:.95rem;font-weight:700;color:#C9A84C;letter-spacing:.3px}}
#hdr-sub{{font-size:.62rem;color:rgba(148,163,184,.6)}}
#hdr-right{{display:flex;align-items:center;gap:10px}}
.hdr-chip{{font-size:.68rem;background:rgba(201,168,76,.12);border:1px solid rgba(201,168,76,.3);color:#C9A84C;padding:3px 10px;border-radius:14px}}
.nav-bar{{position:fixed;top:52px;left:0;right:0;z-index:1000;background:#0a1628;border-top:1px solid rgba(201,168,76,.2)}}
.nav-bar-inner{{padding:0 20px;display:flex;gap:0}}
.nav-link{{color:rgba(255,255,255,.4);text-decoration:none;font-size:.7rem;font-weight:500;padding:7px 12px;border-bottom:2px solid transparent;transition:all .15s}}
.nav-link:hover{{color:#C9A84C}}
.nav-link.active{{color:#C9A84C;border-bottom-color:#C9A84C}}
#layout{{display:flex;height:100vh;padding-top:84px}}
#sidebar{{width:250px;flex-shrink:0;background:rgba(15,29,61,.6);backdrop-filter:blur(12px);overflow-y:auto;padding:10px;display:flex;flex-direction:column;gap:7px;border-right:1px solid rgba(201,168,76,.1)}}
.panel{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:10px 12px}}
.ptitle{{font-size:.6rem;font-weight:700;color:#C9A84C;text-transform:uppercase;letter-spacing:.7px;margin-bottom:6px}}
.sgrid{{display:grid;grid-template-columns:1fr 1fr;gap:5px}}
.sbox{{background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.04);border-radius:6px;padding:6px 8px;text-align:center}}
.snum{{font-size:1.15rem;font-weight:800;color:#C9A84C;line-height:1}}
.slbl{{font-size:.55rem;color:rgba(148,163,184,.6)}}
#search{{width:100%;padding:6px 8px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:6px;color:#e2e8f0;font-size:.72rem;outline:none}}
select{{width:100%;padding:5px 6px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:6px;color:#e2e8f0;font-size:.7rem;outline:none}}
select option{{background:#0f1d3d}}
.flbl{{display:block;font-size:.58rem;color:rgba(148,163,184,.5);margin-bottom:2px}}
#btn-reset{{width:100%;padding:5px;background:rgba(201,168,76,.06);border:1px solid rgba(201,168,76,.15);border-radius:6px;color:#C9A84C;font-size:.68rem;font-weight:600;cursor:pointer}}
#map{{flex:1;z-index:0}}
.leg-item{{display:flex;align-items:center;gap:5px;padding:2px 0;font-size:.64rem;color:rgba(203,213,225,.6)}}
.leg-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
.leaflet-popup-content-wrapper{{border-radius:10px;padding:0;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.4)}}
.leaflet-popup-content{{margin:0;min-width:260px;max-width:340px}}
.leaflet-popup-tip{{background:#1B3A6B!important}}
.pu-head{{padding:10px 14px;font-weight:700;font-size:13px;color:#C9A84C;background:linear-gradient(135deg,#1B3A6B,#0d2244)}}
.pu-body{{padding:6px 12px;font-size:11px;color:#1e293b}}
.pu-row{{display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px dotted #e2e8f0}}
.pu-rk{{color:#475569;width:80px;flex-shrink:0}}
.pu-rv{{font-weight:600}}
.pu-section{{padding:6px 12px;border-top:1px solid #e2e8f0}}
.pu-stitle{{font-size:.58rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px}}
.pu-hrow{{display:flex;justify-content:space-between;font-size:.66rem;padding:1px 0}}
.pu-hk{{color:#475569;flex:1}}
.pu-hv{{color:#1B3A6B;font-weight:700}}
.pu-footer{{padding:4px 12px;font-size:.5rem;color:#94a3b8;border-top:1px solid #f1f5f9;text-align:center}}
.nav-link.home{{color:#C9A84C;font-weight:700}}
@media(max-width:600px){{#sidebar{{display:none}}}}
</style>
</head>
<body>

<div id="hdr">
  <div id="hdr-brand"><div id="hdr-title">Peta KNMP Nasional</div><div id="hdr-sub">PT Agrinas Jaladri Nusantara (Persero)</div></div>
  <div id="hdr-right"><div class="hdr-chip">{total} Lokasi</div></div>
</div>

<div class="nav-bar">
  <div class="nav-bar-inner">
    <a class="nav-link home" href="./index.html">&#128202; Harga</a>
    <a class="nav-link active" href="./knmp.html">&#128506;&#65039; Peta</a>
  </div>
</div>

<div id="layout">
  <div id="sidebar">
    <div class="panel"><div class="ptitle">Ringkasan</div>
      <div class="sgrid">
        <div class="sbox"><div class="snum">{total}</div><div class="slbl">Total</div></div>
        <div class="sbox"><div class="snum">{len(valid)}</div><div class="slbl">Marker</div></div>
        <div class="sbox"><div class="snum">{hub}</div><div class="slbl">HUB</div></div>
        <div class="sbox"><div class="snum">{penyangga}</div><div class="slbl">Penyangga</div></div>
      </div>
    </div>
    <div class="panel"><div class="ptitle">Cari</div>
      <input type="text" id="search" placeholder="Nama, kab, penyedia…">
    </div>
    <div class="panel"><div class="ptitle">Filter</div>
      <label class="flbl">Provinsi</label>
      <select id="filter-prov"><option value="">Semua</option>{prov_opts}</select>
      <div style="height:5px"></div>
      <label class="flbl">Tipe</label>
      <select id="filter-tipe"><option value="">Semua</option><option value="HUB">HUB</option><option value="PENYANGGA">Penyangga</option></select>
      <div style="height:6px"></div>
      <button id="btn-reset">&#x21BA; Reset</button>
    </div>
    <div class="panel"><div class="ptitle">Legenda</div>
      <div class="leg-item"><span class="leg-dot" style="background:#10B981"></span> HUB · Selesai</div>
      <div class="leg-item"><span class="leg-dot" style="background:#F59E0B"></span> HUB · Berjalan</div>
      <div class="leg-item"><span class="leg-dot" style="background:#3B82F6"></span> HUB · Siap</div>
      <div class="leg-item"><span class="leg-dot" style="background:#94A3B8"></span> Penyangga</div>
    </div>
  </div>
  <div id="map"></div>
</div>

<script>
const ALL = {marker_js};
const VALID = {valid_js};
const HARGA = {harga_js};
const PW = {prov_wil_js};
const HT = '{tgl_harga}';

function popupHTML(m){{
  var h = HARGA[PW[m.provinsi]||''];
  var hr = h ? h.slice(0,3).map(function(p){{return '<div class="pu-hrow"><span class="pu-hk">'+p.k+' '+p.s+'</span><span class="pu-hv">Rp '+p.t+'/kg</span></div>'}}).join('') : '';
  return '<div class="pu-head">#'+(m.id||m.id_lokasi)+' '+m.nama+'</div><div class="pu-body">'+
    '<div class="pu-row"><span class="pu-rk">Provinsi</span><span class="pu-rv">'+m.provinsi+'</span></div>'+
    '<div class="pu-row"><span class="pu-rk">Kabupaten</span><span class="pu-rv">'+(m.kabupaten||'')+'</span></div>'+
    (m.kecamatan?'<div class="pu-row"><span class="pu-rk">Kec</span><span class="pu-rv">'+m.kecamatan+'</span></div>':'')+
    '<div class="pu-row"><span class="pu-rk">Tipe</span><span class="pu-rv">'+(m.status_knmp||'')+'</span></div>'+
    '<div class="pu-row"><span class="pu-rk">Nelayan</span><span class="pu-rv">'+(m.nelayan||m.jumlah_nelayan||0)+' org</span></div>'+
    '<div class="pu-row"><span class="pu-rk">Kapal</span><span class="pu-rv">'+(m.kapal||m.jumlah_kapal||0)+' unit</span></div>'+
  '</div>'+(hr?'<div class="pu-section"><div class="pu-stitle">&#128722; Harga</div>'+hr+'<div style="font-size:.5rem;color:#94a3b8;margin-top:2px">Per '+HT+'</div></div>':'')+
  '<div class="pu-footer"><a href="/login" style="color:#3B82F6">🔒 Login</a> untuk detail</div>';
}}

(function(){{
  var map = L.map('map',{{center:[-2.5,118],zoom:5,preferCanvas:true}});
  L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',{{attribution:'&copy; OSM &copy; CARTO',subdomains:'abcd',maxZoom:19}}).addTo(map);

  var mcg = L.markerClusterGroup({{
    chunkedLoading:true, maxClusterRadius:55, disableClusteringAtZoom:16,
    iconCreateFunction:function(c){{var n=c.getChildCount(),s=n<30?34:n<80?42:n<200?50:58
      return L.divIcon({{html:'<div style="background:#1B3A6B;border:2.5px solid #C9A84C;border-radius:50%;width:'+s+'px;height:'+s+'px;display:flex;align-items:center;justify-content:center;color:#C9A84C;font-size:'+(s<42?11:13)+'px;font-weight:800;box-shadow:0 2px 8px rgba(0,0,0,.3)">'+n+'</div>',className:'',iconSize:[s,s],iconAnchor:[s/2,s/2]}})
    }}
  }});

  VALID.forEach(function(m){{
    var c = L.circleMarker([m.lat,m.lon],{{
      radius:m.status_knmp==='HUB'?7:5,
      fillColor:m.status_knmp==='PENYANGGA'?'#94A3B8':'#3B82F6',
      color:'#fff',weight:1.5,fillOpacity:.9
    }});
    c.bindPopup(popupHTML(m),{{maxWidth:340}});
    c.bindTooltip('<b>'+m.nama+'</b><br/>'+m.status_knmp,{{direction:'top',offset:[0,-12]}});
    mcg.addLayer(c);
  }});
  map.addLayer(mcg);

  var sEl=document.getElementById('search'),pEl=document.getElementById('filter-prov'),tEl=document.getElementById('filter-tipe'),rEl=document.getElementById('btn-reset');

  function filter(){{
    var q=sEl.value.toLowerCase().trim(),prov=pEl.value,tipe=tEl.value;
    mcg.clearLayers();
    VALID.filter(function(m){{
      if(prov && m.provinsi!==prov)return false;
      if(tipe && m.status_knmp!==tipe)return false;
      if(q && !(m.nama.toLowerCase().indexOf(q)>=0||m.kabupaten.toLowerCase().indexOf(q)>=0))return false;
      return true;
    }}).forEach(function(m){{var c = L.circleMarker([m.lat,m.lon],{{radius:m.status_knmp==='HUB'?7:5,fillColor:m.status_knmp==='PENYANGGA'?'#94A3B8':'#3B82F6',color:'#fff',weight:1.5,fillOpacity:.9}});c.bindPopup(popupHTML(m),{{maxWidth:340}});c.bindTooltip('<b>'+m.nama+'</b><br/>'+m.status_knmp,{{direction:'top',offset:[0,-12]}});mcg.addLayer(c)}});
  }}

  sEl.addEventListener('input',filter);pEl.addEventListener('change',filter);tEl.addEventListener('change',filter);
  rEl.addEventListener('click',function(){{sEl.value='';pEl.value='';tEl.value='';filter()}});
}})();
</script>
</body>
</html>"""

    os.makedirs("output", exist_ok=True)
    with open("knmp.html", "w", encoding="utf-8") as f:
        f.write(html)
    kb = len(html.encode("utf-8")) // 1024
    print(f"✓ knmp.html ({kb} KB) — {total} lokasi")
    print("=" * 55)


if __name__ == "__main__":
    generate()
