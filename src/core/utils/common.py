"""
Combined utilities for common functionality.
"""
import json
import typer
from datetime import datetime
from pathlib import Path

# Logging functionality
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


# Pretty printing functionality
def readable_size(num_bytes):
    """Convert bytes to MB/GB for readability."""
    try:
        if num_bytes >= 1_000_000_000:
            return f"{num_bytes / 1_000_000_000:.2f} GB"
        elif num_bytes >= 1_000_000:
            return f"{num_bytes / 1_000_000:.2f} MB"
        elif num_bytes >= 1_000:
            return f"{num_bytes / 1_000:.2f} KB"
        return f"{num_bytes} bytes"
    except:
        return "?"


def pretty_print_json(file_name: str, data: dict, raw: bool = False):
    """
    Pretty prints known JSON files in a human-friendly format.
    Falls back to raw JSON dump when unknown or when raw=True.
    """
    if raw:
        typer.echo(json.dumps(data, indent=2))
        return

    # Resume item formatting
    if file_name == "resume_item.json":
        typer.secho("\n📘 Resume Item\n", fg=typer.colors.BLUE, bold=True)
        title = data.get("title", "")
        highlights = data.get("highlights", [])
        typer.secho("Title:", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"  {title}\n")
        typer.secho("Highlights:", fg=typer.colors.GREEN, bold=True)
        for h in highlights:
            typer.echo(f"  {h}")
        typer.echo("")
        return

    # Skill extraction formatting  
    if file_name == "skill_extract.json":
        typer.secho("\n🧠 Resume Skills\n", fg=typer.colors.MAGENTA, bold=True)
        skills = data.get("skills", [])
        for skill in skills[:10]:  # Show top 10
            typer.echo(f"  • {skill}")
        if len(skills) > 10:
            typer.echo(f"  ... and {len(skills) - 10} more skills")
        typer.echo("")
        return

    # Default: raw JSON
    typer.echo(json.dumps(data, indent=2))