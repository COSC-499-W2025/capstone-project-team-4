import json
import typer


def pretty_print_json(file_name: str, data: dict, raw: bool = False):
    """
    Pretty prints known JSON files in a human-friendly format.
    Falls back to raw JSON dump when unknown or when raw=True.
    """

    if raw:
        typer.echo(json.dumps(data, indent=2))
        return

    # Pretty print: overview.json
    if file_name == "overview.json":
        typer.secho("\n📘 Project Overview\n", fg=typer.colors.BLUE, bold=True)
        for key, value in data.items():
            typer.secho(f"{key.capitalize()}: ", fg=typer.colors.GREEN, bold=True)
            typer.echo(f"  {value}\n")
        return

    # Pretty print: skill_extract.json
    if file_name == "skill_extract.json":
        typer.secho("\n🧠 Resume Skills\n", fg=typer.colors.MAGENTA, bold=True)
        for category, skills in data.items():
            typer.secho(f"{category}:", fg=typer.colors.BLUE, bold=True)
            for skill in skills:
                typer.echo(f"  - {skill}")
        return

    # Pretty print: contributors.json
    if file_name == "contributors.json":
        typer.secho("\n👥 Contributors\n", fg=typer.colors.CYAN, bold=True)
        for person in data:
            typer.secho(f"• {person.get('name', 'Unknown')}", bold=True)
            typer.echo(f"  Email: {person.get('primary_email')}")
            typer.echo(f"  Commits: {person.get('commits')}")
            typer.echo(f"  Added: {person.get('total_lines_added')}")
            typer.echo(f"  Deleted: {person.get('total_lines_deleted')}")
            typer.echo("")
        return

    # Pretty print: complexity.json (summary)
    if file_name == "complexity.json":
        functions = data.get("functions", [])
        typer.secho("\n🔧 Code Complexity Summary\n", fg=typer.colors.YELLOW, bold=True)
        typer.echo(f"Total functions analyzed: {len(functions)}\n")

        # Show top 5 most complex functions
        top = sorted(functions, key=lambda x: x["cyclomatic_complexity"], reverse=True)[
            :5
        ]
        typer.secho("Top 5 Most Complex Functions:", fg=typer.colors.GREEN, bold=True)
        for fn in top:
            typer.echo(f"• {fn['name']}  (Complexity: {fn['cyclomatic_complexity']})")
            typer.echo(f"  File: {fn['file_path']}")
            typer.echo("")
        return

    # Pretty print: metadata.json (summary)
    if file_name == "metadata.json":
        typer.secho("\n📁 Metadata Summary\n", fg=typer.colors.BLUE, bold=True)
        typer.echo(f"Total files: {data.get('total_files', '?')}")
        typer.echo(f"Total size: {data.get('total_size_human', '?')}")
        typer.echo(f"Languages detected: {', '.join(data.get('languages', []))}")
        return

    # Unknown file then print raw JSON cause idk I don't wanna create a fallback for that haha
    typer.echo(json.dumps(data, indent=2))
