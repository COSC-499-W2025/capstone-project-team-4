# CLI Documentation

# Mining Digital Work Artifacts — CLI Documentation

A command-line tool for analyzing software projects, extracting metadata, measuring code complexity, ranking contributions, identifying skills, and generating resume-ready artifacts.

---


# Available Commands

| Command               | Description                                                                                       |
|----------------------|---------------------------------------------------------------------------------------------------|
| **`menu`**           | Interactive menu for all features (recommended for most users)                                     |
| **`analyze-project`**| Full project analysis: metadata, complexity, skills, contributors, resume                          |
| **`browse`**         | Browse previously generated outputs                                                                |
| **`delete-output`**  | Delete specific project analysis outputs                                                           |
| **`status`**         | Show current consent & configuration                                                               |
| **`consent`**        | Manage user consent and external-processing permissions                                            |
| **`info`**           | Show list of commands                                                                              |
| **`summarize`**      | Show top-ranked projects from the internal database                                                |
| **`rank-contributions`** | Rank contributor’s impact inside a Git project                                                 |
| **`rank-projects`**  | Rank projects for a contributor from logged history                                                |
| **`skill-timeline`** | Show chronological timeline of skills for a project                                                |

---

# 1. Interactive Menu (Recommended)

### Usage
```python -m src.main menu```


### Description
A user-friendly interface to access all major features:

- Analyze a project  
- Summarize projects  
- Browse outputs  
- Rank contributions  
- Rank projects  
- Skill timeline  
- Delete outputs  
- Consent management  
- Info screen  

If consent has **not been granted**, the menu will **prompt the user to grant it** before continuing.

### Menu options expanded
```
[1] Analyze a Project: Will prompt user to insert project directory or zip path and ask if you want a full file list (metadata.json) 
[2] Summarize top ranked projects: Will prompt user to seelct one of the sorting methods for projects ie complexity, contributions, skills etc. Default is comprehensive. The user can also select how many projects to display (0-N)
[3] Browse previous outputs: Will prompt user whether to show raw json instead or pretty view. Pretty view will have the user type a project number [1-N] before showing the timestamps of each output. The user can select it to view more
[4] Rank Contributions within a project: Will prompt the user to insert a path to a project with a .git folder. The user must insert their email or name, the user must use that same email/name to retrieve their results for ranking later.
[5] Rank projects for a contributor (from log): Will prompt user to input username or email (use the one you used for [4]) to retrieve a list of projects and your contributions within those projects.
[6] Show skill timeline for latest analysis: Will prompt user to input path directory for latest analysis or folder name. This will return a skill timeline of the analysis
[7] Delete a generated output: Will prompt the user to select a output directory with blank being the default ./outputs dir. The user can select the project with 1-9 and delete a specific timestamp
[8] Show status / manage consent: will show the consent json output and ask the user if they would like to change consent settings, the user is then asked if they grant consent and if not, will be asked if they want to revoke consent. External services is also asked.
[9] Info: Shows a list of commands in its raw CLI form that can be ran outside of the menu, running python -m src.main --help also gives a command list. 
```

Menu layout example:

<img width="485" height="325" alt="image" src="https://github.com/user-attachments/assets/92074338-a7b0-42fd-a1c5-f070240023c8" />



# 2. Analyze Project (Main Command)

**Usage:** `python -m src.main analyze-project [OPTIONS] PATH` 

**Description:** Comprehensive project analysis that generates multiple JSON outputs including metadata, code complexity, contributor analysis, skill extraction, and resume items. This is the primary command for full project analysis.

**Arguments:**

- `PATH` - Path to project directory or ZIP file (required)

**Options:**

- `--include-files/--no-include-files` - Include full file list in metadata (default: True)
- `--out, -o PATH` - Output directory (default: ./outputs)

**Examples:**

```bash
# Analyze a project directory
python -m src.main analyze-project /path/to/project

# Analyze a ZIP file
python -m src.main analyze-project project.zip

# Exclude file list from output
python -m src.main analyze-project /path/to/project --no-include-files

# Specify custom output directory
python -m src.main analyze-project project.zip --out /custom/output
```

