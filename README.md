[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20510500&assignment_repo_type=AssignmentRepo)
# Project-Starter
Please use the provided folder structure for your project. You are free to organize any additional internal folder structure as required by the project. 

```
.
├── docs                    # Documentation files
│   ├── contract            # Team contract
│   ├── proposal            # Project proposal 
│   ├── design              # UI mocks
│   ├── minutes             # Minutes from team meetings
│   ├── logs                # Team and individual Logs
│   └── ...          
├── src                     # Source files (alternatively `app`)
├── tests                   # Automated tests 
├── utils                   # Utility files
└── README.md
```

Please use a branching workflow, and once an item is ready, do remember to issue a PR, review, and merge it into the master branch.
Be sure to keep your docs and README.md up-to-date.

## Conventional Commits
Moving forward, we should use convential commits. As this is the industry standard of writing commit messages. More info can be found on [conventionalcommits.org](https://www.conventionalcommits.org/en/v1.0.0/)

Essentially, this is what they are:

```bash
feat: add user login form
fix: correct navbar alignment on mobile
docs: update README with project instructions
style: format code using Prettier
refactor: restructure API call logic
test: add unit test for login validation
chore: update dependencies
perf: improve image load time
```
* * *

### What each type means

- **feat** – A new feature or significant addition
- **fix** – A bug fix or error correction
- **docs** – Documentation-only changes (README, comments, etc.)
- **style** – Code formatting, spacing, or stylistic fixes (no logic changes)
- **refactor** – Code restructuring/refining that doesn't add features or fix bugs
- **test** – Adding or updating tests (unit, integration, etc.)
- **chore** – Routine tasks (e.g., dependency updates, config changes)
- **perf** – Performance improvements (e.g., faster loading, optimized code)

* * *

### Optional Scope

A scope is just a way to categorize the commit by its feature or module. Just written in parentheses right after the type.

**Example:**

```
fix(setup): fix typo in setup script
```
Here, `setup`  would be the scope, it’s just helpful to indicate what exactly has changed. Although for that example, adding `setup` would not be necessary as it's quite clear what is changing.
