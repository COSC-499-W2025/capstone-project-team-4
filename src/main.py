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
from src.core.resume_item_generator import generate_resume_item

# Database functions
from src.core.database import (
    init_db,
    save_project,
    save_files,
    save_complexity,
    save_contributors,
    save_resume_skills,
    assemble_report_from_db,
    save_resume_item,
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
from src.core.contribution_ranking import (
    rank_projects_for_contributor,
    summarize_top_projects,
)
from src.core.project_contribution_log import (
    append_contribution_entry,
    rank_projects_from_log,
)
from src.utils import pretty_print_json

app = typer.Typer(help="Mining Digital Work Artifacts CLI")

# Ensure DB exists every time the app runs
init_db()


def check_virtual_env():
    return sys.prefix != sys.base_prefix


# ============================================================================
# MAIN COMMAND — ANALYZE PROJECT
# ============================================================================
@app.command("analyze-project")
def analyze_project_cli(
    path: Path = typer.Argument(..., help="Path to project directory or ZIP file"),
    include_files: bool = typer.Option(
        True, "--include-files/--no-include-files", help="Include full file list (metadata)"
    ),
    out: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Output directory (default: ./outputs)"
    ),
):
    """Run full analysis on a GitHub-style project and export JSON reports."""
    config_manager.require_consent()

    out_dir = (out or Path.cwd() / "outputs").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    path = path.resolve()
    if not path.exists():
        typer.secho(f"❌ Path not found: {path}", fg="red")
        raise typer.Exit(code=2)

    project_name = path.stem

    # ----------------------------------------------------------------------
    # 1) Parse metadata
    # ----------------------------------------------------------------------
    if path.is_file() and path.suffix.lower() == ".zip":
        typer.echo("📦 Extracting ZIP...")
        with TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
            df, project_root = parse_metadata(temp_dir)
            working_dir = Path(temp_dir)
            file_list = df.to_dict(orient="records")
    elif path.is_dir():
        df, project_root = parse_metadata(str(path))
        working_dir = Path(path)
        file_list = df.to_dict(orient="records")
    else:
        typer.secho("❌ Must provide a directory or ZIP file.", fg="red")
        raise typer.Exit(code=2)

    project_stats = calculate_project_stats(project_root, file_list)

    metadata_block = {
        "metadata": project_stats,
        "project_root": str(project_root),
        "files": file_list,
    }

    # ----------------------------------------------------------------------
    # 2) Save initial project entry
    # ----------------------------------------------------------------------
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    project_id = save_project(project_name, str(project_root), timestamp)

    # ----------------------------------------------------------------------
    # 3) Contributors
    # ----------------------------------------------------------------------
    contributors = analyze_contributors(project_root)

    # ----------------------------------------------------------------------
    # 4) Code Complexity
    # ----------------------------------------------------------------------
    complexity_dict = project_analysis_to_dict(analyze_project(working_dir))

    # ----------------------------------------------------------------------
    # 5) AI-ready skill extraction
    # ----------------------------------------------------------------------
    skill_report = analyze_project_skills(project_root)
    languages = sorted(set(skill_report.get("languages", [])))
    frameworks = sorted(set(skill_report.get("frameworks", [])))
    skills = sorted(set(skill_report.get("skills", [])))
    save_resume_skills(project_id, skill_report.get("skill_categories", {}))

    detected_technologies = {"languages": languages, "frameworks": frameworks, "skills": skills}

    # ----------------------------------------------------------------------
    # 6) Save raw analysis to DB
    # ----------------------------------------------------------------------
    save_files(project_id, file_list)
    save_complexity(project_id, complexity_dict["functions"])
    if contributors:
        save_contributors(project_id, contributors)

    # ----------------------------------------------------------------------
    # 7) Generate résumé item + save to DB
    # ----------------------------------------------------------------------
    resume_item = generate_resume_item(
        project_name=project_name,
        contributors=contributors,
        project_stats=project_stats,
        skill_categories=skill_report.get("skill_categories", {}),
        languages=languages,
        frameworks=frameworks,
        complexity_dict=complexity_dict,
    )
    save_resume_item(project_id, resume_item)

    # ----------------------------------------------------------------------
    # 8) Load everything back from DB as unified JSON
    # ----------------------------------------------------------------------
    report = assemble_report_from_db(project_id)
    report.update(
        {
            "metadata": metadata_block["metadata"],
            "project_root": metadata_block["project_root"],
            "files": metadata_block["files"],
            "stats_summary": project_stats,
        }
    )

    # ----------------------------------------------------------------------
    # 9) Export JSON files
    # ----------------------------------------------------------------------
    project_dir = out_dir / project_name / timestamp
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "metadata.json").write_text(
        json.dumps(
            {"metadata": report["metadata"], "project_root": report["project_root"], "files": report["files"] if include_files else []},
            indent=2,
        )
    )

    (project_dir / "complexity.json").write_text(json.dumps(report["code_complexity"], indent=2))

    if contributors:
        (project_dir / "contributors.json").write_text(json.dumps(report["contributors"], indent=2))

    (project_dir / "skill_extract.json").write_text(json.dumps(report["resume_skills"], indent=2))

    (project_dir / "resume_item.json").write_text(json.dumps(resume_item, indent=2))

    typer.secho(f"🎉 Reports generated → {project_dir}", fg="green")