**Generated Outputs:**
The command creates a timestamped directory with the following JSON files:

- `metadata.json` - Project metadata, file statistics, and file list
- `complexity.json` - Code complexity metrics for functions
- `contributors.json` - Contributor analysis and statistics
- `skill_extract.json` - Extracted skills categorized by type
- `skill_insights.json` - Secondary skill analysis with detailed insights
- `resume_item.json` - Generated resume-worthy project description

**Sample Output:**

<img width="1629" height="199" alt="image" src="https://github.com/user-attachments/assets/090be34c-2802-4897-8bbe-c529f79f76f7" />

---

# 3. Browse Analyzed Projects

**Usage:** `python -m src.main browse [OPTIONS]`


### Description
Interactive viewer:

1. Select a project  
2. Select timestamp  
3. Select output file  
4. View pretty JSON or raw JSON  

### Options
- `--raw` (show raw JSON)
- `--out PATH` (set outputs folder)


**Examples:**

```bash
# Browse default outputs directory
python -m src.main browse

# Browse custom outputs directory
python -m src.main browse --out /custom/outputs

# View raw JSON without formatting
python -m src.main browse --raw
```

**Interactive Flow:**

1. Select a project from the list
2. Select a timestamp (analysis run)
3. Select a JSON file to view
4. View formatted or raw JSON output

---

# 4. Delete Project Outputs

**Usage:** `python -m src.main delete-output [OPTIONS]`


### Description
Selects a project -> timestamp -> confirms deletion.  
Deletes only analysis output, **never the original project files**.

### Options
- `--out PATH`

**Examples:**

```bash
# Delete from default outputs directory
python -m src.main delete-output

# Delete from custom outputs directory
python -m src.main delete-output --out /custom/outputs
```

**Interactive Flow:**

1. Select a project
2. Select a timestamp to delete
3. Confirm deletion by typing 'yes'

---

# 5. Status Check

**Usage:** `python -m src.main status`

### Description
Shows:

```json
{
  "consent_granted": true,
  "external_allowed": false,
  "external_last_notice_version": 1
}

```

**Example:**

```bash
python -m src.main status
```

**Sample Output:**

```json
{
  "consent_granted": true,
  "external_allowed": false,
  "external_last_notice_version": 0
}
```

---

# 6. Consent Management

**Usage:** `python -m src.main consent [OPTIONS]`

**Description:** Manage user consent for data processing and external API usage. Required before running analysis commands.

### Options
- `--grant`
- `--revoke`
- `--external`
- `--no-external`

Each change automatically increments `external_last_notice_version`.

**Examples:**

```bash
# Grant consent to process files
python -m src.main consent --grant

# Revoke consent
python -m src.main consent --revoke

# Allow external API usage
python -m src.main consent --external

# Revoke external API usage
python -m src.main consent --no-external

# Combine options
python -m src.main consent --grant --external
```

**Sample Output:**

```
Consent granted.
External allowed = True

Current configuration:
{'consent_granted': True, 'external_allowed': True, 'external_last_notice_version': 0}
```

---

# 7. Info

### Usage
```python -m src.main info```

### Description
Displays help text and all available commands.



# 8. Summarize Projects

**Usage:** `python -m src.main summarize [OPTIONS]`

**Description:** Shows top projects from the internal database with analysis details.


### Options
- `--sort` = complexity, contributions, skills, lines_of_code, file_count, recent, comprehensive  
- `--limit`
- 
**Examples:**

```bash
# Show top 10 projects with comprehensive ranking
python -m src.main summarize

# Show top 5 most complex projects
python -m src.main summarize --sort complexity --limit 5

# Show top 20 projects by lines of code
python -m src.main summarize --sort lines_of_code --limit 20

# Show most recently analyzed projects
python -m src.main summarize --sort recent
```

---

# 9. Rank Contributions

**Usage:** 
`python -m src.main rank-contributions <PROJECT> --name <name>`
or 
`python -m src.main rank-contributions <PROJECT> --email <email>`

**Description:** 
Analyze and rank a specific contributor's impact within a Git project based on commits, lines changed, and files touched. **The username or email you used must be consistent as you will need to use it again for [10] Rank Projects.**
This command must be ran before running [Rank Projects]

