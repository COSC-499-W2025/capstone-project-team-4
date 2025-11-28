import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import shutil

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
from src.core.project_analyzer import (
    analyze_contributors,
    analyze_project,
    calculate_project_stats,
    project_analysis_to_dict,
)


app = typer.Typer(help="Mining Digital Work Artifacts CLI - Extract metadata and professional skills from code repositories")

# This is for testing if your local environment is running the "virtual environment"
# It should say True


# If you want it to run put in the command: python -m src.main {command name}
def check_virtual_env():
    return sys.prefix != sys.base_prefix


@app.command()
def consent(
    grant: bool = typer.Option(
        False, "--grant", help="Grant consent to process files."
    ),
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


@app.command("analyze-project")
def analyze_project_cli(
    path: Path = typer.Argument(..., help="Path to a project directory or ZIP file."),
    include_files: bool = typer.Option(
        False,
        "--include-files/--no-include-files",
        help="Include full file list from metadata in final report",
    ),
    out: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Output directory (default: ./outputs)"
    ),
):
    """
    Full project pipeline:
      1. Extract metadata
      2. Analyze Git contributors
      3. Run code complexity (Tree-sitter)
      4. Generate a unified final JSON report

    Produces ONE unified report file inside outputs/.
    """

    config_manager.require_consent()

    # Normalize output directory
    out_dir = (out or Path.cwd() / "outputs").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    path = path.resolve()
    if not path.exists():
        typer.secho(f"❌ Path not found: {path}", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    # Project Name (gets the final... name from a path? Like the last thing at the end of chicken/main.txt for example)
    project_name = path.stem

    # 1️. If ZIP -> extract into temp folder

    if path.is_file() and path.suffix.lower() == ".zip":
        typer.echo("📦 Extracting ZIP file...")

        with TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            extracted_root = Path(temp_dir)
            df, project_root = parse_metadata(str(extracted_root))

            # Save metadata
            metadata_path = save_metadata_json(
                df, f"{path.stem}_metadata.json", project_root
            )
            typer.echo(f"📁 Metadata saved: {metadata_path}")

            file_list = json.loads(Path(metadata_path).read_text())["files"]

            # Continue processing using the extracted folder
            working_dir = extracted_root

    # 2️. If directory → parse metadata directly

    elif path.is_dir():
        df, project_root = parse_metadata(str(path))

        metadata_path = save_metadata_json(
            df, f"{path.name}_metadata.json", project_root
        )
        typer.echo(f"📁 Metadata saved: {metadata_path}")

        file_list = json.loads(Path(metadata_path).read_text())["files"]

        working_dir = Path(path)

    # Unsupported path
    else:
        typer.secho("❌ Must provide a directory or ZIP file.", fg=typer.colors.RED)
        raise typer.Exit()

    # 3️. Contributors (Git)
    contributors = analyze_contributors(project_root)
    # 4. Code complexity (Tree-sitter)
    complexity_full = project_analysis_to_dict(analyze_project(working_dir))
    complexity_summary = complexity_full["summary"]

    # 5️. Combine into final report
    project_stats = calculate_project_stats(project_root, file_list)

    final_report = {
        "project_name": project_name,
        "project_root": project_root,
        "metadata": project_stats,
        "code_complexity": complexity_summary
    }

    # Add contributors field if there are actually any contributors, damn my React brain is taking over
    # I thought Python could do something like `&&` for conditional rendering. I'm cooked
    if len(contributors) > 0:
        final_report["contributors"] = contributors

    # If the user wants to list all the files analyzed, then add it to the final report,
    # By default, nah it'll bloat the JSON file
    if include_files:
        final_report["analyzed_files"] = file_list

    # Creating directory stuff, this will make it more clean in the future
    # outputs/{project_name}/{timestamp}
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    project_dir = out_dir / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create subfolder for each timestamp
    run_dir = project_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    # Also I guess we can save the metadata stuff into this folder too? TBH everything in final_report.json already includes
    # metadata stuff but still
    try:
        shutil.copy(metadata_path, run_dir / "metadata.json")
    except Exception as e:
        typer.secho(
            f"⚠️ Warning: Could not copy metadata file: {e} \nbut honestly, eh metadata stuff is already on there",
            fg=typer.colors.YELLOW,
        )

    output_file = run_dir / "final_report.json"
    output_file.write_text(json.dumps(final_report, indent=2))

    typer.secho(f"🎉 Final report saved in {run_dir}", fg=typer.colors.GREEN)

    typer.secho("Skills extracted successfully!", fg="green")
    typer.secho(f"Output saved to: {output_file}", fg="cyan")

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