# ============================================================================
# BROWSING / CONSENT / CONTRIBUTION RANKING — UNCHANGED API
# ============================================================================

@app.command("browse")
def browse(
    out: Optional[Path] = typer.Option(None, "--out", "-o"),
    raw: bool = typer.Option(False, "--raw"),
):
    out_dir = (out or Path.cwd() / "outputs").resolve()
    if not out_dir.exists():
        typer.secho("❌ outputs folder not found.", fg="red")
        raise typer.Exit()

    projects = [d for d in out_dir.iterdir() if d.is_dir()]
    if not projects:
        typer.secho("⚠ No projects found.", fg="yellow")
        return

    typer.secho("\n📁 Select a project:\n", fg="green")
    for i, p in enumerate(projects, start=1):
        typer.echo(f"[{i}] {p.name}")

    project = projects[int(typer.prompt("\nEnter number")) - 1]

    timestamps = sorted([d for d in project.iterdir() if d.is_dir()], key=lambda p: p.name)

    typer.secho(f"\n📁 Select a timestamp for {project.name}:\n", fg="green")
    for i, t in enumerate(timestamps, start=1):
        typer.echo(f"[{i}] {t.name}")

    run = timestamps[int(typer.prompt("\nEnter number")) - 1]

    json_files = [f for f in run.iterdir() if f.suffix == ".json"]

    typer.secho(f"\n📄 Select a file to view:\n", fg="green")
    for i, f in enumerate(json_files, start=1):
        typer.echo(f"[{i}] {f.name}")

    selected_file = json_files[int(typer.prompt("\nEnter number")) - 1]

    typer.secho(f"\n=== {selected_file.name} ===\n", fg="blue", bold=True)
    data = json.loads(selected_file.read_text())
    pretty_print_json.pretty_print_json(selected_file.name, data, raw)


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
    typer.echo("  analyze-project")
    typer.echo("  browse")
    typer.echo("  rank-contributions")
    typer.echo("  rank-projects")
    typer.echo("  consent / status / info\n")


@app.command("rank-contributions")
def rank_contributions(
    project: Path = typer.Argument(...),
    name: Optional[str] = typer.Option(None, "--name"),
    email: Optional[str] = typer.Option(None, "--email"),
):
    config_manager.require_consent()
    if not name and not email:
        typer.secho("You must specify either --name or --email", fg="red")
        raise typer.Exit()

    identifier = email if email else name
    match_by = "email" if email else "name"

    project = project.resolve()
    if not (project.exists() and (project / ".git").exists()):
        typer.secho("❌ Invalid project or missing .git", fg="red")
        raise typer.Exit()

    ranked = rank_projects_for_contributor([project], match_by=match_by, identifier=identifier)
    if not ranked:
        typer.secho("No contributions found.", fg="yellow")
        raise typer.Exit()

    summary_obj = ranked[0]
    append_contribution_entry(summary_obj, extra={"source_command": "rank-contributions"})
    summary = summarize_top_projects(ranked, top_n=1)[0]

    typer.echo("Contribution Summary\n-----------------------")
    typer.echo(summary)


@app.command("rank-projects")
def rank_projects_from_log_cli(
    name: Optional[str] = typer.Option(None, "--name"),
    email: Optional[str] = typer.Option(None, "--email"),
    top_n: Optional[int] = typer.Option(None, "--top-n"),
):
    if not name and not email:
        typer.secho("You must specify either --name or --email", fg="red")
        raise typer.Exit()

    identifier = email if email else name
    match_by = "email" if email else "name"

    ranked_entries = rank_projects_from_log(identifier=identifier, match_by=match_by)
    if not ranked_entries:
        typer.secho("No logged entries found.", fg="yellow")
        raise typer.Exit()

    if top_n is not None and top_n > 0:
        ranked_entries = ranked_entries[:top_n]

    typer.echo("Projects ranked by contribution score:\n")
    for i, entry in enumerate(ranked_entries, start=1):
        proj = entry.get("project_root", "<unknown>")
        score = entry.get("contribution_score", 0.0)
        added = entry.get("total_lines_added", 0)
        deleted = entry.get("total_lines_deleted", 0)
        commits = entry.get("commits", 0)
        files = entry.get("files_touched", 0)
        total_lines = added + deleted
        typer.echo(f"{i}. {proj}")
        typer.echo(
            f"   Score: {score:.2f} | Commits: {commits} | "
            f"Lines changed: +{added}/-{deleted} (total {total_lines}) | Files touched: {files}\n"
        )


if __name__ == "__main__":
    print("Running in virtual env:", check_virtual_env())
    app()
