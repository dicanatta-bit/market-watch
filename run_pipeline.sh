#!/bin/bash
cd /var/www/market-watch
source venv/bin/activate

echo "========================================="
echo "Market Watch AJN v2 — Weekly Pipeline"
echo "========================================="

# Step 1: Scrape eKNMP KKP (live progress + auto-create accounts)
echo ""
echo "=== Step 1: Scrape eKNMP KKP ==="
python scrapers/scrape_eknmp.py

# Step 2: Scrape commodity prices
echo ""
echo "=== Step 2: Scrape Commodity Prices ==="
python scrapers/scrape_commodity.py

# Step 3: Scrape TPI SIHI (if available)
echo ""
echo "=== Step 3: Scrape SIHI TPI ==="
python scrapers/scrape_sihi.py || echo "  SIHI scraper not ready, skip."

# Step 4: Generate static HTML
echo ""
echo "=== Step 4: Generate Static HTML ==="
python generators/buat_knmp_map.py || echo "  Map generator not ready, skip."
python generators/buat_infografis.py || echo "  Infografis generator not ready, skip."

# Commit & push
echo ""
echo "=== Commit & Push ==="
git config user.email "akhdanx@gmail.com"
git config user.name "Market Watch VPS"
git add -A
git diff --cached --quiet || git commit -m "auto: weekly update $(date +%Y-%m-%d)"
git pull --rebase origin main || true
git push origin main || true

echo ""
echo "=== Selesai ==="
