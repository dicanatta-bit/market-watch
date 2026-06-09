"""
generators/buat_infografis.py — Dashboard harga publik (light blue theme)
Query: commodity_prices + regional_prices → static index.html
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
        print("Dashboard Generator — index.html (light theme)")
        print("=" * 55)

        latest_cp = db.session.query(db.func.max(CommodityPrice.tanggal)).scalar()
        prices = CommodityPrice.query.filter_by(tanggal=latest_cp).all() if latest_cp else []
        print(f"  Commodity prices: {len(prices)} from {latest_cp}")

        alerts = AlertLog.query.order_by(AlertLog.tanggal.desc()).limit(15).all()
        total_lokasi = KnmpLocation.query.count()

        latest_snap_date = db.session.query(db.func.max(KnmpLocationSnapshot.snapshot_date)).scalar()
        latest_snaps = (
            KnmpLocationSnapshot.query.filter_by(snapshot_date=latest_snap_date).all()
            if latest_snap_date else []
        )
        if latest_snaps:
            progress_nasional = sum(s.progress_kumulatif or 0 for s in latest_snaps) / len(latest_snaps)
            n_selesai = sum(1 for s in latest_snaps if (s.progress_kumulatif or 0) >= 100)
            n_berjalan = sum(1 for s in latest_snaps if 0 < (s.progress_kumulatif or 0) < 100)
        else:
            progress_nasional = 0
            n_selesai = 0
            n_berjalan = 0

        # Regional prices
        rp_date = db.session.query(db.func.max(RegionalPrice.tanggal)).scalar()
        rp_all = RegionalPrice.query.filter_by(tanggal=rp_date).all() if rp_date else []
        wilayah_count = len(set(r.wilayah for r in rp_all))

        # ── Build HTML ──

        cards_html = ""
        for p in prices:
            cat = "b"
            if any(t in p.komoditas.lower() for t in ["tuna", "cakalang", "kakap", "kerapu", "cumi", "lobster"]):
                cat = "t"
            lo = int(p.harga_tambak_low or 0)
            hi = int(p.harga_tambak_high or 0)
            tambak = f"{lo:,} – {hi:,}".replace(",", ".")
            ekspor = f"{p.harga_ekspor_low:.2f}" if p.harga_ekspor_low else "—"

            cards_html += f"""
        <div class="komod-card" data-cat="{cat}">
          <div class="kcard-top">
            <span class="cat-badge {'cat-b' if cat=='b' else 'cat-t'}">{'Budidaya' if cat=='b' else 'Tangkap'}</span>
          </div>
          <div class="kcard-name">{p.komoditas}</div>
          <div class="kcard-size">{p.size}</div>
          <div class="kcard-harga">Rp {tambak}<span class="kcard-unit">/kg</span></div>
          <div class="kcard-ekspor">Ekspor: USD {ekspor}/kg</div>
          <div class="kcard-source">{p.sumber or ''}</div>
        </div>"""

        # Regional price rows
        rp_rows = ""
        seen_rp = set()
        for r in rp_all:
            key = (r.wilayah, r.komoditas[:30], r.size)
            if key in seen_rp:
                continue
            seen_rp.add(key)
            lo = int(r.harga_tambak_low or 0)
            hi = int(r.harga_tambak_high or 0)
            short = r.komoditas.split("(")[0].strip()[:25]
            rp_rows += f"""
          <tr>
            <td>{r.wilayah}</td>
            <td>{short}</td>
            <td>{r.size}</td>
            <td><strong>Rp {lo:,} – {hi:,}</strong>/kg</td>
          </tr>"""

        # Alert rows
        alert_rows = ""
        for a in alerts:
            cls = "badge-merah" if a.alert_type == "MERAH" else "badge-kuning" if a.alert_type == "KUNING" else "badge-biru"
            alert_rows += f"""
          <tr>
            <td>{a.tanggal}</td>
            <td><span class="{cls}">{a.alert_type}</span></td>
            <td>{a.komoditas}</td>
            <td>{a.pesan or '—'}</td>
          </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Market Watch AJN — {tgl}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#eef2f7;color:#1e293b;font-size:14px;min-height:100vh}}

