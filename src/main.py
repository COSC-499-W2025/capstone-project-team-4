import sys

# This is for testing if your local environment is running the "virtual environment"
# It should say True
print(sys.prefix != sys.base_prefix)
