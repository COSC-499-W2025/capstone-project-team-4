import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
import typer
import zipfile
from tempfile import TemporaryDirectory

from src.core import config_manager

# Database functions
from src.core.database import (
    init_db,
    save_project,
    save_files,
    save_complexity,
    save_contributors,
    save_resume_skills,
    assemble_report_from_db
)

# Metadata / analysis imports
from src.core.metadata_parser import parse_metadata
from src.core.project_analyzer import (
    analyze_contributors,
    analyze_project,
    project_analysis_to_dict,
    calculate_project_stats,
)
from src.core.resume_skill_extractor import analyze_project_skills


app = typer.Typer(help="Mining Digital Work Artifacts CLI")

# Make sure DB exists for every run
init_db()


def check_virtual_env():
    return sys.prefix != sys.base_prefix


@app.command("analyze-project")
def analyze_project_cli(
    path: Path = typer.Argument(..., help="Path to project directory or ZIP file."),
    include_files: bool = typer.Option(
        True, "--include-files/--no-include-files", help="Include full file list (metadata)"
    ),
    out: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Output directory (default: ./outputs)"
    ),
):
    config_manager.require_consent()

    out_dir = (out or Path.cwd() / "outputs").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    path = path.resolve()
    if not path.exists():
        typer.secho(f"❌ Path not found: {path}", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    project_name = path.stem

    # ------------------------- 1️⃣ Parse metadata -------------------------
    if path.is_file() and path.suffix.lower() == ".zip":
        typer.echo("📦 Extracting ZIP...")
        with TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            df, project_root = parse_metadata(temp_dir)
            file_list = df.to_dict(orient="records")
            working_dir = Path(temp_dir)
    elif path.is_dir():
        df, project_root = parse_metadata(str(path))
        file_list = df.to_dict(orient="records")
        working_dir = Path(path)
    else:
        typer.secho("❌ Must provide a directory or ZIP file.", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    # ❌ No temp_metadata.json — build metadata in memory
    metadata_block = {
        "metadata": df.to_dict(orient="records"),
        "project_root": str(project_root),
        "files": file_list,
    }

    # ------------------------- 2️⃣ Create project entry -------------------------
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    project_id = save_project(project_name, str(project_root), timestamp)

    # ------------------------- 3️⃣ Contributors -------------------------
    contributors = analyze_contributors(project_root)

    # ------------------------- 4️⃣ Code complexity -------------------------
    complexity_dict = project_analysis_to_dict(analyze_project(working_dir))

    # ------------------------- 5️⃣ Project stats -------------------------
    project_stats = calculate_project_stats(project_root, file_list)

    # ------------------------- 6️⃣ Resume-ready skills -------------------------
    skill_report = analyze_project_skills(project_root)
    save_resume_skills(project_id, skill_report["skill_categories"])

    # ------------------------- 7️⃣ Save raw analysis to DB -------------------------
    save_files(project_id, file_list)
    save_complexity(project_id, complexity_dict["functions"])
    if len(contributors) > 0:
        save_contributors(project_id, contributors)

    # ------------------------- 8️⃣ Reassemble from DB -------------------------
    report = assemble_report_from_db(project_id)

    # attach metadata + stats for JSON output
    report["metadata"] = metadata_block["metadata"]
    report["project_root"] = metadata_block["project_root"]
    report["files"] = metadata_block["files"]
    report["stats_summary"] = project_stats

    # ------------------------- 9️⃣ Output folder + JSON files -------------------------
    project_dir = out_dir / project_name / timestamp
    project_dir.mkdir(parents=True, exist_ok=True)

    # metadata.json
    (project_dir / "metadata.json").write_text(
        json.dumps({
            "metadata": report["metadata"],
            "project_root": report["project_root"],
            "files": report["files"] if include_files else []
        }, indent=2)
    )

    # complexity
    (project_dir / "complexity.json").write_text(
        json.dumps(report["code_complexity"], indent=2)
    )

    # contributors
    if report.get("contributors") and len(report["contributors"]) > 0:
        (project_dir / "contributors.json").write_text(
            json.dumps(report["contributors"], indent=2)
        )

    # 🆕 renamed from resume_skills.json → skill_extract.json
    (project_dir / "skill_extract.json").write_text(
        json.dumps(report["resume_skills"], indent=2)
    )

    typer.secho(f"🎉 Reports generated → {project_dir}", fg=typer.colors.GREEN)


@app.command("status")
def status() -> None:
    print(config_manager.read_cfg())


@app.command("consent")
def consent(
    grant: bool = typer.Option(False, "--grant"),
    revoke: bool = typer.Option(False, "--revoke"),
    external: Optional[bool] = typer.Option(None, "--external/--no-external"),
) -> None:
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
        print(f"External allowed = {external}")
    print("\nCurrent configuration:")
    print(config_manager.read_cfg())


@app.command("info")
def info() -> None:
    typer.echo("📊 Mining Digital Work Artifacts CLI")
    typer.echo("=" * 40)
    typer.echo("Commands available:")
    typer.echo("  analyze-project   — Full analysis & separated JSON files")
    typer.echo("  consent           — Manage user consent")
    typer.echo("  status            — Show current settings")
    typer.echo("  info              — Show this screen\n")


if __name__ == "__main__":
    print("Running in virtual env:", check_virtual_env())
    app()
