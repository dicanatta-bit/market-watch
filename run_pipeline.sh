#!/bin/bash
cd /var/www/market-watch

echo "=== Market Watch — Weekly Pipeline ==="

cd backend && source venv/bin/activate

# Step 1: Scrape eKNMP
echo "=== Step 1: Scrape eKNMP ==="
python -m app.scrapers.eknmp

# Step 2: Scrape commodity prices
echo "=== Step 2: Scrape Commodity ==="
python -m app.scrapers.commodity

# Step 3: Scrape SIHI TPI
echo "=== Step 3: Scrape SIHI ==="
python -m app.scrapers.scrape_sihi

# Step 4: Alert engine
echo "=== Step 4: Alert Engine ==="
python -m app.scrapers.alert_engine

cd ..

# Step 5: Generate static HTML
echo "=== Step 5: Generate HTML ==="
python generators/buat_infografis.py
python generators/buat_knmp_map.py

# Step 6: Build React frontend
echo "=== Step 6: Build React ==="
npm run build

# Commit + push
echo "=== Git Push ==="
git config user.email "akhdanx@gmail.com"
git config user.name "Market Watch VPS"
git add -A
git diff --cached --quiet || git commit -m "auto: weekly update $(date +%Y-%m-%d)"
git pull --rebase origin main || true
git push origin main || true

echo "=== Done ==="
