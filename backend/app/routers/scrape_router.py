"""Scrape router — trigger manual scrape via Admin"""
import subprocess, sys, os
from fastapi import APIRouter, Depends
from ..auth import get_superadmin

router = APIRouter(tags=["scrape"])

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_script(name):
    """Jalankan 1 scraper script, return stdout."""
    script = os.path.join(BACKEND_DIR, "app", "scrapers", name)
    result = subprocess.run([sys.executable, script], capture_output=True, text=True, timeout=300)
    out = result.stdout.strip()
    err = result.stderr.strip()
    return f"=== {name} ===\n{out}\n{err}\nExit: {result.returncode}"


@router.post("/scrape/trigger")
def trigger_scrape(_=Depends(get_superadmin)):
    """Jalankan semua scraper sequentially (eKNMP → commodity → SIHA → alert)."""
    logs = []

    logs.append(run_script("eknmp.py"))
    logs.append(run_script("commodity.py"))
    logs.append(run_script("scrape_sihi.py"))
    logs.append(run_script("alert_engine.py"))

    return {"success": True, "message": "Scrape complete", "logs": logs}
