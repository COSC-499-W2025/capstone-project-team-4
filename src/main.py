import sys
from src.core.database import init_db
from src.core.config_manager import save_config, load_config
# This is for testing if your local environment is running the "virtual environment"
# It should say True
def check_virtual_env():
    return sys.prefix != sys.base_prefix

if __name__ == "__main__":
#if __name__ == "main":
    #print("Running in virtual env:", check_virtual_env())
    init_db()
    config_data = {"theme": "dark", "notifications": True}
    save_config(config_data)
    print("Loaded:", load_config())
