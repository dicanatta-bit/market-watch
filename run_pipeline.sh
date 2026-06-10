#!/bin/bash
cd /var/www/market-watch

echo "=== Market Watch v3 Pipeline ==="

# Activate backend venv
cd backend && source venv/bin/activate

# Step 1: Scrape eKNMP KKP
echo "=== Step 1: Scrape eKNMP ==="
python -m app.scrapers.eknmp

# Step 2: Scrape commodity prices
echo "=== Step 2: Scrape Commodity ==="
python -m app.scrapers.commodity

cd ..

# Step 3: Build React frontend
echo "=== Step 3: Build Frontend ==="
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
