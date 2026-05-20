"""
Baca Lokasi KNMP.xlsx (sheet KNMP Operasional) ->
generate peta Leaflet interaktif.

Output: output/knmp_YYYYMMDD.html  dan  knmp.html (root)
"""
import openpyxl, json, os
from datetime import datetime

# ── 1. Baca data ──────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook('Lokasi KNMP.xlsx', read_only=True)
ws = wb.active

# Kolom (0-indexed): No=0,ID=1,Nama=2,Desa=3,Kec=4,Kab=5,Prov=6,
#   Tahap=7,Tahun=8,Lat=9,Lon=10,Penyedia=11,NoKontrakP=12,
#   NilaiKontrakP=13,Pengawasan=14,NoKontrakWas=15,NilaiKontrakWas=16,
#   RealisasiP=17,RealisasiWas=18,Progres=19,Kondisi=20,Kategori=21,
#   SarprasAda=22,SarprasNA=23

markers = []
for row in ws.iter_rows(min_row=2, values_only=True):
    no = row[0]
    if no is None or not str(no).strip().isdigit():
        continue
    lat = row[9]
    lon = row[10]
    if lat is None or lon is None:
        continue

    progres = row[19]
    try:
        progres = float(progres) if progres is not None else 0.0
    except (ValueError, TypeError):
        progres = 0.0

    nilai_p = row[13]
    try:
        nilai_p = int(nilai_p) if nilai_p is not None else 0
    except (ValueError, TypeError):
        nilai_p = 0

    realisasi = row[17]
    try:
        realisasi = int(realisasi) if realisasi is not None else 0
    except (ValueError, TypeError):
        realisasi = 0

    markers.append({
        'id':         row[1],
        'nama':       str(row[2] or '').strip(),
        'desa':       str(row[3] or '').strip(),
        'kecamatan':  str(row[4] or '').strip(),
        'kabupaten':  str(row[5] or '').strip(),
        'provinsi':   str(row[6] or '').strip().upper(),
        'tahap':      str(row[7] or '').strip(),
        'tahun':      str(row[8] or '').strip(),
        'lat':        float(lat),
        'lon':        float(lon),
        'penyedia':   str(row[11] or '').strip(),
        'nilai_p':    nilai_p,
        'pengawas':   str(row[14] or '').strip(),
        'realisasi':  realisasi,
        'progres':    progres,
        'kondisi':    str(row[20] or '').strip(),
        'sarAda':     int(row[22]) if row[22] is not None else 0,
        'sarNA':      int(row[23]) if row[23] is not None else 0,
    })

wb.close()

# ── 2. Derived stats ──────────────────────────────────────────────────────────
provinsi_list  = sorted(set(m['provinsi'] for m in markers if m['provinsi']))
tahap_list     = sorted(set(m['tahap']    for m in markers if m['tahap']))
total          = len(markers)
selesai        = sum(1 for m in markers if m['progres'] >= 100)
total_nilai    = sum(m['nilai_p'] for m in markers)

tgl      = datetime.now().strftime('%d %B %Y')
tgl_file = datetime.now().strftime('%Y%m%d')

markers_json  = json.dumps(markers, ensure_ascii=False, separators=(',', ':'))
prov_options  = '\n          '.join(
    f'<option value="{p}">{p.title()}</option>' for p in provinsi_list
)
tahap_options = '\n          '.join(
    f'<option value="{t}">Tahap {t}</option>' for t in tahap_list
)

def fmt_rp(n):
    """Python-side Rp formatter for static stats in HTML."""
    if n >= 1e12:  return f"Rp {n/1e12:.2f} T".replace('.', ',')
    if n >= 1e9:   return f"Rp {n/1e9:.2f} M".replace('.', ',')
    if n >= 1e6:   return f"Rp {n/1e6:.0f} Jt"
    return f"Rp {n:,.0f}"

# ── 3. HTML ───────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Peta KNMP Operasional — PT Agrinas Jaladri Nusantara</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;font-family:'Segoe UI',system-ui,sans-serif;background:#0d2244;overflow:hidden}}

