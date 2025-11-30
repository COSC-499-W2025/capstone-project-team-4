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
import shutil


# Database functions
from src.core.database import (
    init_db,
    save_project,
    save_files,
    save_complexity,
    save_contributors,
    save_resume_skills,
    save_resume_item,  # <-- added
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
from src.core.resume_item_generator import generate_resume_item  # <-- added

from src.core.contribution_ranking import (
    rank_projects_for_contributor,
    summarize_top_projects,
)
from src.core.project_contribution_log import (
    append_contribution_entry,
    rank_projects_from_log,
)
from src.core.alternate_skill_extractor import run_skill_extraction

from src.utils import pretty_print_json

from src.core.aggregate_outputs import aggregate_outputs, format_markdown, _serialize_projects



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
        typer.secho(f"❌ Path not found: {path}", fg="red")
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
        typer.secho("❌ Must provide a directory or ZIP file.", fg="red")
        raise typer.Exit(code=2)

    project_stats = calculate_project_stats(project_root, file_list)

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

    # ------------------------- 5️⃣ Skill extraction -------------------------
    skill_report = analyze_project_skills(project_root)
    languages = sorted(set(skill_report.get("languages", [])))
    frameworks = sorted(set(skill_report.get("frameworks", [])))
    skills = sorted(set(skill_report.get("skills", [])))

    save_resume_skills(project_id, skill_report.get("skill_categories", {}))

    try:
        from src.core.database import save_detected_technologies
    except Exception:
        save_detected_technologies = None
    if save_detected_technologies:
        try:
            save_detected_technologies(project_id, languages, frameworks)
        except Exception:
            pass

    detected_technologies = {
        "languages": languages,
        "frameworks": frameworks,
        "skills": skills,
    }

    # ------------------------- 6️⃣ Save raw analysis to DB -------------------------
    save_files(project_id, file_list)
    save_complexity(project_id, complexity_dict["functions"])
    if contributors:
        save_contributors(project_id, contributors)

    # ------------------------- 7️⃣ Generate resume item  -------------------------
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

    # ------------------------- 8️⃣ Reassemble from DB -------------------------
    report = assemble_report_from_db(project_id)
    report["metadata"] = metadata_block["metadata"]
    report["project_root"] = metadata_block["project_root"]
    report["files"] = metadata_block["files"]
    report["stats_summary"] = project_stats

    # ------------------------- 9️⃣ Output folder + JSON files -------------------------
    project_dir = out_dir / project_name / timestamp
    project_dir.mkdir(parents=True, exist_ok=True)

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

    # Skill extractor secondary output
    skills_output_file = project_dir / "skills_extracted.json"
    metadata_json_path = project_dir / "metadata.json"
    skills_result = run_skill_extraction(
        metadata_path=str(metadata_json_path), output_path=str(skills_output_file)
    )
    skills_output_file.write_text(json.dumps(skills_result, indent=2))

    (project_dir / "complexity.json").write_text(
        json.dumps(report["code_complexity"], indent=2)
    )

    if report.get("contributors") and len(report["contributors"]) > 0:
        (project_dir / "contributors.json").write_text(
            json.dumps(report["contributors"], indent=2)
        )

    (project_dir / "skill_extract.json").write_text(
        json.dumps(report["resume_skills"], indent=2)
    )
    if "detected_technologies" not in report:
        try:
            report.setdefault("resume_skills", {})
            report["resume_skills"]["languages"] = detected_technologies.get(
                "languages", []
            )
            report["resume_skills"]["frameworks"] = detected_technologies.get(
                "frameworks", []
            )
            report["resume_skills"]["skills_flat"] = detected_technologies.get(
                "skills", []
            )
        except Exception:
            pass
        (project_dir / "skill_extract.json").write_text(
            json.dumps(report["resume_skills"], indent=2)
        )

    # ------------------------- resume_item.json export -------------------------
    (project_dir / "resume_item.json").write_text(json.dumps(resume_item, indent=2))

    typer.secho(f"🎉 Reports generated → {project_dir}", fg=typer.colors.GREEN)


# ============================================================================
# OTHER COMMANDS (unchanged)
# ============================================================================
@app.command("browse")
def browse(
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Outputs directory"),
    raw: bool = typer.Option(
        False, "--raw", help="Show raw JSON instead of pretty view"
    ),
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

    timestamps = sorted(
        [d for d in project.iterdir() if d.is_dir()], key=lambda p: p.name
    )
    if not timestamps:
        typer.secho("No timestamps found!", fg="yellow")
        return

    typer.secho(f"\n📁 Select a timestamp for {project.name}:\n", fg="green")
    for i, r in enumerate(timestamps, start=1):
        typer.echo(f"[{i}] {r.name}")

    run = timestamps[int(typer.prompt("\nEnter number")) - 1]

    json_files = [f for f in run.iterdir() if f.suffix == ".json"]

    typer.secho(f"\n📄 Select a file to view:\n", fg="green")
    for i, f in enumerate(json_files, start=1):
        typer.echo(f"[{i}] {f.name}")

    selected_file = json_files[int(typer.prompt("\nEnter number")) - 1]

    typer.secho(f"\n=== {selected_file.name} ===\n", fg=typer.colors.BLUE, bold=True)

    try:
        data = json.loads(selected_file.read_text())
        pretty_print_json.pretty_print_json(selected_file.name, data, raw)
    except Exception as e:
        typer.secho(f"Error reading JSON: {e}", fg="red")

@app.command("delete-output") # Similar to browse, opens a directory selector that lets you select project & timestamp to delete 
def delete_output(
    out: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Outputs directory (default: ./outputs)"
    ),
):
    out_dir = (out or Path.cwd() / "outputs").resolve()

    #Verify outputs folder exists
    if not out_dir.exists():
        typer.secho("outputs folder not found.")
        raise typer.Exit()

    #Select the name of your project 
    projects = [d for d in out_dir.iterdir() if d.is_dir()]
    if not projects:
        typer.secho(" No projects found.")
        return

    typer.secho("\n Select a project to delete an output from:\n")
    for i, p in enumerate(projects, start=1):
        typer.echo(f"[{i}] {p.name}")

    choice = typer.prompt("\nEnter number")
    try:
        project = projects[int(choice) - 1]
    except Exception:
        typer.secho("Invalid selection.")
        raise typer.Exit()

    # Select timestamp you want 
    timestamps = [d for d in project.iterdir() if d.is_dir()]
    if not timestamps:
        typer.secho("No timestamped runs found for this project.")
        return

    timestamps.sort(key=lambda p: p.name)

    typer.secho(
        f"\n Select a timestamp to delete for {project.name}:\n")
    for i, r in enumerate(timestamps, start=1):
        typer.echo(f"[{i}] {r.name}")

    choice = typer.prompt("\nEnter number")
    try:
        run = timestamps[int(choice) - 1]
    except Exception:
        typer.secho("Invalid selection.")
        raise typer.Exit()

    # Confirm delete
    typer.secho(
        f"\n You are about to delete the output folder:\n  {run}\n")
    confirm = typer.prompt("Type 'yes' to confirm deletion", default="no")

    if confirm.lower() != "yes":
        typer.secho("Deletion cancelled.")
        raise typer.Exit()

    # Delete the selected run folder 
    try:
        shutil.rmtree(run)
        typer.secho(f" Deleted portfolio output: {run}")
    except Exception as e:
        typer.secho("Failed to delete output folder.")
        typer.secho(f" Details: {e}")
        raise typer.Exit(code=1)



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


@app.command("info",help="Show information about the CLI.")
def info() -> None:
    typer.echo("📊 Mining Digital Work Artifacts CLI")
    typer.echo("=" * 40)
    typer.echo("Commands available:\n")
    typer.echo(" run command: python -m src.main <command> [options]\n")
    typer.echo("  analyze-project   — Full analysis & separated JSON files")
    typer.echo("  consent           — Manage user consent")
    typer.echo("  status            — Show current settings")
    typer.echo("  info              — Show this screen")
    typer.echo("  rank-contributions — Rank a contributor's impact within a Git project. python -m src.main rank-contributions <file_path> --name <contributor_name> OR --email <contributor_email> \n")
    typer.echo("  rank-projects      — Show all analyzed projects for a contributor, ranked by contribution score. python -m src.main rank-projects <contributor_name> OR <contributor_email>  The name/email you use must be consistent when calling rank-projects\n")
    typer.echo("  browse             — Show all analyzed projects sorted by project name and tiemstamp. ")
    typer.echo("  delete-output      — Show all analyzed projects sorted by project name and timestamp, then user can delete specific analyzed timestamp. ") 
   


@app.command(
    "rank-contributions",
    help="Rank a contributor's impact within a Git project based on commits, lines changed, and files touched.",
)
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

    ranked = rank_projects_for_contributor(
        [project], match_by=match_by, identifier=identifier
    )
    if not ranked:
        typer.secho("No contributions found.", fg="yellow")
        raise typer.Exit()

    summary_obj = ranked[0]
    append_contribution_entry(
        summary_obj, extra={"source_command": "rank-contributions"}
    )
    summary = summarize_top_projects(ranked, top_n=1)[0]

    typer.echo("Contribution Summary\n-----------------------")
    typer.echo(summary)


@app.command(
    "rank-projects",
    help="Show all analyzed projects for a contributor, ranked by contribution score based on the saved log.",
)
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
        commits = entry.get("commits", 0)
        added = entry.get("total_lines_added", 0)
        deleted = entry.get("total_lines_deleted", 0)
        files = entry.get("files_touched", 0)
        total_lines = added + deleted

        typer.echo(f"{i}. {proj}")
        typer.echo(
            f"   Score: {score:.2f} | Commits: {commits} | "
            f"Lines changed: +{added}/-{deleted} (total {total_lines}) | Files touched: {files}\n"
        )


@app.command("aggregate-outputs")
def aggregate_outputs_cli(
    outputs: Path = typer.Argument("outputs", help="Path to outputs directory"),
    json_output: bool = typer.Option(False, "--json", help="Print JSON instead of Markdown"),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Save output to file instead of printing"),
):
    """
    Aggregate all analyzed project outputs into a dashboard summary.
    """
    projects = aggregate_outputs(outputs)

    if json_output:
        serial = _serialize_projects(projects)
        content = json.dumps(serial, ensure_ascii=False, indent=2)
    else:
        content = format_markdown(projects)

    if out:
        out.write_text(content, encoding="utf-8")
        typer.secho(f" Aggregated report saved to: {out}", fg="green")
    else:
        typer.echo(content)

if __name__ == "__main__":
    print("Running in virtual env:", check_virtual_env())
    app()
