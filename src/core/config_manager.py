"""
- Stores config at config.json
- Makes defaults if file is missing or corrupted
"""

from __future__ import annotations
from pathlib import Path
import json
import os
import tempfile
from typing import Dict, Any 

# Default config if no file exists or file is invalid
def _get_cfg_path() -> Path:
    app_dir = Path(os.getenv("WORKMINE_HOME", Path.home() / ".workmine")).expanduser()
    return app_dir / "config.json"

DEFAULT_CFG: Dict[str, Any] = {
"consent_granted": False, # must be true before reading any zip
"external_allowed": False, # permission to use external APIs/services (to read zip)
"external_last_notice_version": 0 # Re-prompts when any privacy notice changes
}

# File I/O helpers


#Writes text to 'path' atomically:
#Writes to a temp file in same directory
#replaces the target file

def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, encoding="utf-8") as tmp:
        tmp.write(text)
        temp_path = Path(tmp.name)
    temp_path.replace(path) 


def _read_json_or_default(path: Path) -> Dict[str, Any]:
        try:
            if path.exists():
                raw = path.read_text(encoding="utf-8")
                data = json.loads(raw)
                if isinstance(data, dict):
                    merged = DEFAULT_CFG.copy()
                    merged.update(data)
                    return merged
        except Exception: #Fallback to defaults if any error occurs
             pass
        return DEFAULT_CFG.copy()


# Public API to call

# Returns current config directory, Safe even if file is missing/corrupted
def read_cfg() -> Dict[str, Any]:
    return _read_json_or_default(_get_cfg_path())


# Persist the config dictionary to disk (atomically)
def write_cfg(cfg: Dict[str, Any]) -> None:
    out = DEFAULT_CFG.copy()
    out.update(cfg or {})
    _atomic_write_text(_get_cfg_path(), json.dumps(out, indent=2))

#Set consent granted flag and persist to disk
def set_consent(granted: bool) -> None:
    cfg = read_cfg()
    cfg["consent_granted"] = bool(granted)
    write_cfg(cfg)


#Set external allowed flag and persist to disk
def set_external_allowed(allowed: bool) -> None:
     cfg = read_cfg()
     cfg["external_allowed"] = bool(allowed)
     write_cfg(cfg) 

# Return True if external processing has been permitted by user
def has_consent() -> bool:
    cfg = read_cfg()
    return bool(cfg.get("consent_granted", False))

# Enforces the consent before any data accessed. Raises SystemExit if not granted.
def require_consent() -> None:
    if not has_consent():
        print("User consent not granted. Exiting.")
        raise SystemExit("User consent required.")
    
def has_external_allowed() -> bool:       # CHANGE: new function
    return bool(read_cfg().get("external_allowed", False))

    # Asks user to approve of extenral service use (LLM/API) if not already allowed
def require_external_consent(notice_version: int = 1):  
    cfg = read_cfg()
    if cfg.get("external_allowed") and cfg.get("external_last_notice_version", 0) >= notice_version:
        return

    print("External Service Privacy Notice")
    print(" - Only selected content you choose may be sent")
    print(" - Risks: Provider logging & cross-region transfer may occur")
    print(" - Alternative: Keep analysis local (no external services or code scan)\n")

    answer = input("Allow external processes for this run? (y/N): ").strip().lower()
    allowed = (answer == "y")
    cfg["external_allowed"] = allowed
    if allowed:
        cfg["external_last_notice_version"] = int(notice_version)
    write_cfg(cfg)
