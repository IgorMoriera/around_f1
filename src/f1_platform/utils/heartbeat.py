"""Write a heartbeat to ensure weekly commits and keep GitHub Actions alive."""
import json
from datetime import datetime, timezone
from pathlib import Path


def write_heartbeat(pending: list[dict], ingested: list[dict]) -> None:
    path = Path("data/state/last_run.json")
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "pending_found": len(pending),
        "sessions_ingested": [
            f"{s['season']}/{s['event']}/{s['session']}" for s in ingested
        ],
    }

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
