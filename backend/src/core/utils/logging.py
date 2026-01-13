"""
Logging utilities for the core analysis modules.

This module provides event logging functionality that was previously
in utils.py.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Default log file location
LOG_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "consent_log.json"

# Standard Python logger
logger = logging.getLogger(__name__)


def log_event(
    service_name: str,
    status: str,
    log_file: Optional[Path] = None,
) -> None:
    """
    Log user consent decisions and other events with timestamps.

    Args:
        service_name: Name of the service being logged
        status: Status of the event (e.g., "granted", "denied")
        log_file: Optional custom log file path (default: LOG_FILE)
    """
    target_file = log_file or LOG_FILE

    log_entry = {
        "service": service_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }

    logs = []
    if target_file.exists():
        try:
            logs = json.loads(target_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not read existing log file: %s", e)
            logs = []

    logs.append(log_entry)

    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(json.dumps(logs, indent=2), encoding="utf-8")
    except OSError as e:
        logger.error("Could not write to log file: %s", e)


def get_log_entries(log_file: Optional[Path] = None) -> list:
    """
    Read all log entries from the log file.

    Args:
        log_file: Optional custom log file path (default: LOG_FILE)

    Returns:
        List of log entry dictionaries
    """
    target_file = log_file or LOG_FILE

    if not target_file.exists():
        return []

    try:
        return json.loads(target_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read log file: %s", e)
        return []
