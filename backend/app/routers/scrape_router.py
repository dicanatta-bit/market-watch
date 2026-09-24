"""Authenticated, lock-protected manual trigger for the normal cron pipeline."""
import subprocess
import os
from fastapi import APIRouter, Depends, HTTPException
from ..auth import get_superadmin

router = APIRouter(tags=["scrape"])

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PIPELINE_PATH = os.path.join(ROOT_DIR, "run_pipeline.sh")


@router.post("/scrape/trigger")
def trigger_scrape(_=Depends(get_superadmin)):
    """Run exactly the same locked pipeline that cron runs."""
    try:
        environment = os.environ.copy()
        environment["PIPELINE_TRIGGER"] = "manual"
        result = subprocess.run(
            ["/usr/bin/bash", PIPELINE_PATH], cwd=ROOT_DIR,
            capture_output=True, text=True, timeout=1800, env=environment,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Pipeline melebihi batas 30 menit")
    log = (result.stdout + "\n" + result.stderr).strip()[-24000:]
    if result.returncode:
        status = 409 if "pipeline lain masih berjalan" in log else 502
        raise HTTPException(status_code=status, detail={"message": "Sinkronisasi gagal", "log": log})
    return {"success": True, "message": "Sinkronisasi selesai", "log": log}