/* ── Header ── */
#hdr{{
  position:fixed;top:0;left:0;right:0;z-index:1000;height:56px;
  background:linear-gradient(135deg,#1B3A6B 0%,#0d2244 100%);
  display:flex;align-items:center;justify-content:space-between;padding:0 20px;
  border-bottom:1px solid rgba(201,168,76,.35);
}}
#hdr-brand{{display:flex;flex-direction:column;gap:1px}}
#hdr-title{{font-size:1.05rem;font-weight:700;color:#C9A84C;letter-spacing:.3px}}
#hdr-sub{{font-size:.68rem;color:rgba(203,213,225,.75)}}
#hdr-right{{display:flex;align-items:center;gap:10px}}
.hdr-chip{{font-size:.75rem;background:rgba(201,168,76,.15);border:1px solid rgba(201,168,76,.4);color:#C9A84C;padding:4px 11px;border-radius:20px;white-space:nowrap}}
#hdr-date{{font-size:.7rem;color:#64748b}}

/* ── Layout ── */
#layout{{display:flex;height:100vh;padding-top:56px}}

/* ── Sidebar ── */
#sidebar{{
  width:285px;flex-shrink:0;background:#162d55;
  overflow-y:auto;overflow-x:hidden;padding:12px;
  display:flex;flex-direction:column;gap:10px;
  border-right:1px solid rgba(201,168,76,.15);
}}
#sidebar::-webkit-scrollbar{{width:3px}}
#sidebar::-webkit-scrollbar-thumb{{background:rgba(201,168,76,.35);border-radius:2px}}

