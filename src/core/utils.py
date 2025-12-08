import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent / "../data/consent_log.json"

def log_event(service_name: str, status: str):
    """Log user consent decisions with timestamps."""
    log_entry = {
        "service": service_name,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

    logs = []
    if LOG_FILE.exists():
        try:
            logs = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            logs = []

    logs.append(log_entry)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(logs, indent=2))
