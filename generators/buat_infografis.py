"""
generators/buat_infografis.py — Generate dashboard harga static HTML dari MySQL
Query: commodity_prices + regional_prices + alert_log → index.html
"""
import os, sys
from datetime import datetime
sys.path.insert(0, "backend")

from app.database import SessionLocal
from app.models import CommodityPrice, RegionalPrice, AlertLog, KnmpLocation


def generate():
    db = SessionLocal()
    now = datetime.now()
    tgl = now.strftime("%d %B %Y")
    print("=" * 55)
    print("Dashboard Generator — MySQL → index.html")
    print("=" * 55)

    try:
        latest_cp = db.query(CommodityPrice.tanggal).order_by(CommodityPrice.tanggal.desc()).first()
        prices = db.query(CommodityPrice).filter(CommodityPrice.tanggal == latest_cp[0]).all() if latest_cp else []
        print(f"  Prices: {len(prices)}")

        latest_rp = db.query(RegionalPrice.tanggal).order_by(RegionalPrice.tanggal.desc()).first()
        rp_all = db.query(RegionalPrice).filter(RegionalPrice.tanggal == latest_rp[0]).all() if latest_rp else []
        wilayah = sorted(set(r.wilayah for r in rp_all))

        alerts = db.query(AlertLog).order_by(AlertLog.tanggal.desc()).limit(10).all()
        total_lokasi = db.query(KnmpLocation).count()

    finally:
        db.close()

    # ── Build HTML cards ──
    cards = ""
    for p in prices:
        cat = "b"
        if any(t in p.komoditas.lower() for t in ["tuna","cakalang","kakap","kerapu","cumi","lobster"]):
            cat = "t"
        lo = int(p.harga_tambak_low or 0); hi = int(p.harga_tambak_high or 0)
        tambak = f"{lo:,} – {hi:,}".replace(",", ".")
        ekspor = f"${p.harga_ekspor_low:.2f}" if p.harga_ekspor_low else "—"
        cards += f'''<div class="kc" data-cat="{cat}"><div class="kc-t"><span class="badge {'b' if cat=='b' else 't'}">{'Budidaya' if cat=='b' else 'Tangkap'}</span></div><div class="kc-n">{p.komoditas}</div><div class="kc-s">{p.size}</div><div class="kc-h">Rp {tambak}<span class="kc-u">/kg</span></div><div class="kc-e">Ekspor: USD {ekspor}/kg</div></div>'''

    # ── Regional price rows ──
    rp_rows = ""
    seen = set()
    for r in rp_all:
        k = (r.wilayah, r.komoditas, r.size)
        if k in seen: continue
        seen.add(k)
        lo = int(r.harga_tambak_low or 0); hi = int(r.harga_tambak_high or 0)
        rp_rows += f'''<tr><td>{r.wilayah}</td><td>{r.komoditas.split("(")[0].strip()}</td><td>{r.size}</td><td><strong>Rp {lo:,} – {hi:,}</strong>/kg</td></tr>'''

    # ── Alert rows ──
    alert_rows = ""
    for a in alerts:
        cls = "merah" if a.alert_type == "MERAH" else "kuning" if a.alert_type == "KUNING" else "biru"
        alert_rows += f'''<tr><td>{a.tanggal}</td><td><span class="badge-alert {cls}">{a.alert_type}</span></td><td>{a.komoditas.split("(")[0].strip()}</td><td>{a.pesan or ''}</td></tr>'''

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market Watch AJN — {tgl}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#eef2f7;color:#1e293b;font-size:14px;min-height:100vh}}
.hdr{{background:linear-gradient(135deg,#1B3A6B 0%,#0d2244 100%);color:#fff;padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:52px}}
.hdr h1{{font-size:1rem;font-weight:800;letter-spacing:.4px;color:#C9A84C}}
.hdr p{{font-size:.65rem;color:rgba(203,213,225,.7)}}
.hdr-r{{display:flex;align-items:center;gap:12px}}
.hdr-date{{font-size:.7rem;background:rgba(201,168,76,.15);border:1px solid rgba(201,168,76,.35);color:#C9A84C;padding:4px 12px;border-radius:16px}}

.nav{{background:#fff;border-bottom:1px solid #e2e8f0;padding:0 24px;display:flex;gap:0}}
.nav a{{color:#64748b;text-decoration:none;font-size:.75rem;font-weight:600;padding:9px 16px;border-bottom:2px solid transparent;transition:all .15s}}
.nav a:hover{{color:#1B3A6B}}
.nav a.act{{color:#1B3A6B;border-bottom-color:#C9A84C}}

.wrap{{max-width:1200px;margin:0 auto;padding:20px 16px}}

.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:20px}}
.sc{{background:#fff;border-radius:10px;padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,.06);border-left:4px solid #1B3A6B}}
.sc.gold{{border-left-color:#C9A84C}}.sc.green{{border-left-color:#10B981}}.sc.blue{{border-left-color:#3B82F6}}
.sc-n{{font-size:1.5rem;font-weight:800;color:#1B3A6B;line-height:1}}
.sc-l{{font-size:.68rem;color:#64748b;margin-top:2px}}

.tl{{font-size:.85rem;font-weight:700;color:#1B3A6B;margin-bottom:12px;padding-bottom:6px;border-bottom:2px solid #C9A84C;display:flex;align-items:center;gap:6px}}
.tl::before{{content:'';width:6px;height:6px;border-radius:50%;background:#C9A84C;flex-shrink:0}}

.fb{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}}
.fb button{{padding:5px 14px;font-size:.75rem;font-weight:600;border-radius:16px;border:2px solid #cbd5e1;background:#fff;color:#475569;cursor:pointer}}
.fb button.act{{background:#1B3A6B;color:#fff;border-color:#1B3A6B}}

.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px}}
@media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:580px){{.grid{{grid-template-columns:1fr}}}}

.kc{{background:#fff;border-radius:10px;padding:12px 14px;box-shadow:0 1px 4px rgba(0,0,0,.06);border-top:3px solid #1B3A6B;cursor:default;transition:transform .15s}}
.kc:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.1)}}
.kc[data-cat="t"]{{border-top-color:#145A30}}
.kc.hide{{display:none}}
.kc-t{{margin-bottom:4px}}
.badge{{display:inline-block;padding:2px 8px;border-radius:8px;font-size:.6rem;font-weight:700}}
.badge.b{{background:#DBEAFE;color:#1E40AF}}
.badge.t{{background:#D1FAE5;color:#065F46}}
.kc-n{{font-size:.8rem;font-weight:700;color:#1B3A6B}}
.kc-s{{font-size:.65rem;color:#94a3b8}}
.kc-h{{font-size:1.15rem;font-weight:800;color:#1e293b;margin-top:3px}}
.kc-u{{font-size:.62rem;font-weight:400;color:#94a3b8}}
.kc-e{{font-size:.65rem;color:#64748b}}

.table-wrap{{background:#fff;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.06);overflow-x:auto;margin-bottom:20px}}
table{{width:100%;border-collapse:collapse;font-size:.75rem}}
th,td{{padding:7px 10px;text-align:left;border-bottom:1px solid #e2e8f0}}
th{{background:#f8fafc;color:#475569;font-weight:700;font-size:.65rem;text-transform:uppercase;letter-spacing:.4px}}
tr:hover td{{background:#f8fafc}}

.badge-alert{{display:inline-block;padding:1px 6px;border-radius:6px;font-size:.6rem;font-weight:700}}
.merah{{background:#FEE2E2;color:#991B1B}}
.kuning{{background:#FEF3C7;color:#92400E}}
.biru{{background:#DBEAFE;color:#1E40AF}}

.footer{{text-align:center;padding:16px;color:#94a3b8;font-size:.65rem;border-top:1px solid #e2e8f0;margin-top:16px}}
</style>
</head>
<body>
<div class="hdr"><div><h1>Market Watch AJN</h1><p>PT Agrinas Jaladri Nusantara (Persero)</p></div><div class="hdr-r"><div class="hdr-date">{tgl}</div></div></div>
<div class="nav"><a class="act" href="./index.html">📊 Harga</a><a href="./knmp.html">🗺️ Peta KNMP</a></div>
<div class="wrap">

<div class="summary">
  <div class="sc"><div class="sc-n">{len(prices)}</div><div class="sc-l">Komoditas</div></div>
  <div class="sc gold"><div class="sc-n">{len(alerts)}</div><div class="sc-l">Alert</div></div>
  <div class="sc blue"><div class="sc-n">{total_lokasi}</div><div class="sc-l">Lokasi KNMP</div></div>
  <div class="sc green"><div class="sc-n">{len(wilayah)}</div><div class="sc-l">Wilayah Harga</div></div>
</div>

<div class="tl">Harga Tambak</div>
<div class="fb"><button class="act" onclick="f('all')">Semua</button><button onclick="f('b')">Budidaya</button><button onclick="f('t')">Tangkap</button></div>
<div class="grid" id="g">
  {cards}
</div>

<div class="tl">Harga per Wilayah ({len(wilayah)} Wilayah)</div>
<div class="table-wrap">{f'''<table><thead><tr><th>Wilayah</th><th>Komoditas</th><th>Size</th><th>Harga</th></tr></thead><tbody>{rp_rows}</tbody></table>''' if rp_rows else '<p style="padding:16px;color:#94a3b8">Belum ada data wilayah.</p>'}</div>

<div class="tl">Alert Pergerakan Harga</div>
<div class="table-wrap">{f'''<table><thead><tr><th>Tanggal</th><th>Level</th><th>Komoditas</th><th>Pesan</th></tr></thead><tbody>{alert_rows}</tbody></table>''' if alert_rows else '<p style="padding:16px;color:#94a3b8">Tidak ada alert saat ini.</p>'}</div>

</div>
<div class="footer">Market Watch AJN &copy; {now.year} — PT Agrinas Jaladri Nusantara (Persero)</div>

<script>
function f(c){{document.querySelectorAll('.fb button').forEach(function(b){{b.classList.remove('act')}});if(c!=='all')document.querySelector('.fb button[onclick*="'+c+'"').classList.add('act');document.querySelectorAll('#g .kc').forEach(function(e){{e.classList.toggle('hide',c!=='all'&&e.getAttribute('data-cat')!==c)}})}}
</script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    kb = len(html.encode("utf-8")) // 1024
    print(f"✓ index.html ({kb} KB) — {len(prices)} komoditas")
    print("=" * 55)


if __name__ == "__main__":
    generate()
