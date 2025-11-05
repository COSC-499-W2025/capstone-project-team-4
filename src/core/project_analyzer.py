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
    author_info = {}

    # Count the total commits for the repo
    for commit in repo.iter_commits():
        email = commit.author.email.lower()
        name = commit.author.name

        # Skip bots, cause who cares about them
        if "[bot]" in name.lower():
            continue

        author_commits[email] += 1
        author_info[email] = name
    
    total = sum(author_commits.values())

    # Right now, this prints the amount of collaborators twice. Asin, it prints the `.noreply.github.com`, and the
    # author's actual email. For functionality and data, we could just keep this as is.
    contributors = [
        {"name": author_info[email], "email":email, "commits": num_of_commits, "percent": round((num_of_commits / total) * 100, 2)}
        for email, num_of_commits in author_commits.items()
    ]

    print(contributors)


if __name__ == "__main__":
    # For testing, just use the current working directory
    working_directory = os.getcwd()
    analyze_contributors(working_directory);