"""This file is for debugging purposes during development and is not required in the production environment."""

import subprocess
import os

# Test parameters - change these to match your setup
repo_path = "/Users/kiichirosuganuma/Downloads/2026_term2/COSC499/capstone-project-team-4"
contributor_email = "aliffmlg@gmail.com"  # Aliff Razak's email
branch = "HEAD"

print(f"Testing git command for contributor: {contributor_email}")
print(f"Repository: {repo_path}")
print(f"Branch: {branch}\n")

# Test 1: Check if repo exists
if not os.path.isdir(repo_path):
    print(f"Repository path not found: {repo_path}")
    exit(1)
else:
    print(f"Repository path exists")

# Test 2: Check if git is available
try:
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print(f"Git repository found: {result.stdout.strip()}")
    else:
        print(f"Not a git repository: {result.stderr}")
        exit(1)
except Exception as e:
    print(f"Git not available: {e}")
    exit(1)

# Test 3: Get commits for the contributor
print(f"\n--- Test: Get commits for {contributor_email} ---")
cmd = [
    "git", "-C", repo_path, "log",
    branch,
    f"--author={contributor_email}",
    "--oneline",
    "--max-count=5"
]
print(f"Command: {' '.join(cmd)}\n")

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if result.returncode == 0:
    lines = result.stdout.strip().split("\n")
    print(f"Found {len(lines)} recent commits:")
    for line in lines[:5]:
        print(f"  {line}")
else:
    print(f"Failed: {result.stderr}")


# Test 4: Get file changes for first commit
print(f"\n--- Test: Get file changes with --numstat ---")
cmd = [
    "git", "-C", repo_path, "log",
    branch,
    f"--author={contributor_email}",
    "--numstat",
    "--pretty=%aN <%aE>",
    "--max-count=3"
]
print(f"Command: {' '.join(cmd)}\n")

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if result.returncode == 0:
    lines = result.stdout.strip().split("\n")
    print(f"✓ Output (first 30 lines):")
    for line in lines[:30]:
        print(f"  {line}")
    print(f"  ... (total {len(lines)} lines)")
else:
    print(f"Failed: {result.stderr}")

# Test 5: Check a specific file
print(f"\n--- Test: Check changes for a specific file ---")
test_file = "backend/src/api/main.py"
cmd = [
    "git", "-C", repo_path, "log",
    branch,
    f"--author={contributor_email}",
    "--numstat",
    "--pretty=%aN <%aE>",
    "--max-count=50",  # Get more commits to find the file
    "--", test_file
]
print(f"File: {test_file}")
print(f"Command: {' '.join(cmd)}\n")

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
if result.returncode == 0:
    lines = result.stdout.strip().split("\n")
    if lines and lines[0]:
        print(f"✓ Output (all lines):")
        for line in lines:
            print(f"  {line}")
    else:
        print(f"⚠ No changes found for this file by this contributor")
else:
    print(f"Failed: {result.stderr}")

print("\nDebug tests completed")
