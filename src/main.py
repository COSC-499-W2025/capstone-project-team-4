import sys
from pathlib import Path
from typing import Optional

import typer

from src.core import config_manager
from src.core.database import init_db
from src.core.config_manager import save_config, load_config
from src.core.run import validate_and_parse
from src.core.metadata_parser import save_metadata_json

app = typer.Typer(help="Mining Digital Work Artifacts CLI")

def check_virtual_env():
    return sys.prefix != sys.base_prefix


@app.command()
def consent(
    grant: bool = typer.Option(False, "--grant", help="Grant consent to process files."),
    revoke: bool = typer.Option(False, "--revoke", help="Revoke consent."),
    external: Optional[bool] = typer.Option(
        None, "--external/--no-external", help="Allow (or disallow) use of external APIs/services."
    ),
) -> None:
    """Manage user consent and external processing permission."""
    if grant and revoke:
        print("Error: choose either --grant OR --revoke.")
        raise typer.Exit(code=2)

    if grant:
        config_manager.set_consent(True)
        print("Consent granted.")
    if revoke:
        config_manager.set_consent(False)
        print("Consent revoked.")

    if external is not None:
        config_manager.set_external_allowed(external)
        print(f"External services allowed = {external}")

    print("\nCurrent configuration:")
    print(config_manager.read_cfg())


@app.command()
def status() -> None:
    """Print current consent and external-usage settings."""
    print(config_manager.read_cfg())


@app.command()
def external_permission(service: str = "API"):
    """Ask for and log permission to use an external service."""
    config_manager.request_external_service_permission(service)


@app.command()
def extract(
    zip_path: Path = typer.Argument(..., exists=True, readable=True, help="Path to a .zip file."),
    out_dir: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Directory to write outputs (default: src/outputs)"
    ),
    external: Optional[bool] = typer.Option(
        None, "--external/--no-external", help="Allow (or disallow) external APIs/services for this run."
    ),
) -> None:
    """Validate ZIP → extract to temp → parse metadata → save metadata.json."""
    config_manager.require_consent()

    if external is not None:
        config_manager.set_external_allowed(external)
        typer.echo(f"External services allowed = {external}")

    # Validate + extract + parse (implemented in src/core/run.py)
    res = validate_and_parse(zip_path)

    if not res["is_valid"]:
        typer.secho(f"❌ ZIP invalid: {zip_path.name}", fg=typer.colors.RED)
        for err in res["validation_errors"]:
            typer.echo(f"  - {err}")
        raise typer.Exit(code=2)

    df = res["metadata"]

    if out_dir is None:
        out_dir = Path("src/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = save_metadata_json(df, output_filename="metadata.json")
    typer.secho(f"✅ Metadata saved: {json_path}", fg=typer.colors.GREEN)


if __name__ == "__main__":
    print("Running in virtual env:", check_virtual_env())

    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization skipped or failed: {e}")

    try:
        config_data = {"theme": "dark", "notifications": True}
        save_config(config_data)
        print("Loaded:", load_config())
    except Exception as e:
        print(f"Config save/load skipped or failed: {e}")

    app()
