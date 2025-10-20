import sys
# This is for testing if your local environment is running the "virtual environment"
# It should say True
#print(sys.prefix != sys.base_prefix)

#Test database and config manager imports

from database import init_db
from config_manager import save_config, load_config

def check_virtual_env():
    return sys.prefix != sys.base_prefix

if __name__ == "__main__":
#if __name__ == "main":  If this crashes please try with this one. This line was orignally written by Aliff from the CI setup. 
    print("Running in virtual env:", check_virtual_env())
    init_db()
    print("Database initialized.")
    data = {"theme": "dark", "notifications": True}
    save_config(data)
    print("Saved config:", data)
    print("Loaded config:", load_config())
