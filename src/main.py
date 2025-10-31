import sys
import typer
from src.core import config_manager
from src.core.database import init_db
from src.core.config_manager import save_config, load_config

app = typer.Typer(help="Mining Digital Work Artifacts CLI")

# This is for testing if your local environment is running the "virtual environment"
# It should say True
def check_virtual_env():
    return sys.prefix != sys.base_prefix


@app.command()
def consent(
    grant: bool = typer.Option(False, "--grant", help="Grant consent to process files."),
    revoke: bool = typer.Option(False, "--revoke", help="Revoke consent."),
    external: bool | None = typer.Option(
        None, "--external", help="Allow external APIs (true/false)."
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

    # Update external permission (if provided)
    if external is not None:
        config_manager.set_external_allowed(bool(external))
        print(f"External services allowed = {bool(external)}")

    # Show current configuration
    print("\nCurrent configuration:")
    print(config_manager.read_cfg())


@app.command()
def status() -> None:
    """Print current consent and external-usage settings."""
    print(config_manager.read_cfg())


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


