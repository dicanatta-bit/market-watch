"""One audited execution path for cron and the internal admin console."""
import argparse
import os
import subprocess
import sys
from datetime import datetime

from app.database import SessionLocal
from app.models import PipelineRun

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STEPS = ("eknmp", "fishinfo_history", "alert_engine")
MAX_LOG_LENGTH = 24000


def run(trigger="cron"):
    db = SessionLocal()
    record = PipelineRun(trigger=trigger, status="running")
    db.add(record)
    db.commit()
    db.refresh(record)
    logs = []
    try:
        for name in STEPS:
            result = subprocess.run(
                [sys.executable, "-m", f"app.scrapers.{name}"], cwd=BACKEND_DIR,
                capture_output=True, text=True, timeout=1200,
            )
            output = (result.stdout + "\n" + result.stderr).strip()
            logs.append(f"=== {name} (exit {result.returncode}) ===\n{output}")
            if result.returncode:
                raise RuntimeError(f"{name} gagal (exit {result.returncode})")
        record.status = "success"
    except Exception as exc:
        record.status = "failed"
        logs.append(f"=== pipeline ===\n{exc}")
        raise
    finally:
        record.finished_at = datetime.utcnow()
        record.log = "\n\n".join(logs)[-MAX_LOG_LENGTH:]
        db.commit()
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", choices=("cron", "manual"), default="cron")
    args = parser.parse_args()
    run(args.trigger)


if __name__ == "__main__":
    main()
