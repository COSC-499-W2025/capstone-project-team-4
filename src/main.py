import sys

# This is for testing if your local environment is running the "virtual environment"
# It should say True
#print(sys.prefix != sys.base_prefix)

#Test database and config manager imports

from database import init_db
from config_manager import save_config, load_config

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
    data = {"theme": "dark", "notifications": True}
    save_config(data)
    print("Saved config:", data)
    print("Loaded config:", load_config())
