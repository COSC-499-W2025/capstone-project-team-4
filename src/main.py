import sys
from pathlib import Path
from typing import Optional

import typer
import zipfile
from tempfile import TemporaryDirectory

from src.core import config_manager
from src.core.database import init_db
from src.core.config_manager import save_config, load_config
from src.core.file_validator import validate_zip
from src.core.run import validate_and_parse
from src.core.metadata_parser import parse_metadata, save_metadata_json

app = typer.Typer(help="Mining Digital Work Artifacts CLI")


# It should say True

# If you want it to run put in the command: python3 -m src.main {command name}
def check_virtual_env():
    return sys.prefix != sys.base_prefix


@app.command()
def consent(
    grant: bool = typer.Option(False, "--grant", help="Grant consent to process files."),
    revoke: bool = typer.Option(False, "--revoke", help="Revoke consent."),
     external: Optional[bool] = typer.Option(
    None,
    "--external/--no-external",
    help="Allow (or disallow) use of external APIs/services.",
    ),
) -> None:
    """Manage user consent and external processing permission."""
    # Conflicting flags
    if grant and revoke:
        print("Error: choose either --grant OR --revoke.")
        raise typer.Exit(code=2)

    # Update consent
    if grant:
        config_manager.set_consent(True)
        print("Consent granted.")
    if revoke:
        config_manager.set_consent(False)
        print("Consent revoked.")

    
    if external is not None:
        config_manager.set_external_allowed(external)
        print(f"External services allowed = {external}")

    # Show current configuration
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
    path: Path = typer.Argument(..., help="Path to a ZIP file, a directory, or a single file."),
    out_dir: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Directory to write outputs (default: ./outputs)"
    ),
    external: Optional[bool] = typer.Option(
        None, "--external/--no-external", help="Allow (or disallow) external APIs/services for this run."
    ),
) -> None:
    """
    Process a path that can be:
      - a .zip (validate → extract to temp → parse)
      - a directory (parse all files recursively)
      - a single file (parse just that file)
    Saves metadata.json (and you can add CSV if desired).
    """
    from src.core.run import validate_and_parse
    from src.core.metadata_parser import parse_metadata, save_metadata_json
    import pandas as po

    config_manager.require_consent()

    if external is not None:
        config_manager.set_external_allowed(external)
        typer.echo(f"External services allowed = {external}")

    # Normalize output directory
    out_dir = (out_dir or Path.cwd() / "outputs").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    path = path.resolve()
    if not path.exists():
        typer.secho(f"Path not found: {path}", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    # CASE 1: .zip file → use existing pipeline
    if path.is_file() and path.suffix.lower() == ".zip":
        res = validate_and_parse(path)
        if not res["is_valid"]:
            typer.secho(f"❌ Invalid ZIP: {path.name}", fg=typer.colors.RED)
            for err in res["validation_errors"]:
                typer.echo(f"  - {err}")
            raise typer.Exit(code=2)
        df = res["metadata"]
        json_path = save_metadata_json(df, output_filename=f"{path.stem}_metadata.json")
        typer.secho(f"✅ Metadata saved: {json_path}", fg=typer.colors.GREEN)
        return

    # CASE 2: directory → parse recursively
    if path.is_dir():
        df = parse_metadata(str(path))
        json_path = save_metadata_json(df, output_filename=f"{path.name}_metadata.json")
        typer.secho(f"✅ Directory metadata saved: {json_path}", fg=typer.colors.GREEN)
        return

    # CASE 3: single non-zip file → build a one-row DataFrame
    if path.is_file():
        try:
            import magic
            st = path.stat()
            try:
                mime = magic.from_file(str(path), mime=True)
            except Exception:
                mime = "unknown/unknown"

            df = po.DataFrame([{
                "filename": path.name,
                "path": str(path),
                "file_type": mime,
                "file_size": st.st_size,
                "created_timestamp": st.st_ctime,
                "last_modified": st.st_mtime,
            }])
            json_path = save_metadata_json(df, output_filename=f"{path.stem}_metadata.json")
            typer.secho(f"✅ File metadata saved: {json_path}", fg=typer.colors.GREEN)
            return
        except Exception as e:
            typer.secho(f"Failed to parse file: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    typer.secho("Unsupported path type.", fg=typer.colors.RED)
    raise typer.Exit(code=2)

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



