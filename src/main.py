import typer
from core import config_manager, file_validator, metadata_parser, utils
import sys
from src.core.database import init_db
from src.core.config_manager import save_config, load_config
# This is for testing if your local environment is running the "virtual environment"
# It should say True
def check_virtual_env():
    return sys.prefix != sys.base_prefix

 if __name__ == "__main__":
        print("Running in virtual env:", check_virtual_env())

#Create Typer app
app = typer.Typer( help="Mining Digital Work Artifacts CLI")

@app.command()
def consent(
    grant: bool = typer.Option(False, "--grant", help="Grant consent to process files."),
    revoke: bool = typer.Option(False, "--revoke", help="Revoke consent."),
    external: bool | None = typer.Option(
        None, "--external", help="Allow external APIs (true/false)."
    ),
):


    # Manage user consent and external processing permission.
    
  # Conflicting consent option handling
  
  if grant and revoke:
        print("Error: choose either --grant OR --revoke.")
        raise typer.Exit(code=2)
  
  if grant: 
      config_manager.set_consent(True)
      print("Consent granted.")
  if revoke: 
      config_manager.set_consent(False)
      print("Consent revoked.")

# Updates external usage flag if its provided. 
  if external is not None:
        config_manager.set_external_allowed(bool(external))
        print(f"External services allowed = {bool(external)}")

  print("Current configuration:")
  print(config_manager.read_cfg())

# Print current consent and external usage settings
  @app.command()
  def status():
    print(config_manager.read_cfg())
    
    """
    Main Workflow:
    1) Ensure consent is given
    2) Validate & extract zip file
    3) Parse file metadata 
    4) Use external API to analyze codes in zips
    5) Extract Skills and generate report
    """
      
if __name__ == "__main__":
#if __name__ == "main":
    #print("Running in virtual env:", check_virtual_env())
    init_db()
    config_data = {"theme": "dark", "notifications": True}
    save_config(config_data)
    print("Loaded:", load_config())