/* ── Header ── */
.hdr{{background:linear-gradient(135deg,#1B3A6B 0%,#0d2244 100%);color:#fff;padding:0}}
.hdr-inner{{max-width:1200px;margin:0 auto;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}}
.hdr-brand{{display:flex;flex-direction:column;gap:2px}}
.hdr-logo{{font-size:1.4rem;font-weight:800;letter-spacing:.4px;color:#C9A84C}}
.hdr-sub{{font-size:.7rem;color:rgba(203,213,225,.8)}}
.hdr-right{{display:flex;align-items:center;gap:12px}}
.hdr-date{{font-size:.75rem;background:rgba(201,168,76,.15);border:1px solid rgba(201,168,76,.35);color:#C9A84C;padding:6px 14px;border-radius:20px;white-space:nowrap}}
.btn-login{{display:inline-flex;align-items:center;gap:6px;padding:7px 16px;background:#C9A84C;color:#0d2244;border-radius:8px;text-decoration:none;font-size:.78rem;font-weight:700;transition:all .15s}}
.btn-login:hover{{background:#e2c16f;transform:translateY(-1px)}}

/* ── Nav ── */
.nav-bar{{background:#fff;border-bottom:1px solid #e2e8f0}}
.nav-bar-inner{{max-width:1200px;margin:0 auto;padding:0 24px;display:flex;gap:0}}
.nav-link{{color:#64748b;text-decoration:none;font-size:.78rem;font-weight:600;padding:10px 20px;border-bottom:3px solid transparent;transition:all .15s}}
.nav-link:hover{{color:#1B3A6B;background:#f8fafc}}
.nav-link.active{{color:#1B3A6B;border-bottom-color:#C9A84C}}

.wrap{{max-width:1200px;margin:0 auto;padding:24px 16px}}

/* ── Summary ── */
.summary-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:24px}}
.sum-card{{background:#fff;border-radius:12px;padding:18px 20px;box-shadow:0 1px 4px rgba(0,0,0,.06);border-left:4px solid #1B3A6B;display:flex;flex-direction:column;gap:4px;transition:transform .15s,box-shadow .15s}}
.sum-card:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.1)}}
.sum-card.gold{{border-left-color:#C9A84C}}
.sum-card.green{{border-left-color:#10B981}}
.sum-card.blue{{border-left-color:#3B82F6}}
.sum-num{{font-size:2rem;font-weight:800;color:#1B3A6B;line-height:1}}
.sum-card.gold .sum-num{{color:#B8860B}}
.sum-card.green .sum-num{{color:#065F46}}
.sum-card.blue .sum-num{{color:#1E40AF}}
.sum-lbl{{font-size:.75rem;color:#64748b;font-weight:500}}

/* ── Sections ── */
.sec-title{{font-size:.9rem;font-weight:700;color:#1B3A6B;margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid #C9A84C;display:flex;align-items:center;gap:8px}}
.sec-title::before{{content:"";width:8px;height:8px;border-radius:50%;background:#C9A84C;flex-shrink:0}}

.filter-bar{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}}
.filter-btn{{padding:7px 18px;border-radius:20px;border:2px solid #cbd5e1;background:#fff;color:#475569;font-size:.78rem;font-weight:600;cursor:pointer;transition:all .15s}}
.filter-btn:hover{{border-color:#1B3A6B;color:#1B3A6B}}
.filter-btn.active{{background:#1B3A6B;color:#fff;border-color:#1B3A6B}}

/* ── Commodity Cards ── */
.komod-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:24px}}
@media(max-width:900px){{.komod-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:580px){{.komod-grid{{grid-template-columns:1fr}}}}

.komod-card{{background:#fff;border-radius:12px;padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,.06);border-top:3px solid #1B3A6B;display:flex;flex-direction:column;gap:6px;transition:transform .15s,box-shadow .15s}}
.komod-card:hover{{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.12)}}
.komod-card[data-cat="t"]{{border-top-color:#145A30}}
.komod-card.hidden{{display:none}}
.kcard-top{{display:flex;justify-content:space-between;align-items:center}}
.cat-badge{{font-size:.62rem;font-weight:700;padding:3px 10px;border-radius:10px}}
.cat-b{{background:#DBEAFE;color:#1E40AF}}
.cat-t{{background:#D1FAE5;color:#065F46}}
.kcard-name{{font-size:.82rem;font-weight:700;color:#1B3A6B;line-height:1.3}}
.kcard-size{{font-size:.7rem;color:#94a3b8}}
.kcard-harga{{font-size:1.2rem;font-weight:800;color:#1e293b;margin-top:4px}}
.kcard-unit{{font-size:.65rem;font-weight:400;color:#94a3b8}}
.kcard-ekspor{{font-size:.7rem;color:#64748b}}
.kcard-source{{font-size:.6rem;color:#cbd5e1;margin-top:auto;padding-top:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}

/* ── Tables ── */
.card{{background:#fff;border-radius:12px;box-shadow:0 1px 4px rgba(0,0,0,.06);padding:20px;margin-bottom:20px;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:.78rem}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #e2e8f0}}
th{{background:#f8fafc;color:#475569;font-weight:700;font-size:.7rem;text-transform:uppercase;letter-spacing:.5px}}
tr:hover td{{background:#f8fafc}}

.badge-merah{{background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:8px;font-size:.65rem;font-weight:700}}
.badge-kuning{{background:#FEF3C7;color:#92400E;padding:2px 8px;border-radius:8px;font-size:.65rem;font-weight:700}}
.badge-biru{{background:#DBEAFE;color:#1E40AF;padding:2px 8px;border-radius:8px;font-size:.65rem;font-weight:700}}

.footer{{text-align:center;padding:20px;color:#94a3b8;font-size:.7rem;border-top:1px solid #e2e8f0;margin-top:20px}}
.empty{{padding:24px;text-align:center;color:#94a3b8}}
</style>
</head>
<body>

<div class="hdr">
  <div class="hdr-inner">
    <div class="hdr-brand">
      <div class="hdr-logo">Market Watch AJN</div>
      <div class="hdr-sub">PT Agrinas Jaladri Nusantara (Persero) — Pemantauan Harga Komoditas Perikanan Strategis</div>
    </div>
    <div class="hdr-right">
      <div class="hdr-date">{tgl}</div>
      <a href="/login" class="btn-login">&#128274; Login</a>
    </div>
  </div>
</div>

<div class="nav-bar">
  <div class="nav-bar-inner">
    <a class="nav-link active" href="/">&#128202; Harga Komoditas</a>
    <a class="nav-link" href="/knmp">&#128506;&#65039; Peta KNMP</a>
  </div>
</div>

<div class="wrap">

  <div class="summary-row">
    <div class="sum-card">
      <div class="sum-num">{len(prices)}</div>
      <div class="sum-lbl">Komoditas Dipantau</div>
    </div>
    <div class="sum-card gold">
      <div class="sum-num">{len(alerts)}</div>
      <div class="sum-lbl">Alert Aktif</div>
    </div>
    <div class="sum-card blue">
      <div class="sum-num">{total_lokasi or 0}</div>
      <div class="sum-lbl">Lokasi KNMP</div>
    </div>
    <div class="sum-card green">
      <div class="sum-num">{progress_nasional:.1f}%</div>
      <div class="sum-lbl">Progress Nasional</div>
    </div>
  </div>

  <div class="sec-title">Harga Tambak — {now.strftime('%d %B %Y')}</div>
  <div class="filter-bar">
    <button class="filter-btn active" data-filter="all">Semua</button>
    <button class="filter-btn" data-filter="b">Budidaya</button>
    <button class="filter-btn" data-filter="t">Tangkap</button>
  </div>
  <div class="komod-grid" id="komodGrid">
    {cards_html or '<div class="empty">Belum ada data harga. Jalankan scrape_commodity.py.</div>'}
  </div>

  <div class="sec-title">Harga per Wilayah ({wilayah_count} Wilayah)</div>
  <div class="card">
    {f'''<table>
      <thead><tr><th>Wilayah</th><th>Komoditas</th><th>Size</th><th>Harga Tambak</th></tr></thead>
      <tbody>{rp_rows}</tbody>
    </table>''' if rp_rows else '<div class="empty">Belum ada data harga per wilayah.</div>'}
  </div>

  <div class="sec-title">Alert & Pergerakan Harga</div>
  <div class="card">
    {f'''<table>
      <thead><tr><th>Tanggal</th><th>Level</th><th>Komoditas</th><th>Pesan</th></tr></thead>
      <tbody>{alert_rows}</tbody>
    </table>''' if alert_rows else '<div class="empty">Tidak ada alert saat ini.</div>'}
  </div>

</div>

<div class="footer">
  Market Watch AJN &copy; {now.year} — PT Agrinas Jaladri Nusantara (Persero)
</div>

<script>
(function(){{
  var btns=document.querySelectorAll('.filter-btn');
  btns.forEach(function(b){{
    b.addEventListener('click',function(){{
      var f=this.getAttribute('data-filter');
      btns.forEach(function(x){{x.classList.remove('active')}});
      this.classList.add('active');
      document.querySelectorAll('#komodGrid .komod-card').forEach(function(c){{
        c.classList.toggle('hidden', f!=='all' && c.getAttribute('data-cat')!==f);
      }});
    }});
  }});
}})();
</script>
</body>
</html>"""

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)

        kb = len(html.encode("utf-8")) // 1024
        print(f"\n✓ index.html ({kb} KB)")
        print(f"  {len(prices)} komoditas | {len(alerts)} alerts | {total_lokasi} lokasi KNMP")
        print("=" * 55)


if __name__ == "__main__":
    generate()
