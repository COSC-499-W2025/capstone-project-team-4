import sys
from src.core.database import init_db
from src.core.config_manager import save_config, load_config

# This is for testing if your local environment is running the "virtual environment"
# It should say True
def check_virtual_env():
    return sys.prefix != sys.base_prefix

if __name__ == "__main__":
    print("Running in virtual env:", check_virtual_env())
    init_db()
    config_data = {
        "theme": "dark",                      # UI theme preference
        "notifications": True,                # Enable system notifications
        "language": "en-US",                  # Default language setting
        "autosave_interval": 10,              # Auto-save every 10 minutes
        "backup_enabled": True,               # Enable local backup of user data
        "privacy_mode": False,                # If True, limit data sharing
        "font_size": 14,                      # UI font size
        "recent_files": ["report1.docx", "notes.txt"],  # Recently accessed files
        "default_view": "dashboard",          # Default screen when app starts
        "analytics_opt_in": True              # Consent to anonymous usage data
    }
    save_config(config_data)
    print("Loaded:", load_config())
    