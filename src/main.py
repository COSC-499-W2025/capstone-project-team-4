import sys
import typer
from core import config_manager

app = typer.Typer(help="Mining Digital Work Artifacts CLI")


def check_virtual_env() -> bool:
    """Return True if running inside a virtual environment."""
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
    app()
