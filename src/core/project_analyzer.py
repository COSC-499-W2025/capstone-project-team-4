from git import Repo
# Use defaultdict instead of a regular dict to initialize default keys automatically 
from collections import defaultdict

import os

def analyze_contributors(project_path = "."):
    """
    Opens up the project folder that analyzes the contributors on a project
    Looks at the amount of contributors and returns an object

    Keyword arguments:
    project_path -- the path to the root project (default "." or current directory)

    Returns:
    A dictionary/hash map of contributors each having their name, commits, and the amount of work committed (percentage)
    """
    repo = Repo(project_path)
    author_commits = defaultdict(int)

    # Count the total commits for the repo
    for commit in repo.iter_commits():
        author_commits[commit.author.name] += 1
    total = sum(author_commits.values())

    print(f"The total is: ${total}")
    print(author_commits)

    


if __name__ == "__main__":
    # For testing, just use the current working directory
    working_directory = os.getcwd()
    analyze_contributors(working_directory);