Calculates a contributor score per project using:
* commits
* lines added/deleted
* files touched

Formula for contribution store is 
```
contribution_score =
    (commits * weight_commits)
    + (total_lines_changed * weight_lines_changed)
    + (files_touched * weight_files_touched)
```

Also logs the result to `contributions.json`.

**Arguments:**

- `PROJECT` - Path to Git project directory (required)

**Options:**

- `--name NAME` - Contributor name (required if --email not provided)
- `--email EMAIL` - Contributor email (required if --name not provided)

**Examples:**

```bash
# Rank contributions by name
python -m src.main rank-contributions /path/to/project --name "John Doe"

# Rank contributions by email
python -m src.main rank-contributions /path/to/project --email "john@example.com"
```

**Sample Output:**

```
Contribution Summary
-----------------------
Project: my-project
Commits: 45
Lines Added: 2,345
Lines Deleted: 1,234
Files Touched: 67
Contribution Score: 87.5
```

---

### 10. Rank Projects

**Usage:** 
`python -m src.main rank-projects --name <NAME>`
or 
`python -m src.main rank-projects --email <EMAIL>`
**Description:** Display all analyzed projects for a contributor, ranked by contribution score based on the saved contribution log. **Must use same username/email as one used in [Rank Contributions]**

**Options:**

- `--name NAME` - Contributor name (required if --email not provided)
- `--email EMAIL` - Contributor email (required if --name not provided)
- `--top-n N` - Show only top N projects

**Examples:**

```bash
# Show all projects for contributor by name
python -m src.main rank-projects --name "John Doe"

# Show all projects by email
python -m src.main rank-projects --email "john@example.com"

# Show top 5 projects
python -m src.main rank-projects --name "John Doe" --top-n 5
```

**Sample Output:**

```
Projects ranked by contribution score:

1. project-alpha
   Score: 95.50 | Commits: 123 | Lines changed: +4567/-2345 (total 6912) | Files touched: 89

2. project-beta
   Score: 87.25 | Commits: 98 | Lines changed: +3456/-1234 (total 4690) | Files touched: 56
```

---

### 11. Skill Timeline

**Usage:** `python -m src.main skill-timeline PROJECT_PATH`

### Description
Shows chronological skill usage from the most recent project analysis.  
Uses database-backed skill tracking

**Arguments:**

- `PROJECT_PATH` - Path to project directory or folder name in outputs (required)

**Examples:**

```bash
# View skill timeline for a project
python -m src.main skill-timeline /path/to/project

# View skill timeline using folder name
python -m src.main skill-timeline my-project
```

**Sample Output:**

```
📌 Skill Timeline (Chronological)

📅 2025-01-15
   - Python (15)
   - REST API Design (8)
   - Database Management (5)

📅 2025-02-20
   - JavaScript (22)
   - React (18)
   - CSS (12)
```

---


# Database & Storage

### SQLite Database

The CLI uses a SQLite database to store:

- Project metadata and analysis results
- File information and statistics
- Code complexity metrics
- Contributor data
- Skill extraction results
- Resume items
- Contribution logs

### Output Directory Structure

```
outputs/
├── project-name/
│   ├── 2025-12-07_14-30-45/
│   │   ├── metadata.json
│   │   ├── complexity.json
│   │   ├── contributors.json
│   │   ├── skill_extract.json
│   │   ├── skill_insights.json
│   │   └── resume_item.json
│   └── 2025-12-08_10-15-20/
│       └── ...
└── another-project/
    └── ...
```

---

## Configuration Files

The CLI creates and manages configuration files in `src/data/`:

- `config.json` - User preferences and settings
- `config.db` - SQLite database for all analysis data
- `consent_log.json` - Log of user consent decisions
- `project_contributions_log.json` - Contribution tracking across projects

---

## Output File Descriptions

### metadata.json

Contains comprehensive project metadata:

- Project statistics (file counts, total size, languages used)
- File list with paths, types, sizes, and timestamps
- Project root directory information

### complexity.json

Code complexity analysis:

- Function-level complexity metrics
- Cyclomatic complexity scores
- Maintainability indicators

