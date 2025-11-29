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
    assemble_report_from_db,
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

# Make sure DB exists for every run
init_db()


def check_virtual_env():
    return sys.prefix != sys.base_prefix


@app.command("analyze-project")
def analyze_project_cli(
    path: Path = typer.Argument(..., help="Path to project directory or ZIP file."),
    include_files: bool = typer.Option(
        True,
        "--include-files/--no-include-files",
        help="Include full file list (metadata)",
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

    # This is just a summary so like... yeah this should finally get actual metadata stuff
    project_stats = calculate_project_stats(project_root, file_list)

    # ❌ No temp_metadata.json — build metadata in memory
    metadata_block = {
        "metadata": project_stats,
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
        json.dumps(
            {
                "metadata": report["metadata"],
                "project_root": report["project_root"],
                "files": report["files"] if include_files else [],
            },
            indent=2,
        )
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


#
@app.command("browse")
def browse(
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Outputs directory"),
    raw: bool = typer.Option(
        False, "--raw", help="Show raw JSON instead of pretty view"
    ),
):
    """
    Interactive menu to browse previously generated project reports.
    """
    out_dir = (out or Path.cwd() / "outputs").resolve()

    # 0. Verify if outputs folder actually exists
    if not out_dir.exists():
        typer.secho("❌ outputs folder not found.", fg=typer.colors.RED)
        raise typer.Exit()

    # 1. Select project

    projects = [d for d in out_dir.iterdir() if d.is_dir()]
    if not projects:
        typer.secho("⚠ No projects found.", fg=typer.colors.YELLOW)
        return

    typer.secho("\n📁 Select a project:\n", fg=typer.colors.GREEN)
    for i, p in enumerate(projects, start=1):
        typer.echo(f"[{i}] {p.name}")

    choice = typer.prompt("\nEnter number")
    try:
        project = projects[int(choice) - 1]
    except:
        typer.secho("❌ Invalid selection.", fg=typer.colors.RED)
        raise typer.Exit()

    # 2. Select timestamp
    timestamp = [d for d in project.iterdir() if d.is_dir()]
    timestamp.sort(key=lambda p: p.name)

    typer.secho(f"\n📁 Select a timestamp for {project.name}:\n", fg=typer.colors.GREEN)
    for i, r in enumerate(timestamp, start=1):
        typer.echo(f"[{i}] {r.name}")

    choice = typer.prompt("\nEnter number")
    try:
        run = timestamp[int(choice) - 1]
    except:
        typer.secho("❌ Invalid selection.", fg=typer.colors.RED)
        raise typer.Exit()

    # 3: SELECT WHICH JSON FILE

    json_files = [f for f in run.iterdir() if f.suffix == ".json"]

    typer.secho(f"\n📄 Select a file to view:\n", fg=typer.colors.GREEN)
    for i, f in enumerate(json_files, start=1):
        typer.echo(f"[{i}] {f.name}")

    choice = typer.prompt("\nEnter number")
    try:
        selected_file = json_files[int(choice) - 1]
    except:
        typer.secho("❌ Invalid selection.", fg=typer.colors.RED)
        raise typer.Exit()

    # 4. Show file contents

    typer.secho(f"\n=== {selected_file.name} ===\n", fg=typer.colors.BLUE, bold=True)

    try:
        data = json.loads(selected_file.read_text())
        # typer.echo(json.dumps(data, indent=2))
        # Bruh why is Python like this?
        pretty_print_json.pretty_print_json(selected_file.name, data, raw)
    except Exception as e:
        typer.secho(f"Error reading JSON: {e}", fg=typer.colors.RED)


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


@app.command(
    "rank-contributions",
    help="Rank a contributor's impact within a Git project based on commits, lines changed, and files touched.",
)
def rank_contributions(
    project: Path = typer.Argument(
        ..., help="Path to a project directory containing a .git folder"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", help="Contributor name (case-insensitive)"
    ),
    email: Optional[str] = typer.Option(
        None, "--email", help="Contributor email (case-insensitive)"
    ),
):
    # Rank a contributor's impact within a project based on Git history. Uses analyze_contributors() under the hood.
    # Consent check (same pattern as analyze-project)
    config_manager.require_consent()

    try:
        if not name and not email:
            typer.secho("You must specify either --name or --email", fg="red")
            raise typer.Exit(code=2)

        project = project.resolve()

        if not project.exists():
            typer.secho(f"Path not found: {project}", fg="red")
            raise typer.Exit(code=2)

        git_dir = project / ".git"
        if not git_dir.exists() or not git_dir.is_dir():
            typer.secho("This folder does not contain a .git directory.", fg="red")
            raise typer.Exit(code=2)

        # Decide how to match the contributor
        if email:
            match_by = "email"
            identifier = email
        else:
            match_by = "name"
            identifier = name  # type: ignore[assignment]

        typer.echo(f"Analyzing contributions in: {project}")
        typer.echo(f"Contributor: {identifier} ({match_by})\n")

        # Use your ranking helper (wraps analyze_contributors internally)
        ranked = rank_projects_for_contributor(
            [project],
            match_by=match_by,  # "name" or "email"
            identifier=identifier,
        )

        if not ranked:
            typer.secho("No contributions found for this contributor.", fg="yellow")
            raise typer.Exit()

        # Take the top (only) project summary object
        summary_obj = ranked[0]

        # Log this contribution so we can rank projects across runs later
        append_contribution_entry(
            summary_obj,
            extra={
                "source_command": "rank-contributions",
            },
        )

        summary = summarize_top_projects(ranked, top_n=1)[0]

        typer.echo("Contribution Summary")
        typer.echo("-----------------------")
        typer.echo(summary)

    except Exception as e:
        typer.secho("\n The command failed due to an unexpected error.", fg="red")
        typer.secho(f" Details: {str(e)}", fg="yellow")
        typer.secho(
            " Tip: Ensure the project path is correct and contains a valid .git directory.",
            fg="cyan",
        )
        raise typer.Exit(code=1)


@app.command(
    "rank-projects",
    help="Show all analyzed projects for a contributor, ranked by contribution score based on the saved log.",
)
def rank_projects_from_log_cli(
    name: Optional[str] = typer.Option(
        None, "--name", help="Contributor name (case-insensitive)"
    ),
    email: Optional[str] = typer.Option(
        None, "--email", help="Contributor email (case-insensitive)"
    ),
    top_n: Optional[int] = typer.Option(
        None,
        "--top-n",
        help="Limit the number of projects shown. If not provided, show all.",
    ),
):
    if (
        not name and not email
    ):  # Rank importance of each project based on a user's contributions, using entries stored in project_contributions_log.json.
        typer.secho("You must specify either --name or --email", fg="red")
        raise typer.Exit(code=2)

    if email:
        match_by = "email"
        identifier = email
    else:
        match_by = "name"
        identifier = name  # type: ignore[assignment]

    typer.echo(
        f"Ranking projects for contributor: {identifier} ({match_by}) "
        "based on logged contribution summaries.\n"
    )

    try:
        ranked_entries = rank_projects_from_log(
            identifier=identifier,
            match_by=match_by,
        )

        if not ranked_entries:
            typer.secho(
                "No logged contribution entries found for this contributor.",
                fg="yellow",
            )
            raise typer.Exit()

        if top_n is not None and top_n > 0:
            ranked_entries = ranked_entries[:top_n]

        typer.echo("Projects ranked by contribution score:\n")

        for i, entry in enumerate(ranked_entries, start=1):
            proj = entry.get("project_root", "<unknown>")
            score = entry.get("contribution_score", 0.0)
            commits = entry.get("commits", 0)
            added = entry.get("total_lines_added", 0)
            deleted = entry.get("total_lines_deleted", 0)
            files = entry.get("files_touched", 0)

            total_lines = added + deleted

            typer.echo(f"{i}. {proj}")
            typer.echo(
                f"   Score: {score:.2f}  |  Commits: {commits}  |  "
                f"Lines changed: +{added} / -{deleted} (total {total_lines})  |  "
                f"Files touched: {files}"
            )
            typer.echo("")

    except Exception as e:
        typer.secho("\n Failed to rank projects from log.", fg="red")
        typer.secho(f" Details: {str(e)}", fg="yellow")
        typer.secho(
            " Tip: Make sure you've run 'rank-contributions' at least once so the log file exists.",
            fg="cyan",
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    print("Running in virtual env:", check_virtual_env())
    app()
