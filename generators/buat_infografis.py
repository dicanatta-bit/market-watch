"""
generators/buat_infografis.py — Generate index.html dashboard harga dari MySQL
Query: commodity_prices + regional_prices → embedded JS → static HTML
"""
import json, os, sys
from datetime import datetime, date
from config import Config
from app import create_app
from models import db, CommodityPrice, RegionalPrice, AlertLog, KnmpLocation, KnmpLocationSnapshot


def generate():
    app = create_app(Config)
    with app.app_context():
        now = datetime.now()
        tgl = now.strftime("%d %B %Y")

        print("=" * 55)
        print(f"Dashboard Generator — MySQL → index.html")
        print("=" * 55)

        latest_date = db.session.query(db.func.max(CommodityPrice.tanggal)).scalar()
        if not latest_date:
            latest_date = date.today()

        prices = CommodityPrice.query.filter_by(tanggal=latest_date).all()
        print(f"  Prices: {len(prices)} komoditas from {latest_date}")

        alerts = AlertLog.query.order_by(AlertLog.tanggal.desc()).limit(20).all()
        total_lokasi = KnmpLocation.query.count()
        latest_snaps = (
            KnmpLocationSnapshot.query
            .filter_by(snapshot_date=db.session.query(db.func.max(KnmpLocationSnapshot.snapshot_date)).scalar())
            .all()
        ) if KnmpLocationSnapshot.query.first() else []
        progress_nasional = (
            sum(s.progress_kumulatif or 0 for s in latest_snaps) / len(latest_snaps)
            if latest_snaps else 0
        )

        # Build commodity cards HTML
        cards_html = ""
        for p in prices:
            k_nama = p.komoditas
            k_size = p.size
            cat = "b"  # budidaya default
            if any(t in k_nama.lower() for t in ["tuna", "cakalang", "kakap", "kerapu", "cumi", "lobster"]):
                cat = "t"  # tangkap

            tambak = f"{int(p.harga_tambak_low or 0):,} – {int(p.harga_tambak_high or 0):,}".replace(",", ".")
            ekspor = f"{p.harga_ekspor_low:.2f}" if p.harga_ekspor_low else "—"

            # Trend (simplified — always flat for now)
            trend_icon = "→"
            trend_class = "trend-flat"
            pct_label = "Stabil"

            cards_html += f"""
      <div class="komod-card" data-cat="{cat}">
        <div class="kcard-top">
          <span class="cat-badge {'cat-b' if cat == 'b' else 'cat-t'}">{'Budidaya' if cat == 'b' else 'Tangkap'}</span>
          <span class="trend-icon {trend_class}">{trend_icon}</span>
        </div>
        <div class="kcard-name">{k_nama}</div>
        <div class="kcard-size">{k_size}</div>
        <div class="kcard-harga">Rp {tambak}<span class="kcard-unit">/kg</span></div>
        <div class="kcard-ekspor">Ekspor: USD {ekspor}/kg</div>
        <div class="kcard-badges">
          <span class="pct-badge badge-neutral">{pct_label}</span>
          <span class="pct-badge badge-neutral">{p.tingkat_kepercayaan or 'Estimasi'}</span>
        </div>
        <div class="kcard-hint">&#9432; {p.sumber or ''}</div>
      </div>"""

        # Alert rows
        alert_rows = ""
        for a in alerts:
            alert_rows += f"""
        <tr>
          <td>{a.tanggal}</td>
          <td><span class="badge {'badge-merah' if a.alert_type == 'MERAH' else 'badge-kuning' if a.alert_type == 'KUNING' else 'badge-biru'}">{a.alert_type}</span></td>
          <td>{a.komoditas}</td>
          <td>{a.pesan or '—'}</td>
        </tr>"""

        # Regional price table
        rp_date = db.session.query(db.func.max(RegionalPrice.tanggal)).scalar()
        rp_rows = ""
        wilayah_count = 0
        if rp_date:
            rp = RegionalPrice.query.filter_by(tanggal=rp_date).all()
            wilayah_count = len(set(r.wilayah for r in rp))
            seen = set()
            for r in rp:
                key = (r.wilayah, r.komoditas, r.size)
                if key in seen:
                    continue
                seen.add(key)
                lo = int(r.harga_tambak_low or 0)
                hi = int(r.harga_tambak_high or 0)
                rp_rows += f"""
        <tr>
          <td>{r.wilayah}</td>
          <td>{r.komoditas.split('(')[0].strip()}</td>
          <td>{r.size}</td>
          <td><strong>Rp {lo:,} – {hi:,}</strong>/kg</td>
        </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market Watch AJN — {tgl}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#eef2f7;color:#1a1a1a;font-size:14px;min-height:100vh}}

/* ── Header ── */
.hdr{{background:linear-gradient(135deg,#1B3A6B 0%,#0d2244 100%);color:#fff;padding:0}}
.hdr-inner{{max-width:1200px;margin:0 auto;padding:18px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
.hdr-brand{{display:flex;flex-direction:column;gap:4px}}
.hdr-logo{{font-size:1.5rem;font-weight:800;letter-spacing:.5px;color:#C9A84C}}
.hdr-sub{{font-size:.75rem;opacity:.85;color:#cbd5e1}}
.hdr-meta{{text-align:right}}
.hdr-date{{font-size:.8rem;background:rgba(201,168,76,.2);border:1px solid rgba(201,168,76,.4);color:#C9A84C;padding:5px 12px;border-radius:20px;white-space:nowrap}}

/* ── Nav Bar ── */
.nav-bar{{background:#0d2244;border-top:1px solid rgba(201,168,76,.3)}}
.nav-bar-inner{{max-width:1200px;margin:0 auto;padding:0 24px;display:flex;gap:0}}
.nav-link{{color:rgba(255,255,255,.5);text-decoration:none;font-size:.78rem;font-weight:500;padding:8px 16px;border-bottom:2px solid transparent;transition:all .15s}}
.nav-link:hover{{color:#C9A84C;background:rgba(201,168,76,.08)}}
.nav-link.active{{color:#C9A84C;border-bottom-color:#C9A84C;background:rgba(201,168,76,.1)}}

.wrap{{max-width:1200px;margin:0 auto;padding:20px 14px}}

.summary-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:20px}}
.sum-card{{background:#fff;border-radius:10px;padding:16px 20px;box-shadow:0 1px 6px rgba(0,0,0,.09);border-left:4px solid #1B3A6B;display:flex;flex-direction:column;gap:4px}}
.sum-card.gold{{border-left-color:#C9A84C}}
.sum-card.green{{border-left-color:#1E7E34}}
.sum-card.red{{border-left-color:#721C24}}
.sum-num{{font-size:2rem;font-weight:800;color:#1B3A6B;line-height:1}}
.sum-lbl{{font-size:.78rem;color:#666;font-weight:500}}

.sec-title{{font-size:.92rem;font-weight:700;color:#1B3A6B;margin-bottom:12px;padding-bottom:6px;border-bottom:2px solid #C9A84C;display:flex;align-items:center;gap:8px}}
.sec-title .dot{{width:8px;height:8px;border-radius:50%;background:#C9A84C;flex-shrink:0}}

.filter-bar{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}}
.filter-btn{{padding:6px 16px;border-radius:20px;border:2px solid #1B3A6B;background:#fff;color:#1B3A6B;font-size:.8rem;font-weight:600;cursor:pointer;transition:all .18s}}
.filter-btn:hover,.filter-btn.active{{background:#1B3A6B;color:#fff}}

.komod-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}}
@media(max-width:900px){{.komod-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:580px){{.komod-grid{{grid-template-columns:1fr}}}}
.komod-card{{background:#fff;border-radius:10px;padding:14px 16px;box-shadow:0 1px 5px rgba(0,0,0,.09);border-top:3px solid #1B3A6B;display:flex;flex-direction:column;gap:5px;transition:transform .18s,box-shadow .18s}}
.komod-card:hover{{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.16)}}
.komod-card[data-cat="t"]{{border-top-color:#145A30}}
.komod-card.hidden{{display:none}}
.kcard-top{{display:flex;justify-content:space-between;align-items:center}}
.cat-badge{{font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px}}
.cat-b{{background:#dbeafe;color:#1e3a8a}}
.cat-t{{background:#dcfce7;color:#14532d}}
.trend-icon{{font-size:1.3rem;font-weight:800;line-height:1}}
.trend-up{{color:#1E7E34}}.trend-dn{{color:#721C24}}.trend-flat{{color:#6C757D}}
.kcard-name{{font-size:.88rem;font-weight:700;color:#1B3A6B;margin-top:2px}}
.kcard-size{{font-size:.75rem;color:#888}}
.kcard-harga{{font-size:1.25rem;font-weight:800;color:#1a1a1a;margin-top:4px}}
.kcard-unit{{font-size:.7rem;font-weight:400;color:#888}}
.kcard-ekspor{{font-size:.75rem;color:#555}}
.kcard-badges{{display:flex;gap:5px;flex-wrap:wrap;margin-top:5px}}
.pct-badge{{font-size:.68rem;font-weight:700;padding:2px 7px;border-radius:8px}}
.badge-neutral{{background:#f0f0f0;color:#6C757D}}
.kcard-hint{{font-size:.6rem;color:#bbb;text-align:right;margin-top:auto;padding-top:6px;letter-spacing:.3px}}

table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #e2e8f0}}
th{{background:#1B3A6B;color:#fff;font-weight:600;font-size:.75rem}}
.badge-merah{{background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:8px;font-size:.65rem;font-weight:700}}
.badge-kuning{{background:#FEF3C7;color:#92400E;padding:2px 8px;border-radius:8px;font-size:.65rem;font-weight:700}}
.badge-biru{{background:#DBEAFE;color:#1E40AF;padding:2px 8px;border-radius:8px;font-size:.65rem;font-weight:700}}

.card{{background:#fff;border-radius:10px;box-shadow:0 1px 6px rgba(0,0,0,.08);padding:20px;margin-bottom:16px}}

.footer{{text-align:center;padding:20px;color:#94a3b8;font-size:.7rem;border-top:1px solid #e2e8f0;margin-top:20px}}
</style>
</head>
<body>

<div class="hdr">
  <div class="hdr-inner">
    <div class="hdr-brand">
      <div class="hdr-logo">Market Watch AJN</div>
      <div class="hdr-sub">PT Agrinas Jaladri Nusantara (Persero) — Pemantauan Harga Komoditas Perikanan Strategis</div>
    </div>
    <div class="hdr-meta">
      <div class="hdr-date">Last Update: {tgl}</div>
    </div>
  </div>
</div>

<div class="nav-bar">
  <div class="nav-bar-inner">
    <a class="nav-link active" href="./">&#128202; Harga</a>
    <a class="nav-link" href="./knmp.html">&#128506;&#65039; Peta KNMP</a>
  </div>
</div>

<div class="wrap">

  <div class="summary-row">
    <div class="sum-card">
      <div class="sum-num">{len(prices)}</div>
      <div class="sum-lbl">Total Komoditas Dipantau</div>
    </div>
    <div class="sum-card gold">
      <div class="sum-num">{len(alerts)}</div>
      <div class="sum-lbl">Alert Aktif</div>
    </div>
    <div class="sum-card green">
      <div class="sum-num">{total_lokasi}</div>
      <div class="sum-lbl">Lokasi KNMP Dipantau</div>
    </div>
    <div class="sum-card">
      <div class="sum-num">{progress_nasional:.1f}%</div>
      <div class="sum-lbl">Progress Nasional</div>
    </div>
  </div>

  <div class="sec-title"><span class="dot"></span>Harga Tambak — {tgl}</div>
  <div class="filter-bar">
    <button class="filter-btn active" data-filter="all">Semua</button>
    <button class="filter-btn" data-filter="b">Budidaya</button>
    <button class="filter-btn" data-filter="t">Tangkap</button>
  </div>
  <div class="komod-grid" id="komodGrid">
    {cards_html}
  </div>

  <div class="sec-title"><span class="dot"></span>Alert & Pergerakan Harga</div>
  <div class="card" style="overflow-x:auto">
    {f'''<table>
      <thead><tr><th>Tanggal</th><th>Level</th><th>Komoditas</th><th>Pesan</th></tr></thead>
      <tbody>{alert_rows}</tbody>
    </table>''' if alerts else '<p style="padding:16px;color:#64748b">Tidak ada alert saat ini.</p>'}
  </div>

  <div class="sec-title"><span class="dot"></span>Harga per Wilayah ({wilayah_count} Wilayah)</div>
  <div class="card" style="overflow-x:auto">
    {f'''<table>
      <thead><tr><th>Wilayah</th><th>Komoditas</th><th>Size</th><th>Harga Tambak</th></tr></thead>
      <tbody>{rp_rows}</tbody>
    </table>''' if rp_rows else '<p style="padding:16px;color:#64748b">Belum ada data harga wilayah.</p>'}
  </div>

</div>

<div class="footer">
  Market Watch AJN — PT Agrinas Jaladri Nusantara (Persero) &copy; {now.year}
</div>

<script>
(function() {{
  var btns = document.querySelectorAll('.filter-btn');
  btns.forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      var filter = this.getAttribute('data-filter');
      btns.forEach(function(b) {{ b.classList.remove('active'); }});
      this.classList.add('active');
      var cards = document.querySelectorAll('#komodGrid .komod-card');
      cards.forEach(function(c) {{
        if (filter === 'all' || c.getAttribute('data-cat') === filter) {{
          c.classList.remove('hidden');
        }} else {{
          c.classList.add('hidden');
        }}
      }});
    }});
  }});
}})();
</script>
</body>
</html>"""

        os.makedirs("output", exist_ok=True)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)

        kb = len(html.encode("utf-8")) // 1024
        print(f"\n✓ index.html ({kb} KB)")
        print(f"  Komoditas: {len(prices)} | Alert: {len(alerts)} | Lokasi KNMP: {total_lokasi}")
        print(f"  Harga per wilayah: {wilayah_count}")
        print("=" * 55)


if __name__ == "__main__":
    generate()