### contributors.json

Git contributor analysis:

- Commit counts per contributor
- Lines added/deleted per contributor
- Files touched by each contributor
- Contribution percentages

### skill_extract.json

Extracted technical skills:

- Detected programming languages
- Identified frameworks and libraries
- Categorized skills by type
- Proficiency assessments

### skill_insights.json

Secondary skill analysis:

- Detailed skill patterns
- Technology stack insights
- Advanced skill mappings

### resume_item.json

Generated resume-worthy project description:

- Professional project summary
- Key technologies and achievements
- Contribution highlights
- Quantified impact metrics

---

## Requirements

### System Requirements

- Python 3.11.0 or higher
- Git (for contribution analysis)
- 100MB+ free disk space for database and outputs

### Setup Requirements

- Python virtual environment (recommended)
- All dependencies from `requirements.txt`
- User consent must be granted before processing files

### Optional Requirements

- Docker & Docker Compose (for containerized deployment)
- External API keys (if using external services)

---

## Best Practices

1. **Grant Consent First**: Always run `python -m src.main consent --grant` before analysis
2. **Use Virtual Environment**: Activate your virtual environment before running commands
3. **Regular Cleanup**: Use `delete-output` to remove old analysis results
4. **Consistent Naming**: Use consistent contributor names/emails across commands for accurate tracking
5. **Review Outputs**: Use `browse` command to review analysis results interactively
6. **Aggregate Insights**: Run `aggregate-outputs` periodically to generate summary dashboards

---

## Troubleshooting

### Common Issues

**"Consent not granted" error:**

```bash
python -m src.main consent --grant
```

**"outputs folder not found" error:**

```bash
# Create the outputs directory
mkdir outputs
```

**Database errors:**

```bash
# The database is automatically initialized on first run
# If issues persist, delete src/data/config.db and restart
```

**Git repository not found:**

```bash
# Ensure the project directory contains a .git folder
# For rank-contributions command
```

---

## Examples Workflow

### Running Menu Workflow
```bash
# 1. Activate environment
.\.venv\Scripts\activate

# 2. Run Menu
python -m src.main menu

# 3. Consent
prompt with :
Consent is required to use the interactive menu.
Grant consent now? [Y/n]:
Type y

# 4. Run Menu again
python -m src.main menu

# 5. Choose option: [1-9] or [q] to quit
========================================
 [1] Analyze a project
 [2] Summarize top ranked projects
 [3] Browse previous outputs
 [4] Rank contributions within a project
 [5] Rank projects for a contributor (from log)
 [6] Show skill timeline for latest analysis
 [7] Delete a generated output
 [8] Show status / manage consent
 [9] Info (list commands)
 [q] Quit



```


### Complete Analysis Workflow

```bash
## Examples Workflow

### Complete Analysis Workflow

```bash
# 1. Grant consent
python -m src.main consent --grant

# 2. Analyze a project
python -m src.main analyze-project /path/to/project

# 3. Browse results
python -m src.main browse

# 4. Rank contributions
python -m src.main rank-contributions /path/to/project --name "Your Name"

# 5. View all your projects
python -m src.main rank-projects --name "Your Name"

# 6. Generate summary dashboard
python -m src.main aggregate-outputs --out dashboard.md
```

### Quick Analysis

```bash
# One-command full analysis
python -m src.main analyze-project my-project.zip
```

### Contributor Portfolio

```bash
# Analyze multiple projects
python -m src.main analyze-project project1/
python -m src.main analyze-project project2/
python -m src.main analyze-project project3/

# Rank contributions across all analyzed projects
python -m src.main rank-projects --name "Your Name"

# Show top contribution-heavy projects
python -m src.main summarize --sort contributions --limit 5

```

### Quick Analysis

```bash
# One-command full analysis
python -m src.main analyze-project my-project.zip
```

### Contributor Portfolio

```bash
# Analyze multiple projects
python -m src.main analyze-project project1/
python -m src.main analyze-project project2/
python -m src.main analyze-project project3/

# Generate ranked portfolio
python -m src.main rank-projects --name "Your Name"
python -m src.main summarize --sort contributions
```
