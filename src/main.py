import sys
import os
from pathlib import Path
from typing import Optional
import json 

import typer
import zipfile
from tempfile import TemporaryDirectory

from src.core import config_manager
from src.core.database import init_db
from src.core.config_manager import save_config, load_config
# from src.core.file_validator import validate_zip
from src.core.run import validate_and_parse
from src.core.metadata_parser import parse_metadata, save_metadata_json
from src.core.language_analyzer import ProjectAnalyzer, StatsFormatter
from src.core.project_analyzer import analyze_project, project_analysis_to_dict


app = typer.Typer(help="Mining Digital Work Artifacts CLI")

# This is for testing if your local environment is running the "virtual environment"
# It should say True

# If you want it to run put in the command: python -m src.main {command name}
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
def info() -> None:
    """Show information about the application and available commands."""
    typer.echo("📊 Mining Digital Work Artifacts CLI")
    typer.echo("=" * 40)
    typer.echo("Available commands:")
    typer.echo("  • consent           - Manage user consent")
    typer.echo("  • status            - Show current settings")
    typer.echo("  • extract-metadata  - Extract and analyze file metadata")
    typer.echo("  • analyze-language  - Language analysis and line counting")
    typer.echo("  • analyze-code      - Code complexity analysis")
    typer.echo("  • info              - Show this information")
    typer.echo("\nUse --help with any command for detailed options.")

@app.command()
def external_permission(service: str = "API"):
    """Ask for and log permission to use an external service."""
    config_manager.request_external_service_permission(service)

@app.command("extract-metadata")
def extract_metadata(
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
      - a .zip (validate -> extract to temp -> parse)
      - a directory (parse all files recursively)
      - a single file (parse just that file)
    Saves metadata.json in the output directory.
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

    # CASE 1: .zip file -> use existing framework.
    if path.is_file() and path.suffix.lower() == ".zip":
        res = validate_and_parse(path)
        if not res["is_valid"]:
            typer.secho(f"Invalid ZIP: {path.name}", fg=typer.colors.RED)
            for err in res["validation_errors"]:
                typer.echo(f"  - {err}")
            raise typer.Exit(code=2)
        df = res["metadata"]
        json_path = save_metadata_json(df, output_filename=f"{path.stem}_metadata.json")
        typer.secho(f"Metadata saved: {json_path}", fg=typer.colors.GREEN)
        return

    # CASE 2: directory -> parse recursively and returns each file inside of a folder 
    if path.is_dir():
        df, project_root = parse_metadata(str(path))
        json_path = save_metadata_json(df, f"{path.name}_metadata.json", project_root)
        typer.secho(f"Directory metadata saved: {json_path}", fg=typer.colors.GREEN)
        return

    # CASE 3: single non-zip file -> build a one-row DataFrame
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
                "created_timestamp": os.path.getctime(path),
                "last_modified": os.path.getmtime(path),
            }])
            json_path = save_metadata_json(df, output_filename=f"{path.stem}_metadata.json")
            typer.secho(f"File metadata saved: {json_path}", fg=typer.colors.GREEN)
            return
        except Exception as e:
            typer.secho(f"Failed to parse file: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

    typer.secho("Unsupported path type.", fg=typer.colors.RED)
    raise typer.Exit(code=2)

@app.command("analyze-language")
def analyze_language(
    path: Path = typer.Argument(..., help="Path to directory or ZIP file to analyze (required)"),
    unknown_only: bool = typer.Option(False, "--unknown", help="Show only unknown file types")
) -> None:
    """Analyze programming languages and lines of code in a project directory or ZIP file."""
    
    path = path.resolve()
    if not path.exists():
        typer.secho(f"Path not found: {path}", fg=typer.colors.RED)
        raise typer.Exit(code=2)
    
    try:
        # Create analyzer and formatter
        analyzer = ProjectAnalyzer()
        formatter = StatsFormatter()
        
        # Handle ZIP file by extracting to temporary directory
        if path.is_file() and path.suffix.lower() == ".zip":
            typer.secho(f"Extracting ZIP file: {path.name}", fg=typer.colors.BLUE)
            
            with TemporaryDirectory() as temp_dir:
                try:
                    with zipfile.ZipFile(path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Analyze the extracted content
                    if unknown_only:
                        formatter.show_unknown_files(analyzer, temp_dir)
                    else:
                        formatter.print_detailed_language_stats(analyzer, temp_dir, show_filtered=False)
                        # Use original ZIP filename for output
                        output_filename = f"{path.stem}_language_analysis.json"
                        json_file_path = formatter.save_analysis_to_json(analyzer, temp_dir, output_file=output_filename, include_filtered=False)
                        typer.secho(f"Analysis saved to: {json_file_path}", fg=typer.colors.GREEN)
                        
                except zipfile.BadZipFile:
                    typer.secho(f"Invalid ZIP file: {path}", fg=typer.colors.RED)
                    raise typer.Exit(code=2)
                    
        elif path.is_dir():
            # Handle directory as before
            if unknown_only:
                formatter.show_unknown_files(analyzer, str(path))
            else:
                formatter.print_detailed_language_stats(analyzer, str(path), show_filtered=False)
                json_file_path = formatter.save_analysis_to_json(analyzer, str(path), include_filtered=False)
                typer.secho(f"Analysis saved to: {json_file_path}", fg=typer.colors.GREEN)
        else:
            typer.secho("Language analysis requires a directory or ZIP file.", fg=typer.colors.RED)
            raise typer.Exit(code=2)
    
    except Exception as e:
        typer.secho(f"Analysis failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command("analyze-code")
def analyze_code(path: str, out: Optional[Path] = typer.Option(None, "--out", "-o")):
    """Analyze code complexity and generate metrics for Python files."""
    root = Path(path)
    result = analyze_project(root)
    data = project_analysis_to_dict(result)

    if out is None:
        out_dir = Path.cwd() / "outputs"
        out_dir.mkdir(exist_ok=True)
        out = out_dir / "code_complexity.json"

    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(f"Saved JSON -> {out}")



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