.panel{{background:rgba(255,255,255,.05);border:1px solid rgba(201,168,76,.18);border-radius:8px;padding:10px 12px}}
.ptitle{{font-size:.66rem;font-weight:700;color:#C9A84C;text-transform:uppercase;letter-spacing:.9px;margin-bottom:8px}}

/* ── Stats grid ── */
.stats-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.stat-box{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);border-radius:6px;padding:8px 10px}}
.stat-num{{font-size:1.4rem;font-weight:800;color:#C9A84C;line-height:1}}
.stat-lbl{{font-size:.64rem;color:#94a3b8;margin-top:2px}}
.stat-box.wide{{grid-column:1/-1}}
.stat-num.sm{{font-size:1rem}}

/* ── Search ── */
#search{{
  width:100%;padding:7px 10px;
  background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);
  border-radius:6px;color:#fff;font-size:.82rem;outline:none;
}}
#search::placeholder{{color:rgba(255,255,255,.32)}}
#search:focus{{border-color:rgba(201,168,76,.55)}}

/* ── Filters ── */
.flbl{{display:block;font-size:.7rem;color:#94a3b8;margin-bottom:3px}}
.fgap{{height:8px}}
select{{
  width:100%;padding:7px 10px;
  background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);
  border-radius:6px;color:#fff;font-size:.79rem;
  outline:none;cursor:pointer;-webkit-appearance:none;
}}
select option{{background:#1B3A6B}}
select:focus{{border-color:rgba(201,168,76,.55)}}

#btn-reset{{
  width:100%;padding:7px;margin-top:10px;
  background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.38);
  border-radius:6px;color:#C9A84C;font-size:.8rem;font-weight:700;
  cursor:pointer;transition:background .15s;letter-spacing:.3px;
}}
#btn-reset:hover{{background:rgba(201,168,76,.25)}}

/* ── Filter count ── */
#filter-count{{font-size:.75rem;color:#60a5fa;margin-top:8px;display:none;text-align:center}}

/* ── Legend ── */
.leg-item{{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:.77rem;color:#cbd5e1}}
.leg-dot{{width:12px;height:12px;border-radius:50%;flex-shrink:0;border:1.5px solid rgba(255,255,255,.22)}}
.leg-cnt{{margin-left:auto;font-size:.68rem;color:#94a3b8;font-variant-numeric:tabular-nums}}

/* ── Map ── */
#map{{flex:1;z-index:0}}

/* ── Popup ── */
.leaflet-popup-content-wrapper{{border-radius:9px;padding:0;box-shadow:0 6px 24px rgba(0,0,0,.35)}}
.leaflet-popup-content{{margin:0;min-width:240px;max-width:320px}}
.pu-head{{
  background:linear-gradient(135deg,#1B3A6B,#0d2244);
  color:#C9A84C;font-weight:700;font-size:.82rem;
  padding:9px 13px;border-radius:9px 9px 0 0;line-height:1.35;
}}
.pu-prog-wrap{{height:5px;background:#e2e8f0}}
.pu-prog-bar{{height:5px;transition:width .3s;border-radius:0 2px 2px 0}}
.pu-tbl{{width:100%;border-collapse:collapse;font-size:.76rem}}
.pu-tbl td{{padding:4px 11px;vertical-align:top}}
.pu-tbl tr:nth-child(even){{background:#f1f5f9}}
.pu-tbl td:first-child{{font-weight:600;color:#475569;width:90px;white-space:nowrap}}
.pu-tbl td:last-child{{color:#1e293b;word-break:break-word}}
.pu-badge{{
  display:inline-block;padding:1px 8px;border-radius:10px;
  font-size:.7rem;font-weight:700;color:#fff;
}}

/* ── Responsive ── */
@media(max-width:600px){{
  #sidebar{{display:none}}
  #hdr-date{{display:none}}
}}
</style>
</head>
<body>

<div id="hdr">
  <div id="hdr-brand">
    <div id="hdr-title">Peta KNMP Operasional</div>
    <div id="hdr-sub">PT Agrinas Jaladri Nusantara (Persero)</div>
  </div>
  <div id="hdr-right">
    <div class="hdr-chip">{total} Lokasi</div>
    <div id="hdr-date">{tgl}</div>
  </div>
</div>

<div id="layout">
  <div id="sidebar">

    <!-- Stats -->
    <div class="panel">
      <div class="ptitle">Ringkasan</div>
      <div class="stats-grid">
        <div class="stat-box">
          <div class="stat-num" id="stat-total">{total}</div>
          <div class="stat-lbl">Total KNMP</div>
        </div>
        <div class="stat-box">
          <div class="stat-num" id="stat-selesai">{selesai}</div>
          <div class="stat-lbl">Selesai 100%</div>
        </div>
        <div class="stat-box wide">
          <div class="stat-num sm">{fmt_rp(total_nilai)}</div>
          <div class="stat-lbl">Total Nilai Kontrak Penyedia</div>
        </div>
      </div>
      <div id="filter-count"></div>
    </div>

    <!-- Search -->
    <div class="panel">
      <div class="ptitle">Cari KNMP</div>
      <input type="text" id="search" placeholder="Nama, kabupaten, penyedia…">
    </div>

    <!-- Filters -->
    <div class="panel">
      <div class="ptitle">Filter</div>
      <label class="flbl">Provinsi</label>
      <select id="filter-prov">
        <option value="">Semua Provinsi</option>
          {prov_options}
      </select>
      <div class="fgap"></div>
      <label class="flbl">Tahap</label>
      <select id="filter-tahap">
        <option value="">Semua Tahap</option>
          {tahap_options}
      </select>
      <div class="fgap"></div>
      <label class="flbl">Status Progres</label>
      <select id="filter-status">
        <option value="">Semua Status</option>
        <option value="selesai">Selesai (100%)</option>
        <option value="berjalan">Berjalan (1–99%)</option>
        <option value="belum">Belum Mulai (0%)</option>
      </select>
      <button id="btn-reset">&#x21BA; Reset Filter</button>
    </div>

    <!-- Legend -->
    <div class="panel">
      <div class="ptitle">Legenda</div>
      <div class="leg-item"><span class="leg-dot" style="background:#10B981"></span><span>Selesai (100%)</span><span class="leg-cnt" id="lcnt-selesai"></span></div>
      <div class="leg-item"><span class="leg-dot" style="background:#F59E0B"></span><span>Berjalan (1–99%)</span><span class="leg-cnt" id="lcnt-berjalan"></span></div>
      <div class="leg-item"><span class="leg-dot" style="background:#EF4444"></span><span>Belum Mulai (0%)</span><span class="leg-cnt" id="lcnt-belum"></span></div>
    </div>

  </div><!-- /sidebar -->

  <div id="map"></div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const DATA = {markers_json};

function esc(s){{return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}

function fmtRp(n){{
  if(!n || n===0) return '-';
  if(n>=1e12) return 'Rp '+(n/1e12).toFixed(2).replace('.',',')+' T';
  if(n>=1e9)  return 'Rp '+(n/1e9).toFixed(2).replace('.',',')+' M';
  if(n>=1e6)  return 'Rp '+(n/1e6).toFixed(0)+' Jt';
  return 'Rp '+n.toLocaleString('id');
}}

function statusOf(p){{
  if(p>=100) return 'selesai';
  if(p>0)    return 'berjalan';
  return 'belum';
}}
const STATUS_COLOR = {{selesai:'#10B981',berjalan:'#F59E0B',belum:'#EF4444'}};
const STATUS_LABEL = {{selesai:'Selesai',berjalan:'Berjalan',belum:'Belum Mulai'}};

// ── Init map ──────────────────────────────────────────────────────────────────
const map = L.map('map',{{center:[-2.5,118],zoom:5}});

L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',{{
  attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
  subdomains:'abcd',maxZoom:19
}}).addTo(map);

// ── Cluster group ─────────────────────────────────────────────────────────────
const cluster = L.markerClusterGroup({{
  chunkedLoading:true,
  maxClusterRadius:55,
  iconCreateFunction:function(c){{
    const n=c.getChildCount();
    const sz=n<10?30:n<30?36:n<70?42:48;
    return L.divIcon({{
      html:`<div style="background:#1B3A6B;border:2.5px solid #C9A84C;border-radius:50%;width:${{sz}}px;height:${{sz}}px;display:flex;align-items:center;justify-content:center;color:#C9A84C;font-size:${{sz<36?11:13}}px;font-weight:800;">${{n}}</div>`,
      className:'',iconSize:[sz,sz],iconAnchor:[sz/2,sz/2]
    }});
  }}
}});

// ── Build markers ─────────────────────────────────────────────────────────────
const allMarkers = DATA.map(d=>{{
  const status = statusOf(d.progres);
  const color  = STATUS_COLOR[status];
  const m = L.circleMarker([d.lat,d.lon],{{
    radius:8,fillColor:color,color:'#fff',weight:1.5,opacity:1,fillOpacity:.88
  }});

  const progPct  = Math.round(d.progres);
  const progBar  = `<div class="pu-prog-wrap"><div class="pu-prog-bar" style="width:${{progPct}}%;background:${{color}}"></div></div>`;
  const kondisi  = d.kondisi ? `<tr><td>Kondisi</td><td>${{esc(d.kondisi.slice(0,120))}}</td></tr>` : '';
  const sarRow   = `<tr><td>Sarpras</td><td>Ada: ${{d.sarAda}} &nbsp;|&nbsp; N/A: ${{d.sarNA}}</td></tr>`;
  const nilaiRow = d.nilai_p ? `<tr><td>Nilai Kontrak</td><td>${{fmtRp(d.nilai_p)}}</td></tr>` : '';
  const rlsRow   = d.realisasi ? `<tr><td>Realisasi</td><td>${{fmtRp(d.realisasi)}}</td></tr>` : '';

  m.bindPopup(`
    <div class="pu-head">KNMP #${{esc(d.id)}} &mdash; ${{esc(d.nama)}}</div>
    ${{progBar}}
    <table class="pu-tbl">
      <tr><td>Tahap</td><td>Tahap ${{esc(d.tahap)}} &middot; ${{esc(d.tahun)}} &nbsp;<span class="pu-badge" style="background:${{color}}">${{STATUS_LABEL[status]}} ${{progPct}}%</span></td></tr>
      <tr><td>Desa/Kel.</td><td>${{esc(d.desa)}}</td></tr>
      <tr><td>Kecamatan</td><td>${{esc(d.kecamatan)}}</td></tr>
      <tr><td>Kabupaten</td><td>${{esc(d.kabupaten)}}</td></tr>
      <tr><td>Provinsi</td><td>${{esc(d.provinsi)}}</td></tr>
      <tr><td>Penyedia</td><td>${{esc(d.penyedia)}}</td></tr>
      ${{nilaiRow}}
      ${{rlsRow}}
      <tr><td>Pengawas</td><td>${{esc(d.pengawas)}}</td></tr>
      ${{sarRow}}
      ${{kondisi}}
    </table>
  `,{{maxWidth:320}});

  m._d = d;
  return m;
}});

cluster.addLayers(allMarkers);
map.addLayer(cluster);

// ── Legend counts ─────────────────────────────────────────────────────────────
const LCNT = {{selesai:0,berjalan:0,belum:0}};
DATA.forEach(d=>{{ LCNT[statusOf(d.progres)]++; }});
document.getElementById('lcnt-selesai').textContent  = LCNT.selesai;
document.getElementById('lcnt-berjalan').textContent = LCNT.berjalan;
document.getElementById('lcnt-belum').textContent    = LCNT.belum;

// ── Filter logic ──────────────────────────────────────────────────────────────
const searchEl  = document.getElementById('search');
const provEl    = document.getElementById('filter-prov');
const tahapEl   = document.getElementById('filter-tahap');
const statusEl  = document.getElementById('filter-status');
const btnReset  = document.getElementById('btn-reset');
const fcountEl  = document.getElementById('filter-count');
const statTotal = document.getElementById('stat-total');
const statSel   = document.getElementById('stat-selesai');

function applyFilters(){{
  const q     = searchEl.value.toLowerCase().trim();
  const prov  = provEl.value;
  const tahap = tahapEl.value;
  const sts   = statusEl.value;

  const filtered = allMarkers.filter(m=>{{
    const d = m._d;
    if(prov  && d.provinsi!==prov)       return false;
    if(tahap && d.tahap!==tahap)         return false;
    if(sts   && statusOf(d.progres)!==sts) return false;
    if(q && ![d.nama,d.kabupaten,d.kecamatan,d.desa,d.penyedia]
             .some(v=>v.toLowerCase().includes(q))) return false;
    return true;
  }});

  cluster.clearLayers();
  cluster.addLayers(filtered);

  const n = filtered.length;
  statTotal.textContent = n;
  statSel.textContent   = filtered.filter(m=>m._d.progres>=100).length;

  if(n < allMarkers.length){{
    fcountEl.style.display='block';
    fcountEl.textContent=`dari ${{allMarkers.length}} total`;
  }} else {{
    fcountEl.style.display='none';
  }}

  if(n>0 && n<allMarkers.length){{
    const bounds = L.featureGroup(filtered).getBounds();
    if(bounds.isValid()) map.fitBounds(bounds,{{padding:[40,40],maxZoom:13}});
  }}
}}

searchEl.addEventListener('input',  applyFilters);
provEl.addEventListener('change',   applyFilters);
tahapEl.addEventListener('change',  applyFilters);
statusEl.addEventListener('change', applyFilters);

btnReset.addEventListener('click',()=>{{
  searchEl.value=''; provEl.value=''; tahapEl.value=''; statusEl.value='';
  statTotal.textContent = allMarkers.length;
  statSel.textContent   = allMarkers.filter(m=>m._d.progres>=100).length;
  fcountEl.style.display='none';
  cluster.clearLayers(); cluster.addLayers(allMarkers);
  map.setView([-2.5,118],5);
}});
</script>
</body>
</html>"""

# ── 4. Tulis output ───────────────────────────────────────────────────────────
os.makedirs('output', exist_ok=True)

out_dated = f'output/knmp_{tgl_file}.html'
out_root  = 'knmp.html'

with open(out_dated, 'w', encoding='utf-8') as f:
    f.write(html)
with open(out_root, 'w', encoding='utf-8') as f:
    f.write(html)

kb = len(html.encode('utf-8')) // 1024
print(f"Generated {out_root} ({kb} KB)")
print(f"Generated {out_dated}")
print(f"Total markers: {total}  |  Selesai: {selesai}  |  Total kontrak: {fmt_rp(total_nilai)}")
