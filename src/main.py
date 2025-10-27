import sys


# This is for testing if your local environment is running the "virtual environment"
# It should say True
def check_virtual_env():
    return sys.prefix != sys.base_prefix


if __name__ == "__main__":
    print("Running in virtual env:", check_virtual_env())
